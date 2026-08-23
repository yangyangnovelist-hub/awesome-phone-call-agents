import copy

import countersignal as c
import permission


EXPERIMENT = {
    "experiment_id": "smallbet-permit-ops-v1",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "the problem recurs enough to require a workaround",
    "questions": ["What happened?", "What did you do?", "How often does it recur?"],
    "decision_rule": {"min_answered": 3, "support_if_at_least": 2, "weaken_if_at_least": 2},
}
RECIPIENT = {"phone": "+14155550123", "region": "US", "locale": "en-US"}
VALID = {
    "experiment_id": "smallbet-permit-ops-v1",
    "phone": "+14155550123",
    "ai_interview_opt_in": True,
    "channel": "email",
    "consented_at": "2026-08-23T13:30:00+08:00",
    "statement": "I agree to receive one AI-assisted customer research interview by phone.",
}


def exp():
    return c.parse_experiment(EXPERIMENT)


def rec():
    return c.parse_recipient(RECIPIENT)


def test_valid_permission_receipt_returns_redacted_summary():
    result = permission.validate_permission_receipt(exp(), rec(), VALID)
    assert result["permission_verified"] is True
    assert result["channel"] == "email"
    assert result["identity_redacted"] is True
    assert RECIPIENT["phone"] not in str(result)


def test_false_opt_in_is_rejected():
    value = copy.deepcopy(VALID)
    value["ai_interview_opt_in"] = False
    try:
        permission.validate_permission_receipt(exp(), rec(), value)
    except ValueError as exc:
        assert "opt_in=true" in str(exc)
    else:
        raise AssertionError("false opt-in must be rejected")


def test_wrong_recipient_is_rejected():
    value = copy.deepcopy(VALID)
    value["phone"] = "+14155550124"
    try:
        permission.validate_permission_receipt(exp(), rec(), value)
    except ValueError as exc:
        assert "reviewed recipient" in str(exc)
    else:
        raise AssertionError("mismatched recipient must be rejected")


def test_phone_call_is_not_an_allowed_permission_channel():
    value = copy.deepcopy(VALID)
    value["channel"] = "phone"
    try:
        permission.validate_permission_receipt(exp(), rec(), value)
    except ValueError as exc:
        assert "non-phone" in str(exc)
    else:
        raise AssertionError("phone cannot establish permission for the proof call")


def test_consent_timestamp_requires_timezone():
    value = copy.deepcopy(VALID)
    value["consented_at"] = "2026-08-23T13:30:00"
    try:
        permission.validate_permission_receipt(exp(), rec(), value)
    except ValueError as exc:
        assert "timezone" in str(exc)
    else:
        raise AssertionError("naive timestamp must be rejected")
