"""Guard dnspython's public WKS record parser against unbounded allocation.

GHSA-vvf4-9x63-8xvv: service numbers must fit the DNS WKS bitmap.
65536 exceeds the valid range by one and keeps the old parser's allocation small.
"""

import dns.exception
import dns.rdata
import pytest


def test_wks_rejects_service_above_65535():
    record_text = "192.0.2.1 17 65536"

    with pytest.raises(dns.exception.SyntaxError):
        dns.rdata.from_text("IN", "WKS", record_text)


@pytest.mark.parametrize(
    "services", ["0 53", "65535"], ids=["ordinary-services", "maximum-service"],
)
def test_wks_preserves_valid_services_through_wire_format(services):
    record_text = f"192.0.2.1 17 {services}"

    record = dns.rdata.from_text("IN", "WKS", record_text)
    wire = record.to_wire()
    restored = dns.rdata.from_wire("IN", "WKS", wire, 0, len(wire))

    assert restored.to_text() == record_text
