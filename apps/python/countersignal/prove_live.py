"""Privacy-safe CounterSignal proof runner.

Preview is the default. A real call requires the same explicit live gates as
CounterSignal's core CLI. Successful live runs append only redacted evidence to
an audit ledger and print a judge-safe summary. Raw provider payloads are never
printed and are persisted only when --private-result-out is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import audit
import countersignal as core


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise ValueError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_live_summary(
    experiment: core.Experiment,
    record: dict[str, Any],
    packet: dict[str, Any],
    *,
    private_result_persisted: bool,
    audit_out: Path,
) -> dict[str, Any]:
    return {
        "mode": "live_redacted_proof",
        "call_id": record.get("call_id"),
        "experiment_id": experiment.experiment_id,
        "protocol_hash": core.protocol_hash(experiment),
        "bucket": record["bucket"],
        "confidence": record.get("confidence", 0.0),
        "grounded": bool(record.get("grounded", False)),
        "recipient_ref": record.get("recipient_ref"),
        "decision": packet["decision"],
        "answered_denominator": packet["answered_denominator"],
        "counts": packet["counts"],
        "audit_packet": str(audit_out),
        "private_provider_result_persisted": private_result_persisted,
        "privacy_boundary": "stdout contains no phone number or full transcript",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--recipient", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-one-reviewed-recipient", action="store_true")
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--reservation-database", type=Path, default=Path("data/countersignal.sqlite3"))
    parser.add_argument("--audit-database", type=Path, default=Path("data/countersignal-audit.sqlite3"))
    parser.add_argument("--audit-out", type=Path, default=Path("data/countersignal-audit.json"))
    parser.add_argument("--private-result-out", type=Path)
    args = parser.parse_args(argv)

    try:
        experiment = core.parse_experiment(_load(args.experiment))
        recipient = core.parse_recipient(_load(args.recipient))
        if not args.execute:
            preview = core.preview(experiment, recipient)
            preview["recommended_live_command"] = "prove_live.py --execute with explicit reviewed-recipient gates"
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0

        if not args.confirm_one_reviewed_recipient:
            raise ValueError("--execute requires --confirm-one-reviewed-recipient")
        if recipient.phone not in set(args.allow):
            raise ValueError("--execute requires the exact recipient phone in --allow")
        if os.environ.get("CALLE_LIVE_CALLS_ENABLED", "").lower() != "true":
            raise ValueError("--execute requires CALLE_LIVE_CALLS_ENABLED=true")

        base_url = core.validate_base_url(os.environ.get("CALLE_BASE_URL", core.DEFAULT_BASE_URL))
        key = core.api_key_for_base_url(base_url)
        from calle import CalleClient

        with CalleClient(api_key=key, base_url=base_url) as client:
            payload = core.execute(
                experiment,
                recipient,
                client.calls,
                core.ReservationLedger(args.reservation_database),
                args.timeout_seconds,
            )

        provider_result = payload["provider_result"]
        call_id = payload["call_id"]
        record = audit.evidence_record(
            experiment, recipient, provider_result, expected_call_id=call_id
        )
        ledger = audit.AuditLedger(args.audit_database)
        ledger.append(experiment, record)
        packet = ledger.packet(experiment)

        args.audit_out.parent.mkdir(parents=True, exist_ok=True)
        args.audit_out.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        private_persisted = False
        if args.private_result_out is not None:
            _write_new(args.private_result_out, provider_result)
            private_persisted = True

        print(
            json.dumps(
                safe_live_summary(
                    experiment,
                    record,
                    packet,
                    private_result_persisted=private_persisted,
                    audit_out=args.audit_out,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
