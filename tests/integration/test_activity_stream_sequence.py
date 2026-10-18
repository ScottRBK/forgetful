"""Integration tests for SSE sequence numbers on the activity stream.

``seq`` is the client's gap detector, so a stream opened with entity_type/action
filters must number only the events it receives: an event excluded by a filter is
not a gap, while a matching event dropped because the subscriber queue is full is.
"""

import asyncio
import json
import re
from types import SimpleNamespace
from uuid import uuid4

from fastmcp import FastMCP
from starlette.requests import Request

from app.events import EventBus
from app.models.activity_models import ActionType, ActivityEvent, EntityType
from app.routes.api import activity as activity_routes


def _event(user_id, entity_id, action, entity_type=EntityType.MEMORY):
    return ActivityEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        snapshot={"id": entity_id},
        user_id=str(user_id),
    )


async def _read_sse(query_string: bytes, emit_plan, expected_events: int):
    """Open the real SSE route, run ``emit_plan(bus, user_id)``, return events seen."""
    mcp = FastMCP("activity-stream-seq")
    bus = EventBus()
    mcp.event_bus = bus
    user_id = uuid4()

    async def fake_get_user(request, _mcp):
        return SimpleNamespace(id=user_id)

    activity_routes.register(mcp)
    route = next(
        r for r in mcp.http_app().routes
        if getattr(r, "path", None) == "/api/v1/activity/stream"
    )

    original = activity_routes.get_user_from_request
    activity_routes.get_user_from_request = fake_get_user
    disconnect = asyncio.Event()
    chunks: list[bytes] = []
    stream_task = None
    try:
        async def receive():
            await disconnect.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            if message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/activity/stream",
            "raw_path": b"/api/v1/activity/stream",
            "query_string": query_string,
            "headers": [],
            "server": ("test", 80),
            "client": ("127.0.0.1", 1234),
        }
        response = await route.endpoint(Request(scope, receive))
        stream_task = asyncio.create_task(response(scope, receive, send))

        for _ in range(200):
            if bus.stream_subscriber_count(str(user_id)) == 1:
                break
            await asyncio.sleep(0.01)
        assert bus.stream_subscriber_count(str(user_id)) == 1, "stream never subscribed"

        await emit_plan(bus, user_id)

        def seen():
            text = b"".join(chunks).decode()
            return [json.loads(m) for m in re.findall(r"^data: (.*)$", text, flags=re.M)]

        for _ in range(300):
            if len(seen()) >= expected_events:
                break
            await asyncio.sleep(0.01)
        return seen()
    finally:
        activity_routes.get_user_from_request = original
        disconnect.set()
        if stream_task is not None:
            try:
                await asyncio.wait_for(stream_task, timeout=2)
            except (TimeoutError, asyncio.CancelledError, Exception):
                stream_task.cancel()


async def _created_updated_created(bus, user_id):
    await bus.emit(_event(user_id, 1, ActionType.CREATED))
    await bus.emit(_event(user_id, 1, ActionType.UPDATED))
    await bus.emit(_event(user_id, 2, ActionType.CREATED))


def _gaps(events):
    """Client-side gap detection as documented for the stream endpoint."""
    seqs = [e["seq"] for e in events]
    return [(a, b) for a, b in zip(seqs, seqs[1:], strict=False) if b != a + 1]


class TestStreamSequenceNumbers:
    async def test_unfiltered_stream_sees_every_sequence_number(self):
        events = await _read_sse(b"", _created_updated_created, expected_events=3)
        assert [e["seq"] for e in events] == [1, 2, 3]

    async def test_filtered_stream_does_not_signal_false_gap(self):
        events = await _read_sse(
            b"entity_type=memory&action=created", _created_updated_created, expected_events=2,
        )
        assert [(e["action"], e["entity_id"]) for e in events] == [
            ("created", 1),
            ("created", 2),
        ]
        assert _gaps(events) == [], [e["seq"] for e in events]
        assert [e["seq"] for e in events] == [1, 2]

    async def test_entity_type_filter_alone_is_gap_free(self):
        async def plan(bus, user_id):
            await bus.emit(_event(user_id, 1, ActionType.CREATED, EntityType.PROJECT))
            await bus.emit(_event(user_id, 1, ActionType.CREATED))
            await bus.emit(_event(user_id, 2, ActionType.CREATED, EntityType.PROJECT))
            await bus.emit(_event(user_id, 2, ActionType.UPDATED))

        events = await _read_sse(b"entity_type=memory", plan, expected_events=2)
        assert [(e["entity_type"], e["action"]) for e in events] == [
            ("memory", "created"),
            ("memory", "updated"),
        ]
        assert [e["seq"] for e in events] == [1, 2]


class TestEventBusStreamFilters:
    async def _subscribe(self, bus, user_id, **filters):
        received: list[dict] = []

        async def consume():
            async for event_dict in bus.subscribe_stream(user_id, **filters):
                received.append(event_dict)

        task = asyncio.create_task(consume())
        expected = bus.stream_subscriber_count(str(user_id)) + 1
        for _ in range(200):
            if bus.stream_subscriber_count(str(user_id)) == expected:
                break
            await asyncio.sleep(0.01)
        return task, received

    async def _settle(self):
        await asyncio.sleep(0.05)

    async def test_filtered_subscribers_number_only_matching_events(self):
        bus = EventBus()
        user_id = uuid4()
        everything_task, everything = await self._subscribe(bus, user_id)
        created_task, created = await self._subscribe(bus, user_id, action="created")
        project_task, projects = await self._subscribe(bus, user_id, entity_type="project")
        try:
            await bus.emit(_event(user_id, 1, ActionType.CREATED))
            await bus.emit(_event(user_id, 1, ActionType.UPDATED))
            await bus.emit(_event(user_id, 2, ActionType.CREATED, EntityType.PROJECT))
            await bus.emit(_event(user_id, 3, ActionType.CREATED))
            await self._settle()
        finally:
            for task in (everything_task, created_task, project_task):
                task.cancel()

        assert [e["seq"] for e in everything] == [1, 2, 3, 4]
        assert [e["entity_id"] for e in created] == [1, 2, 3]
        assert [e["seq"] for e in created] == [1, 2, 3]
        assert [e["seq"] for e in projects] == [1]
        # the unfiltered, per-user counter is unchanged
        assert bus.get_current_seq(str(user_id)) == 4

    async def test_subscribers_with_the_same_filter_share_sequence_numbers(self):
        bus = EventBus()
        user_id = uuid4()
        first_task, first = await self._subscribe(bus, user_id, action="created")
        second_task, second = await self._subscribe(bus, user_id, action="created")
        try:
            await bus.emit(_event(user_id, 1, ActionType.UPDATED))
            await bus.emit(_event(user_id, 1, ActionType.CREATED))
            await bus.emit(_event(user_id, 2, ActionType.CREATED))
            await self._settle()
        finally:
            first_task.cancel()
            second_task.cancel()

        assert [e["seq"] for e in first] == [1, 2]
        assert [e["seq"] for e in second] == [1, 2]

    async def test_dropped_matching_event_is_still_visible_as_a_gap(self):
        bus = EventBus(max_queue_size=2)
        user_id = uuid4()
        task, received = await self._subscribe(bus, user_id, action="created")
        try:
            # No await point is reached between these emits, so the consumer
            # cannot drain the queue: the third matching event is dropped.
            await bus.emit(_event(user_id, 1, ActionType.CREATED))
            await bus.emit(_event(user_id, 2, ActionType.CREATED))
            await bus.emit(_event(user_id, 2, ActionType.UPDATED))  # filtered out
            await bus.emit(_event(user_id, 3, ActionType.CREATED))  # queue full: dropped
            await self._settle()
            await bus.emit(_event(user_id, 4, ActionType.CREATED))
            await self._settle()
        finally:
            task.cancel()

        assert [e["entity_id"] for e in received] == [1, 2, 4]
        assert [e["seq"] for e in received] == [1, 2, 4]
        assert _gaps(received) == [(2, 4)]
