# CounterSignal

> **Customer research that can prove you wrong.**

CounterSignal is a **decision-integrity layer for AI customer research** built on CALL-E. It freezes the hypothesis, questions, and decision thresholds before evidence collection; keeps contradictory evidence load-bearing; excludes silence and unreliable results from the answered denominator; and makes the exact decision transition replayable.

It is not a lead qualifier, booking workflow, or generic AI interview summarizer. The product question is narrower and harder:

**Given the evidence we actually collected, should we lose confidence in the business hypothesis we wrote down before the interviews began?**

## Start here — the judge experience

Open `index.html` first.

The flagship surface is designed to communicate the product in about 60 seconds:

1. Start at provisional support under the frozen **8 / 5 / 3** rule.
2. Add a voicemail. Attempted calls increase; the answered denominator stays **8**.
3. Add one grounded contradiction. Provisional support disappears and the decision becomes **inconclusive**.
4. Add three grounded contradictions. The hypothesis becomes **`hypothesis_weakened`**, even though five supporting interviews remain visible.
5. Inspect the deterministic benchmark: the naive majority baseline is still `positive_signal` at 5 support vs 3 contradictions.
6. Use the embedded local verifier for a future sealed live CALL-E audit packet.

For deeper inspection:

- `judge-console.html` — full Decision Audit Console: replay, fragility, provenance, counterfactual next evidence, audit import/export.
- `audit-verifier.html` — dedicated offline verifier for permissioned live-proof packets.
- `BENCHMARK.md` — exact deterministic benchmark and claim boundary.
- `LIVE-PROOF.md` — permission-first real CALL-E proof workflow.
- `DEMO.md` — award video script.

## Product thesis

AI can make customer interviews faster. Speed alone does not solve confirmation bias.

Customer-discovery evidence is unusually easy to contaminate after the fact: questions drift, supportive anecdotes dominate memory, contradictions get reframed as objections, failed contacts silently disappear from the denominator, and an ambiguous model summary can be mistaken for respondent evidence.

CounterSignal treats these as **data-integrity and decision-governance problems**, not prompt-writing problems.

Five invariants are therefore load-bearing:

1. **Pre-registration** — segment, hypothesis, fixed questions, and thresholds are hashed before evidence collection.
2. **No silent protocol drift** — changing the study changes the protocol identity.
3. **Contradictions remain load-bearing** — supportive evidence cannot average away a pre-registered contradiction threshold.
4. **Honest denominators** — voicemail, refusal, unreachable, and invalid results do not become answered interviews.
5. **Evidence binding** — usable live evidence must belong to the exact experiment, protocol, accepted CALL-E call and reviewed recipient, and answered evidence must pass transcript grounding before public redaction.

The decision is an **operational experiment rule**, not a population estimate and not a product-market-fit claim.

## Frozen SmallBet protocol

The award-facing dogfood protocol is `smallbet-permit-ops-v1`.

Protocol hash:

```text
a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56
```

Decision rule:

- minimum answered interviews: **8**
- provisional support: **5 supporting interviews and zero contradictions**
- hypothesis weakening: **3 grounded contradictions**

Changing the hypothesis, segment, questions, or thresholds creates a different protocol hash and therefore a different experiment version.

## Same evidence, different epistemic policy

`benchmark.py` compares CounterSignal against a deliberately simple, fully specified naive-majority policy over the same classified evidence.

It is **not** presented as a benchmark against any named commercial research product.

| Evidence | Naive majority | CounterSignal |
| --- | --- | --- |
| 5 support + 3 neutral | `positive_signal` | `hypothesis_supported_under_rule` |
| + 1 contradiction | `positive_signal` | `inconclusive` |
| + 2 contradictions | `positive_signal` | `inconclusive` |
| + 3 contradictions | `positive_signal` | `hypothesis_weakened` |
| + 5 voicemails instead | `positive_signal` | support unchanged; answered stays 8 |

Reproduce it:

```bash
cd apps/python/countersignal
python benchmark.py --json
```

The benchmark establishes a difference between two deterministic decision policies. It does not establish superior population inference, product-market-fit prediction, interview quality, or commercial outcomes.

## Decision Audit Console

`judge-console.html` makes the evidence policy visible rather than leaving it in backend code.

It exposes:

- the current decision and reason;
- the exact frozen protocol identity;
- attempted vs answered counts;
- supporting, disconfirming, neutral, nonresponse, and invalid outcomes;
- **Decision Replay** — the exact evidence item that changed the state;
- **Decision Fragility** — how many contradictions remain before support disappears or the hypothesis weakens;
- **Adversarial Evidence Queue** — contradictions are kept visible instead of averaged away;
- **Next-evidence counterfactuals** — what each possible next classified outcome would do to the decision, without pretending to predict the next respondent;
- per-record provenance;
- local audit import/export.

The built-in reviewer fixture is deterministic, simulated, and labeled as such. It places no phone calls.

## Permission-first live proof

The preferred real-call path is `prove_live.py`, not the raw core CLI.

A public phone number is **not** treated as permission for an AI research call.

A live proof requires a private local permission receipt such as:

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

Supported machine values for the permission channel are:

- `email`
- `sms`
- `web_form`
- `in_person`
- `other_non_phone`

Human-facing product copy calls these **non-call permission channels**: permission must exist before the proof call itself.

Preview first:

```bash
python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient recipient.json
```

Preview masks the destination and places no call.

A permissioned real proof uses the explicit gates documented in `LIVE-PROOF.md`:

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

Before the CALL-E SDK is imported or the production key is used, the proof runner validates the permission receipt and exact allowlist boundary.

## What counts as usable live evidence

A completed CALL-E call is not automatically evidence.

For an answered result to enter the decision path, CounterSignal requires:

- terminal successful provider state;
- `task_completed=true`;
- completion confidence at or above the configured gate;
- exact structured-result schema;
- exact accepted CALL-E call ID when supplied;
- exact experiment metadata;
- exact protocol hash;
- exact reviewed-recipient binding; and
- a recipient-side key quote that is grounded in the recipient transcript before public redaction.

Classification is conservative:

- **disconfirming** — the respondent directly contradicts a load-bearing hypothesis condition or reports the problem does not occur;
- **supporting** — the problem occurs and a current workaround already exists;
- **neutral** — valid answered interview that satisfies neither rule;
- **nonresponse** — refusal, voicemail, unreachable, or other non-answered outcome;
- **invalid** — incomplete, low-confidence, unbound, malformed, or ungrounded result.

Disconfirming evidence takes priority after the minimum answered sample is reached. Provisional support requires the configured support count **and zero contradictions**.

## Privacy-minimizing audit trail

`audit.py` converts accepted results into an append-only redacted evidence ledger.

The public recipient reference is **not derived from the phone number**. It is call-bound using public experiment/protocol/call identity, after raw recipient binding has already been verified.

The durable evidence layer supports:

- append-only SQLite persistence;
- idempotent re-ingestion of an identical CALL-E call record;
- fail-closed rejection when the same call ID appears with different evidence;
- cross-experiment rejection;
- cross-protocol rejection;
- decision replay;
- decision fragility;
- next-evidence sensitivity.

Raw provider results are never printed by the proof runner. They are persisted only when the operator explicitly supplies `--private-result-out`.

## Interview permission is not publication permission

A respondent agreeing to an AI-assisted research interview is **not** interpreted as permission to publish their transcript or quote.

For public live proof, `proof_packet.py` therefore withholds by default:

- phone number;
- phone-derived hashes;
- raw transcript;
- private permission statement;
- real participant quote text.

The public record can expose that transcript grounding succeeded, but the real quote itself is replaced with an empty public field.

`proof_packet.live_audit_packet()` also requires at least **one actual `source="calle_live"` record**. A zero-record or simulation-only packet cannot masquerade as live proof.

## Content seal and independent verification

Public proof packets receive `countersignal.content-seal.v1`, a deterministic SHA-256 digest over canonical packet content excluding the seal itself.

`audit-verifier.html` recomputes that digest locally and additionally checks:

- audit schema;
- `mode=live_redacted_ledger`;
- exact experiment ID;
- exact protocol hash;
- at least one CALL-E live evidence record;
- `live_proof_policy.minimum_live_evidence_records=1`;
- permission proof and supported permission channel/time;
- reviewed-recipient binding;
- call-bound public reference;
- transcript grounding for answered live evidence before redaction;
- real participant quote withholding;
- absence of obvious raw recipient fields.

The verifier has no network request API: no `fetch`, XHR, beacon, analytics, or remote scripts.

The seal has a narrow claim boundary. It detects packet changes relative to its recorded digest. It does **not** authenticate the author, prove a trusted timestamp, independently attest the private consent statement, or make storage tamper-proof.

## Reliability boundary

Consequential outbound operations use durable reservation semantics.

Before dispatch, CounterSignal reserves the exact stable call intent in SQLite. Once CALL-E accepts the call, the returned call ID is bound to that reservation. If an exception or timeout leaves the provider outcome ambiguous, the state becomes `outcome_unknown` and the same intent is not blindly redialed.

The production base URL is pinned to the official CALL-E HTTPS origin. Plain HTTP is accepted only for an explicit loopback test server, which receives a fixed non-secret test key instead of the production API key.

## One-command verification

The award-facing claims are tied into the automated verification path:

```bash
cd apps/python/countersignal
python -m pytest -q
python verify_product_v2.py
python benchmark.py --json
```

The dedicated GitHub Actions workflow runs all three on Ubuntu / Python 3.12.

`verify_product_v2.py` checks the frozen rule, contradiction divergence, one-contradiction state change, voicemail denominator integrity, content sealing, full Decision Audit Console invariants, dedicated verifier invariants, and the flagship award surface.

## Current proof status

The deterministic product, benchmark, privacy boundary, verification path, and permission-first CALL-E execution path are implemented and CI-verified.

A public packet should be labeled **live** only when at least one actually permissioned CALL-E interview has produced a valid `calle_live` evidence record. The simulated reviewer fixture must never be relabeled as live evidence.

## Claim boundary

CounterSignal currently demonstrates:

- a frozen operational research policy;
- conservative evidence admission;
- contradiction-preserving decisions;
- honest nonresponse denominators;
- replayable state transitions;
- permission-first outbound execution;
- privacy-minimizing public proof; and
- independent content/integrity verification.

It does **not** claim from this small study to prove population prevalence, product-market fit, statistical significance, ROI, conversion uplift, or superior commercial outcomes.
