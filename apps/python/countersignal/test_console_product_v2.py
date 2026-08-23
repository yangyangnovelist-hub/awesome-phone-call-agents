from pathlib import Path


def test_decision_audit_console_keeps_product_v2_contract():
    html = (Path(__file__).with_name("judge-console.html")).read_text(encoding="utf-8")

    assert "Customer research that can prove you wrong." in html
    assert "Decision replay" in html
    assert "Adversarial evidence queue" in html
    assert "Contradiction stress benchmark" in html
    assert "Export audit JSON" in html
    assert "Load audit JSON" in html
    assert "countersignal.audit.v1" in html
    assert "a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56" in html


def test_console_preserves_safe_local_reviewer_boundary():
    html = (Path(__file__).with_name("judge-console.html")).read_text(encoding="utf-8")

    assert "Deterministic reviewer mode · NO CALL" in html
    assert "Silence never enters the answered denominator" in html
    assert "Nothing is uploaded" in html
    assert "fetch(" not in html
