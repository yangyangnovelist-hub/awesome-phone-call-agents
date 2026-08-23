# CounterSignal — 60-second judge quickstart

CounterSignal is not trying to be another AI interview dashboard. The fastest way to evaluate it is to see whether contradictory evidence can actually change the operator's decision under a rule frozen before the interviews.

## 0–20 seconds: break the supported result

Open `judge-console.html`.

The deterministic reviewer fixture starts at the frozen SmallBet boundary:

- 8 answered interviews;
- 5 supporting;
- 3 neutral;
- 0 contradictions;
- decision: `hypothesis_supported_under_rule`.

Click **+ Voicemail** once. `attempted` increases, but `answered denominator` must remain **8**.

Click **+ Contradiction** once. Five supporting interviews are still visible, but the decision must become **`inconclusive`** because provisional support requires zero grounded contradictions.

## 20–35 seconds: make falsification load-bearing

Click **+ Contradiction** two more times.

At three grounded contradictions the decision must become **`hypothesis_weakened`** while all five supporting interviews remain in the ledger.

Open **Decision replay**. It shows the exact evidence sequence where the state changed instead of presenting a post-hoc summary.

## 35–50 seconds: reproduce the policy difference

From this directory:

```bash
python benchmark.py --json
```

The critical case is:

```text
5 supporting + 3 neutral + 3 contradictions
naive majority  -> positive_signal
CounterSignal   -> hypothesis_weakened
```

That is not a claim about a named commercial product. It is a controlled comparison between two explicit deterministic evidence policies over the same evidence.

## 50–60 seconds: verify the product invariants

```bash
python verify_product_v2.py
python -m pytest -q
```

The verification path requires no credentials and places no phone calls.

For a real CALL-E proof, use `prove_live.py`. It refuses to cross the live boundary without a structured affirmative permission receipt, exact reviewed-recipient allowlisting, and the live-call flag. The public proof withholds phone numbers, raw transcripts, private permission statements, and real participant quote text. Drop the resulting sealed JSON into `audit-verifier.html` to recompute its SHA-256 content seal and check permission, recipient binding, grounding, and protocol identity locally.

## What to judge

The central product question is simple:

> Can the system preserve evidence that makes its operator less confident, and can a reviewer reconstruct exactly why the decision changed?

CounterSignal's answer is encoded in the frozen protocol, evidence classification, decision state machine, replay, benchmark, and live-proof boundary — not in a generated narrative.
