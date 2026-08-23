# CounterSignal real-world validation: SmallBet permit-ops experiment

This is the pre-registration for the first real CounterSignal dogfood run. It exists so the result cannot be rewritten after hearing the calls.

## Study question

Do small and midsize US commercial contractors experience enough permit-status ambiguity to already spend recurring operator time on a manual workaround?

The purpose is **problem discovery**, not selling a permit service. The phone task must not quote a price, pitch automation, book a sales meeting, or convert a respondent into a lead score.

## Frozen protocol

Use [`smallbet-experiment.json`](smallbet-experiment.json) unchanged for the run. Its SHA-derived `protocol_hash` is the experiment version. If wording or thresholds change, create a new experiment ID rather than continuing the old denominator.

Target segment:

- US commercial/general contractors or permit-heavy specialty contractors;
- small or midsize operating teams rather than national enterprise headquarters;
- business appears to manage permit-dependent work directly; and
- a public business contact channel is available for an operator-reviewed participation invitation.

Do not infer that a generic construction company belongs in the segment merely because it exists. The operator must review the company context first.

## Decision rule

- Minimum answered interviews: **8**.
- Provisional support threshold: **5 supporting** and **0 disconfirming**.
- Weaken threshold: **3 disconfirming** once the minimum answered denominator is reached.
- Refusal, voicemail, unreachable, low-confidence, ungrounded, or schema-invalid outcomes never enter the answered denominator.

A supporting interview means the respondent reports that the problem occurs and that an existing workaround/process is used. A disconfirming interview means the respondent directly says the problem does not occur, is immaterial, or the assumed workflow is wrong. Everything else is neutral.

This is an operational decision rule for one discovery experiment. It is not a prevalence estimate, confidence interval, total-addressable-market estimate, or product-market-fit claim.

## Why 8 / 5 / 3

These thresholds encode the **cost of a bad early-stage decision**, not a claim about statistical significance.

The design is intentionally conservative against confirmation bias:

- **8 minimum answered** prevents one or two memorable anecdotes from becoming a terminal experiment decision. It is still small enough to fit a bounded SmallBet discovery loop.
- **5 supporting** requires the target pattern to repeat across several answered interviews. A “supporting” record is also deliberately stronger than generic interest: the respondent must report the problem **and an existing workaround/process**.
- **0 contradictions for provisional support** makes support fragile by design. One grounded contradiction is enough to remove the `supported` label and move the experiment to `inconclusive`; supportive anecdotes cannot simply outvote it.
- **3 contradictions to weaken** creates a second stage rather than allowing one unusual respondent to kill the idea. The first contradiction removes confidence; repeated contradiction across three valid answered interviews is the stop/rescope signal.
- **Minimum sample applies before weakening** so the system does not declare `hypothesis_weakened` from a tiny two- or three-call sample even if every early answer is negative.
- **Neutral answers still count in the answered denominator**. The operator cannot hide ambiguous but valid interviews and compute thresholds only over convenient support/disconfirm cases.

The resulting contradiction path is explicit:

```text
0 contradictions + enough support -> hypothesis_supported_under_rule
1 or 2 contradictions             -> inconclusive
3+ contradictions after 8 answers -> hypothesis_weakened
```

This is an **asymmetric loss policy** for a cheap discovery experiment: it is intentionally harder to keep the positive label once credible counterevidence appears, but it still requires repeated counterevidence before the hypothesis is actively weakened.

Changing these numbers after seeing evidence would be a different experiment version. CounterSignal's contribution is not that 8/5/3 is universally optimal; it is that the decision policy is explicit, frozen, replayable, and allowed to produce an inconvenient result.

## Recipient and consent rules

For this US dogfood run, a public business phone number is **not** treated as permission for an AI-voice call. Candidate businesses are contacted first through a non-call participation invitation such as a published business email, SMS initiated with appropriate permission, web form, in-person agreement, or another reviewed channel. CALL-E is used only after the intended participant affirmatively agrees to the AI phone research interview and confirms the business number/time window to use.

This deliberately conservative study rule exists because AI-generated speech can trigger artificial/prerecorded voice requirements and consent requirements vary with jurisdiction, destination, and context. CounterSignal does not infer legal permission from the fact that a number is publicly listed.

For every CALL-E dogfood interview:

- retain a private operator-side reference to the affirmative participation response before execution;
- review the exact recipient, number, time window, segment fit, and suppression status;
- identify the caller as an AI research assistant at the start of the call;
- ask whether the participant is still willing to continue before substantive questions;
- end immediately on refusal or uncertainty; and
- do not reuse the permission for a sales call or a separate PermitDiff municipal call.

Maintain an operator-side suppression list for any business that asks not to be contacted again. A refusal is a completed compliance outcome, not a failed conversion.

## Permission funnel metrics

The permission stage is part of the evidence packet rather than hidden operational overhead. Record:

- reviewed candidate businesses;
- participation invitations sent;
- affirmative opt-ins;
- explicit declines;
- nonresponses;
- opt-in-to-valid-interview conversion; and
- elapsed/operator time required to obtain permission.

A low permission rate is real evidence about deployability and must not be excluded from the product story.

## What to measure during CALL-E interviews

Record these directly rather than estimating them after the fact:

- authorized attempted calls;
- answered calls;
- interviews that continue after AI disclosure;
- refusals / voicemail / unreachable;
- supporting / disconfirming / neutral / invalid outcomes;
- number of transcript-grounded contradictions preserved;
- operator minutes spent preparing/reviewing each delegated call;
- for a small manual baseline, operator minutes required to conduct and summarize the same interview without delegation; and
- whether the frozen experiment decision changes after each valid answered interview.

The primary product KPI is **operator minutes displaced per valid answered discovery interview**, reported together with the permission funnel and outcome-integrity metrics. Do not turn a short call into a dollar ROI claim without observed labor-cost inputs.

## Stop conditions

Stop the experiment instead of spending the remaining call budget when any of the following occurs:

- an implementation or evidence-binding defect makes results unreliable;
- recipient sourcing is no longer clearly within the intended segment;
- a compliance/consent issue is discovered;
- the frozen rule reaches `hypothesis_weakened` and further calls would only be used to rescue the idea; or
- enough evidence has been collected to move to a separately defined pilot-recruitment experiment.

Reaching `hypothesis_supported_under_rule` does not authorize a sales blast. It authorizes the next explicit experiment: ask a small number of qualified operators whether they will separately opt in to providing an authorized real permit case for a PermitDiff pilot.

A CounterSignal research opt-in is not permission to call a municipality about that respondent's permit. PermitDiff requires its own applicant-side authorization and case-specific validation.

## Judge evidence packet

After the run, publish a privacy-minimized aggregate containing the frozen experiment JSON/hash, permission-funnel counts, counts by interview outcome bucket, decision sequence by interview number, measured operator-time methodology, failures/nonresponses, and publication-safe aggregate evidence. Do not publish phone numbers, identities, email thread IDs, full transcripts, private recordings, or real participant quote text unless separate publication permission exists.
