"""Plan registration and runner contracts; candidate-only, not baseline collection."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.config.plan_plugin import load_plan_plugin
from app.exceptions import PlanPluginRejectedError, PlanPluginUnavailableError
from app.models.plan_models import Plan, PlanCreate
from app.models.plan_plugin_models import PlanSavedRequest, PlanWriteRequest
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.plan_plugin_protocol import PlanPlugin
from app.services.plan_write_plugin_service import PlanWritePluginService


def write_request():
    data = PlanCreate(title="Plan runtime fixture", project_id=1, source_files=["synthetic.py"])
    return PlanWriteRequest(
        operation="create", user_id=uuid4(), submitted=data.model_copy(deep=True),
        previous=None, proposed=data.model_copy(deep=True),
    )


def saved_request():
    request = write_request()
    saved = Plan(**request.proposed.model_dump(), id=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    return PlanSavedRequest(operation="create", user_id=request.user_id, saved=saved, previous=None)


async def allow(request):
    return WriteDecision(outcome="allow")


@pytest.mark.parametrize("phase", ["before_save", "after_save"])
@pytest.mark.parametrize("handlers", [None, [], {"claim": allow}, {"create": lambda request: None}])
def test_registration_rejects_invalid_mapping(phase, handlers):
    with pytest.raises(ValueError):
        PlanPlugin(**{phase: handlers})


def test_registration_requires_single_context_and_freezes_a_copy():
    async def wrong(first, second):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="one context"):
        PlanPlugin(before_save={"create": wrong})
    mapping = {"create": allow}
    plugin = PlanPlugin(before_save=mapping)
    mapping.clear()
    assert plugin.before_save["create"] is allow
    with pytest.raises(TypeError):
        plugin.before_save["delete"] = allow


@pytest.mark.parametrize("reference", ["bad", ":handler", "bad-module:handler", "good:a.b"])
def test_loader_rejects_invalid_reference(reference):
    with pytest.raises(ValueError, match="module:object"):
        load_plan_plugin(SimpleNamespace(PLAN_WRITE_PLUGIN=reference))


def test_loader_disabled_and_wrong_registration(monkeypatch):
    assert load_plan_plugin(SimpleNamespace(PLAN_WRITE_PLUGIN=" ")) is None
    monkeypatch.setattr("app.config.plan_plugin.importlib.import_module", lambda name: SimpleNamespace(plugin=object()))
    with pytest.raises(ValueError, match="PlanPlugin registration"):
        load_plan_plugin(SimpleNamespace(PLAN_WRITE_PLUGIN="synthetic:plugin"))


@pytest.mark.asyncio
async def test_unregistered_operation_and_detached_before_context():
    request = write_request()
    empty = PlanWritePluginService(PlanPlugin())
    assert await empty.before_save(request) == []
    assert await empty.after_save(saved_request()) == []

    async def mutate(context):
        context.submitted.title = "Mutated"
        context.proposed.source_files.append("not-persisted.py")
        return WriteDecision(outcome="allow")

    runner = PlanWritePluginService(PlanPlugin(before_save={"create": mutate}))
    assert await runner.before_save(request) == []
    assert request.submitted.title == "Plan runtime fixture"
    assert request.proposed.source_files == ["synthetic.py"]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("outcome", ["allow", "warn", "reject"])
async def test_before_decision_modes(mode, outcome):
    async def decide(context):
        return WriteDecision(outcome=outcome, message="Synthetic policy message", code="SYNTHETIC")

    runner = PlanWritePluginService(PlanPlugin(before_save={"create": decide}), mode=mode)
    if mode == "enforce" and outcome == "reject":
        with pytest.raises(PlanPluginRejectedError, match="Synthetic policy message"):
            await runner.before_save(write_request())
    else:
        warnings = await runner.before_save(write_request())
        assert len(warnings) == (outcome != "allow")
        if warnings:
            assert warnings[0].message == "Synthetic policy message"
            assert warnings[0].outcome == "warn"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["exception", "malformed", "timeout"])
async def test_before_failure_is_sanitized(mode, failure, caplog):
    async def fail(context):
        if failure == "exception":
            raise RuntimeError("PRIVATE_TEST_SENTINEL")
        if failure == "timeout":
            await asyncio.sleep(60)
        return {"outcome": "warn", "message": "", "secret": "PRIVATE_TEST_SENTINEL"}

    runner = PlanWritePluginService(PlanPlugin(before_save={"create": fail}), mode=mode, timeout_seconds=0.001)
    if mode == "enforce":
        with pytest.raises(PlanPluginUnavailableError, match="Plan Write Plugin unavailable") as error:
            await runner.before_save(write_request())
        assert "PRIVATE_TEST_SENTINEL" not in str(error.value)
    else:
        warnings = await runner.before_save(write_request())
        assert warnings[0].code == "PLAN_PLUGIN_UNAVAILABLE"
        assert "PRIVATE_TEST_SENTINEL" not in warnings[0].message
    assert "PRIVATE_TEST_SENTINEL" not in caplog.text


@pytest.mark.asyncio
async def test_before_cancellation_propagates():
    async def cancel(context):
        raise asyncio.CancelledError

    runner = PlanWritePluginService(PlanPlugin(before_save={"create": cancel}), mode="warn")
    with pytest.raises(asyncio.CancelledError):
        await runner.before_save(write_request())


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["exception", "malformed", "timeout", "child_cancel"])
async def test_after_failure_is_advisory(failure, caplog):
    async def fail(context):
        if failure == "exception":
            raise RuntimeError("PRIVATE_TEST_SENTINEL")
        if failure == "child_cancel":
            raise asyncio.CancelledError
        if failure == "timeout":
            await asyncio.sleep(60)
        return {"message": "", "secret": "PRIVATE_TEST_SENTINEL"}

    runner = PlanWritePluginService(PlanPlugin(after_save={"create": fail}), timeout_seconds=0.001)
    warnings = await runner.after_save(saved_request())
    assert warnings[0].code == "PLAN_PLUGIN_AFTER_SAVE_UNAVAILABLE"
    assert "PRIVATE_TEST_SENTINEL" not in warnings[0].message
    assert "PRIVATE_TEST_SENTINEL" not in caplog.text


@pytest.mark.asyncio
async def test_after_request_cancellation_propagates():
    entered = asyncio.Event()

    async def wait(context):
        entered.set()
        await asyncio.Event().wait()

    runner = PlanWritePluginService(PlanPlugin(after_save={"create": wait}))
    task = asyncio.create_task(runner.after_save(saved_request()))
    await asyncio.wait_for(entered.wait(), timeout=10)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_after_warning_and_detached_saved_snapshot():
    request = saved_request()

    async def warn(context):
        context.saved.title = "Mutated"
        return PluginWarning(message="Synthetic after warning", code="AFTER")

    runner = PlanWritePluginService(PlanPlugin(after_save={"create": warn}))
    warnings = await runner.after_save(request)
    assert warnings[0].code == "AFTER"
    assert request.saved.title == "Plan runtime fixture"
