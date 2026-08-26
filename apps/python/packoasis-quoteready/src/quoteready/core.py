"""PackOasis QuoteReady: bounded CALL-E qualification for warm packaging inquiries."""

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
SUPPORTED_REGIONS = {
    "US", "SG", "MY", "IN", "AE", "AU", "CA", "GB", "VN", "DE", "JP", "FR", "MX",
    "BR", "ID", "PH", "KE", "NL", "PL", "BD", "NG", "OM", "TH", "NA", "CM", "MZ",
    "SA", "FI", "UA", "LK", "BW", "PK", "TR", "HN",
}
CONTACT_BASIS = {"inbound_inquiry", "existing_customer", "warm_followup", "explicit_permission"}
TERMINAL_SUCCESS = {"completed", "succeeded"}
MIN_CONFIDENCE = 0.8
RECIPIENT_SPEAKERS = {"recipient", "user", "callee"}


@dataclass(frozen=True)
class RFQRequest:
    request_id: str
    lead_name: str
    company_name: str
    phone: str
    region: str
    locale: str
    contact_basis: str
    known_requirements: str


class CallsAPI(Protocol):
    def create(self, **kwargs: Any) -> dict[str, Any]: ...
    def wait_for_result(self, call_id: str, *, timeout_seconds: int, interval_seconds: int) -> dict[str, Any]: ...


RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "contact_outcome", "continued_after_ai_disclosure", "request_id_confirmed",
        "box_type", "dimensions", "quantity", "material", "printing", "finish", "insert",
        "target_unit_price", "delivery_country", "required_delivery_date", "sample_required",
        "existing_supplier", "decision_timeline", "quote_requested", "next_action",
    ],
    "properties": {
        "contact_outcome": {"type": "string", "enum": ["answered", "wrong_contact", "refused", "voicemail", "unreachable", "unknown"]},
        "continued_after_ai_disclosure": {"type": "boolean"},
        "request_id_confirmed": {"type": "boolean"},
        "box_type": {"type": "string", "maxLength": 160},
        "dimensions": {"type": "string", "maxLength": 200},
        "quantity": {"type": "string", "maxLength": 100},
        "material": {"type": "string", "maxLength": 200},
        "printing": {"type": "string", "maxLength": 240},
        "finish": {"type": "string", "maxLength": 240},
        "insert": {"type": "string", "maxLength": 240},
        "target_unit_price": {"type": "string", "maxLength": 120},
        "delivery_country": {"type": "string", "maxLength": 120},
        "required_delivery_date": {"type": "string", "maxLength": 120},
        "sample_required": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "existing_supplier": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "decision_timeline": {"type": "string", "maxLength": 160},
        "quote_requested": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "next_action": {"type": "string", "maxLength": 300},
    },
}

QUOTE_READY_FIELDS = (
    "box_type", "dimensions", "quantity", "material", "printing", "finish",
    "delivery_country", "required_delivery_date",
)


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _contains_sequence(haystack: list[str], needle: list[str]) -> bool:
    if not needle or len(needle) > len(haystack):
        return False
    return any(haystack[i:i + len(needle)] == needle for i in range(len(haystack) - len(needle) + 1))


def parse_request(raw: dict[str, Any]) -> RFQRequest:
    keys = ("request_id", "lead_name", "company_name", "phone", "region", "locale", "contact_basis", "known_requirements")
    missing = [key for key in keys if not isinstance(raw.get(key), str) or not raw[key].strip()]
    if missing:
        raise ValueError(f"missing required string fields: {', '.join(missing)}")
    req = RFQRequest(**{key: raw[key].strip() for key in keys})
    if not re.fullmatch(r"[A-Za-z0-9._-]{4,100}", req.request_id):
        raise ValueError("request_id must be a stable safe identifier")
    if not E164.fullmatch(req.phone):
        raise ValueError("phone must use E.164")
    if req.region.upper() not in SUPPORTED_REGIONS:
        raise ValueError("recipient region is not currently supported by CALL-E")
    if req.contact_basis not in CONTACT_BASIS:
        raise ValueError("live calls require inbound, existing-customer, warm-followup, or explicit-permission basis")
    if len(req.known_requirements) > 1800:
        raise ValueError("known_requirements is too long")
    return RFQRequest(**{**req.__dict__, "region": req.region.upper()})


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}{'*' * max(4, len(phone) - 6)}{phone[-3:]}"


def build_task(req: RFQRequest) -> str:
    return (
        f"You are an AI sales-operations assistant calling {req.lead_name} at {req.company_name} "
        "on behalf of PackOasis about packaging requirements they previously inquired about or "
        "explicitly permitted us to follow up on. Start by disclosing that you are an AI assistant "
        "and ask whether they are willing to continue. If not, disclose no additional inquiry details "
        "and end the call. The internal inquiry reference is "
        f"{req.request_id}; ask the recipient to confirm that reference or the packaging inquiry context. "
        "Your job is only to collect factual RFQ requirements: box type, dimensions and units, quantity, "
        "material preference, printing, finish, insert, target unit price if they choose to share it, "
        "delivery country, required delivery date, whether a physical sample is needed, whether they have "
        "an existing supplier, decision timeline, whether they want a formal quote, and the next action. "
        "Read back the captured requirements once for correction. Do not promise a price, discount, lead "
        "time, production capability, certification, shipping date, sample approval, or contract term. "
        "Do not collect payment data, credentials, private customer data, or make a binding commercial "
        f"commitment. Known requirements from the existing inquiry: {req.known_requirements}"
    )


def call_arguments(req: RFQRequest) -> dict[str, Any]:
    return {
        "task": build_task(req),
        "recipients": [{"phones": [req.phone], "region": req.region, "locale": req.locale}],
        "result_schema": RESULT_SCHEMA,
        "metadata": {"app": "packoasis-quoteready", "request_id": req.request_id, "company_name": req.company_name},
    }


def idempotency_key(req: RFQRequest) -> str:
    canonical = json.dumps(call_arguments(req), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return f"packoasis-quoteready-{hashlib.sha256(canonical).hexdigest()}"


def preview(req: RFQRequest) -> dict[str, Any]:
    args = call_arguments(req)
    args["recipients"] = [{"phones": [mask_phone(req.phone)], "region": req.region, "locale": req.locale}]
    return {"mode": "preview", "creates_phone_call": False, "request_id": req.request_id, "contact_basis": req.contact_basis, "call_arguments": args, "idempotency_key": idempotency_key(req)}


def confidence(value: Any) -> float:
    if isinstance(value, dict) and isinstance(value.get("score"), (int, float)) and not isinstance(value.get("score"), bool):
        return float(value["score"])
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def valid_result(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(RESULT_SCHEMA["required"]):
        return False
    for field in RESULT_SCHEMA["required"]:
        rule = RESULT_SCHEMA["properties"][field]
        observed = value[field]
        if rule["type"] == "boolean":
            if not isinstance(observed, bool):
                return False
        elif not isinstance(observed, str) or len(observed) > rule.get("maxLength", 10000):
            return False
        elif "enum" in rule and observed not in rule["enum"]:
            return False
    return True


def _recipient_transcript(result: dict[str, Any], destination: str) -> str:
    recipients = result.get("recipients")
    if not isinstance(recipients, list) or len(recipients) != 1 or not isinstance(recipients[0], dict):
        return ""
    if recipients[0].get("phone") != destination:
        return ""
    texts: list[str] = []
    for attempt in recipients[0].get("attempts", []):
        if not isinstance(attempt, dict):
            continue
        for turn in attempt.get("transcript_turns", []):
            if isinstance(turn, dict) and str(turn.get("speaker", "")).lower() in RECIPIENT_SPEAKERS and isinstance(turn.get("text"), str):
                texts.append(turn["text"])
    return "\n".join(texts)


def quote_ready(structured: dict[str, Any]) -> bool:
    unknown = {"", "unknown", "n/a", "not sure"}
    return all(str(structured[field]).strip().casefold() not in unknown for field in QUOTE_READY_FIELDS)


def route_result(req: RFQRequest, result: dict[str, Any], *, expected_call_id: str | None = None) -> dict[str, Any]:
    structured = result.get("structured_result")
    expected_meta = {"app": "packoasis-quoteready", "request_id": req.request_id, "company_name": req.company_name}
    if result.get("status") not in TERMINAL_SUCCESS or result.get("task_completed") is not True or confidence(result.get("completion_confidence")) < MIN_CONFIDENCE:
        return {"route": "human_review", "quote_ready": False, "reason": "CALL-E did not return reliable terminal success"}
    if not valid_result(structured):
        return {"route": "human_review", "quote_ready": False, "reason": "strict result validation failed"}
    assert isinstance(structured, dict)
    evidence = result.get("evidence")
    transcript = _recipient_transcript(result, req.phone)
    if result.get("metadata") != expected_meta or (expected_call_id is not None and result.get("id") != expected_call_id) or not transcript or not isinstance(evidence, list) or not any(isinstance(x, str) and x.strip() for x in evidence):
        return {"route": "human_review", "quote_ready": False, "reason": "result is not bound to approved request/call/destination evidence"}
    if structured["contact_outcome"] == "wrong_contact":
        return {"route": "reroute", "quote_ready": False, "reason": "recipient is not the inquiry contact"}
    if structured["contact_outcome"] != "answered" or structured["continued_after_ai_disclosure"] is not True:
        return {"route": "stop", "quote_ready": False, "reason": "no consented answered conversation"}
    if structured["request_id_confirmed"] is not True or not _contains_sequence(_tokens(transcript), _tokens(req.request_id)):
        return {"route": "human_review", "quote_ready": False, "reason": "inquiry reference was not recipient-corroborated"}
    ready = quote_ready(structured)
    return {"route": "prepare_quote" if ready else "collect_remaining_fields", "quote_ready": ready, "reason": "recipient-corroborated RFQ facts captured"}


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return TOKEN_LIKE.sub("[credential-redacted]", EMAIL_LIKE.sub("[email-redacted]", PHONE_LIKE.sub("[phone-redacted]", value)))
    if isinstance(value, list):
        return [redact(x) for x in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def execute(req: RFQRequest, calls: CallsAPI, *, timeout_seconds: int = 600) -> dict[str, Any]:
    created = calls.create(**call_arguments(req), idempotency_key=idempotency_key(req))
    call_id = created.get("id")
    if not isinstance(call_id, str) or not call_id:
        raise RuntimeError("CALL-E create response did not contain a call id")
    completed = calls.wait_for_result(call_id, timeout_seconds=timeout_seconds, interval_seconds=2)
    return {"mode": "execute", "creates_phone_call": True, "call_id": call_id, "request_id": req.request_id, "status": completed.get("status"), "task_completed": completed.get("task_completed"), "completion_confidence": completed.get("completion_confidence"), "structured_result": redact(completed.get("structured_result")), "evidence_present": bool(completed.get("evidence")), "decision": route_result(req, completed, expected_call_id=call_id)}
