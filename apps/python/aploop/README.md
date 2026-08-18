# APLoop

APLoop is a bounded CALL-E workflow for a narrow B2B accounts-receivable problem: an invoice already exists, the supplier already has a legitimate business relationship with the customer, and somebody still has to call accounts payable to find out whether the invoice was received, what is blocking it, and when the next payment step is expected.

It is **not** a debt-collection bot. It does not take payment details, negotiate settlements, threaten consequences, issue new payment instructions, or make binding commercial commitments.

## What it asks for

For a known invoice reference, APLoop asks only for ordinary business-process facts:

- whether the invoice reference is recognized and received;
- whether it is pending approval, approved, scheduled, paid, disputed, or not found;
- whether a PO, receipt, tax document, approval, or other ordinary document is missing;
- the high-level reason for a dispute if the recipient chooses to provide it;
- any expected payment date the recipient is willing to state; and
- the correct AP contact or next action.

If payment-instruction changes, bank verification, credentials, tax IDs, or other sensitive data come up, the call is instructed to move the issue back to the parties' established secure channel and flag human follow-up.

## Why this is useful

Small suppliers and service businesses often lose real cash-flow time to a simple visibility problem: an invoice is sitting somewhere inside the customer's AP workflow and the supplier does not know where. APLoop converts a repetitive status call into a structured operational record so the team can distinguish `scheduled`, `missing document`, `disputed`, `wrong desk`, and `follow up later` instead of repeatedly making the same call.

## Safety / side effects

Preview is the default and creates **no phone call**. Live execution requires:

1. `--execute`;
2. `--confirm-existing-b2b-invoice`;
3. the exact E.164 destination supplied again through `--allow`;
4. `CALLE_LIVE_CALLS_ENABLED=true`; and
5. a local `CALLE_API_KEY`.

The request itself must use `existing_customer`, `vendor_relationship`, or `explicit_permission` as its contact basis. Cold-prospect calling is intentionally rejected by this app.

The call must disclose that it is AI-assisted. APLoop only records an actionable payment status when CALL-E reports a completed task, the invoice reference was confirmed, and provider evidence is present. Disputes and sensitive blockers route to a human.

### Cancellation / rollback

APLoop creates only one-off calls and no recurring schedule. Before dispatch, cancellation means remaining in preview mode. Once the provider has accepted the real call, that phone side effect cannot be undone by this app; reconcile the existing CALL-E call before attempting another. APLoop does not change an ERP, send payment instructions, or mark an invoice paid on its own, so a disputed or incorrect call result can be discarded without mutating the authoritative accounting record.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

The live runtime uses:

```text
calle-ai==0.2.0
```

## Preview — no call

```bash
aploop --request examples/request.example.json
```

The preview prints the masked destination, exact call task, strict result schema, contact basis, and stable idempotency key.

## Execute one authorized real call

Use a private request file containing the real AP/business contact. Do not commit customer phone numbers or invoice records.

```bash
export CALLE_API_KEY='...'
export CALLE_LIVE_CALLS_ENABLED=true

aploop \
  --request /path/to/private-request.json \
  --execute \
  --confirm-existing-b2b-invoice \
  --allow +15551234567
```

## Result routing

- `approved`, `scheduled`, or `paid` + confirmed reference + evidence -> `record_payment_status`
- `disputed` or sensitive/human blocker -> `human_action`
- wrong AP desk -> `reroute`
- pending approval or other non-terminal state -> `follow_up`
- missing evidence, failed call, or unconfirmed invoice reference -> `human_review`

## Tests

```bash
pytest
ruff check .
```

The tests cover no-call preview behavior, rejection of cold-prospect use, sensitive-financial boundaries, idempotency, evidence gating, disputes, and non-terminal AP states.

## Hackathon angle

APLoop is deliberately specific: it solves the phone gap between "invoice sent" and "cash-flow status known" without becoming an autonomous collections system. The judge-facing no-call path is safe to run, while authorized real calls demonstrate CALL-E doing actual business phone work and returning a directly useful operational outcome.
