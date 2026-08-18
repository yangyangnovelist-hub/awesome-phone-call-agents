"""Core request, preview, CALL-E arguments, and evidence routing for PermitPulse."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
PHONE_LIKE = re.compile(r"(?<!\w)\+?[1-9]\d{7,14}(?!\w)")
EMAIL_LIKE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TOKEN_LIKE = re.compile(
    r"(?i)(bearer|token|api[_ -]?key|access[_ -]?token|password|client[_ -]?secret)"
    r"\s*[:=]?\s*\S+"
)
ALLOWED_CONTACT_BASIS = {
    "authorized_project",
    "existing_client",
    "public_agency_inquiry",
}
SUPPORTED_REGIONS = {
    "US",
    "SG",
    "MY",
    "IN",
    "AE",
    "AU",
    "CA",
    "GB",
    "VN",
    "DE",
    "JP",
    "FR",
    "MX",
    "BR",
    "ID",
    "PH",
    "KE",
    "NL",
    "PL",
    "BD",
    "NG",
    "OM",
    "TH",
    "NA",
    "CM",
    "MZ",
    "SA",
    "FI",
    "UA",
    "LK",
    "BW",
    "PK",
    "TR",
    "HN",
}
TERMINAL_SUCCESS = {"completed", "succeeded"}
MIN_CONFIDENCE = 0.8
RECIPIENT_SPEAKERS = {"recipient", "user", "callee"}


@dataclass(frozen=True)
class PermitRequest:
    request_id: str
    caller_business_name: str
    jurisdiction: str
    permit_reference: str
    support_phone: str
    region: str
    locale: str
    contact_basis: str
    project_summary: str = ""


class CallsAPI(Protocol):
    def create(self, **kwargs: Any) -> dict[str, Any]: ...

    def wait_for_result(
        self, call_id: str, *, timeout_seconds: int, interval_seconds: int
    ) -> dict[str, Any]: ...


RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "contact_outcome",
        "continued_after_ai_disclosure",
        "permit_reference_confirmed",
        "permit_status",
        "missing_items",
        "next_milestone",
        "processing_window",
        "official_source",
        "next_contact",
        "needs_human_followup",
    ],
    "properties": {
        "contact_outcome": {
            "type": "string",
            "enum": [
                "answered",
                "wrong_office",
                "refused",
                "voicemail",
                "unreachable",
                "unknown",
            ],
        },
        "continued_after_ai_disclosure": {"type": "boolean"},
        "permit_reference_confirmed": {"type": "boolean"},
        "permit_status": {"type": "string", "maxLength": 240},
        "missing_items": {"type": "string", "maxLength": 500},
        "next_milestone": {"type": "string", "maxLength": 300},
        "processing_window": {"type": "string", "maxLength": 160},
        "official_source": {"type": "string", "maxLength": 300},
        "next_contact": {"type": "string", "maxLength": 300},
        "needs_human_followup": {"type": "boolean"},
    },
}


def _reference_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _contains_token_sequence(haystack: list[str], needle: list[str]) -> bool:
    if not needle or len(needle) > len(haystack):
        return False
    return any(
        haystack[index : index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def parse_request(payload: dict[str, Any]) -> PermitRequest:
    required = (
        "request_id",
        "caller_business_name",
        "jurisdiction",
        "permit_reference",
        "support_phone",
        "region",
        "locale",
        "contact_basis",
    )
    missing = [
        key
        for key in required
        if not isinstance(payload.get(key), str) or not payload[key].strip()
    ]
    if missing:
        raise ValueError(f"missing required string fields: {', '.join(missing)}")
    request = PermitRequest(
        request_id=payload["request_id"].strip(),
        caller_business_name=payload["caller_business_name"].strip(),
        jurisdiction=payload["jurisdiction"].strip(),
        permit_reference=payload["permit_reference"].strip(),
        support_phone=payload["support_phone"].strip(),
        region=payload["region"].strip().upper(),
        locale=payload["locale"].strip(),
        contact_basis=payload["contact_basis"].strip(),
        project_summary=str(payload.get("project_summary", "")).strip(),
    )
    validate_request(request)
    return request


def validate_request(request: PermitRequest) -> None:
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", request.request_id):
        raise ValueError("request_id must be a stable 3-100 character safe identifier")
    if not E164.fullmatch(request.support_phone):
        raise ValueError("support_phone must be E.164")
    if request.region not in SUPPORTED_REGIONS:
        raise ValueError(f"unsupported CALL-E recipient region: {request.region}")
    if request.contact_basis not in ALLOWED_CONTACT_BASIS:
        raise ValueError(
            "contact_basis must describe an authorized project or factual public-agency inquiry"
        )
    if sum(len(token) for token in _reference_tokens(request.permit_reference)) < 4:
        raise ValueError("permit_reference is too short to corroborate safely")
    if len(request.project_summary) > 1500:
        raise ValueError("project_summary is too long; keep the spoken context bounded")


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}{'*' * max(4, len(phone) - 6)}{phone[-3:]}"


def build_task(request: PermitRequest) -> str:
    context = request.project_summary or "No additional project context is necessary."
    return (
        f"You are an AI assistant calling on behalf of {request.caller_business_name} about an "
        f"authorized permit-status inquiry with {request.jurisdiction}. At the start, disclose that "
        "you are an AI assistant and ask whether the recipient is willing to continue. If they do "
        "not clearly agree, do not disclose project details and end the call. Do not impersonate "
        "the applicant, claim authority you do not have, or ask for protected personal information. "
        f"The permit/application reference is {request.permit_reference}. Ask only for factual "
        "process information the office is willing and authorized to provide: whether the reference "
        "is recognized, current status, missing checklist or correction items, next review or "
        "inspection milestone, any processing window the office is willing to state, where official "
        "updates are published, and the correct next contact or department. Read back the reference "
        "and captured facts once so they can be corrected. If the office cannot verify the record, "
        "refuses, requires a human applicant, or says a written channel is authoritative, record "
        f"that instead of guessing. Known context: {context}"
    )


def call_arguments(request: PermitRequest) -> dict[str, Any]:
    return {
        "task": build_task(request),
        "recipients": [
            {
                "phones": [request.support_phone],
                "region": request.region,
                "locale": request.locale,
            }
        ],
        "result_schema": RESULT_SCHEMA,
        "metadata": {
            "app": "permitpulse",
            "request_id": request.request_id,
            "permit_reference": request.permit_reference,
        },
    }


def idempotency_key(request: PermitRequest) -> str:
    canonical = json.dumps(
        call_arguments(request),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return f"permitpulse-{hashlib.sha256(canonical).hexdigest()}"


def preview(request: PermitRequest) -> dict[str, Any]:
    arguments = call_arguments(request)
    arguments["recipients"] = [
        {
            "phones": [mask_phone(request.support_phone)],
            "region": request.region,
            "locale": request.locale,
        }
    ]
    return {
        "mode": "preview",
        "creates_phone_call": False,
        "request_id": request.request_id,
        "destination": mask_phone(request.support_phone),
        "contact_basis": request.contact_basis,
        "idempotency_key": idempotency_key(request),
        "call_arguments": arguments,
    }


def confidence_score(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        score = value.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            return float(score)
    return 0.0


def valid_result(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = RESULT_SCHEMA["required"]
    if set(value) != set(required):
        return False
    for field in required:
        rule = RESULT_SCHEMA["properties"][field]
        field_value = value[field]
        if rule["type"] == "boolean":
            if not isinstance(field_value, bool):
                return False
            continue
        if not isinstance(field_value, str):
            return False
        if len(field_value) > rule.get("maxLength", 10_000):
            return False
        if "enum" in rule and field_value not in rule["enum"]:
            return False
    return True


def _expected_metadata(request: PermitRequest) -> dict[str, str]:
    return {
        "app": "permitpulse",
        "request_id": request.request_id,
        "permit_reference": request.permit_reference,
    }


def _recipient_transcript(provider_result: dict[str, Any], destination: str) -> str:
    recipients = provider_result.get("recipients")
    if not isinstance(recipients, list) or len(recipients) != 1:
        return ""
    recipient = recipients[0]
    if not isinstance(recipient, dict) or recipient.get("phone") != destination:
        return ""
    attempts = recipient.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return ""
    turns: list[str] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        transcript = attempt.get("transcript_turns")
        if not isinstance(transcript, list):
            continue
        for turn in transcript:
            if (
                isinstance(turn, dict)
                and str(turn.get("speaker", "")).lower() in RECIPIENT_SPEAKERS
                and isinstance(turn.get("text"), str)
            ):
                turns.append(turn["text"])
    return "\n".join(turns)


def _bound_to_approved_call(
    request: PermitRequest,
    provider_result: dict[str, Any],
    expected_call_id: str | None,
) -> bool:
    if provider_result.get("metadata") != _expected_metadata(request):
        return False
    if expected_call_id is not None and provider_result.get("id") != expected_call_id:
        return False
    evidence = provider_result.get("evidence")
    if not isinstance(evidence, list) or not any(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        return False
    return bool(_recipient_transcript(provider_result, request.support_phone))


def _reference_corroborated(request: PermitRequest, provider_result: dict[str, Any]) -> bool:
    transcript = _recipient_transcript(provider_result, request.support_phone)
    return _contains_token_sequence(
        _reference_tokens(transcript),
        _reference_tokens(request.permit_reference),
    )


def route_result(
    request: PermitRequest,
    provider_result: dict[str, Any],
    *,
    expected_call_id: str | None = None,
) -> dict[str, str]:
    structured = provider_result.get("structured_result")
    if (
        provider_result.get("status") not in TERMINAL_SUCCESS
        or provider_result.get("task_completed") is not True
        or confidence_score(provider_result.get("completion_confidence")) < MIN_CONFIDENCE
    ):
        return {"route": "human_review", "reason": "CALL-E did not return reliable success"}
    if not valid_result(structured):
        return {"route": "human_review", "reason": "structured result failed strict validation"}
    assert isinstance(structured, dict)
    if not _bound_to_approved_call(request, provider_result, expected_call_id):
        return {
            "route": "human_review",
            "reason": "result was not bound to the approved call, destination, and evidence",
        }
    outcome = structured["contact_outcome"]
    if outcome == "wrong_office":
        return {"route": "reroute", "reason": "office said another contact is responsible"}
    if outcome != "answered":
        return {"route": "human_followup", "reason": f"contact outcome was {outcome}"}
    if structured["continued_after_ai_disclosure"] is not True:
        return {"route": "human_review", "reason": "recipient did not consent after AI disclosure"}
    if structured["permit_reference_confirmed"] is not True:
        return {"route": "human_review", "reason": "permit reference was not confirmed"}
    if not _reference_corroborated(request, provider_result):
        return {
            "route": "human_review",
            "reason": "confirmed permit reference was not corroborated in recipient transcript",
        }
    if structured["needs_human_followup"] is True:
        return {
            "route": "human_followup",
            "reason": "office requested or outcome requires a human",
        }
    return {
        "route": "update_project_record",
        "reason": "bound, corroborated permit facts are actionable",
    }


def redact(value: Any) -> Any:
    if isinstance(value, str):
        value = PHONE_LIKE.sub("[phone-redacted]", value)
        value = EMAIL_LIKE.sub("[email-redacted]", value)
        return TOKEN_LIKE.sub("[credential-redacted]", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def execute(
    request: PermitRequest,
    calls: CallsAPI,
    *,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    created = calls.create(
        **call_arguments(request),
        idempotency_key=idempotency_key(request),
    )
    call_id = created.get("id")
    if not isinstance(call_id, str) or not call_id:
        raise RuntimeError("CALL-E create response did not contain a call id")
    completed = calls.wait_for_result(
        call_id,
        timeout_seconds=timeout_seconds,
        interval_seconds=2,
    )
    return {
        "mode": "execute",
        "creates_phone_call": True,
        "request_id": request.request_id,
        "call_id": call_id,
        "idempotency_key": idempotency_key(request),
        "status": completed.get("status"),
        "task_completed": completed.get("task_completed"),
        "completion_confidence": completed.get("completion_confidence"),
        "structured_result": redact(completed.get("structured_result")),
        "evidence_present": bool(completed.get("evidence")),
        "decision": route_result(request, completed, expected_call_id=call_id),
    }


def dumps_preview(request: PermitRequest) -> str:
    return json.dumps(preview(request), ensure_ascii=False, indent=2)
