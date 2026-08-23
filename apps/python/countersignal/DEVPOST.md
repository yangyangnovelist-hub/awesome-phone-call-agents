# CounterSignal — CALL-E Devpost submission packet

This is the current copy source for the CALL-E submission. Keep deterministic evidence, CI evidence, and real CALL-E evidence clearly separated.

## Title

CounterSignal

## One-line summary

**CounterSignal is a decision-integrity layer for AI customer research: freeze what would change your mind before the first interview, keep contradictions load-bearing, and replay the exact evidence that changed the decision.**

## Problem

AI can make customer interviews dramatically faster, but faster interviews do not automatically produce better decisions. Customer discovery has an asymmetric failure mode: supportive anecdotes are easy to remember while contradictions get rationalized away. Questions can drift between interviews, failed contacts can silently disappear from denominators, and an ambiguous AI synthesis can become “evidence” even when it is not grounded in what the respondent actually said.

CounterSignal treats those as **research-integrity failures**, not prompt-writing failures.

The real-world task is deliberately bounded: run a permissioned customer-discovery phone interview under a frozen protocol, conservatively classify the resulting evidence, and decide whether the accumulated record should cause the operator to keep collecting, provisionally support, become inconclusive, or weaken the original business hypothesis.

## Solution

Before evidence collection, CounterSignal freezes:

- target segment;
- bounded problem;
- working hypothesis;
- ordered substantive questions; and
- decision thresholds.

Those inputs produce a deterministic protocol hash. Changing the study changes the identity; the operator cannot silently rewrite the protocol after seeing answers.

CALL-E is the **interview instrument**, not the decision maker. It discloses that it is an AI research assistant, asks the fixed questions in order, may use only a neutral clarification for ambiguity, and is forbidden from selling, negotiating, offering discounts, scheduling a purchase, or inventing a new substantive question.

A completed phone call is not automatically evidence. CounterSignal requires terminal success, completion confidence, the exact structured-result contract, exact CALL-E call / experiment / protocol / reviewed-recipient binding, and recipient-side transcript grounding for answered evidence.

Voicemail, refusal, unreachable, malformed, low-confidence, mismatched, and ungrounded outcomes cannot silently become positive evidence.

## The decision rule judges can verify

The frozen SmallBet protocol is:

- experiment: `smallbet-permit-ops-v1`
- protocol: `a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56`
- minimum answered: **8**
- provisional support: **5 supporting + zero contradictions**
- weakening threshold: **3 grounded contradictions**

The award-facing product starts at 8 answered interviews: 5 supporting, 3 neutral, 0 contradictions.

- Add voicemail → attempted rises, answered remains 8.
- Add one contradiction → support disappears; the state becomes `inconclusive`.
- Add three contradictions → `hypothesis_weakened`.

Five supporting interviews still remain visible. CounterSignal does not average the contradiction threshold away.

## Reproducible benchmark

`benchmark.py` compares CounterSignal with a deliberately simple, fully specified naive-majority policy over the same classified evidence.

At **5 supporting vs 3 contradictions**:

- naive majority → `positive_signal`
- CounterSignal → `hypothesis_weakened`

This is a comparison between deterministic decision policies, **not** a benchmark against any named commercial AI research product.

## Why this is meaningfully different

A lead workflow asks whether a person should advance toward a commercial next step.

A survey runner standardizes respondent data collection.

CounterSignal asks a different question:

> **Should accumulated evidence make the operator lose confidence in a hypothesis they registered before the interviews began?**

That changes the state machine, evidence contract, denominator, output, and decision authority. CounterSignal never books a meeting, never returns `qualified`, and never treats willingness to talk again as proof of demand.

## Award-facing product experience

### `index.html` — flagship judge surface

The primary experience opens with:

**Customer research that can prove you wrong.**

It gives a judge a 60-second interactive proof of:

- the frozen 8/5/3 rule;
- the honest answered denominator;
- contradiction-driven state changes;
- the deterministic majority-vs-CounterSignal benchmark;
- the permission-first CALL-E proof boundary; and
- local independent audit verification.

### `judge-console.html` — Decision Audit Console

The deeper console exposes:

- Decision Replay;
- decision fragility;
- Adversarial Evidence Queue;
- per-record provenance;
- next-evidence counterfactuals;
- audit import/export.

### `audit-verifier.html` — independent local verifier

A public live-proof packet is accepted only when it satisfies the shipped proof contract. The verifier recomputes its SHA-256 content seal locally and performs no network request.

## Permission-first CALL-E proof

A public phone number is not permission for an AI research call.

`prove_live.py` is preview/no-call by default. A real proof call requires a private structured permission receipt with:

- `ai_interview_opt_in=true`;
- exact experiment match;
- exact reviewed-recipient match;
- an approved **non-call** permission channel; and
- timezone-aware consent time.

The proof path fails before live configuration when that receipt is absent.

After CALL-E returns, accepted evidence must still pass exact binding and transcript grounding before it can enter the experiment.

## Privacy-minimizing public proof

Interview permission is **not** treated as permission to publish a participant quote.

The public live-proof packet therefore withholds by default:

- phone number;
- phone-derived identifier;
- raw transcript;
- private permission statement; and
- real participant quote text.

It may expose that grounding was verified before redaction, together with the CALL-E call ID, protocol identity, classification, confidence, decision state, and a call-bound public reference that is not derived from the phone number.

A packet cannot claim the live-proof path with zero real evidence: `proof_packet.py` requires at least one actual `source="calle_live"` record, and both browser verifiers independently enforce that condition.

## Reliability engineering

The live path includes:

- published CALL-E Python SDK;
- production API origin pinning;
- exact recipient allowlist;
- explicit live-call enable gate;
- durable SQLite reservation before dispatch;
- call-ID binding after acceptance;
- `outcome_unknown` after ambiguous provider outcomes; and
- no blind redial of an already-reserved consequential intent.

## Verification evidence

The dedicated `CounterSignal PR Verification` workflow runs on Ubuntu / Python 3.12 and verifies:

```bash
python -m pytest -q
python verify_product_v2.py
python benchmark.py --json
```

Latest verified award-surface run:

- test suite: **51 passed**
- judge invariant verifier: **`ok: true`**
- contradiction benchmark: reproduced the 5-support / 3-contradiction divergence

Do not hardcode the test count in the public video because the suite can continue to grow.

## Testing instructions

1. Clone the repository branch containing CounterSignal and enter `apps/python/countersignal`.
2. Use Python 3.11+.
3. Run `python -m pytest -q`.
4. Run `python verify_product_v2.py`.
5. Run `python benchmark.py --json`.
6. Open `index.html` and press **Run proof**, or manually add voicemail followed by contradictions.
7. Open `judge-console.html` for Decision Replay, provenance, fragility, and audit import/export.
8. Open `audit-verifier.html` to inspect the live-proof verification boundary.
9. Run `python prove_live.py --experiment smallbet-experiment.json --recipient recipient.json` to inspect the masked no-call preview.
10. Do not use a random public number for live testing. A real proof call requires affirmative permission and the explicit gates in `LIVE-PROOF.md`.

## Demo video — target 2:30–2:40

Use `DEMO.md` as the recording source.

The intended sequence is:

1. flagship product thesis;
2. frozen decision rule;
3. voicemail demonstrates denominator honesty;
4. first contradiction removes support;
5. third contradiction weakens the hypothesis;
6. deterministic majority-vs-CounterSignal divergence;
7. permission → binding/grounding → redaction/seal;
8. local independent proof verification;
9. end on: **“decide, in advance, what evidence would prove you wrong.”**

If no actually permissioned CounterSignal live proof exists at recording time, do not manufacture one. Show the deterministic product and the live-proof gate honestly.

## Screenshot shot list

1. `index.html` hero with the product thesis and exact frozen rule.
2. 60-second judge test showing attempted vs answered after voicemail.
3. transition to `INCONCLUSIVE` after the first contradiction.
4. `HYPOTHESIS WEAKENED` after the third contradiction.
5. majority-vs-CounterSignal divergence table.
6. permission / binding / redaction-seal product flow.
7. audit verifier boundary.
8. optional real live packet showing `VERIFIED` — **only if actual permissioned CALL-E evidence exists**.

## Official submission fields

- **Submitter Type:** Individual
- **Country of residence/incorporation:** TODO — enter the truthful eligibility value used for the submission.
- **Organization name:** leave blank unless applicable.
- **App status:** Newly created
- **If pre-existing, explain updates:** Not applicable — CounterSignal was created during the submission period.
- **Project submission pull request URL:** https://github.com/CALLE-AI/awesome-phone-call-agents/pull/198
- **Upstream PR status:** merged
- **Functional demo URL:** current public URL is `https://countersignal.vercel.app`; replace/verify it against the final product-v2 deployment before submission.
- **Demo video URL:** TODO — public YouTube or Vimeo under 3 minutes.
- **Email associated with CALL-E account:** TODO — use the actual CALL-E account email; do not infer or use a placeholder.
- **Primary use case:** Other
- **One-sentence real-world task:** Runs permissioned customer-discovery phone interviews under a frozen protocol and turns grounded supporting and contradictory evidence into an auditable experiment decision.
- **Eligibility / country / conflict-of-interest attestations:** submitter must affirm truthfully in Devpost.

## Current proof status

- Required upstream contribution: **merged as PR #198**.
- Deterministic award product and CI verification: implemented.
- Public product-v2 deployment: must be verified before final Devpost submission; do not assume the existing production URL contains the newest flagship surface.
- Permissioned CounterSignal live evidence: do not claim unless at least one actual CALL-E `calle_live` record has passed the shipped permission/binding/grounding gates.

## Claim boundary

CounterSignal demonstrates a pre-registered **operational decision rule**, conservative evidence admission, contradiction-preserving decisions, denominator honesty, replayable state transitions, permission-first outbound execution, privacy-minimizing public proof, and independent content verification.

It does **not** claim from this small dogfood study to prove population prevalence, product-market fit, statistical significance, ROI, conversion uplift, author identity, consent authenticity, or a trusted timestamp.
