from permitpulse.core import (
    PermitRequest,
    build_task,
    idempotency_key,
    parse_request,
    preview,
    route_result,
)


def sample() -> PermitRequest:
    return PermitRequest(
        request_id="permit-001",
        caller_business_name="Example Permit Ops",
        jurisdiction="Example City Building Department",
        permit_reference="PERMIT-123",
        support_phone="+15555550101",
        region="US",
        locale="en-US",
        contact_basis="authorized_project",
        project_summary="Commercial renovation",
    )


def structured(**overrides):
    value = {
        "contact_outcome": "answered",
        "continued_after_ai_disclosure": True,
        "permit_reference_confirmed": True,
        "permit_status": "plan review",
        "missing_items": "none",
        "next_milestone": "review completion",
        "processing_window": "5 business days",
        "official_source": "city permit portal",
        "next_contact": "plan review desk",
        "needs_human_followup": False,
    }
    value.update(overrides)
    return value


def provider_result(
    *,
    result=None,
    transcript="Permit PERMIT 123 is in plan review.",
    evidence=True,
    metadata=None,
    call_id="call-123",
    destination="+15555550101",
    confidence=0.95,
):
    request = sample()
    return {
        "id": call_id,
        "status": "completed",
        "task_completed": True,
        "completion_confidence": {"score": confidence, "label": "high"},
        "structured_result": result or structured(),
        "evidence": ["Recipient supplied permit status facts."] if evidence else [],
        "metadata": metadata
        or {
            "app": "permitpulse",
            "request_id": request.request_id,
            "permit_reference": request.permit_reference,
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
    assert "AI assistant" in out["call_arguments"]["task"]
    assert "+15555550101" not in str(out)


def test_idempotency_is_stable_and_changes_with_reference():
    first = sample()
    second = PermitRequest(**{**first.__dict__, "permit_reference": "PERMIT-124"})
    assert idempotency_key(first) == idempotency_key(first)
    assert idempotency_key(first) != idempotency_key(second)


def test_task_forbids_impersonation_and_requires_ai_consent():
    task = build_task(sample())
    assert "Do not impersonate the applicant" in task
    assert "protected personal information" in task
    assert "willing to continue" in task


def test_parse_rejects_unsupported_region():
    payload = {
        "request_id": "permit-001",
        "caller_business_name": "Example",
        "jurisdiction": "Example City",
        "permit_reference": "PERMIT-123",
        "support_phone": "+15555550101",
        "region": "ZZ",
        "locale": "en-US",
        "contact_basis": "authorized_project",
    }
    try:
        parse_request(payload)
    except ValueError as exc:
        assert "unsupported CALL-E recipient region" in str(exc)
    else:
        raise AssertionError("unsupported region should fail")


def test_parse_rejects_reference_too_short_to_corroborate():
    payload = {
        "request_id": "permit-001",
        "caller_business_name": "Example",
        "jurisdiction": "Example City",
        "permit_reference": "P-1",
        "support_phone": "+15555550101",
        "region": "US",
        "locale": "en-US",
        "contact_basis": "authorized_project",
    }
    try:
        parse_request(payload)
    except ValueError as exc:
        assert "too short to corroborate" in str(exc)
    else:
        raise AssertionError("short reference should fail")


def test_actionable_result_requires_full_binding_and_reference_corroboration():
    request = sample()
    good = provider_result()
    assert route_result(request, good, expected_call_id="call-123")["route"] == (
        "update_project_record"
    )

    assert route_result(request, provider_result(evidence=False))["route"] == "human_review"
    assert route_result(request, provider_result(destination="+15555550199"))["route"] == (
        "human_review"
    )
    assert route_result(request, good, expected_call_id="other-call")["route"] == "human_review"


def test_reference_prefix_is_not_enough_to_drive_action():
    result = provider_result(transcript="Permit PERMIT 12 is in plan review.")
    assert route_result(sample(), result)["route"] == "human_review"


def test_ai_disclosure_refusal_never_updates_project_record():
    result = provider_result(
        result=structured(continued_after_ai_disclosure=False),
        transcript="I do not want to continue. Permit PERMIT 123.",
    )
    assert route_result(sample(), result)["route"] == "human_review"


def test_low_confidence_never_drives_action():
    assert route_result(sample(), provider_result(confidence=0.4))["route"] == "human_review"


def test_wrong_office_routes_only_when_call_is_bound():
    wrong = structured(
        contact_outcome="wrong_office",
        continued_after_ai_disclosure=True,
        permit_reference_confirmed=False,
        needs_human_followup=True,
    )
    result = provider_result(result=wrong, transcript="This is the wrong department.")
    assert route_result(sample(), result)["route"] == "reroute"

    result["metadata"]["request_id"] = "different-request"
    assert route_result(sample(), result)["route"] == "human_review"
