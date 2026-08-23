import json

import countersignal as c
import prove_live


EXPERIMENT = {
    "experiment_id": "proof-test",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "the problem recurs enough to require a workaround",
    "questions": ["What happened?", "What did you do?", "How often does it recur?"],
    "decision_rule": {"min_answered": 3, "support_if_at_least": 2, "weaken_if_at_least": 2},
}
RECIPIENT = {"phone": "+14155550123", "region": "US", "locale": "en-US"}


def write_inputs(tmp_path):
    exp = tmp_path / "experiment.json"
    rec = tmp_path / "recipient.json"
    exp.write_text(json.dumps(EXPERIMENT), encoding="utf-8")
    rec.write_text(json.dumps(RECIPIENT), encoding="utf-8")
    return exp, rec


def test_proof_runner_defaults_to_no_call_and_masks_phone(tmp_path, capsys):
    exp, rec = write_inputs(tmp_path)
    assert prove_live.main(["--experiment", str(exp), "--recipient", str(rec)]) == 0
    output = capsys.readouterr().out
    assert '"creates_phone_call": false' in output
    assert RECIPIENT["phone"] not in output
    assert "prove_live.py --execute" in output
    assert "--permission-receipt" in output


def test_execute_without_permission_receipt_fails_before_live_configuration(tmp_path, capsys, monkeypatch):
    exp, rec = write_inputs(tmp_path)
    monkeypatch.delenv("CALLE_API_KEY", raising=False)
    monkeypatch.delenv("CALLE_LIVE_CALLS_ENABLED", raising=False)
    code = prove_live.main(
        [
            "--experiment", str(exp),
            "--recipient", str(rec),
            "--execute",
            "--confirm-one-reviewed-recipient",
            "--allow", RECIPIENT["phone"],
        ]
    )
    assert code == 2
    error = capsys.readouterr().err
    assert "--permission-receipt" in error
    assert "CALLE_API_KEY" not in error
    assert "CALLE_LIVE_CALLS_ENABLED" not in error


def test_safe_live_summary_contains_no_raw_identity_or_conversation_content():
    exp = c.parse_experiment(EXPERIMENT)
    record = {
        "call_id": "call_safe",
        "permission_verified": True,
        "permission_channel": "email",
        "permission_consented_at": "2026-08-23T13:30:00+08:00",
        "bucket": "supporting",
        "confidence": 0.93,
        "grounded": True,
        "recipient_binding_verified": True,
        "recipient_ref": "call-bound:abcdef0123456789",
    }
    packet = {
        "decision": "collect_more",
        "answered_denominator": 1,
        "counts": {"supporting": 1, "disconfirming": 0, "neutral": 0, "nonresponse": 0, "invalid": 0},
        "integrity_seal": {"digest": "abc123"},
    }
    summary = prove_live.safe_live_summary(
        exp,
        record,
        packet,
        private_result_persisted=False,
        audit_out=__import__("pathlib").Path("data/audit.json"),
    )
    encoded = json.dumps(summary)
    assert RECIPIENT["phone"] not in encoded
    assert "We call the city every week" not in encoded
    assert "recipients" not in encoded
    assert summary["permission_verified"] is True
    assert summary["recipient_binding_verified"] is True
    assert summary["audit_digest_sha256"] == "abc123"
    assert summary["private_provider_result_persisted"] is False
    assert "no phone number or full transcript" in summary["privacy_boundary"]


def test_private_result_writer_refuses_overwrite(tmp_path):
    target = tmp_path / "private-result.json"
    prove_live._write_new(target, {"id": "call_1"})
    try:
        prove_live._write_new(target, {"id": "call_2"})
    except ValueError as exc:
        assert "refusing to overwrite" in str(exc)
    else:
        raise AssertionError("private provider result must not overwrite silently")
