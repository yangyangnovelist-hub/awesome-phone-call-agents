from aploop.core import (
    InvoiceRequest,
    build_task,
    idempotency_key,
    parse_request,
    preview,
    route_result,
)


def sample() -> InvoiceRequest:
    return InvoiceRequest(
        request_id="invoice-001",
        caller_business_name="Example Supplier",
        customer_company="Example Customer",
        invoice_reference="INV-123",
        support_phone="+15555550102",
        region="US",
        locale="en-US",
        contact_basis="existing_customer",
        invoice_context="Invoice already issued through the normal business channel",
    )


def structured(status="scheduled", **overrides):
    value = {
        "contact_outcome": "answered",
        "continued_after_ai_disclosure": True,
        "invoice_reference_confirmed": True,
        "invoice_received": True,
        "payment_status": status,
        "missing_documents": "none",
        "dispute_reason": "none",
        "expected_payment_date": "Friday",
        "next_contact": "accounts payable",
        "next_action": "check remittance after Friday",
        "needs_human_followup": False,
    }
    value.update(overrides)
    return value


def provider_result(
    *,
    result=None,
    transcript="Invoice INV 123 is scheduled for Friday.",
    evidence=True,
    metadata=None,
    call_id="call-123",
    destination="+15555550102",
    confidence=0.95,
):
    request = sample()
    return {
        "id": call_id,
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": confidence, "label": "high"},
        "evidence": ["AP confirmed the invoice status."] if evidence else [],
        "structured_result": result or structured(),
        "metadata": metadata
        or {
            "app": "aploop",
            "request_id": request.request_id,
            "invoice_reference": request.invoice_reference,
        },
        "recipients": [
            {
                "phone": destination,
                "attempts": [
                    {
                        "transcript_turns": [
                            {"speaker": "recipient", "text": transcript},
                        ]
                    }
                ],
            }
        ],
    }


def test_preview_never_creates_call_or_exposes_full_phone():
    out = preview(sample())
    assert out["creates_phone_call"] is False
    assert out["destination"].startswith("+15")
    assert "+15555550102" not in str(out)


def test_task_discloses_ai_requires_consent_and_blocks_sensitive_behavior():
    task = build_task(sample())
    assert "Disclose that you are an AI assistant" in task
    assert "willing to continue" in task
    assert "Do not ask for or accept card numbers" in task
    assert "Do not provide changed payment instructions" in task
    assert "negotiate a discount or settlement" in task


def test_idempotency_is_stable_and_changes_with_reference():
    first = sample()
    second = InvoiceRequest(**{**first.__dict__, "invoice_reference": "INV-124"})
    assert idempotency_key(first) == idempotency_key(first)
    assert idempotency_key(first) != idempotency_key(second)


def test_parse_rejects_cold_contact_basis():
    payload = {
        "request_id": "invoice-001",
        "caller_business_name": "Example Supplier",
        "customer_company": "Example Customer",
        "invoice_reference": "INV-123",
        "support_phone": "+15555550102",
        "region": "US",
        "locale": "en-US",
        "contact_basis": "cold_prospect",
    }
    try:
        parse_request(payload)
    except ValueError as exc:
        assert "existing B2B relationship" in str(exc)
    else:
        raise AssertionError("cold prospect should fail")


def test_scheduled_payment_requires_binding_evidence_and_invoice_corroboration():
    request = sample()
    good = provider_result()
    assert route_result(request, good, expected_call_id="call-123")["route"] == (
        "record_payment_status"
    )

    assert route_result(request, provider_result(evidence=False))["route"] == "human_review"
    assert route_result(request, provider_result(destination="+15555550199"))["route"] == (
        "human_review"
    )
    assert route_result(request, good, expected_call_id="other-call")["route"] == "human_review"


def test_invoice_prefix_is_not_enough_to_drive_payment_status():
    result = provider_result(transcript="Invoice INV 12 is scheduled for Friday.")
    assert route_result(sample(), result)["route"] == "human_review"


def test_dispute_routes_to_human_action():
    result = provider_result(result=structured("disputed", dispute_reason="PO mismatch"))
    assert route_result(sample(), result)["route"] == "human_action"


def test_pending_approval_stays_in_follow_up():
    result = provider_result(result=structured("pending_approval"))
    assert route_result(sample(), result)["route"] == "follow_up"


def test_ai_disclosure_refusal_never_records_payment_status():
    result = provider_result(
        result=structured(continued_after_ai_disclosure=False),
        transcript="I do not want to continue. Invoice INV 123.",
    )
    assert route_result(sample(), result)["route"] == "human_review"


def test_low_confidence_never_drives_action():
    assert route_result(sample(), provider_result(confidence=0.4))["route"] == "human_review"


def test_wrong_desk_routes_only_when_call_is_bound():
    wrong = structured(
        contact_outcome="wrong_desk",
        continued_after_ai_disclosure=True,
        invoice_reference_confirmed=False,
        needs_human_followup=True,
    )
    result = provider_result(result=wrong, transcript="Please call the AP desk instead.")
    assert route_result(sample(), result)["route"] == "reroute"

    result["metadata"]["request_id"] = "different-request"
    assert route_result(sample(), result)["route"] == "human_review"
