from aploop.core import InvoiceRequest, build_task, idempotency_key, parse_request, preview, route_result


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


def test_preview_never_creates_call_or_exposes_full_phone():
    out = preview(sample())
    assert out["creates_phone_call"] is False
    assert out["destination"].startswith("+15")
    assert "+15555550102" not in str(out)


def test_task_discloses_ai_and_blocks_sensitive_collection_behavior():
    task = build_task(sample())
    assert "Disclose that you are an AI assistant" in task
    assert "Do not ask for or accept card numbers" in task
    assert "Do not provide changed payment instructions" in task
    assert "negotiate a discount or settlement" in task


def test_idempotency_is_stable():
    assert idempotency_key(sample()) == idempotency_key(sample())


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


def completed(status: str, *, evidence: bool = True, followup: bool = False):
    return {
        "status": "completed",
        "task_completed": True,
        "evidence": ["AP confirmed the invoice status."] if evidence else [],
        "structured_result": {
            "contact_outcome": "answered",
            "invoice_reference_confirmed": True,
            "invoice_received": True,
            "payment_status": status,
            "missing_documents": "none",
            "dispute_reason": "none",
            "expected_payment_date": "Friday",
            "next_contact": "accounts payable",
            "next_action": "check remittance after Friday",
            "needs_human_followup": followup,
        },
    }


def test_scheduled_payment_requires_evidence():
    assert route_result(completed("scheduled", evidence=False))["route"] == "human_review"
    assert route_result(completed("scheduled"))["route"] == "record_payment_status"


def test_dispute_routes_to_human_action():
    assert route_result(completed("disputed"))["route"] == "human_action"


def test_pending_approval_stays_in_follow_up():
    assert route_result(completed("pending_approval"))["route"] == "follow_up"
