"""Strict public-packet projection for permissioned live CounterSignal evidence."""

from __future__ import annotations

from typing import Any, Iterable

import audit
import countersignal as core
import permission


def live_audit_packet(
    experiment: core.Experiment, records: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Build a public audit packet from permissioned CALL-E evidence only.

    The private permission receipt itself is never exported. Interview permission
    is not treated as publication permission: real participant quote text is
    withheld from the public packet even after transcript grounding succeeds.
    """
    items = [dict(record) for record in records]
    if not items:
        raise ValueError("live proof requires at least one CALL-E live evidence record")
    non_live = [record for record in items if record.get("source") != "calle_live"]
    if non_live:
        raise ValueError("public live proof cannot mix non-live evidence records")

    packet = audit.audit_packet(experiment, items, mode="live_redacted_ledger")
    by_call_id = {
        record.get("call_id"): record
        for record in items
        if isinstance(record.get("call_id"), str) and record.get("call_id")
    }

    for evidence in packet["evidence"]:
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
        answered = evidence.get("bucket") in {"supporting", "disconfirming", "neutral"}
        if answered and evidence.get("grounded") is not True:
            raise ValueError("answered live evidence is not transcript-grounded")

        evidence["permission_verified"] = True
        evidence["permission_channel"] = channel
        evidence["permission_consented_at"] = consented_at
        evidence["grounding_verified_before_public_redaction"] = bool(evidence.get("grounded", False))
        evidence["quote"] = ""
        evidence["public_quote_withheld"] = True

    packet["live_proof_policy"] = {
        "minimum_live_evidence_records": 1,
        "live_evidence_only": True,
        "permission_required": True,
        "recipient_binding_required": True,
        "answered_quote_grounding_required": True,
        "interview_permission_is_publication_permission": False,
        "live_quote_text_exported": False,
        "raw_permission_receipt_exported": False,
        "raw_phone_exported": False,
        "raw_transcript_exported": False,
    }
    return packet
