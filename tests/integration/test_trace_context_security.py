"""Guard the public trace parser used for FastMCP request metadata.

GHSA-mf5v-w3w3-f6cg: reject oversized input before regular-expression matching.
Use a small boundary input, not a CPU-heavy payload or an elapsed-time assertion.
"""

import pytest
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"


def test_trace_context_rejects_input_above_512_characters():
    # A future-version extension is otherwise valid; version 00 forbids extensions.
    traceparent = "01" + TRACEPARENT[2:] + "-" + "x" * 457
    propagator = TraceContextTextMapPropagator()

    context = propagator.extract({"traceparent": traceparent}, context=Context())

    assert not trace.get_current_span(context).get_span_context().is_valid


@pytest.mark.parametrize(
    "traceparent",
    [TRACEPARENT, "01" + TRACEPARENT[2:] + "-" + "x" * 456],
    ids=["ordinary-header", "512-character-future-version"],
)
def test_trace_context_preserves_valid_headers(traceparent):
    propagator = TraceContextTextMapPropagator()

    context = propagator.extract({"traceparent": traceparent}, context=Context())
    span_context = trace.get_current_span(context).get_span_context()

    assert span_context.is_valid
    assert span_context.is_remote
    assert span_context.trace_id == 0x0AF7651916CD43DD8448EB211C80319C
    assert span_context.span_id == 0xB7AD6B7169203331
    assert span_context.trace_flags.sampled
