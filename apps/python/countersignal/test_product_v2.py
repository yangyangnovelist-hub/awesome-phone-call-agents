import audit
import benchmark
import countersignal as c


EXPERIMENT_DATA = {
    "experiment_id": "smallbet-permit-ops-v1",
    "segment": "small construction firms that manage municipal permits",
    "problem": "staff spend repeated operator time resolving permit status ambiguity",
    "hypothesis": "the problem recurs often enough that firms already use a workaround",
    "questions": [
        "Tell me about the last time a permit status was unclear.",
        "How did your team resolve it?",
        "How often does this happen?",
        "What happens if nobody follows up?",
        "Who keeps track of exceptions?",
    ],
    "decision_rule": {"min_answered": 8, "support_if_at_least": 5, "weaken_if_at_least": 3},
}
RECIPIENT_DATA = {"phone": "+14155550123", "region": "US", "locale": "en-US"}


def experiment():
    return c.parse_experiment(EXPERIMENT_DATA)


def recipient():
    return c.parse_recipient(RECIPIENT_DATA)


def provider_result(bucket="supporting", call_id="call_123"):
    exp = experiment()
    rec = recipient()
    structured = {
        "continued_after_ai_disclosure": "yes",
        "disposition": "answered",
        "problem_occurred": "yes",
        "current_workaround": "yes",
        "would_take_followup": "no",
        "contradicts_hypothesis": "no",
        "key_quote": "we call the city every week",
        "notes": "",
    }
    recipient_text = "We call the city every week until someone clarifies it."
    if bucket == "disconfirming":
        structured.update(
            problem_occurred="no",
            current_workaround="no",
            contradicts_hypothesis="yes",
            key_quote="the portal is usually enough",
        )
        recipient_text = "The portal is usually enough for us."
    elif bucket == "neutral":
        structured.update(
            problem_occurred="unknown",
            current_workaround="no",
            key_quote="only on unusual projects",
        )
        recipient_text = "It happens only on unusual projects."
    elif bucket == "nonresponse":
        structured.update(
            continued_after_ai_disclosure="no",
            disposition="voicemail",
            problem_occurred="unknown",
            current_workaround="unknown",
            key_quote="",
        )
        recipient_text = ""
    return {
        "id": call_id,
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": 0.93},
        "metadata": {
            "workflow_type": "falsifiable_customer_discovery",
            "experiment_id": exp.experiment_id,
            "protocol_hash": c.protocol_hash(exp),
        },
        "structured_result": structured,
        "recipients": [
            {
                "phone": rec.phone,
                "attempts": [
                    {"transcript_turns": [{"speaker": "recipient", "text": recipient_text}]}
                ],
            }
        ],
    }


def test_live_evidence_record_redacts_phone_and_preserves_provenance():
    record = audit.evidence_record(
        experiment(), recipient(), provider_result(), expected_call_id="call_123"
    )
    assert record["bucket"] == "supporting"
    assert record["call_id"] == "call_123"
    assert record["source"] == "calle_live"
    assert record["grounded"] is True
    assert record["recipient_binding_verified"] is True
    assert RECIPIENT_DATA["phone"] not in str(record)
    assert record["recipient_ref"].startswith("call-bound:")


def test_nonresponse_audit_record_does_not_require_a_quote():
    record = audit.evidence_record(
        experiment(), recipient(), provider_result("nonresponse", "call_vm")
    )
    assert record["bucket"] == "nonresponse"
    assert record["answered"] is False
    assert record["grounded"] is False
    assert record["recipient_binding_verified"] is True
    assert record["quote"] == ""


def test_decision_replay_exposes_support_inconclusive_and_weakened_transitions():
    exp = experiment()
    records = []
    for i, bucket in enumerate(
        ["supporting"] * 5 + ["neutral"] * 3 + ["disconfirming"] * 3
    ):
        records.append(
            audit.evidence_record(
                exp,
                recipient(),
                provider_result(bucket, f"call_{i}"),
                expected_call_id=f"call_{i}",
            )
        )
    states = [step["decision"] for step in audit.decision_replay(exp, records)]
    assert states[-3:] == [
        "hypothesis_supported_under_rule",
        "inconclusive",
        "hypothesis_weakened",
    ]


def test_audit_packet_rejects_cross_protocol_evidence():
    exp = experiment()
    record = audit.evidence_record(exp, recipient(), provider_result())
    record["protocol_hash"] = "wrong"
    try:
        audit.audit_packet(exp, [record])
    except ValueError as exc:
        assert "different protocol" in str(exc)
    else:
        raise AssertionError("cross-protocol evidence must be rejected")


def test_audit_packet_rejects_cross_experiment_evidence():
    exp = experiment()
    record = audit.evidence_record(exp, recipient(), provider_result())
    record["experiment_id"] = "other-experiment"
    try:
        audit.audit_packet(exp, [record])
    except ValueError as exc:
        assert "different experiment" in str(exc)
    else:
        raise AssertionError("cross-experiment evidence must be rejected")


def test_decision_fragility_reports_exact_distance_to_weaken():
    exp = experiment()
    records = []
    for i, bucket in enumerate(["supporting"] * 5 + ["neutral"] * 3):
        records.append(
            audit.evidence_record(
                exp,
                recipient(),
                provider_result(bucket, f"call_f{i}"),
                expected_call_id=f"call_f{i}",
            )
        )
    fragility = audit.decision_fragility(exp, records)
    assert fragility["current_decision"] == "hypothesis_supported_under_rule"
    assert fragility["contradictions_to_remove_support"] == 1
    assert fragility["contradictions_to_weaken"] == 3


def test_next_evidence_counterfactuals_identify_decision_relevant_outcome():
    exp = experiment()
    records = []
    for i, bucket in enumerate(["supporting"] * 5 + ["neutral"] * 3):
        records.append(
            audit.evidence_record(
                exp,
                recipient(),
                provider_result(bucket, f"call_cf{i}"),
                expected_call_id=f"call_cf{i}",
            )
        )
    scenarios = {
        row["next_bucket"]: row for row in audit.counterfactual_next_evidence(exp, records)
    }
    assert scenarios["disconfirming"]["before"] == "hypothesis_supported_under_rule"
    assert scenarios["disconfirming"]["after"] == "inconclusive"
    assert scenarios["disconfirming"]["changes_decision"] is True
    assert scenarios["supporting"]["changes_decision"] is False
    assert scenarios["nonresponse"]["answered_after"] == 8


def test_redacted_ledger_is_idempotent_and_never_persists_phone(tmp_path):
    exp = experiment()
    record = audit.evidence_record(
        exp, recipient(), provider_result("supporting", "call_ledger_1"), expected_call_id="call_ledger_1"
    )
    ledger = audit.AuditLedger(tmp_path / "audit.sqlite3")
    assert ledger.append(exp, record) is True
    assert ledger.append(exp, record) is False
    packet = ledger.packet(exp)
    assert packet["counts"]["supporting"] == 1
    assert RECIPIENT_DATA["phone"].encode() not in (tmp_path / "audit.sqlite3").read_bytes()


def test_redacted_ledger_rejects_conflicting_duplicate_call_id(tmp_path):
    exp = experiment()
    ledger = audit.AuditLedger(tmp_path / "audit.sqlite3")
    first = audit.evidence_record(
        exp, recipient(), provider_result("supporting", "call_same"), expected_call_id="call_same"
    )
    assert ledger.append(exp, first) is True
    conflicting = dict(first)
    conflicting["bucket"] = "neutral"
    try:
        ledger.append(exp, conflicting)
    except ValueError as exc:
        assert "different evidence" in str(exc)
    else:
        raise AssertionError("conflicting duplicate call id must fail closed")


def test_benchmark_makes_three_contradictions_load_bearing():
    rows = {row["case"]: row for row in benchmark.run_benchmark(experiment())["rows"]}
    row = rows["three_grounded_contradictions"]
    assert row["supporting"] == 5
    assert row["disconfirming"] == 3
    assert row["naive_majority"] == "positive_signal"
    assert row["countersignal"] == "hypothesis_weakened"
    assert row["diverges"] is True


def test_benchmark_keeps_voicemail_out_of_answered_denominator():
    rows = {row["case"]: row for row in benchmark.run_benchmark(experiment())["rows"]}
    row = rows["five_voicemails_do_not_change_denominator"]
    assert row["nonresponse"] == 5
    assert row["answered"] == 8
