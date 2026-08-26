# PermitPulse

PermitPulse is a bounded CALL-E workflow for one of the least glamorous but most persistent pieces of construction operations: calling a permit office to recover factual status and next-step information for an authorized project.

It is deliberately **not** a generic voice agent and it is **not** a permit-law interpreter. The app takes a known jurisdiction, permit/application reference and authorized caller context, generates a masked no-call preview, then can place one disclosed AI-assisted call through the official CALL-E Python SDK. The structured output is designed to answer the operational question: **what is the next thing the project team can actually do?**

## What it asks for

PermitPulse limits the conversation to factual process information the office is willing and authorized to provide:

- whether the application/permit reference is recognized;
- current status;
- missing checklist/correction items;
- next review or inspection milestone;
- any processing window the office is willing to state;
- the official source for updates; and
- the correct next contact or department.

If the office cannot verify the record, refuses, requires a human applicant, or says a written channel is authoritative, the app records that instead of guessing.

## Why this is useful

Contractors, permit expediters, architects and owners routinely lose time to hold queues, transfers, wrong departments and repeated status calls. PermitPulse turns that phone work into an inspectable structured result that can update a project record or produce a specific human follow-up task.

## Safety / side effects

Preview is the default and creates **no phone call**. Live execution requires all of the following:

1. `--execute`;
2. `--confirm-authorized-project`;
3. the exact E.164 destination supplied again with `--allow`;
4. `CALLE_LIVE_CALLS_ENABLED=true`; and
5. a local `CALLE_API_KEY`.

The task text requires AI disclosure and forbids applicant impersonation, invented authority and requests for protected personal information. A completed phone call is treated as evidence, not as legal advice or an official written determination. Weak or ambiguous outcomes fail closed to human review.

Stable idempotency keys are derived from the project request, permit reference and destination so the workflow can be reconciled instead of blindly creating a duplicate call.

### Cancellation / rollback

PermitPulse creates only one-off calls and no recurring schedule. Before execution, cancellation means simply staying in preview mode. After a call has been accepted by the provider, the phone side effect cannot be rolled back by this app; do not launch a replacement call until the existing CALL-E call ID has been reconciled. PermitPulse never performs a downstream permit-system mutation automatically, so an incorrect or disputed result can be discarded and routed to a human without changing the authoritative project record.

## Install

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

The runtime uses the official CALL-E SDK:

```text
calle-ai==0.2.0
```

## Preview — no call

```bash
permitpulse --request examples/request.example.json
```

The preview prints the masked destination, exact task, strict result schema and idempotency key. It does not instantiate the CALL-E client.

## Execute one authorized real call

Use a real destination only when the project team is authorized to make the inquiry and the number is appropriate for the permit office.

```bash
export CALLE_API_KEY='...'
export CALLE_LIVE_CALLS_ENABLED=true

permitpulse \
  --request /path/to/private-request.json \
  --execute \
  --confirm-authorized-project \
  --allow +15551234567
```

Do not commit real project phone numbers or private project records to the repository.

## Result routing

PermitPulse only routes a result to `update_project_record` when CALL-E reports a completed task, the office answered, the permit reference was confirmed and provider evidence is present. Wrong-office outcomes become `reroute`; voicemail, refusal and unreachable outcomes become follow-up; missing/weak evidence becomes human review.

## Tests

```bash
pytest
ruff check .
```

The test suite covers no-call preview behavior, stable idempotency, region validation, anti-impersonation language, evidence gating and fail-closed routing.

## Hackathon angle

The project is intentionally scoped around a real phone-work bottleneck rather than generic outbound calling. A judge can exercise the preview and fixtures without making a real call, while authorized live runs demonstrate the actual CALL-E integration and return a concrete operational artifact: an evidence-backed permit next step.
