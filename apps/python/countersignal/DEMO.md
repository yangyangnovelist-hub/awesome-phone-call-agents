# CounterSignal award demo — target 2:35

The video should make one idea unforgettable:

> **CounterSignal is not an AI interviewer with a dashboard. It is a decision-integrity system that decides whether customer evidence should make you lose confidence in a hypothesis you wrote down before the interviews began.**

Start on `index.html`. Use the deeper Decision Audit Console only after the product thesis is already clear.

## 0:00–0:15 — The problem

**Screen:** flagship hero.

Show:

- `Decision integrity for AI customer research`
- `Customer research that can prove you wrong.`
- `Not a prettier summary. A different epistemic policy.`

**Narration:**

> AI can make customer interviews faster. But faster confirmation bias is still confirmation bias. CounterSignal freezes what would change your mind before the first interview, then makes every decision change replayable back to evidence.

Do not start with code, architecture, or CALL-E implementation details.

## 0:15–0:32 — Freeze the rule before evidence

**Screen:** flagship protocol chips and frozen 8 / 5 / 3 contract.

**Narration:**

> This experiment requires eight valid answered interviews. Five supporting interviews can provisionally support the hypothesis only with zero contradictions. Three grounded contradictions weaken it. The hypothesis, questions and thresholds are frozen into a protocol identity before evidence collection.

Point briefly at protocol `a7229d00…b47a56`.

## 0:32–0:52 — Prove the denominator is honest

**Screen:** 60-second judge test on `index.html`.

Start at:

- 8 answered
- 5 supporting
- 0 contradictions
- `SUPPORTED`

Press **+ Voicemail** once.

**Narration:**

> First, a failed contact. Attempted calls increase, but answered stays eight. A voicemail cannot make the evidence base look larger.

Pause just long enough for the judge to see attempted change while answered remains 8.

## 0:52–1:20 — Let one contradiction remove support

**Screen:** press **+ Contradiction** once.

**Narration:**

> Now one grounded contradiction arrives. Five supporting interviews still exist, but provisional support disappears immediately. The state becomes inconclusive because the support rule required zero contradictions.

Point at the decision transition timeline.

This is the first “aha” moment. Do not rush it.

## 1:20–1:42 — Let three contradictions weaken the hypothesis

**Screen:** add the second and third contradictions.

**Narration:**

> At three contradictions the pre-registered weakening threshold is crossed. CounterSignal returns `hypothesis_weakened`. It does not average those contradictions away just because supportive anecdotes are still the numerical majority.

End this beat with `HYPOTHESIS WEAKENED` visibly on screen.

## 1:42–1:58 — Same evidence, different policy

**Screen:** scroll to `Same evidence, different policy`.

**Narration:**

> The behavior is reproducible outside the UI. With five supporting interviews and three contradictions, a fully specified naive majority rule is still positive. CounterSignal weakens the hypothesis because the contradiction threshold was fixed before the evidence arrived.

Point at:

- naive majority → `positive_signal`
- CounterSignal → `hypothesis_weakened`

Say explicitly that the baseline is a deterministic policy, **not** a commercial-product comparison.

## 1:58–2:17 — A live result must earn its way into the decision

**Screen:** `Permission-first real proof` section.

**Narration:**

> The real CALL-E path is stricter than the simulated judge mode. A public phone number is not permission. Before a proof call, CounterSignal requires affirmative opt-in. After CALL-E, the call ID, frozen protocol and reviewed recipient must bind exactly, and answered evidence must be grounded in recipient-side transcript evidence before it can count.

Point across the three cards:

`PERMISSION → BIND + GROUND → REDACT + SEAL`

## 2:17–2:30 — Public proof without publishing the participant

**Screen:** independent verification section / `audit-verifier.html`.

**Narration:**

> Public proof withholds the phone number, raw transcript, private consent statement, and real participant quote text. A live packet must contain at least one actual CALL-E evidence record, then the browser independently recomputes its SHA-256 seal and checks permission, binding and grounding locally with no network request.

If no actually permissioned CounterSignal live packet exists at recording time, do **not** manufacture one. Show the verifier boundary and say the public live-proof slot remains gated until real permissioned evidence exists.

If a legitimate packet does exist, drag it into the verifier and show `VERIFIED`.

## 2:30–2:35 — End on the product claim

**Screen:** return to the weakened decision or hero.

**Narration:**

> CounterSignal does not tell a founder what they want to hear. It makes them decide, in advance, what evidence would prove them wrong.

End there. No code editor. No terminal scrolling.

---

# Optional technical cutaways

Use only if the final edit is comfortably under 3:00.

### Decision Audit Console

Briefly open `judge-console.html` to show:

- exact Decision Replay transition;
- Adversarial Evidence Queue;
- next-evidence sensitivity;
- provenance drawer.

### CI proof

A one-second title card can say:

`GitHub Actions: pytest + judge invariants + deterministic benchmark — GREEN`

Do not hardcode a test count into the recorded narration because the suite can grow after recording.

### Reproducibility

If useful, show only these three commands:

```bash
python verify_product_v2.py
python benchmark.py --json
python -m pytest -q
```

Do not spend video time reading their full output.

---

# Recording rules

- Final public video must stay under 3:00; target **2:30–2:40**.
- Start on `index.html`, not on code.
- Keep the real SmallBet **8 / 5 / 3** rule and exact protocol identity visible.
- Preset evidence is simulated and must remain labeled as simulated.
- Never call a packet `live` unless it contains at least one actual permissioned `source="calle_live"` record.
- Never show phone numbers, API keys, raw transcripts, private permission receipts, or real participant quote text.
- Interview permission is not publication permission.
- A SHA-256 content seal is not an identity signature or trusted timestamp.
- The naive-majority benchmark is not a benchmark against a named commercial AI research platform.
- Do not claim product-market fit, population inference, statistical significance, ROI or conversion uplift from the dogfood experiment.
- End on **`hypothesis_weakened`** or the hero product claim, not on implementation details.
