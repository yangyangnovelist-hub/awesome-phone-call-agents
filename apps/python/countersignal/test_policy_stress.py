import countersignal as core
import policy_stress


EXPERIMENT = {
    "experiment_id": "stress-v1",
    "segment": "small contractors",
    "problem": "manual permit follow-up",
    "hypothesis": "manual follow-up recurs enough to require a workaround",
    "questions": ["What happened?", "What did you do?", "How often?"],
    "decision_rule": {"min_answered": 8, "support_if_at_least": 5, "weaken_if_at_least": 3},
}


def test_seeded_policy_stress_has_zero_invariant_failures():
    report = policy_stress.run_stress(
        core.parse_experiment(EXPERIMENT),
        trials=10_000,
        seed=20260823,
    )
    assert report["trials"] == 10_000
    assert report["seed"] == 20260823
    assert report["invariants_ok"] is True
    assert all(value == 0 for value in report["failures"].values())
    assert report["observed_states"]["weakened"] > 0
    assert report["observed_states"]["supported"] > 0
    assert report["observed_states"]["naive_positive_but_countersignal_nonpositive"] > 0
    assert "does not measure interview accuracy" in report["claim_boundary"]
