"""Core request, preview, CALL-E arguments, and evidence routing for PermitPulse."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
ALLOWED_CONTACT_BASIS = {"authorized_project", "existing_client", "public_agency_inquiry"}
SUPPORTED_REGIONS = {
    "US", "SG", "MY", "IN", "AE", "AU", "CA", "GB", "VN", "DE", "JP", "FR", "MX",
    "BR", "ID", "PH", "KE", "NL", "PL", "BD", "NG", "OM", "TH", "NA", "CM", "MZ",
    "SA", "FI", "UA", "LK", "BW", "PK", "TR", "HN",
}


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
            "enum": ["answered", "wrong_office", "refused", "voicemail", "unreachable", "unknown"],
        },
        "permit_reference_confirmed": {"type": "boolean"},
        "permit_status": {"type": "string"},
        "missing_items": {"type": "string"},
        "next_milestone": {"type": "string"},
        "processing_window": {"type": "string"},
        "official_source": {"type": "string"},
        "next_contact": {"type": "string"},
        "needs_human_followup": {"type": "boolean"},
    },
}


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
    missing = [key for key in required if not isinstance(payload.get(key), str) or not payload[key].strip()]
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
        raise ValueError("contact_basis must describe an authorized project or factual public-agency inquiry")
    if len(request.project_summary) > 1500:
        raise ValueError("project_summary is too long; keep the spoken context bounded")


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}{'*' * max(4, len(phone) - 6)}{phone[-3:]}"


def idempotency_key(request: PermitRequest) -> str:
    stable = "|".join((request.request_id, request.permit_reference, request.support_phone))
    digest = hashlib.sha256(stable.encode()).hexdigest()[:32]
    return f"permitpulse-{digest}"


def build_task(request: PermitRequest) -> str:
    context = request.project_summary or "No additional project context is necessary."
    return (
        f"You are an AI assistant calling on behalf of {request.caller_business_name} about an "
        f"authorized permit-status inquiry with {request.jurisdiction}. At the start, disclose that "
        "you are an AI assistant. Do not impersonate the applicant, claim authority you do not have, "
        "or ask for protected personal information. The permit/application reference is "
        f"{request.permit_reference}. Ask only for factual process information the office is willing "
        "and authorized to provide: whether the reference is recognized, current status, missing "
        "checklist or correction items, next review or inspection milestone, any processing window "
        "the office is willing to state, where official updates are published, and the correct next "
        "contact or department. If the office cannot verify the record, refuses, requires a human "
        "applicant, or says a written channel is authoritative, record that instead of guessing. "
        f"Known context: {context}"
    )


def call_arguments(request: PermitRequest) -> dict[str, Any]:
    return {
        "task": build_task(request),
        "recipients": [
            {"phones": [request.support_phone], "region": request.region, "locale": request.locale}
        ],
        "result_schema": RESULT_SCHEMA,
        "metadata": {
            "app": "permitpulse",
            "request_id": request.request_id,
            "permit_reference": request.permit_reference,
        },
    }


def preview(request: PermitRequest) -> dict[str, Any]:
    return {
        "mode": "preview",
        "creates_phone_call": False,
        "request_id": request.request_id,
        "destination": mask_phone(request.support_phone),
        "contact_basis": request.contact_basis,
        "idempotency_key": idempotency_key(request),
        "task": build_task(request),
        "result_schema": RESULT_SCHEMA,
    }


def _has_evidence(result: dict[str, Any]) -> bool:
    evidence = result.get("evidence")
    return isinstance(evidence, list) and any(isinstance(item, str) and item.strip() for item in evidence)


def route_result(result: dict[str, Any]) -> dict[str, str]:
    structured = result.get("structured_result")
    if result.get("status") != "completed" or result.get("task_completed") is not True:
        return {"route": "human_review", "reason": "call did not complete successfully"}
    if not isinstance(structured, dict):
        return {"route": "human_review", "reason": "missing structured result"}
    outcome = structured.get("contact_outcome")
    if outcome == "wrong_office":
        return {"route": "reroute", "reason": "office said another contact is responsible"}
    if outcome != "answered":
        return {"route": "human_followup", "reason": f"contact outcome was {outcome or 'unknown'}"}
    if not _has_evidence(result):
        return {"route": "human_review", "reason": "no provider evidence supports the result"}
    if structured.get("permit_reference_confirmed") is not True:
        return {"route": "human_review", "reason": "permit reference was not confirmed"}
    if structured.get("needs_human_followup") is True:
        return {"route": "human_followup", "reason": "office requested or outcome requires a human"}
    return {"route": "update_project_record", "reason": "evidence-backed permit facts are actionable"}


def execute(
    request: PermitRequest,
    calls: CallsAPI,
    *,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    created = calls.create(**call_arguments(request), idempotency_key=idempotency_key(request))
    call_id = created.get("id")
    if not isinstance(call_id, str) or not call_id:
        raise RuntimeError("CALL-E create response did not contain a call id")
    completed = calls.wait_for_result(call_id, timeout_seconds=timeout_seconds, interval_seconds=2)
    return {
        "mode": "execute",
        "creates_phone_call": True,
        "request_id": request.request_id,
        "call_id": call_id,
        "idempotency_key": idempotency_key(request),
        "status": completed.get("status"),
        "task_completed": completed.get("task_completed"),
        "completion_confidence": completed.get("completion_confidence"),
        "structured_result": completed.get("structured_result"),
        "evidence": completed.get("evidence"),
        "decision": route_result(completed),
    }


def dumps_preview(request: PermitRequest) -> str:
    return json.dumps(preview(request), ensure_ascii=False, indent=2)
