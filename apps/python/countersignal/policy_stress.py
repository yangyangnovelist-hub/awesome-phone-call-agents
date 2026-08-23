"""Seeded stress harness for CounterSignal's deterministic decision policy.

This is an invariant/reproducibility test, not a customer-research accuracy
benchmark. It generates evidence states and attacks properties that should hold
regardless of ordering or nonresponse noise.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import benchmark
import countersignal as core


def _buckets(counts: dict[str, int]) -> list[str]:
    out: list[str] = []
    for name in ("supporting", "disconfirming", "neutral", "nonresponse", "invalid"):
        out.extend([name] * counts[name])
    return out


def run_stress(
    experiment: core.Experiment,
    *,
    trials: int = 10_000,
    seed: int = 20260823,
) -> dict[str, Any]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)
    failures = {
        "denominator_noise_invariance": 0,
        "permutation_invariance": 0,
        "weakening_threshold": 0,
        "support_requires_zero_contradictions": 0,
        "support_launders_weakened_state": 0,
    }
    divergence = 0
    weakened_states = 0
    supported_states = 0

    for _ in range(trials):
        counts = {
            "supporting": rng.randint(0, 12),
            "disconfirming": rng.randint(0, 6),
            "neutral": rng.randint(0, 8),
            "nonresponse": rng.randint(0, 12),
            "invalid": rng.randint(0, 8),
        }
        evidence = _buckets(counts)
        result = core.experiment_decision(experiment, evidence)
        answered_only = [
            bucket
            for bucket in evidence
            if bucket in {"supporting", "disconfirming", "neutral"}
        ]
        no_noise = core.experiment_decision(experiment, answered_only)

        if (
            result["decision"] != no_noise["decision"]
            or result["answered_denominator"] != no_noise["answered_denominator"]
        ):
            failures["denominator_noise_invariance"] += 1

        permuted = list(evidence)
        rng.shuffle(permuted)
        shuffled = core.experiment_decision(experiment, permuted)
        if (
            shuffled["decision"] != result["decision"]
            or shuffled["answered_denominator"] != result["answered_denominator"]
            or shuffled["counts"] != result["counts"]
        ):
            failures["permutation_invariance"] += 1

        answered = counts["supporting"] + counts["disconfirming"] + counts["neutral"]
        rule = experiment.decision_rule
        if answered >= rule.min_answered and counts["disconfirming"] >= rule.weaken_if_at_least:
            weakened_states += 1
            if result["decision"] != "hypothesis_weakened":
                failures["weakening_threshold"] += 1
            after_support = core.experiment_decision(
                experiment, evidence + ["supporting"] * rng.randint(1, 8)
            )
            if after_support["decision"] != "hypothesis_weakened":
                failures["support_launders_weakened_state"] += 1

        if result["decision"] == "hypothesis_supported_under_rule":
            supported_states += 1
            if (
                counts["disconfirming"] != 0
                or counts["supporting"] < rule.support_if_at_least
                or answered < rule.min_answered
            ):
                failures["support_requires_zero_contradictions"] += 1

        naive = benchmark.naive_majority(evidence)
        if naive == "positive_signal" and result["decision"] in {
            "inconclusive",
            "hypothesis_weakened",
        }:
            divergence += 1

    return {
        "harness": "countersignal_policy_stress_v1",
        "trials": trials,
        "seed": seed,
        "invariants_ok": all(value == 0 for value in failures.values()),
        "failures": failures,
        "observed_states": {
            "weakened": weakened_states,
            "supported": supported_states,
            "naive_positive_but_countersignal_nonpositive": divergence,
        },
        "claim_boundary": (
            "Synthetic policy-state stress test only; it does not measure interview accuracy, "
            "population inference, product-market fit, or business outcomes."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="smallbet-experiment.json")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    experiment = core.parse_experiment(
        json.loads(Path(args.experiment).read_text(encoding="utf-8"))
    )
    report = run_stress(experiment, trials=args.trials, seed=args.seed)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"trials={report['trials']} seed={report['seed']} invariants_ok={report['invariants_ok']}")
        for name, value in report["failures"].items():
            print(f"{name}={value}")
        print(
            "naive_positive_but_countersignal_nonpositive="
            f"{report['observed_states']['naive_positive_but_countersignal_nonpositive']}"
        )
    return 0 if report["invariants_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
