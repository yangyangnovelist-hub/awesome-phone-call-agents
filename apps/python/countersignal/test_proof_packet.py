import json

import countersignal as c
import proof_packet


EXPERIMENT = {
    "experiment_id": "smallbet-permit-ops-v1",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "the problem recurs enough to require a workaround",
    "questions": ["What happened?", "What did you do?", "How often does it recur?"],
    "decision_rule": {"min_answered": 3, "support_if_at_least": 2, "weaken_if_at_least": 2},
}


def experiment():
    return c.parse_experiment(EXPERIMENT)


def live_record(**overrides):
    exp = experiment()
    record = {
        "schema": "countersignal.audit.v1",
        "source": "calle_live",
        "call_id": "call_permissioned",
        "recipient_ref": "call-bound:abcdef0123456789",
        "recipient_binding_verified": True,
        "experiment_id": exp.experiment_id,
        "protocol_hash": c.protocol_hash(exp),
        "bucket": "supporting",
        "answered": True,
        "confidence": 0.93,
        "grounded": True,
        "quote": "we already use a manual workaround",
        "disposition": "answered",
        "reason": "Recipient reported the problem and an existing workaround.",
        "permission_verified": True,
        "permission_channel": "email",
        "permission_consented_at": "2026-08-23T13:30:00+08:00",
    }
    record.update(overrides)
    return record


def test_public_live_packet_carries_only_redacted_permission_proof():
    packet = proof_packet.live_audit_packet(experiment(), [live_record()])
    evidence = packet["evidence"][0]
    assert evidence["permission_verified"] is True
    assert evidence["permission_channel"] == "email"
    assert evidence["permission_consented_at"].endswith("+08:00")
    assert evidence["grounding_verified_before_public_redaction"] is True
    assert evidence["public_quote_withheld"] is True
    assert evidence["quote"] == ""
    assert packet["live_proof_policy"]["minimum_live_evidence_records"] == 1
    assert packet["live_proof_policy"]["interview_permission_is_publication_permission"] is False
    assert packet["live_proof_policy"]["live_quote_text_exported"] is False
    assert packet["live_proof_policy"]["raw_permission_receipt_exported"] is False
    assert packet["live_proof_policy"]["raw_phone_exported"] is False
    encoded = json.dumps(packet)
    assert '"phone":' not in encoded
    assert "+14155550123" not in encoded
    assert "I agree" not in encoded
    assert "we already use a manual workaround" not in encoded


def test_live_packet_rejects_zero_live_records():
    try:
        proof_packet.live_audit_packet(experiment(), [])
    except ValueError as exc:
        assert "at least one CALL-E live evidence record" in str(exc)
    else:
        raise AssertionError("zero-record live proof must fail closed")


def test_live_packet_rejects_missing_permission_proof():
    record = live_record(permission_verified=False)
    try:
        proof_packet.live_audit_packet(experiment(), [record])
    except ValueError as exc:
        assert "permission proof" in str(exc)
    else:
        raise AssertionError("live evidence without permission proof must fail closed")


def test_live_packet_rejects_unbound_or_ungrounded_answered_evidence():
    for record, expected in [
        (live_record(recipient_binding_verified=False), "reviewed recipient"),
        (live_record(grounded=False), "transcript-grounded"),
    ]:
        try:
            proof_packet.live_audit_packet(experiment(), [record])
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError("invalid live evidence must fail closed")
