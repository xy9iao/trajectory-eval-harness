"""Offline tests for the MCP tool layer — pure lookups + tool registration. No subprocess, no API."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mcp.server import (  # noqa: E402
    _lookup_account,
    _lookup_order,
    _lookup_policy,
    _lookup_ticket_history,
    mcp,
)


def test_account_found_and_not_found():
    assert _lookup_account("u_1001")["status"] == "locked"
    assert _lookup_account("u_2002")["flags"] == ["abuse_warned"]
    assert _lookup_account("u_9999") == {"found": False, "user_id": "u_9999"}


def test_order_duplicate_vs_single_charge():
    dup = _lookup_order("10231")
    assert dup["duplicate_charge"] is True and dup["charge_count"] == 2
    single = _lookup_order("10199")
    assert single["duplicate_charge"] is False and single["charge_count"] == 1
    assert _lookup_order("99999")["found"] is False


def test_ticket_history():
    assert _lookup_ticket_history("u_2002")["tickets"][0]["resolution"] == "warned"
    assert _lookup_ticket_history("u_1000")["found"] is True
    assert _lookup_ticket_history("nobody")["tickets"] == []


def test_policy_lookup_and_aliases():
    assert "90 days" in _lookup_policy("refund")["text"]
    assert _lookup_policy("lockout")["topic"] == "account_access"  # alias resolves
    assert _lookup_policy("nonsense")["found"] is False


def test_four_tools_registered_with_schemas():
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {"get_account", "get_order", "get_ticket_history", "get_policy"}
    # each tool exposes a typed input schema (untrusted-arg validation)
    for t in tools:
        assert t.inputSchema.get("type") == "object"
