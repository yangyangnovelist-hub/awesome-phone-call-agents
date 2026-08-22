# CounterSignal judge demo — target 2:20

The demo should prove one thing: CounterSignal is not an AI interviewer with a dashboard. It is a decision-audit system that makes contradictory customer evidence load-bearing. Everything below can be shown with the deterministic Decision Audit Console and no credentials. A real-call clip can replace the marked section later without changing the story.

## 0:00–0:16 — The category problem

**Screen:** Decision Audit Console hero: `Customer research that can prove you wrong.`

**Narration:**

> AI can make customer interviews faster, but faster confirmation bias is still confirmation bias. CounterSignal freezes what would change your mind before the first interview, then makes every conclusion replayable back to evidence.

## 0:16–0:38 — Freeze the decision contract

**Screen:** pre-registered hypothesis, protocol hash, and the **8 / 5 / 3** rule.

**Narration:**

> Before any call, the segment, hypothesis, five questions, and decision thresholds are frozen into a protocol identity. This protocol requires eight valid answered interviews, five supporting interviews for provisional support, and three grounded contradictions to weaken the hypothesis. Changing the study creates a new identity; the operator cannot rewrite the experiment after seeing the answers.

## 0:38–0:58 — Evidence, not call completion

**Screen:** click an evidence-ledger row to open provenance.

**Narration:**

> A completed call is not evidence by itself. A usable result must bind to the exact CALL-E call, reviewed recipient, experiment, protocol hash, confidence gate, and a quote grounded in recipient-side transcript text. Refusal, voicemail, unreachable, low-confidence, mismatched, and ungrounded results stay outside the answered denominator.

**Later live-proof replacement:** show one permissioned CALL-E call ID and redacted evidence record here.

## 0:58–1:14 — Honest denominator

**Screen:** note `8 answered`; press `Inject voicemail` once.

**Narration:**

> The study starts at eight answered interviews: five support and three neutral. Add a voicemail and the attempted count rises, but the answered denominator stays eight. Silence cannot inflate the research result.

## 1:14–1:48 — Replay exactly when the conclusion changes

**Screen:** press `Replay decision`, then inject contradictions one by one. Keep the Decision Replay and Adversarial Evidence Queue visible.

**Narration:**

> Now add evidence against the founder's idea. The first grounded contradiction immediately removes provisional support and moves the study to inconclusive. At three contradictions the frozen weakening threshold is reached. Five supportive interviews remain visible; CounterSignal refuses to average away the evidence that falsified the working hypothesis.

**Judge point:** point at the replay rows showing the exact interview number where the state changed.

## 1:48–2:05 — Show the next discriminating evidence

**Screen:** decision card and Decision Memo.

**Narration:**

> CounterSignal also exposes decision fragility. Before a contradiction it tells you that one negative case is enough to remove support and three would weaken the hypothesis. After the state changes, the memo reports what remains uncertain and what evidence would be decision-relevant next.

## 2:05–2:20 — Reliability boundary

**Screen:** CALL-E evidence contract and Export Audit JSON.

**Narration:**

> The live path uses the published CALL-E Python SDK with explicit participation permission, exact allowlisting, durable intent reservation, content-bound idempotency, and no blind redial after ambiguous provider outcomes. The output is an exportable audit trail, not a product-market-fit claim.

## Recording rules

- Keep the final public video under 3:00; target 2:15–2:25.
- Do not show real phone numbers, CALL-E keys, full transcripts, or recipient identities.
- The console uses deterministic simulated evidence and says so on screen; never present it as a live call.
- The displayed rule must remain the real SmallBet **8 / 5 / 3** rule.
- If a live clip is available, show a redacted provider call ID plus the exact evidence-binding fields; do not show raw participant identity.
- End on the decision replay / `hypothesis_weakened` transition, not on a code editor.
