# CounterSignal live proof workflow

The preferred proof path is `prove_live.py`, not the raw core CLI. It keeps the real-call boundary explicit while making the default output safe to show in a terminal recording or judge demo.

## 1. Preview first — zero calls

```bash
python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient recipient.json
```

Preview masks the destination, shows the frozen protocol identity and CALL-E task, and places no call.

## 2. Run one permissioned live interview

Only use a recipient who affirmatively opted in to the AI research interview.

```bash
export CALLE_API_KEY="<key>"
export CALLE_LIVE_CALLS_ENABLED=true

python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient recipient.json \
  --execute \
  --confirm-one-reviewed-recipient \
  --allow +15551234567
```

The exact destination must match `--allow`. The production API origin remains pinned by `countersignal.py`.

## 3. What is persisted

By default the live proof runner writes two local artifacts:

- `data/countersignal-audit.sqlite3` — append-only API over a redacted evidence ledger;
- `data/countersignal-audit.json` — sealed portable `countersignal.audit.v1` packet for the browser Decision Audit Console.

The redacted evidence record contains:

- CALL-E call ID;
- experiment ID and protocol hash;
- an opaque call-bound public reference derived from experiment/protocol/call identity, **not from the phone number**;
- `recipient_binding_verified`, recorded only after the raw provider recipient matches the reviewed destination;
- classification bucket;
- confidence;
- whether the accepted key quote was transcript-grounded;
- the already-grounded key quote;
- disposition and conservative classification reason.

It does **not** contain the phone number, a phone-derived hash, or the full transcript.

The same call ID can be appended twice only when the redacted record is byte-for-byte equivalent after canonicalization. A conflicting second record for the same call ID fails closed.

## 4. Raw provider result is opt-in only

The live proof runner never prints the raw provider payload. If a private debugging copy is required, it must be requested explicitly:

```bash
python prove_live.py ... \
  --private-result-out private/call_001.json
```

The writer refuses to overwrite an existing file. Raw provider payloads may contain participant identity or transcript material and must never be committed, uploaded to the judge demo, or placed in the public audit packet.

## 5. Content seal and independent verification

Each exported audit JSON carries `countersignal.content-seal.v1`, a deterministic SHA-256 digest over canonical packet content excluding the seal itself.

Open `audit-verifier.html` and drop the JSON onto the page. The verifier recomputes the digest locally, checks the exact SmallBet experiment ID and protocol hash, and shows the evidence/decision summary. It uses no network request API.

The seal detects changes to the exported packet after the digest was computed. It is deliberately **not** described as an identity signature, trusted timestamp, or tamper-proof external anchor; someone able to rewrite the whole packet can compute a new digest.

## 6. Load the result into the judge console

Open `judge-console.html`, choose **Load audit JSON**, and select `data/countersignal-audit.json`.

The browser checks the audit schema, experiment ID, and exact protocol hash before replacing the simulated reviewer fixture. Imported data stays local to the browser; the console performs no network `fetch()`.

## 7. Zero-credential verification

Before recording the final demo:

```bash
python verify_product_v2.py
python benchmark.py --json
python -m pytest -q
```

`verify_product_v2.py` checks the frozen 8/5/3 rule, benchmark divergence, next-evidence sensitivity, honest nonresponse denominator, sealed-packet verification, no-call copy, local audit import, and both browser surfaces' no-network invariants.

## Claim boundary

A successful proof demonstrates that a permissioned CALL-E result can be bound to the frozen experiment, converted into redacted evidence, durably accumulated, replayed, content-sealed, independently checked, and allowed to change the pre-registered decision. It does not prove product-market fit, population prevalence, ROI, statistical significance, author identity, or an external timestamp.
