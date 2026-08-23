"""Audit and replay helpers for CounterSignal evidence.

This module is deliberately privacy-minimizing: it emits a stable recipient
fingerprint instead of a phone number and includes only the transcript quote
already accepted by CounterSignal's grounding gate.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

import countersignal as core

AUDIT_SCHEMA_VERSION = "countersignal.audit.v1"
ALLOWED_BUCKETS = {"supporting", "disconfirming", "neutral", "nonresponse", "invalid"}


def _recipient_fingerprint(phone: str) -> str:
    digest = hashlib.sha256(f"countersignal-recipient:{phone}".encode()).hexdigest()
    return f"sha256:{digest[:16]}"


def evidence_record(
    experiment: core.Experiment,
    recipient: core.Recipient,
    provider_result: dict[str, Any],
    *,
    expected_call_id: str | None = None,
) -> dict[str, Any]:
    """Convert one provider result into a redacted, judge-safe evidence record."""
    classification = core.classify_call(
        experiment, recipient, provider_result, expected_call_id=expected_call_id
    )
    bucket = classification["bucket"]
    if bucket not in ALLOWED_BUCKETS:
        raise ValueError(f"unsupported bucket: {bucket}")

    structured = provider_result.get("structured_result")
    if not isinstance(structured, dict):
        structured = {}
    transcript = core.recipient_transcript(provider_result, recipient.phone)
    quote = structured.get("key_quote", "")
    grounded = bool(quote) and core.quote_grounded(quote, transcript)
    call_id = provider_result.get("id")

    return {
        "schema": AUDIT_SCHEMA_VERSION,
        "source": "calle_live" if isinstance(call_id, str) and call_id else "provider_result",
        "call_id": call_id if isinstance(call_id, str) else None,
        "recipient_ref": _recipient_fingerprint(recipient.phone),
        "experiment_id": experiment.experiment_id,
        "protocol_hash": core.protocol_hash(experiment),
        "bucket": bucket,
        "answered": bucket in {"supporting", "disconfirming", "neutral"},
        "confidence": core.confidence_score(provider_result.get("completion_confidence")),
        "grounded": grounded,
        "quote": quote if grounded else "",
        "disposition": structured.get("disposition"),
        "reason": classification["reason"],
    }


def _normalized_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"evidence record {index} must be an object")
        bucket = record.get("bucket")
        if bucket not in ALLOWED_BUCKETS:
            raise ValueError(f"evidence record {index} has invalid bucket")
        out.append(dict(record))
    return out


def decision_replay(
    experiment: core.Experiment, records: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return only decision-state transitions, preserving the evidence sequence."""
    items = _normalized_records(records)
    transitions: list[dict[str, Any]] = []
    buckets: list[str] = []
    previous: str | None = None
    for sequence, record in enumerate(items, start=1):
        buckets.append(record["bucket"])
        decision = core.experiment_decision(experiment, buckets)
        current = decision["decision"]
        if current != previous:
            transitions.append(
                {
                    "sequence": sequence,
                    "decision": current,
                    "trigger_bucket": record["bucket"],
                    "trigger_call_id": record.get("call_id"),
                    "answered_denominator": decision["answered_denominator"],
                    "counts": decision["counts"],
                }
            )
            previous = current
    return transitions


def decision_fragility(
    experiment: core.Experiment, records: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Quantify how much new evidence can change the current decision."""
    items = _normalized_records(records)
    buckets = [record["bucket"] for record in items]
    decision = core.experiment_decision(experiment, buckets)
    counts = decision["counts"]
    rule = experiment.decision_rule
    return {
        "current_decision": decision["decision"],
        "answers_to_minimum": max(0, rule.min_answered - decision["answered_denominator"]),
        "contradictions_to_remove_support": (
            1 if decision["decision"] == "hypothesis_supported_under_rule" else 0
        ),
        "contradictions_to_weaken": max(0, rule.weaken_if_at_least - counts["disconfirming"]),
        "supporting_to_threshold": max(0, rule.support_if_at_least - counts["supporting"]),
    }


def audit_packet(
    experiment: core.Experiment,
    records: Iterable[dict[str, Any]],
    *,
    mode: str = "live_redacted",
) -> dict[str, Any]:
    """Build a portable audit object consumed by the browser Decision Audit Console."""
    items = _normalized_records(records)
    expected_hash = core.protocol_hash(experiment)
    for index, record in enumerate(items, start=1):
        record_hash = record.get("protocol_hash")
        if record_hash is not None and record_hash != expected_hash:
            raise ValueError(f"evidence record {index} belongs to a different protocol")
        record_exp = record.get("experiment_id")
        if record_exp is not None and record_exp != experiment.experiment_id:
            raise ValueError(f"evidence record {index} belongs to a different experiment")

    buckets = [record["bucket"] for record in items]
    decision = core.experiment_decision(experiment, buckets)
    return {
        "schema": AUDIT_SCHEMA_VERSION,
        "mode": mode,
        "experiment_id": experiment.experiment_id,
        "protocol_hash": expected_hash,
        "decision": decision["decision"],
        "answered_denominator": decision["answered_denominator"],
        "counts": decision["counts"],
        "fragility": decision_fragility(experiment, items),
        "replay": decision_replay(experiment, items),
        "claim_boundary": decision["claim_boundary"],
        "evidence": [
            {
                "sequence": index,
                "source": record.get("source", "unknown"),
                "call_id": record.get("call_id"),
                "recipient_ref": record.get("recipient_ref"),
                "bucket": record["bucket"],
                "confidence": record.get("confidence", 0.0),
                "grounded": bool(record.get("grounded", False)),
                "quote": record.get("quote", ""),
                "disposition": record.get("disposition"),
                "reason": record.get("reason", ""),
            }
            for index, record in enumerate(items, start=1)
        ],
    }
