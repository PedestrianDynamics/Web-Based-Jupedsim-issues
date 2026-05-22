"""Smoke test for the public jupedsim_scenarios API.

Fails loudly when upstream renames or removes a symbol that this
repository depends on. Cheap enough to run on every CI invocation.
"""

import inspect

import pytest


@pytest.fixture(scope="module")
def jps():
    return pytest.importorskip("jupedsim_scenarios")


REQUIRED_SYMBOLS = (
    "Scenario",
    "ScenarioResult",
    "SweepResult",
    "Trial",
    "load_scenario",
    "run_scenario",
    "run_sweep",
    "run_sweep_from_factory",
)


def test_required_symbols_exported(jps):
    missing = [name for name in REQUIRED_SYMBOLS if not hasattr(jps, name)]
    assert not missing, f"jupedsim_scenarios missing public symbols: {missing}"


def test_load_scenario_signature(jps):
    sig = inspect.signature(jps.load_scenario)
    params = list(sig.parameters)
    assert params == ["path"], (
        f"load_scenario signature drifted: {sig}; "
        "this repo passes a single positional path argument."
    )


def test_run_scenario_signature(jps):
    sig = inspect.signature(jps.run_scenario)
    params = sig.parameters
    assert "scenario" in params, f"run_scenario lost `scenario` param: {sig}"
    assert "seed" in params, f"run_scenario lost `seed` param: {sig}"
    assert params["seed"].kind is inspect.Parameter.KEYWORD_ONLY, (
        f"run_scenario.seed should remain keyword-only: {sig}"
    )


def test_scenario_class_exposes_used_methods(jps):
    required = {
        "set_seed",
        "set_max_time",
        "set_model_type",
        "set_model_params",
    }
    missing = required - set(dir(jps.Scenario))
    assert not missing, f"Scenario lost methods used by this repo: {missing}"


def test_scenario_result_exposes_used_attrs(jps):
    required = {"success", "evacuation_time", "cleanup"}
    missing = required - set(dir(jps.ScenarioResult))
    assert not missing, f"ScenarioResult lost attrs used by this repo: {missing}"
