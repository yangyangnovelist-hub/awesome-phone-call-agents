# CounterSignal — judge evidence matrix

This page maps the CALL-E judging dimensions to concrete, reproducible evidence. It intentionally separates **implemented proof**, **deterministic simulation**, and **real-world proof still missing**.

## Executive claim

> **CounterSignal is a decision-integrity layer for AI customer research. It freezes what would change your mind before the first interview, keeps contradictions load-bearing, and makes the exact evidence that changed the decision replayable.**

The fastest product proof is `index.html` → **Run proof**.

---

## 1. Real World Impact

### Product problem

Customer interviews can become faster with AI without becoming epistemically safer. The failure mode CounterSignal targets is **confirmation-biased decision making**: protocol drift, supportive anecdotes dominating memory, contradictory answers being averaged away, and failed contacts disappearing from the denominator.

### Implemented evidence

- Real CALL-E execution path exists and uses the published SDK.
- Permission-first live gate: a public number is not treated as consent.
- Permission receipt must match the experiment and reviewed recipient and contain affirmative opt-in before the live boundary.
- Result admission binds the exact accepted CALL-E call, frozen protocol, experiment, and reviewed recipient.
- Answered evidence must be transcript-grounded before it can count.
- Voicemail/refusal/unreachable/invalid outcomes cannot inflate the answered denominator.
- Live evidence is persisted in a privacy-minimized ledger with no phone number, full transcript, or real quote text at rest.
- Ambiguous submission outcome is `outcome_unknown`; the same consequential intent is not blindly redialed.

### Reproduce

```bash
python prove_live.py \
  --experiment smallbet-experiment.json \
  --recipient example-recipient.json
```

The default path is a masked, no-call preview.

`test_proof_orchestration_e2e.py` exercises the post-authorization path end-to-end using a deterministic fake CALL-E transport:

```text
validated permission
→ durable reservation/idempotency
→ accepted call ID
→ provider result
→ protocol + recipient binding
→ transcript grounding
→ privacy-minimized AuditLedger
→ live-only public packet
→ SHA-256 content seal
```

### What is not yet proved

A **real permissioned CounterSignal CALL-E interview** has not yet been promoted into a public live-proof packet for the award build. Simulated evidence must not be relabeled as live evidence.

Therefore CounterSignal does not currently claim observed PMF, population prevalence, ROI, or business-outcome uplift.

**Remaining highest-value proof:** one or more actually permissioned CALL-E interviews passed through the shipped proof pipeline.

---

## 2. Quality of the Idea

### Differentiation

A generic interview tool optimizes collection or synthesis.

CounterSignal asks a different question:

> **Should this evidence make the operator lose confidence in the hypothesis they registered before evidence collection?**

That changes the product state machine, denominator, evidence admission policy, and output.

### Frozen decision contract

Dogfood protocol:

```text
experiment: smallbet-permit-ops-v1
protocol:   a7229d00ec935e760d5764572b142a33a062095db0df8c5f3f32c18b88b47a56
minimum answered: 8
support:          >=5 supporting AND 0 contradictions
weaken:           >=3 contradictions after minimum answered
```

### Why 8 / 5 / 3

This is an **operational asymmetric-loss policy**, not a significance test.

- **8 answered**: prevents one or two memorable anecdotes from becoming a terminal discovery decision while keeping the experiment intentionally small.
- **5 support + 0 contradiction**: requires repeated problem + workaround evidence; one grounded contradiction immediately removes provisional support.
- **3 contradictions**: repeated counterevidence weakens the hypothesis, while one unusual respondent cannot kill it.
- **minimum sample before weakening**: prevents a tiny early sample from becoming a terminal negative decision.
- **neutral answers count**: the operator cannot discard inconvenient ambiguity from the answered denominator.

CounterSignal does not claim that 8/5/3 is universally optimal. The product contribution is that the rule is explicit, frozen, replayable, and allowed to produce an inconvenient result.

### Deterministic benchmark

Same evidence, two explicit policies:

```text
5 supporting + 3 contradictions
naive majority → positive_signal
CounterSignal  → hypothesis_weakened
```

Reproduce:

```bash
python benchmark.py --json
```

This is a policy comparison, not a benchmark against a named commercial AI research product.

### Seeded policy stress

```bash
python policy_stress.py --trials 10000 --seed 20260823 --json
```

Latest verified runner evidence:

```text
trials: 10,000
seed: 20260823
invariants_ok: true

denominator_noise_invariance failures:      0
permutation_invariance failures:            0
weakening_threshold failures:               0
support_requires_zero_contradictions:       0
support_launders_weakened_state failures:   0
```

The stress harness is an invariant test, **not an accuracy benchmark**.

---

## 3. Technical Implementation

### Evidence admission

A completed provider call is not automatically accepted evidence.

Answered live evidence must satisfy:

- terminal successful state;
- `task_completed=true`;
- completion-confidence gate;
- exact structured-result schema;
- accepted CALL-E call-ID binding;
- exact experiment metadata;
- exact frozen protocol hash;
- exact reviewed-recipient binding;
- recipient-side transcript grounding.

### Durable reliability

- SQLite intent reservation before consequential dispatch.
- Stable idempotency key bound to call arguments + recipient.
- Accepted call ID stored after provider acceptance.
- ambiguous provider failures become `outcome_unknown` rather than permission to redial.
- append-only audit ledger.
- identical duplicate call record is idempotent.
- conflicting duplicate call ID fails closed.
- cross-protocol and cross-experiment evidence rejected.

### Privacy architecture

Grounding happens while the raw provider result is still in memory. For live evidence, `AuditLedger` then removes real quote text **before durable storage**.

Default durable/public path excludes:

- phone number;
- phone-derived public identifiers;
- raw transcript;
- real quote text;
- private permission statement.

Public recipient reference is call-bound and is not derived from the phone number.

`test_audit_storage_privacy.py` scans the SQLite bytes to confirm the phone and real quote are absent.

### Public proof integrity

A public live packet must be:

- non-empty;
- **100% `source="calle_live"` evidence**;
- permission-verified;
- recipient-bound;
- grounded for answered evidence before redaction;
- privacy-redacted;
- SHA-256 content-sealed.

Zero-record packets fail. Mixed simulated/live packets fail.

The seal detects packet changes relative to its digest. It does not authenticate the author, provide a trusted timestamp, or independently attest consent.

### CI evidence

Latest award-surface verified run on GitHub Actions:

```text
Ubuntu 24.04
Python 3.12.14
pytest: 55 passed
verify_product_v2.py: ok = true
10,000-state policy stress: all invariant failures = 0
benchmark: 5 support / 3 contradictions → hypothesis_weakened
```

The repository-level `Validate` workflow also completed successfully on the same head.

Reproduce locally:

```bash
python -m pytest -q
python verify_product_v2.py
python benchmark.py --json
python policy_stress.py --trials 10000 --seed 20260823 --json
```

---

## 4. Product Experience & Demo

### Flagship experience — `index.html`

The first 60 seconds are intentionally judge-driven rather than narration-driven.

Starting state:

```text
8 answered
5 supporting
3 neutral
0 contradictions
SUPPORTED
```

Judge interactions:

1. **+ Voicemail** → attempted rises, answered stays 8.
2. **+ Contradiction** → five supports remain, state becomes `INCONCLUSIVE`.
3. Add two more contradictions → state becomes `HYPOTHESIS WEAKENED`.

The product then shows:

- why 8/5/3 exists;
- same-evidence policy divergence;
- permission → bind/ground → redact/seal live path;
- embedded independent local verifier.

### Deeper reviewer surface — `judge-console.html`

- Decision Replay
- Decision Fragility
- Adversarial Evidence Queue
- evidence provenance
- next-evidence counterfactuals
- audit import/export

### Independent proof surface — `audit-verifier.html`

The verifier independently checks:

- schema and live-proof mode;
- experiment and protocol identity;
- SHA-256 digest;
- non-empty evidence;
- every record is CALL-E live;
- live-only policy flag;
- permission channel/time;
- recipient binding;
- call-bound public reference;
- grounding-before-redaction;
- participant quote withholding;
- absence of obvious raw recipient fields.

No network request APIs are used by the verifier.

### Video structure

`DEMO.md` targets ~2:35:

```text
problem
→ freeze the rule
→ voicemail denominator
→ first contradiction removes support
→ third contradiction weakens
→ deterministic benchmark
→ permission/binding/redaction proof boundary
→ independent verification
→ final product claim
```

The video should end on:

> **CounterSignal makes you decide, in advance, what evidence would prove you wrong.**

---

## Fast judge commands

```bash
cd apps/python/countersignal
python verify_product_v2.py
python benchmark.py --json
python policy_stress.py --trials 10000 --seed 20260823 --json
python -m pytest -q
```

## Current award gap

The engineering and deterministic product proof are strong and independently reproducible.

The single most valuable remaining evidence is **real, permissioned CALL-E dogfood** passed through the exact same live-proof pipeline. Until that exists, the product should preserve the distinction between simulated reviewer evidence and live real-world evidence rather than weakening its credibility with a manufactured demo.
