"""Audit, replay, and durable redacted-evidence helpers for CounterSignal.

The audit layer is deliberately privacy-minimizing: public evidence contains no
phone-derived identifier. Recipient binding is checked against the raw provider
result before redaction; the exported reference is derived only from the public
experiment/protocol/call identity. The durable ledger stores those redacted
records, never raw provider payloads or full transcripts.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import countersignal as core

AUDIT_SCHEMA_VERSION = "countersignal.audit.v1"
ALLOWED_BUCKETS = {"supporting", "disconfirming", "neutral", "nonresponse", "invalid"}


def _recipient_binding_matches(provider_result: dict[str, Any], destination: str) -> bool:
    recipients = provider_result.get("recipients")
    return (
        isinstance(recipients, list)
        and len(recipients) == 1
        and isinstance(recipients[0], dict)
        and recipients[0].get("phone") == destination
    )


def _call_bound_recipient_ref(experiment: core.Experiment, call_id: Any) -> str | None:
    """Return an opaque public reference that is not derived from the phone number."""
    if not isinstance(call_id, str) or not call_id:
        return None
    material = f"{experiment.experiment_id}:{core.protocol_hash(experiment)}:{call_id}".encode()
    return f"call-bound:{hashlib.sha256(material).hexdigest()[:16]}"


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
    binding_verified = _recipient_binding_matches(provider_result, recipient.phone)

    return {
        "schema": AUDIT_SCHEMA_VERSION,
        "source": "calle_live" if isinstance(call_id, str) and call_id else "provider_result",
        "call_id": call_id if isinstance(call_id, str) else None,
        "recipient_ref": _call_bound_recipient_ref(experiment, call_id),
        "recipient_binding_verified": binding_verified,
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
        quote = record.get("quote", "")
        if not isinstance(quote, str) or len(quote) > 300:
            raise ValueError(f"evidence record {index} has invalid quote")
        binding = record.get("recipient_binding_verified")
        if binding is not None and not isinstance(binding, bool):
            raise ValueError(f"evidence record {index} has invalid recipient binding flag")
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


def counterfactual_next_evidence(
    experiment: core.Experiment, records: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Show how each possible next evidence bucket would change the decision.

    This is a structural sensitivity analysis, not a prediction of what a future
    respondent will say.
    """
    items = _normalized_records(records)
    buckets = [record["bucket"] for record in items]
    current = core.experiment_decision(experiment, buckets)
    rows: list[dict[str, Any]] = []
    for candidate in ("supporting", "neutral", "disconfirming", "nonresponse", "invalid"):
        after = core.experiment_decision(experiment, [*buckets, candidate])
        rows.append(
            {
                "next_bucket": candidate,
                "before": current["decision"],
                "after": after["decision"],
                "changes_decision": after["decision"] != current["decision"],
                "answered_before": current["answered_denominator"],
                "answered_after": after["answered_denominator"],
            }
        )
    return rows


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
        "counterfactual_next_evidence": counterfactual_next_evidence(experiment, items),
        "replay": decision_replay(experiment, items),
        "claim_boundary": decision["claim_boundary"],
        "evidence": [
            {
                "sequence": index,
                "source": record.get("source", "unknown"),
                "call_id": record.get("call_id"),
                "recipient_ref": record.get("recipient_ref"),
                "recipient_binding_verified": bool(record.get("recipient_binding_verified", False)),
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


class AuditLedger:
    """Append-only API over SQLite containing only redacted evidence records."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS evidence ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT, "
                "call_id TEXT NOT NULL UNIQUE, "
                "experiment_id TEXT NOT NULL, "
                "protocol_hash TEXT NOT NULL, "
                "record_json TEXT NOT NULL)"
            )

    @staticmethod
    def _canonical(record: dict[str, Any]) -> str:
        return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def append(self, experiment: core.Experiment, record: dict[str, Any]) -> bool:
        """Append one live record. Identical retries are idempotent; conflicts fail closed."""
        item = _normalized_records([record])[0]
        call_id = item.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            raise ValueError("durable evidence requires a CALL-E call_id")
        expected_hash = core.protocol_hash(experiment)
        if item.get("experiment_id") != experiment.experiment_id:
            raise ValueError("evidence belongs to a different experiment")
        if item.get("protocol_hash") != expected_hash:
            raise ValueError("evidence belongs to a different protocol")
        canonical = self._canonical(item)
        with sqlite3.connect(self.path) as db:
            existing = db.execute(
                "SELECT record_json FROM evidence WHERE call_id=?", (call_id,)
            ).fetchone()
            if existing is not None:
                if existing[0] == canonical:
                    return False
                raise ValueError("call_id already exists with different evidence")
            db.execute(
                "INSERT INTO evidence(call_id, experiment_id, protocol_hash, record_json) "
                "VALUES (?, ?, ?, ?)",
                (call_id, experiment.experiment_id, expected_hash, canonical),
            )
        return True

    def records(self, experiment: core.Experiment) -> list[dict[str, Any]]:
        expected_hash = core.protocol_hash(experiment)
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                "SELECT record_json FROM evidence WHERE experiment_id=? AND protocol_hash=? "
                "ORDER BY sequence",
                (experiment.experiment_id, expected_hash),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def packet(self, experiment: core.Experiment) -> dict[str, Any]:
        return audit_packet(experiment, self.records(experiment), mode="live_redacted_ledger")
