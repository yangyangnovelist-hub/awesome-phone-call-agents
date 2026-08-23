# CounterSignal judge demo — target 2:35

The demo should prove one thing: CounterSignal is not an AI interviewer with a dashboard. It is a decision-audit system that makes contradictory customer evidence load-bearing. The deterministic console is safe to show without credentials; a permissioned live CALL-E audit packet can replace the simulated evidence later without changing the story.

## 0:00–0:15 — The category problem

**Screen:** Decision Audit Console hero: `Customer research that can prove you wrong.`

**Narration:**

> AI can make customer interviews faster, but faster confirmation bias is still confirmation bias. CounterSignal freezes what would change your mind before the first interview, then makes every conclusion replayable back to evidence.

## 0:15–0:35 — Freeze the decision contract

**Screen:** pre-registered hypothesis, protocol hash, and the **8 / 5 / 3** rule.

**Narration:**

> Before any call, the segment, hypothesis, five questions, and decision thresholds are frozen into a protocol identity. Eight valid answers are required, five supporting interviews can provisionally support the hypothesis only with zero contradictions, and three grounded contradictions weaken it. Changing the study creates a new identity.

## 0:35–0:55 — Evidence, not call completion

**Screen:** click an evidence-ledger row to open provenance.

**Narration:**

> A completed call is not evidence by itself. A usable result must bind to the exact CALL-E call, reviewed recipient, experiment, protocol hash, confidence gate, and a quote grounded in recipient-side transcript text. Refusal, voicemail, low-confidence, mismatched, and ungrounded outcomes cannot become positive evidence.

**Live replacement:** if a permissioned dogfood call exists, load the redacted `countersignal.audit.v1` packet and show its CALL-E call ID plus hashed recipient reference here.

## 0:55–1:10 — Honest denominator

**Screen:** start at `8 answered`; press `+ Voicemail` once.

**Narration:**

> Add a voicemail. Attempted calls rise, but the answered denominator stays eight. Silence never enters the denominator.

## 1:10–1:45 — Replay exactly when the conclusion changes

**Screen:** inject contradictions one by one while Decision Replay is visible.

**Narration:**

> Now add evidence against the founder's idea. The first grounded contradiction immediately removes provisional support and the study becomes inconclusive. At three contradictions the frozen weakening threshold is reached. Five supportive interviews remain visible; CounterSignal refuses to average away the evidence that falsified the working hypothesis.

**Judge point:** point at the exact replay step where the state changes.

## 1:45–2:08 — Reproducible contradiction benchmark

**Screen:** Contradiction Stress Benchmark.

**Narration:**

> This behavior is reproducible outside the UI. The benchmark compares two fully specified deterministic policies over the same evidence. A naive majority rule still says positive when five supporting interviews outnumber three contradictions. CounterSignal returns `hypothesis_weakened` because the three contradictions crossed the rule frozen before data collection.

**Proof:** mention `python benchmark.py --json`. Do not describe the naive baseline as a commercial AI product.

## 2:08–2:25 — Portable audit trail

**Screen:** Export Audit JSON, then point to Load Audit JSON.

**Narration:**

> Every evidence row can be exported as a redacted audit packet. The browser only accepts the exact experiment and protocol hash, so evidence from a different study cannot silently enter the decision replay. A live packet keeps CALL-E provenance while replacing the phone number with a stable one-way recipient reference.

## 2:25–2:35 — Reliability boundary

**Screen:** CALL-E evidence contract.

**Narration:**

> The live path uses the published CALL-E Python SDK with explicit participation permission, exact allowlisting, durable intent reservation, and no blind redial after an ambiguous provider outcome. The output is an auditable research decision, not a product-market-fit claim.

## Recording rules

- Keep the final public video under 3:00; target 2:30–2:40.
- Do not show real phone numbers, CALL-E keys, full transcripts, or recipient identities.
- The preset console evidence is simulated and must remain labeled as such.
- The displayed rule must remain the real SmallBet **8 / 5 / 3** rule.
- Only call an audit packet `live` when its records were built from permissioned real CALL-E results.
- The benchmark compares deterministic policies; do not imply it measures a named commercial research platform.
- End on `hypothesis_weakened` plus the benchmark divergence, not on a code editor.
