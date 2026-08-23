from pathlib import Path


def test_audit_verifier_is_local_and_protocol_pinned():
    html = (Path(__file__).with_name("audit-verifier.html")).read_text(encoding="utf-8")
    script = html.split("<script>", 1)[1].split("</script>", 1)[0]
    assert "smallbet-permit-ops-v1" in script
    assert "a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56" in script
    assert "crypto.subtle.digest" in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "sendBeacon" not in script
    assert "does not authenticate the author" in html
    assert "packet.schema==='countersignal.audit.v1'" in script
