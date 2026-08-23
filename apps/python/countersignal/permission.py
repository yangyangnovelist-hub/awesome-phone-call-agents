"""Local permission-receipt validation for CounterSignal live proof calls."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import countersignal as core

ALLOWED_PERMISSION_CHANNELS = {"email", "sms", "web_form", "in_person", "other_non_call"}


def _text(value: Any, field: str, limit: int = 200) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"permission receipt {field} must be non-empty text")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"permission receipt {field} exceeds {limit} characters")
    return value


def validate_permission_receipt(
    experiment: core.Experiment,
    recipient: core.Recipient,
    value: Any,
) -> dict[str, Any]:
    """Validate affirmative permission without exporting recipient identity.

    The raw receipt is a private local input because it contains the destination.
    The returned summary deliberately excludes the phone number.
    """
    if not isinstance(value, dict):
        raise ValueError("permission receipt must be an object")
    if value.get("ai_interview_opt_in") is not True:
        raise ValueError("permission receipt must record ai_interview_opt_in=true")
    if value.get("experiment_id") != experiment.experiment_id:
        raise ValueError("permission receipt belongs to a different experiment")
    if value.get("phone") != recipient.phone:
        raise ValueError("permission receipt does not match the reviewed recipient")

    channel = _text(value.get("channel"), "channel", 40)
    if channel not in ALLOWED_PERMISSION_CHANNELS:
        raise ValueError("permission receipt channel must be a supported non-call permission channel")

    consented_at = _text(value.get("consented_at"), "consented_at", 80)
    try:
        parsed = datetime.fromisoformat(consented_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("permission receipt consented_at must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("permission receipt consented_at must include a timezone")

    statement = _text(value.get("statement"), "statement", 500)
    return {
        "permission_verified": True,
        "experiment_id": experiment.experiment_id,
        "channel": channel,
        "consented_at": consented_at,
        "statement": statement,
        "identity_redacted": True,
    }
