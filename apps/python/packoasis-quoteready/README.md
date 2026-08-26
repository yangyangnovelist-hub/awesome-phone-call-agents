# PackOasis QuoteReady

PackOasis QuoteReady uses CALL-E to turn an incomplete **existing packaging inquiry** into a quote-ready RFQ. It is buyer-side sales operations for a real custom-packaging workflow, not generic cold calling and not supplier-side manufacturing clarification.

A buyer may ask for “50,000 custom boxes” while omitting the dimensions, structure, materials, printing, finish, delivery location, deadline, sample requirement, or buying timeline needed for an accurate quote. Email ping-pong can take days. QuoteReady makes one bounded follow-up call, reads the requirements back for correction, and returns a structured RFQ plus an explicit `quote_ready` decision.

## What CALL-E collects

- box type / structure;
- dimensions and units;
- quantity;
- material preference;
- printing;
- finish;
- insert;
- target unit price, only if the buyer chooses to share it;
- delivery country;
- required delivery date;
- physical-sample requirement;
- existing-supplier status;
- decision timeline;
- whether a formal quote is requested; and
- the next action.

QuoteReady never promises a price, discount, lead time, production capability, certification, shipping date, sample approval, or contract term. Those remain with the human commercial team.

## Real-world boundary

The live workflow accepts only `inbound_inquiry`, `existing_customer`, `warm_followup`, or `explicit_permission` contact bases. `cold_prospect` is rejected. At the beginning of a call the agent discloses that it is an AI assistant and asks whether the recipient is willing to continue. A refusal stops the workflow.

The application is designed to be used with PackOasis's actual packaging pipeline so hackathon evidence can measure business outcomes such as:

- answered-call rate;
- RFQ completion rate;
- quote-ready rate;
- number of missing fields recovered;
- sample-request rate;
- formal-quote request rate;
- time from inquiry to quote-ready requirements; and
- later quote/order progression.

A completed phone call by itself is **not** counted as business impact.

## Evidence and result integrity

An actionable RFQ must satisfy all of these conditions:

1. CALL-E returned a terminal successful task at sufficient confidence;
2. the strict result schema validates exactly;
3. provider metadata matches the approved PackOasis inquiry;
4. the returned call ID matches the call that was actually created;
5. the result belongs to the exact approved destination;
6. provider evidence is present;
7. the buyer continued after AI disclosure;
8. the inquiry reference is confirmed; and
9. that reference is corroborated in recipient-side transcript text using normalized token-sequence matching.

A prefix such as `RFQ-EXAMPLE-00` cannot corroborate `RFQ-EXAMPLE-001`.

Only after those checks does the application decide whether the minimum quote fields are complete. Complete records route to `prepare_quote`; incomplete ones route to `collect_remaining_fields`.

## Preview — no phone call

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

packoasis-quoteready --request examples/request.example.json
```

The preview masks the phone number and shows the exact CALL-E task, result schema, contact basis, and idempotency key without instantiating a live call.

## Execute one authorized warm follow-up

Use a private request file containing the actual business contact. Never commit a real buyer phone number or customer record.

```bash
export CALLE_API_KEY='...'
export CALLE_LIVE_CALLS_ENABLED=true

packoasis-quoteready \
  --request /path/to/private-rfq.json \
  --execute \
  --confirm-warm-business-contact \
  --allow +15551234567
```

Live execution is one-off. Before dispatch, cancellation means remaining in preview mode. After CALL-E has accepted a call, do not blindly create a replacement call if the result is uncertain; reconcile the existing call first. QuoteReady itself never writes a binding quote or contract.

## Tests

```bash
pytest
ruff check .
```

Tests cover no-call preview, rejection of cold prospects, non-commitment language, idempotency, quote-readiness gates, call/destination/evidence binding, transcript-reference corroboration, prefix rejection, refusal after AI disclosure, and confidence gating.

## Why this is distinct

QuoteReady is not an incident-support workflow like IncidentBridge and not a permit-office workflow like PermitPulse. It is also intentionally different from generic supplier-clarification examples: the operational artifact here is a **buyer-confirmed, quote-ready custom-packaging RFQ tied to measurable commercial progression in an existing packaging business**.
