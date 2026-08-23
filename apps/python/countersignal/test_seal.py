import copy

import seal


def packet():
    return {
        "schema": "countersignal.audit.v1",
        "experiment_id": "exp-1",
        "protocol_hash": "abc",
        "decision": "inconclusive",
        "counts": {"supporting": 2, "disconfirming": 1, "neutral": 0, "nonresponse": 0, "invalid": 0},
        "evidence": [{"call_id": "call_1", "bucket": "supporting"}],
    }


def test_seal_is_deterministic_and_verifies():
    first = seal.seal_packet(packet())
    second = seal.seal_packet(packet())
    assert first["integrity_seal"]["digest"] == second["integrity_seal"]["digest"]
    assert seal.verify_packet(first) is True


def test_seal_detects_evidence_or_decision_mutation():
    original = seal.seal_packet(packet())

    changed_evidence = copy.deepcopy(original)
    changed_evidence["evidence"][0]["bucket"] = "disconfirming"
    assert seal.verify_packet(changed_evidence) is False

    changed_decision = copy.deepcopy(original)
    changed_decision["decision"] = "hypothesis_weakened"
    assert seal.verify_packet(changed_decision) is False


def test_seal_explicitly_does_not_claim_authenticity():
    sealed = seal.seal_packet(packet())
    boundary = sealed["integrity_seal"]["does_not_prove"]
    assert "author identity" in boundary
    assert "timestamp" in boundary
    assert "tamper-proof" in boundary
