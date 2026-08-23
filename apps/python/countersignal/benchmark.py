"""Deterministic benchmark for CounterSignal's contradiction handling.

The comparison baseline is intentionally simple and fully specified: a naive
majority heuristic calls the evidence positive whenever supporting interviews
outnumber disconfirming interviews. It is not presented as a model of any
specific commercial AI synthesis product.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import countersignal as core


def naive_majority(buckets: list[str]) -> str:
    support = sum(bucket == "supporting" for bucket in buckets)
    contradict = sum(bucket == "disconfirming" for bucket in buckets)
    if support > contradict:
        return "positive_signal"
    if contradict > support:
        return "negative_signal"
    return "mixed_signal"


def benchmark_cases() -> list[tuple[str, list[str]]]:
    baseline = ["supporting"] * 5 + ["neutral"] * 3
    return [
        ("baseline_support", baseline),
        ("one_grounded_contradiction", baseline + ["disconfirming"]),
        ("two_grounded_contradictions", baseline + ["disconfirming"] * 2),
        ("three_grounded_contradictions", baseline + ["disconfirming"] * 3),
        ("five_voicemails_do_not_change_denominator", baseline + ["nonresponse"] * 5),
    ]


def run_benchmark(experiment: core.Experiment) -> dict[str, Any]:
    rows = []
    for name, buckets in benchmark_cases():
        counter = core.experiment_decision(experiment, buckets)
        naive = naive_majority(buckets)
        rows.append(
            {
                "case": name,
                "answered": counter["answered_denominator"],
                "supporting": counter["counts"]["supporting"],
                "disconfirming": counter["counts"]["disconfirming"],
                "nonresponse": counter["counts"]["nonresponse"],
                "naive_majority": naive,
                "countersignal": counter["decision"],
                "diverges": (
                    naive == "positive_signal"
                    and counter["decision"] in {"inconclusive", "hypothesis_weakened"}
                ),
            }
        )
    return {
        "benchmark": "contradiction_load_bearing_v1",
        "baseline": "naive majority over supporting vs disconfirming answered interviews",
        "claim_boundary": "This benchmark compares deterministic decision policies, not commercial AI research products.",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default="smallbet-experiment.json")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    data = json.loads(Path(args.experiment).read_text(encoding="utf-8"))
    experiment = core.parse_experiment(data)
    report = run_benchmark(experiment)
    if args.as_json:
        print(json.dumps(report, indent=2))
        return 0
    print("case\tanswered\tsupport\tcontra\tnonresponse\tnaive\tcountersignal\tdiverges")
    for row in report["rows"]:
        print(
            f"{row['case']}\t{row['answered']}\t{row['supporting']}\t{row['disconfirming']}\t"
            f"{row['nonresponse']}\t{row['naive_majority']}\t{row['countersignal']}\t{row['diverges']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
