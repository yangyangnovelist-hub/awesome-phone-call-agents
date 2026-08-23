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
    assert "packet.mode==='live_redacted_ledger'" in script
    assert "live.length>0" in script
    assert "policy.minimum_live_evidence_records===1" in script
    assert "permission_verified===true" in script
    assert "other_non_phone" in script
    assert "PERMISSION_CHANNELS.has(e.permission_channel)" in script
    assert "permission_consented_at" in script
    assert "recipient_binding_verified===true" in script
    assert "recipient_ref.startsWith('call-bound:')" in script
    assert "grounding_verified_before_public_redaction===true" in script
    assert "public_quote_withheld===true" in script
    assert "e.quote===''" in script
