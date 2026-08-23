# CounterSignal live proof workflow

The preferred proof path is `prove_live.py`, not the raw core CLI. It keeps the real-call boundary explicit while making the default output safe to show in a terminal recording or judge demo.

## 1. Preview first — zero calls

```bash
python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient recipient.json
```

Preview masks the destination, shows the frozen protocol identity and CALL-E task, and places no call.

## 2. Record affirmative permission before any proof call

A reviewed phone number is not enough. The live proof runner requires a private local permission receipt from a **non-phone** channel before it will cross the CALL-E boundary.

Example `permission.json`:

```json
{
  "experiment_id": "smallbet-permit-ops-v1",
  "phone": "+15551234567",
  "ai_interview_opt_in": true,
  "channel": "email",
  "consented_at": "2026-08-23T13:30:00+08:00",
  "statement": "I agree to receive one AI-assisted customer research interview by phone."
}
```

Accepted permission channels are `email`, `sms`, `web_form`, `in_person`, and `other_non_phone`. A phone call cannot be used to establish permission for the proof call itself. The consent timestamp must include a timezone.

The receipt is private because it contains the destination and consent statement. It must not be committed or uploaded to the public demo.

## 3. Run one permissioned live interview

```bash
export CALLE_API_KEY="<key>"
export CALLE_LIVE_CALLS_ENABLED=true

python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient recipient.json \
  --permission-receipt permission.json \
  --execute \
  --confirm-one-reviewed-recipient \
  --allow +15551234567
```

Before importing the CALL-E SDK or reading the production API key, the proof runner verifies that the receipt has `ai_interview_opt_in=true`, matches the exact experiment and reviewed recipient, uses an allowed non-phone channel, and contains a timezone-aware consent time. The exact destination must also match `--allow`.

## 4. What is persisted publicly

By default the live proof runner writes two local artifacts:

- `data/countersignal-audit.sqlite3` — append-only API over a redacted evidence ledger;
- `data/countersignal-audit.json` — sealed portable `countersignal.audit.v1` packet for the browser Decision Audit Console.

The redacted evidence record contains:

- CALL-E call ID;
- experiment ID and protocol hash;
- an opaque call-bound public reference derived from experiment/protocol/call identity, **not from the phone number**;
- `permission_verified=true`, the non-phone permission channel, and consent timestamp — but not the private receipt statement or destination;
- `recipient_binding_verified`, recorded only after the raw provider recipient matches the reviewed destination;
- classification bucket and confidence;
- whether the accepted key quote was transcript-grounded;
- the already-grounded key quote;
- disposition and conservative classification reason.

It does **not** contain the phone number, a phone-derived hash, the private permission statement, or the full transcript.

Every `calle_live` record in the public proof packet must have affirmative permission proof, exact recipient binding, and — when it enters the answered denominator — a grounded transcript quote. Missing any of those conditions fails closed.

The same call ID can be appended twice only when the redacted record is byte-for-byte equivalent after canonicalization. A conflicting second record for the same call ID fails closed.

## 5. Raw provider result is opt-in only

The live proof runner never prints the raw provider payload. If a private debugging copy is required, it must be requested explicitly:

```bash
python prove_live.py ... \
  --private-result-out private/call_001.json
```

The writer refuses to overwrite an existing file. Raw provider payloads may contain participant identity or transcript material and must never be committed, uploaded to the judge demo, or placed in the public audit packet.

## 6. Content seal and independent verification

Each exported audit JSON carries `countersignal.content-seal.v1`, a deterministic SHA-256 digest over canonical packet content excluding the seal itself.

Open `audit-verifier.html` and drop the JSON onto the page. The verifier recomputes the digest locally and checks:

- the exact SmallBet experiment ID and protocol hash;
- affirmative permission proof on every live record;
- a supported non-phone permission channel and consent timestamp;
- exact recipient-binding verification;
- call-bound rather than phone-derived public references;
- transcript grounding for every answered live record; and
- absence of obvious raw phone/recipient fields.

The verifier uses no network request API.

The seal detects changes to the exported packet after the digest was computed. It is deliberately **not** described as an identity signature, trusted timestamp, verification of the private consent statement itself, or tamper-proof external anchor; someone able to rewrite the whole packet can compute a new digest.

## 7. Load the result into the judge console

Open `judge-console.html`, choose **Load audit JSON**, and select `data/countersignal-audit.json`.

The browser checks the audit schema, experiment ID, and exact protocol hash before replacing the simulated reviewer fixture. Imported data stays local to the browser; the console performs no network `fetch()`.

## 8. Zero-credential verification

Before recording the final demo:

```bash
python verify_product_v2.py
python benchmark.py --json
python -m pytest -q
```

The test suite separately exercises permission-receipt validation, missing-permission failure before live configuration, public proof projection, binding/grounding requirements, content sealing, benchmark divergence, and browser no-network invariants.

## Claim boundary

A successful proof demonstrates that a permissioned CALL-E result can be bound to the frozen experiment, converted into redacted evidence, durably accumulated, replayed, content-sealed, independently checked, and allowed to change the pre-registered decision. It does not prove product-market fit, population prevalence, ROI, statistical significance, author identity, that an external trusted party witnessed the consent, or an external timestamp.
