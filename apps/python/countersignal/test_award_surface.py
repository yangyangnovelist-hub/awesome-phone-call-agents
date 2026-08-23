from pathlib import Path


def _html() -> str:
    return (Path(__file__).with_name("index.html")).read_text(encoding="utf-8")


def _script(html: str) -> str:
    return html.split("<script>", 1)[1].split("</script>", 1)[0]


def test_award_surface_tells_the_decision_integrity_story():
    html = _html()
    assert "Customer research that can prove you wrong." in html
    assert "Decision integrity for AI customer research" in html
    assert "Not a prettier summary. A different epistemic policy." in html
    assert "Try to kill the hypothesis." in html
    assert "Why 8 / 5 / 3" in html
    assert "An asymmetric loss policy, not a significance test." in html
    assert "CI GREEN" in html
    assert "10K" in html
    assert "46/46" not in html
    assert "smallbet-permit-ops-v1" in html
    assert "a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56" in html


def test_award_surface_keeps_the_frozen_rule_and_honest_denominator_visible():
    html = _html()
    script = _script(html)
    assert "8 MIN ANSWERED" in html
    assert "5 SUPPORT" in html
    assert "3 CONTRADICTIONS WEAKEN" in html
    assert "Attempt increases. Answered stays 8." in html
    assert "First contradiction removes support." in html
    assert "Third contradiction crosses frozen threshold." in html
    assert "state.nonresponse++" in script
    assert "state.answered++" in script
    assert "state.contra>=3" in script


def test_award_surface_verifies_live_proof_fail_closed_and_locally():
    html = _html()
    script = _script(html)
    assert "crypto.subtle.digest" in script
    assert "p.mode==='live_redacted_ledger'" in script
    assert "live.length>0" in script
    assert "live.length===evidence.length" in script
    assert "policy.minimum_live_evidence_records===1" in script
    assert "policy.live_evidence_only===true" in script
    assert "permission_verified===true" in script
    assert "CHANNELS.has(e.permission_channel)" in script
    assert "permission_consented_at" in script
    assert "recipient_binding_verified===true" in script
    assert "recipient_ref.startsWith('call-bound:')" in script
    assert "grounding_verified_before_public_redaction===true" in script
    assert "public_quote_withheld===true" in script
    assert "e.quote===''" in script
    assert "other_non_phone" in script  # legacy schema value; UI calls these non-call channels.
    assert 'raw.includes(\'"phone"\')' in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "sendBeacon" not in script


def test_award_surface_routes_to_deeper_reviewer_tools():
    html = _html()
    assert 'href="judge-console.html"' in html
    assert 'href="audit-verifier.html"' in html
    assert "python verify_product_v2.py" in html
    assert "python benchmark.py --json" in html
    assert "python policy_stress.py --trials 10000 --seed 20260823 --json" in html
    assert "python -m pytest -q" in html
