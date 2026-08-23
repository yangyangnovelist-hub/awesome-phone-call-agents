# CounterSignal — 60-second judge quickstart

CounterSignal is not another AI interview dashboard. The fastest way to evaluate it is to test whether contradictory evidence can actually change the operator's decision under a rule frozen before the interviews.

## 0–30 seconds — try to kill the hypothesis

Open **`index.html`**.

The deterministic reviewer fixture starts at the frozen SmallBet boundary:

- 8 answered interviews;
- 5 supporting;
- 3 neutral;
- 0 contradictions;
- decision: `SUPPORTED` under the pre-registered rule.

Click **+ Voicemail** once.

Expected result: `attempted` increases, but `answered` remains **8**.

Click **+ Contradiction** once.

Expected result: five supporting interviews still exist, but provisional support disappears and the state becomes **`INCONCLUSIVE`** because support requires zero contradictions.

Click **+ Contradiction** twice more.

Expected result: at three contradictions the state becomes **`HYPOTHESIS WEAKENED`** while the five supporting interviews remain visible.

## 30–45 seconds — inspect the policy difference

Scroll to **Same evidence, different policy**.

The critical state is:

```text
5 supporting + 3 contradictions
naive majority  -> positive_signal
CounterSignal   -> hypothesis_weakened
```

This is a controlled comparison between two explicit deterministic evidence policies, not a claim about a named commercial research product.

For deeper replay/provenance, open **`judge-console.html`**.

## 45–60 seconds — reproduce and verify

```bash
python verify_product_v2.py
python benchmark.py --json
python policy_stress.py --trials 10000 --seed 20260823 --json
python -m pytest -q
```

The verification path requires no credentials and places no phone calls.

The seeded policy stress harness attacks denominator-noise invariance, order invariance, contradiction thresholds, support-with-zero-contradiction semantics, and attempts to “launder” an already weakened state with extra support. It is an invariant test, **not an accuracy benchmark**.

## Real CALL-E proof boundary

A live proof uses `prove_live.py` and cannot cross the CLI boundary without a structured affirmative permission receipt, exact reviewed-recipient allowlisting, and the live-call flag.

After CALL-E, accepted evidence is bound to the exact call / protocol / reviewed recipient and grounded before persistence. The default audit ledger stores no phone number, raw transcript, or real participant quote text.

A public live-proof packet must be:

- non-empty;
- **100% `calle_live` evidence** — no simulated/live mixing;
- permission-verified;
- recipient-bound;
- grounded for answered evidence;
- privacy-redacted; and
- SHA-256 content-sealed.

Drop a legitimate packet into **`audit-verifier.html`** for local verification. If no actually permissioned CALL-E evidence exists, do not manufacture a live packet.

## What to judge

The central product question is:

> **Can the system preserve evidence that makes its operator less confident, and can a reviewer reconstruct exactly why the decision changed?**

CounterSignal's answer is encoded in the frozen protocol, evidence admission rules, decision state machine, replay, benchmark, stress harness, end-to-end proof orchestration, and live-proof boundary — not in a generated narrative.
