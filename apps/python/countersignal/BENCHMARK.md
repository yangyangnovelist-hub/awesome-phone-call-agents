# CounterSignal contradiction stress benchmark

This benchmark isolates one product claim: **evidence against the operator's hypothesis remains load-bearing even when supportive interviews are still the numerical majority.**

It compares two explicit deterministic decision policies over the same evidence. It is not a comparison against a named commercial AI research product.

## Frozen protocol

The dogfood study uses the pre-registered `smallbet-permit-ops-v1` rule:

- minimum answered interviews: **8**
- provisional support: **5 supporting and zero grounded contradictions**
- hypothesis weakening: **3 grounded contradictions**
- voicemail/refusal/unreachable/invalid results do not enter the answered denominator

## Expected deterministic result

| Evidence state | Answered | Support | Contradictions | Naive majority | CounterSignal |
| --- | ---: | ---: | ---: | --- | --- |
| 5 support + 3 neutral | 8 | 5 | 0 | `positive_signal` | `hypothesis_supported_under_rule` |
| + 1 contradiction | 9 | 5 | 1 | `positive_signal` | `inconclusive` |
| + 2 contradictions | 10 | 5 | 2 | `positive_signal` | `inconclusive` |
| + 3 contradictions | 11 | 5 | 3 | `positive_signal` | `hypothesis_weakened` |
| + 5 voicemails instead | 8 | 5 | 0 | `positive_signal` | `hypothesis_supported_under_rule` |

The important row is the fourth one. The supportive interviews still outnumber the contradictions **5 to 3**, so the naive majority remains positive. CounterSignal weakens the hypothesis because the contradiction threshold was fixed before evidence collection.

The voicemail case demonstrates a separate invariant: adding attempts that never become valid answered interviews must not make the evidence base appear larger.

## Reproduce

From `apps/python/countersignal/`:

```bash
python benchmark.py
python benchmark.py --json
pytest -q test_product_v2.py test_console_product_v2.py
```

The benchmark has no network dependency and places no phone calls.

## Claim boundary

This benchmark demonstrates a difference between two deterministic evidence policies. It does **not** establish that CounterSignal improves population inference, product-market-fit prediction, interview quality, or business outcomes. Those require separate empirical validation. The live dogfood study is designed to add real CALL-E evidence without changing the pre-registered decision rule.
