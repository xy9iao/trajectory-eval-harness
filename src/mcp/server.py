"""Minimal MCP server: 4 read-only triage tools over mock data (GUIDE §5).

Security posture (the talking point): tool arguments come from an LLM, not the user, so they are
treated as **untrusted**. Every tool is:
  * read-only — no side effects, never mutates state (writes happen behind the HITL gate, not here);
  * strictly typed — FastMCP derives a JSON schema from the signature and validates inputs;
so even a prompt-injected ticket cannot make a *read* tool do something unsafe.

Run as a stdio server (what the agent's MCP client spawns):  `python -m src.mcp.server`

The data-access logic lives in plain `_lookup_*` functions (pure, unit-testable without the MCP
transport); the @mcp.tool wrappers only handle protocol registration. Logic vs. protocol, separated.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("triage-tools")

# --------------------------------------------------------------------------------------
# Mock data — kept internally consistent with the labels/notes in data/eval_set.jsonl.
# order 10231 -> double charge (refundable); u_1001 locked; u_2002 abuse_warned (+ history);
# u_9999 absent -> not_found. Policies cover refund / account_access / abuse / billing.
# --------------------------------------------------------------------------------------
_ACCOUNTS: dict[str, dict] = {
    "u_1000": {"plan": "pro", "status": "active", "signup_date": "2023-01-15", "flags": []},
    "u_1001": {"plan": "free", "status": "locked", "signup_date": "2022-07-02", "flags": ["login_locked"]},
    "u_2002": {"plan": "pro", "status": "active", "signup_date": "2021-03-10", "flags": ["abuse_warned"]},
    "u_3003": {"plan": "free", "status": "active", "signup_date": "2024-05-20", "flags": []},
}

_ORDERS: dict[str, dict] = {
    # Two identical charge events => duplicate charge, refundable within policy.
    "10231": {
        "user_id": "u_1000", "amount": 49.99, "currency": "USD", "date": "2026-05-01",
        "charges": [
            {"charge_id": "ch_1a", "amount": 49.99, "ts": "2026-05-01T10:00:00Z"},
            {"charge_id": "ch_1b", "amount": 49.99, "ts": "2026-05-01T10:00:05Z"},
        ],
        "refund_status": "none",
    },
    # Single charge => no duplicate; cannot auto-refund without further evidence.
    "10199": {
        "user_id": "u_3003", "amount": 19.99, "currency": "USD", "date": "2026-04-15",
        "charges": [{"charge_id": "ch_9", "amount": 19.99, "ts": "2026-04-15T08:00:00Z"}],
        "refund_status": "none",
    },
}

_TICKET_HISTORY: dict[str, list[dict]] = {
    "u_1000": [
        {"ticket_id": "t_900", "summary": "Double charge on order 10231 (earlier occurrence)", "resolution": "refunded"},
    ],
    "u_2002": [
        {"ticket_id": "t_500", "summary": "Harassment report — user warned", "resolution": "warned"},
    ],
}

_POLICIES: dict[str, str] = {
    "refund": (
        "Duplicate charges are refundable within 90 days when two or more identical charge events "
        "exist for a single order. A single charge requires documented evidence of error before any "
        "refund; absent that, escalate rather than auto-refund. Annual plans: refunds are prorated "
        "within 30 days of renewal."
    ),
    "account_access": (
        "Any account-access change (unlock, password/email reset) requires identity verification "
        "through the secure flow. Triage must ESCALATE to that flow and must never change access "
        "directly."
    ),
    "abuse": (
        "First-time or low-severity abuse reports are ESCALATED for human review. A ban requires a "
        "repeated violation after a prior warning — i.e. the reported account already carries an "
        "'abuse_warned' flag."
    ),
    "billing": (
        "General billing: charges post at renewal; disputes are handled via the refund policy. "
        "Informational billing questions are answered directly without an account action."
    ),
}

# Aliases so get_policy is forgiving about the LLM's topic phrasing.
_POLICY_ALIASES: dict[str, str] = {
    "refunds": "refund", "billing_refund": "refund", "duplicate_charge": "refund", "pricing": "billing",
    "plans": "billing", "account": "account_access", "access": "account_access", "login": "account_access",
    "lockout": "account_access", "ban": "abuse", "harassment": "abuse", "report": "abuse",
}


# ---------- pure data-access logic (unit-testable without MCP) ----------

def _lookup_account(user_id: str) -> dict:
    acct = _ACCOUNTS.get(user_id)
    if acct is None:
        return {"found": False, "user_id": user_id}
    return {"found": True, "user_id": user_id, **acct}


def _lookup_order(order_id: str) -> dict:
    order = _ORDERS.get(order_id)
    if order is None:
        return {"found": False, "order_id": order_id}
    n = len(order["charges"])
    return {"found": True, "order_id": order_id, "duplicate_charge": n > 1, "charge_count": n, **order}


def _lookup_ticket_history(user_id: str) -> dict:
    history = _TICKET_HISTORY.get(user_id, [])
    return {"found": bool(history), "user_id": user_id, "tickets": history}


def _lookup_policy(topic: str) -> dict:
    key = (topic or "").strip().lower().replace(" ", "_")
    key = _POLICY_ALIASES.get(key, key)
    text = _POLICIES.get(key)
    if text is None:
        return {"found": False, "topic": topic}
    return {"found": True, "topic": key, "text": text}


# ---------- MCP tool wrappers (protocol registration only) ----------

@mcp.tool()
def get_account(user_id: str) -> dict:
    """Look up an account by user_id. Returns plan, status, signup date, and flags. Read-only."""
    return _lookup_account(user_id)


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Look up an order by order_id. Returns amount, date, charge events, and refund status.

    `duplicate_charge` is True when more than one charge event exists for the order. Read-only.
    """
    return _lookup_order(order_id)


@mcp.tool()
def get_ticket_history(user_id: str) -> dict:
    """Return prior tickets and their resolutions for a user_id. Read-only."""
    return _lookup_ticket_history(user_id)


@mcp.tool()
def get_policy(topic: str) -> dict:
    """Return the relevant policy snippet for a topic (refund, account_access, abuse, billing). Read-only."""
    return _lookup_policy(topic)


if __name__ == "__main__":
    mcp.run()  # stdio transport
