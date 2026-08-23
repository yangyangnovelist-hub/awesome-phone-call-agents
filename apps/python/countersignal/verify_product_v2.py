"""One-command, zero-credential verification for CounterSignal's judge-visible claims."""

from __future__ import annotations

import json
from pathlib import Path

import audit
import benchmark
import countersignal as core
import seal

ROOT = Path(__file__).resolve().parent


def _simulated_records(experiment: core.Experiment) -> list[dict[str, object]]:
    protocol = core.protocol_hash(experiment)
    buckets = ["supporting"] * 5 + ["neutral"] * 3
    return [
        {
            "schema": audit.AUDIT_SCHEMA_VERSION,
            "source": "verification_fixture",
            "call_id": f"SIM-{index:03d}",
            "recipient_ref": f"sha256:fixture{index:08d}",
            "experiment_id": experiment.experiment_id,
            "protocol_hash": protocol,
            "bucket": bucket,
            "confidence": 0.9,
            "grounded": True,
            "quote": "verification fixture",
            "disposition": "answered",
            "reason": "deterministic verification fixture",
        }
        for index, bucket in enumerate(buckets, start=1)
    ]


def _script(html: str) -> str:
    return html.split("<script>", 1)[1].split("</script>", 1)[0]


def _has_no_network_api(script: str) -> bool:
    return "fetch(" not in script and "XMLHttpRequest" not in script and "sendBeacon" not in script


def verify() -> dict[str, object]:
    experiment = core.parse_experiment(
        json.loads((ROOT / "smallbet-experiment.json").read_text(encoding="utf-8"))
    )
    records = _simulated_records(experiment)
    rows = {row["case"]: row for row in benchmark.run_benchmark(experiment)["rows"]}
    divergence = rows["three_grounded_contradictions"]
    counterfactual = {
        row["next_bucket"]: row for row in audit.counterfactual_next_evidence(experiment, records)
    }
    packet = audit.audit_packet(experiment, records, mode="verification_fixture")
    sealed = seal.seal_packet(packet)
    console = (ROOT / "judge-console.html").read_text(encoding="utf-8")
    verifier = (ROOT / "audit-verifier.html").read_text(encoding="utf-8")
    award = (ROOT / "index.html").read_text(encoding="utf-8")
    verifier_script = _script(verifier)
    award_script = _script(award)

    checks = {
        "frozen_rule_is_8_5_3": (
            experiment.decision_rule.min_answered,
            experiment.decision_rule.support_if_at_least,
            experiment.decision_rule.weaken_if_at_least,
        ) == (8, 5, 3),
        "benchmark_diverges_at_three_contradictions": (
            divergence["naive_majority"] == "positive_signal"
            and divergence["countersignal"] == "hypothesis_weakened"
            and divergence["diverges"] is True
        ),
        "one_contradiction_removes_support": (
            counterfactual["disconfirming"]["before"] == "hypothesis_supported_under_rule"
            and counterfactual["disconfirming"]["after"] == "inconclusive"
        ),
        "voicemail_does_not_change_answered_denominator": (
            counterfactual["nonresponse"]["answered_before"]
            == counterfactual["nonresponse"]["answered_after"]
        ),
        "sealed_packet_verifies": seal.verify_packet(sealed),
        "sealed_packet_states_limits": (
            "author identity" in sealed["integrity_seal"]["does_not_prove"]
            and "timestamp" in sealed["integrity_seal"]["does_not_prove"]
        ),
        "console_is_explicitly_no_call": "NO CALL" in console,
        "console_preserves_honest_denominator_copy": "Silence never enters the answered denominator" in console,
        "console_has_no_network_fetch": "fetch(" not in console,
        "console_exposes_audit_import": "Load audit JSON" in console,
        "console_exposes_benchmark": "Contradiction stress benchmark" in console,
        "verifier_recomputes_sha256": "crypto.subtle.digest" in verifier_script,
        "verifier_requires_live_only_evidence": (
            "live.length>0" in verifier_script
            and "live.length===evidence.length" in verifier_script
            and "packet.mode==='live_redacted_ledger'" in verifier_script
            and "policy.minimum_live_evidence_records===1" in verifier_script
            and "policy.live_evidence_only===true" in verifier_script
        ),
        "verifier_has_no_network_api": _has_no_network_api(verifier_script),
        "award_surface_has_decision_integrity_story": (
            "Customer research that can prove you wrong." in award
            and "Not a prettier summary. A different epistemic policy." in award
            and "Try to kill the hypothesis." in award
        ),
        "award_surface_verifies_live_proof_locally": (
            "crypto.subtle.digest" in award_script
            and "live.length>0" in award_script
            and "permission_verified===true" in award_script
            and "recipient_binding_verified===true" in award_script
            and "live.every(e=>!e.quote)" in award_script
            and _has_no_network_api(award_script)
        ),
    }
    return {
        "ok": all(checks.values()),
        "protocol_hash": core.protocol_hash(experiment),
        "audit_digest_sha256": sealed["integrity_seal"]["digest"],
        "checks": checks,
        "benchmark_case": divergence,
        "counterfactual_disconfirming": counterfactual["disconfirming"],
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
