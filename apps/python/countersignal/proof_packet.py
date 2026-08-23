"""Strict public-packet projection for permissioned live CounterSignal evidence."""

from __future__ import annotations

from typing import Any, Iterable

import audit
import countersignal as core
import permission


def live_audit_packet(
    experiment: core.Experiment, records: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Build a public audit packet and require permission proof for every live record.

    The private permission receipt itself is never exported. Only the boolean
    verification result, non-phone permission channel, and consent timestamp
    survive into the public packet.
    """
    items = [dict(record) for record in records]
    packet = audit.audit_packet(experiment, items, mode="live_redacted_ledger")
    by_call_id = {
        record.get("call_id"): record
        for record in items
        if isinstance(record.get("call_id"), str) and record.get("call_id")
    }

    for evidence in packet["evidence"]:
        if evidence.get("source") != "calle_live":
            continue
        record = by_call_id.get(evidence.get("call_id"))
        if record is None:
            raise ValueError("live evidence is missing its redacted source record")
        if record.get("permission_verified") is not True:
            raise ValueError("live evidence is missing affirmative permission proof")
        channel = record.get("permission_channel")
        if channel not in permission.ALLOWED_PERMISSION_CHANNELS:
            raise ValueError("live evidence has an invalid permission channel")
        consented_at = record.get("permission_consented_at")
        if not isinstance(consented_at, str) or not consented_at.strip():
            raise ValueError("live evidence is missing permission consent time")
        if evidence.get("recipient_binding_verified") is not True:
            raise ValueError("live evidence is not bound to the reviewed recipient")
        if evidence.get("bucket") in {"supporting", "disconfirming", "neutral"} and evidence.get("grounded") is not True:
            raise ValueError("answered live evidence is not transcript-grounded")

        evidence["permission_verified"] = True
        evidence["permission_channel"] = channel
        evidence["permission_consented_at"] = consented_at

    packet["live_proof_policy"] = {
        "permission_required": True,
        "recipient_binding_required": True,
        "answered_quote_grounding_required": True,
        "raw_permission_receipt_exported": False,
        "raw_phone_exported": False,
        "raw_transcript_exported": False,
    }
    return packet
