import countersignal as core
import audit


EXPERIMENT = {
    "experiment_id": "storage-privacy-v1",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "manual follow-up recurs enough to require a workaround",
    "questions": ["What happened?", "What did you do?", "How often?"],
    "decision_rule": {"min_answered": 3, "support_if_at_least": 2, "weaken_if_at_least": 2},
}
RECIPIENT = {"phone": "+14155550123", "region": "US", "locale": "en-US"}
QUOTE = "we call the city every week"


def test_live_quote_is_grounded_in_memory_but_not_persisted_to_sqlite(tmp_path):
    exp = core.parse_experiment(EXPERIMENT)
    rec = core.parse_recipient(RECIPIENT)
    result = {
        "id": "call_storage_privacy",
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": 0.95},
        "metadata": {
            "workflow_type": "falsifiable_customer_discovery",
            "experiment_id": exp.experiment_id,
            "protocol_hash": core.protocol_hash(exp),
        },
        "structured_result": {
            "continued_after_ai_disclosure": "yes",
            "disposition": "answered",
            "problem_occurred": "yes",
            "current_workaround": "yes",
            "would_take_followup": "no",
            "contradicts_hypothesis": "no",
            "key_quote": QUOTE,
            "notes": "",
        },
        "recipients": [{
            "phone": rec.phone,
            "attempts": [{"transcript_turns": [{"speaker": "recipient", "text": "We call the city every week until someone clarifies it."}]}],
        }],
    }

    record = audit.evidence_record(exp, rec, result, expected_call_id="call_storage_privacy")
    assert record["grounded"] is True
    assert record["quote"] == QUOTE

    db_path = tmp_path / "audit.sqlite3"
    ledger = audit.AuditLedger(db_path)
    assert ledger.append(exp, record) is True

    stored = ledger.records(exp)[0]
    assert stored["grounded"] is True
    assert stored["quote"] == ""
    assert stored["quote_withheld_at_rest"] is True

    raw = db_path.read_bytes()
    assert RECIPIENT["phone"].encode() not in raw
    assert QUOTE.encode() not in raw
