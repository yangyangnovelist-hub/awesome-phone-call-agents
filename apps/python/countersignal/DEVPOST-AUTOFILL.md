# CounterSignal — Devpost autofill

Use this only as a submission checklist. Fields marked **TODO — verify truthfully** must not be inferred or populated with placeholders.

- **Submitter Type:** Individual
- **Country of residence/incorporation:** TODO — verify truthfully against CALL-E eligibility
- **Organization name:** leave blank unless applicable
- **App status:** Newly created
- **If pre-existing, explain updates:** Not applicable — CounterSignal was created during the submission period
- **Functional demo URL:** `https://countersignal.vercel.app` is the current public URL, but verify it contains the final product-v2 build before submission
- **Project submission pull request URL:** https://github.com/CALLE-AI/awesome-phone-call-agents/pull/198
- **Upstream PR status:** merged
- **Email associated with CALL-E account:** TODO — verify the actual CALL-E account email; never use a placeholder
- **Primary use case:** Other
- **One-sentence real-world task:** Runs permissioned customer-discovery phone interviews under a frozen protocol and turns grounded supporting and contradictory evidence into an auditable experiment decision.
- **Eligible Age:** TODO — submitter must affirm truthfully
- **Country eligibility:** TODO — submitter must affirm truthfully
- **Conflict of interest:** TODO — submitter must affirm truthfully
- **Demo video URL:** TODO — public YouTube or Vimeo, under 3 minutes

## Judge testing instructions

1. Use the product-v2 branch and enter `apps/python/countersignal`.
2. Use Python 3.11+.
3. Run `python -m pytest -q`.
4. Run `python verify_product_v2.py`.
5. Run `python benchmark.py --json`.
6. Open `index.html` for the flagship 60-second judge experience.
7. Press **+ Voicemail** and verify attempted increases while answered remains 8.
8. Add one contradiction and verify provisional support becomes `inconclusive`.
9. Add three contradictions and verify the frozen rule reaches `hypothesis_weakened` while five supporting interviews remain present.
10. Open `judge-console.html` for replay, provenance, fragility, and counterfactual next-evidence analysis.
11. Open `audit-verifier.html` for the permissioned live-proof verification boundary.
12. Run `python prove_live.py --experiment smallbet-experiment.json --recipient example-recipient.json` only as a masked no-call preview unless an actually permissioned reviewed recipient exists.

## Evidence labeling rule

- Deterministic reviewer fixtures must stay labeled simulated.
- A public packet may be labeled live only when it contains at least one actual `source="calle_live"` record and **all** evidence in that packet is live CALL-E evidence.
- Do not manufacture a live packet for the video.
