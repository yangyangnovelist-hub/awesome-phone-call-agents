from quoteready.core import RFQRequest, build_task, idempotency_key, parse_request, preview, quote_ready, route_result


def request() -> RFQRequest:
    return RFQRequest(
        request_id="RFQ-EXAMPLE-001",
        lead_name="Alex",
        company_name="Example Skincare",
        phone="+15555550103",
        region="US",
        locale="en-US",
        contact_basis="inbound_inquiry",
        known_requirements="Buyer asked about 50,000 custom skincare boxes.",
    )


def structured(**overrides):
    value = {
        "contact_outcome": "answered",
        "continued_after_ai_disclosure": True,
        "request_id_confirmed": True,
        "box_type": "rigid box",
        "dimensions": "100 x 60 x 40 mm",
        "quantity": "50000",
        "material": "1200 gsm greyboard with art paper wrap",
        "printing": "CMYK exterior",
        "finish": "matte lamination",
        "insert": "paper insert",
        "target_unit_price": "USD 0.35",
        "delivery_country": "United States",
        "required_delivery_date": "within 8 weeks",
        "sample_required": "yes",
        "existing_supplier": "yes",
        "decision_timeline": "this month",
        "quote_requested": "yes",
        "next_action": "send formal quotation and sample options",
    }
    value.update(overrides)
    return value


def result(*, payload=None, transcript="Yes, this is RFQ EXAMPLE 001. We need 50,000 rigid boxes.", evidence=True, destination="+15555550103", call_id="call-1", confidence=0.95):
    req = request()
    return {
        "id": call_id,
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": confidence, "label": "high"},
        "structured_result": payload or structured(),
        "evidence": ["Buyer confirmed the RFQ and requirements."] if evidence else [],
        "metadata": {"app": "packoasis-quoteready", "request_id": req.request_id, "company_name": req.company_name},
        "recipients": [{"phone": destination, "attempts": [{"transcript_turns": [{"speaker": "recipient", "text": transcript}]}]}],
    }


def test_preview_masks_phone_and_creates_no_call():
    out = preview(request())
    assert out["creates_phone_call"] is False
    assert request().phone not in str(out)
    assert "AI assistant" in out["call_arguments"]["task"]


def test_cold_prospect_is_rejected():
    raw = request().__dict__.copy()
    raw["contact_basis"] = "cold_prospect"
    try:
        parse_request(raw)
    except ValueError as exc:
        assert "warm-followup" in str(exc)
    else:
        raise AssertionError("cold prospect should fail")


def test_task_cannot_commit_price_or_terms():
    task = build_task(request())
    assert "Do not promise a price" in task
    assert "binding commercial commitment" in task


def test_idempotency_changes_when_business_request_changes():
    first = request()
    second = RFQRequest(**{**first.__dict__, "request_id": "RFQ-EXAMPLE-002"})
    assert idempotency_key(first) == idempotency_key(first)
    assert idempotency_key(first) != idempotency_key(second)


def test_quote_ready_requires_operational_minimum_fields():
    assert quote_ready(structured()) is True
    assert quote_ready(structured(dimensions="unknown")) is False


def test_prepare_quote_requires_call_destination_and_transcript_binding():
    req = request()
    good = result()
    assert route_result(req, good, expected_call_id="call-1")["route"] == "prepare_quote"
    assert route_result(req, result(evidence=False))["route"] == "human_review"
    assert route_result(req, result(destination="+15555550199"))["route"] == "human_review"
    assert route_result(req, good, expected_call_id="other")["route"] == "human_review"


def test_reference_prefix_is_not_corroboration():
    assert route_result(request(), result(transcript="This is RFQ EXAMPLE 00."))["route"] == "human_review"


def test_missing_field_routes_to_collect_remaining_fields():
    incomplete = structured(dimensions="unknown")
    out = route_result(request(), result(payload=incomplete))
    assert out["route"] == "collect_remaining_fields"
    assert out["quote_ready"] is False


def test_refusal_after_ai_disclosure_stops():
    refused = structured(contact_outcome="refused", continued_after_ai_disclosure=False, request_id_confirmed=False)
    out = route_result(request(), result(payload=refused, transcript="I do not want to continue."))
    assert out["route"] == "stop"


def test_low_confidence_never_drives_quote():
    assert route_result(request(), result(confidence=0.5))["route"] == "human_review"
