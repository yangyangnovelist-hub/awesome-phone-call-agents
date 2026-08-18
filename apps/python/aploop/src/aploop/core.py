"""Core request, preview, CALL-E arguments, and result routing for APLoop."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Protocol

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
ALLOWED_CONTACT_BASIS = {"existing_customer", "vendor_relationship", "explicit_permission"}
SUPPORTED_REGIONS = {
    "US", "SG", "MY", "IN", "AE", "AU", "CA", "GB", "VN", "DE", "JP", "FR", "MX",
    "BR", "ID", "PH", "KE", "NL", "PL", "BD", "NG", "OM", "TH", "NA", "CM", "MZ",
    "SA", "FI", "UA", "LK", "BW", "PK", "TR", "HN",
}


@dataclass(frozen=True)
class InvoiceRequest:
    request_id: str
    caller_business_name: str
    customer_company: str
    invoice_reference: str
    support_phone: str
    region: str
    locale: str
    contact_basis: str
    invoice_context: str = ""


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
        "invoice_reference_confirmed",
        "invoice_received",
        "payment_status",
        "missing_documents",
        "dispute_reason",
        "expected_payment_date",
        "next_contact",
        "next_action",
        "needs_human_followup",
    ],
    "properties": {
        "contact_outcome": {
            "type": "string",
            "enum": ["answered", "wrong_desk", "refused", "voicemail", "unreachable", "unknown"],
        },
        "invoice_reference_confirmed": {"type": "boolean"},
        "invoice_received": {"type": "boolean"},
        "payment_status": {
            "type": "string",
            "enum": [
                "pending_approval",
                "approved",
                "scheduled",
                "paid",
                "disputed",
                "not_found",
                "unknown",
            ],
        },
        "missing_documents": {"type": "string"},
        "dispute_reason": {"type": "string"},
        "expected_payment_date": {"type": "string"},
        "next_contact": {"type": "string"},
        "next_action": {"type": "string"},
        "needs_human_followup": {"type": "boolean"},
    },
}


def parse_request(payload: dict[str, Any]) -> InvoiceRequest:
    required = (
        "request_id",
        "caller_business_name",
        "customer_company",
        "invoice_reference",
        "support_phone",
        "region",
        "locale",
        "contact_basis",
    )
    missing = [key for key in required if not isinstance(payload.get(key), str) or not payload[key].strip()]
    if missing:
        raise ValueError(f"missing required string fields: {', '.join(missing)}")
    request = InvoiceRequest(
        request_id=payload["request_id"].strip(),
        caller_business_name=payload["caller_business_name"].strip(),
        customer_company=payload["customer_company"].strip(),
        invoice_reference=payload["invoice_reference"].strip(),
        support_phone=payload["support_phone"].strip(),
        region=payload["region"].strip().upper(),
        locale=payload["locale"].strip(),
        contact_basis=payload["contact_basis"].strip(),
        invoice_context=str(payload.get("invoice_context", "")).strip(),
    )
    validate_request(request)
    return request


def validate_request(request: InvoiceRequest) -> None:
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", request.request_id):
        raise ValueError("request_id must be a stable 3-100 character safe identifier")
    if not E164.fullmatch(request.support_phone):
        raise ValueError("support_phone must be E.164")
    if request.region not in SUPPORTED_REGIONS:
        raise ValueError(f"unsupported CALL-E recipient region: {request.region}")
    if request.contact_basis not in ALLOWED_CONTACT_BASIS:
        raise ValueError("live workflow is limited to an existing B2B relationship or explicit permission")
    if len(request.invoice_context) > 1200:
        raise ValueError("invoice_context is too long; keep the spoken briefing bounded")


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}{'*' * max(4, len(phone) - 6)}{phone[-3:]}"


def idempotency_key(request: InvoiceRequest) -> str:
    stable = "|".join((request.request_id, request.invoice_reference, request.support_phone))
    return f"aploop-{hashlib.sha256(stable.encode()).hexdigest()[:32]}"


def build_task(request: InvoiceRequest) -> str:
    context = request.invoice_context or "No additional invoice context is needed."
    return (
        f"You are an AI assistant calling the accounts-payable/business contact at "
        f"{request.customer_company} on behalf of {request.caller_business_name} about an existing "
        f"B2B invoice, reference {request.invoice_reference}. Disclose that you are an AI assistant "
        "at the start. This is a status and blocker follow-up, not a debt-negotiation call. Confirm "
        "whether the invoice reference is recognized and received, current AP status, whether a PO, "
        "receipt, tax document, approval, or other ordinary business document is missing, whether "
        "there is a dispute and its high-level business reason, any expected payment date the "
        "recipient is willing to state, and the correct AP follow-up contact or next action. Do not "
        "ask for or accept card numbers, bank credentials, passwords, security codes, tax IDs, or "
        "other secrets. Do not provide changed payment instructions, threaten consequences, claim "
        "legal rights, negotiate a discount or settlement, or make a binding commercial commitment. "
        "If a payment-instruction change or sensitive verification is raised, direct the recipient "
        "to the parties' established secure channel and mark human follow-up. If the invoice cannot "
        f"be verified, say so rather than guessing. Known context: {context}"
    )


def call_arguments(request: InvoiceRequest) -> dict[str, Any]:
    return {
        "task": build_task(request),
        "recipients": [
            {"phones": [request.support_phone], "region": request.region, "locale": request.locale}
        ],
        "result_schema": RESULT_SCHEMA,
        "metadata": {
            "app": "aploop",
            "request_id": request.request_id,
            "invoice_reference": request.invoice_reference,
        },
    }


def preview(request: InvoiceRequest) -> dict[str, Any]:
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
    if outcome == "wrong_desk":
        return {"route": "reroute", "reason": "recipient identified a different AP contact"}
    if outcome != "answered":
        return {"route": "follow_up", "reason": f"contact outcome was {outcome or 'unknown'}"}
    if not _has_evidence(result):
        return {"route": "human_review", "reason": "no provider evidence supports the result"}
    if structured.get("invoice_reference_confirmed") is not True:
        return {"route": "human_review", "reason": "invoice reference was not confirmed"}
    if structured.get("payment_status") == "disputed" or structured.get("needs_human_followup") is True:
        return {"route": "human_action", "reason": "dispute or sensitive blocker requires a person"}
    if structured.get("payment_status") in {"approved", "scheduled", "paid"}:
        return {"route": "record_payment_status", "reason": "evidence-backed AP status is actionable"}
    return {"route": "follow_up", "reason": "invoice remains in a non-terminal AP workflow state"}


def execute(
    request: InvoiceRequest,
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
