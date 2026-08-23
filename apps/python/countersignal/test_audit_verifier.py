from pathlib import Path


def test_audit_verifier_is_local_and_protocol_pinned():
    html = (Path(__file__).with_name("audit-verifier.html")).read_text(encoding="utf-8")
    assert "smallbet-permit-ops-v1" in html
    assert "a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56" in html
    assert "crypto.subtle.digest" in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" in html  # only appears in the explicit no-network footer
    assert "does not authenticate the author" in html
    assert 'packet.schema===\'countersignal.audit.v1\'' in html
