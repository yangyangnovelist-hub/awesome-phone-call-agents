import audit
import countersignal as core
import permission
import prove_live
import seal


EXPERIMENT = {
    "experiment_id": "proof-e2e-v1",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "manual follow-up recurs enough to require a workaround",
    "questions": [
        "Tell me about the last unclear permit status.",
        "How did your team resolve it?",
        "How often does it happen?",
    ],
    "decision_rule": {"min_answered": 3, "support_if_at_least": 2, "weaken_if_at_least": 2},
}
RECIPIENT = {"phone": "+14155550123", "region": "US", "locale": "en-US"}
QUOTE = "we call the city every week"


class FakeCalls:
    def __init__(self, result):
        self.result = result
        self.create_kwargs = None
        self.waited_call_id = None

    def create(self, **kwargs):
        self.create_kwargs = kwargs
        return {"id": "call_e2e_001"}

    def wait_for_result(self, call_id, *, timeout_seconds, interval_seconds):
        self.waited_call_id = call_id
        assert timeout_seconds == 9
        assert interval_seconds == 2
        return self.result


def test_permission_to_sealed_public_proof_end_to_end(tmp_path):
    exp = core.parse_experiment(EXPERIMENT)
    rec = core.parse_recipient(RECIPIENT)
    permission_summary = permission.validate_permission_receipt(
        exp,
        rec,
        {
            "experiment_id": exp.experiment_id,
            "phone": rec.phone,
            "ai_interview_opt_in": True,
            "channel": "email",
            "consented_at": "2026-08-23T13:30:00+08:00",
            "statement": "I agree to one AI-assisted customer research interview by phone.",
        },
    )

    provider_result = {
        "id": "call_e2e_001",
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": 0.96},
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
            "attempts": [{
                "transcript_turns": [
                    {"speaker": "recipient", "text": "We call the city every week until someone clarifies it."}
                ]
            }],
        }],
    }

    calls = FakeCalls(provider_result)
    reservation = core.ReservationLedger(tmp_path / "reservation.sqlite3")
    audit_ledger = audit.AuditLedger(tmp_path / "audit.sqlite3")

    proof = prove_live.run_after_live_gates(
        exp,
        rec,
        permission_summary,
        calls,
        reservation,
        audit_ledger,
        timeout_seconds=9,
    )

    assert calls.create_kwargs is not None
    assert calls.create_kwargs["metadata"]["experiment_id"] == exp.experiment_id
    assert calls.create_kwargs["metadata"]["protocol_hash"] == core.protocol_hash(exp)
    assert calls.waited_call_id == "call_e2e_001"

    reservation_state = reservation.get(core.idempotency_key(exp, rec))
    assert reservation_state is not None
    assert reservation_state[0] == "completed"
    assert reservation_state[1] == "call_e2e_001"

    stored = proof["record"]
    assert stored["source"] == "calle_live"
    assert stored["permission_verified"] is True
    assert stored["recipient_binding_verified"] is True
    assert stored["grounded"] is True
    assert stored["quote"] == ""
    assert stored["quote_withheld_at_rest"] is True

    packet = proof["packet"]
    assert seal.verify_packet(packet) is True
    assert packet["mode"] == "live_redacted_ledger"
    assert packet["live_proof_policy"]["minimum_live_evidence_records"] == 1
    assert packet["live_proof_policy"]["live_evidence_only"] is True
    assert len(packet["evidence"]) == 1

    public = packet["evidence"][0]
    assert public["source"] == "calle_live"
    assert public["permission_verified"] is True
    assert public["recipient_binding_verified"] is True
    assert public["grounding_verified_before_public_redaction"] is True
    assert public["public_quote_withheld"] is True
    assert public["quote"] == ""
    assert public["recipient_ref"].startswith("call-bound:")

    serialized = str(packet)
    assert rec.phone not in serialized
    assert QUOTE not in serialized
    audit_bytes = (tmp_path / "audit.sqlite3").read_bytes()
    assert rec.phone.encode() not in audit_bytes
    assert QUOTE.encode() not in audit_bytes
