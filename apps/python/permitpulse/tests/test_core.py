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


def test_preview_never_creates_call():
    out = preview(sample())
    assert out["creates_phone_call"] is False
    assert out["destination"].startswith("+15")
    assert "AI assistant" in out["task"]
    assert "+15555550101" not in str(out)


def test_idempotency_is_stable_and_changes_with_reference():
    first = sample()
    second = PermitRequest(**{**first.__dict__, "permit_reference": "PERMIT-124"})
    assert idempotency_key(first) == idempotency_key(first)
    assert idempotency_key(first) != idempotency_key(second)


def test_task_forbids_impersonation_and_protected_personal_data():
    task = build_task(sample())
    assert "Do not impersonate the applicant" in task
    assert "protected personal information" in task


def test_parse_rejects_unsupported_region():
    payload = {
        "request_id": "permit-001",
        "caller_business_name": "Example",
        "jurisdiction": "Example City",
        "permit_reference": "P-1",
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


def test_actionable_result_requires_evidence_and_confirmed_reference():
    base = {
        "status": "completed",
        "task_completed": True,
        "structured_result": {
            "contact_outcome": "answered",
            "permit_reference_confirmed": True,
            "permit_status": "plan review",
            "missing_items": "none",
            "next_milestone": "review completion",
            "processing_window": "5 business days",
            "official_source": "city permit portal",
            "next_contact": "plan review desk",
            "needs_human_followup": False,
        },
    }
    assert route_result(base)["route"] == "human_review"
    base["evidence"] = ["The clerk confirmed permit PERMIT-123 is in plan review."]
    assert route_result(base)["route"] == "update_project_record"


def test_wrong_office_routes_without_guessing():
    result = {
        "status": "completed",
        "task_completed": True,
        "evidence": ["This is the wrong department."],
        "structured_result": {
            "contact_outcome": "wrong_office",
            "permit_reference_confirmed": False,
            "permit_status": "unknown",
            "missing_items": "unknown",
            "next_milestone": "unknown",
            "processing_window": "unknown",
            "official_source": "unknown",
            "next_contact": "zoning desk",
            "needs_human_followup": True,
        },
    }
    assert route_result(result)["route"] == "reroute"
