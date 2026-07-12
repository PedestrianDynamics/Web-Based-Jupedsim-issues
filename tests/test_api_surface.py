"""Smoke test for the public jupedsim_scenarios API.

Fails loudly when upstream renames or removes a symbol that this
repository depends on. Cheap enough to run on every CI invocation.
"""

import inspect

import jupedsim_scenarios as jps

# Only symbols this repo actually imports — verified via
# `rg 'from jupedsim_scenarios import'` across the tree.
REQUIRED_SYMBOLS = (
    "Scenario",
    "ScenarioResult",
    "load_scenario",
    "run_scenario",
    "run_sweep",
    "run_sweep_from_factory",
)


def test_required_symbols_exported():
    missing = [name for name in REQUIRED_SYMBOLS if not hasattr(jps, name)]
    assert not missing, f"jupedsim_scenarios missing public symbols: {missing}"


def test_load_scenario_accepts_path():
    sig = inspect.signature(jps.load_scenario)
    params = list(sig.parameters.values())
    assert params, "load_scenario() lost all parameters"
    first = params[0]
    assert first.name == "path", (
        f"load_scenario first parameter renamed: {sig}; this repo passes "
        "the scenario path positionally."
    )
    assert first.kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ), f"load_scenario.path can no longer be passed positionally: {sig}"
    # Any additional parameters must be optional (have a default).
    extras_without_default = [p for p in params[1:] if p.default is inspect.Parameter.empty]
    assert not extras_without_default, (
        f"load_scenario gained required parameters beyond `path`: {sig}"
    )


def test_run_scenario_accepts_scenario_and_seed_kwarg():
    sig = inspect.signature(jps.run_scenario)
    params = sig.parameters
    assert "scenario" in params, f"run_scenario lost `scenario` param: {sig}"
    assert "seed" in params, f"run_scenario lost `seed` param: {sig}"
    assert params["seed"].kind is not inspect.Parameter.POSITIONAL_ONLY, (
        f"run_scenario.seed can no longer be passed as a keyword: {sig}"
    )


def test_scenario_class_exposes_used_methods():
    # The ``set_seed`` / ``set_max_time`` / ``set_model_type`` methods were
    # removed upstream in 0.5; this repo now assigns the attributes directly.
    # ``seed`` / ``model_type`` are dataclass fields (only on instances),
    # ``max_simulation_time`` is a property and ``set_model_params`` a method.
    members = set(dir(jps.Scenario)) | set(getattr(jps.Scenario, "__dataclass_fields__", {}))
    required = {
        "seed",
        "max_simulation_time",
        "model_type",
        "set_model_params",
    }
    missing = required - members
    assert not missing, f"Scenario lost members used by this repo: {missing}"


def test_scenario_result_exposes_used_attrs():
    required = {"success", "evacuation_time", "cleanup"}
    missing = required - set(dir(jps.ScenarioResult))
    assert not missing, f"ScenarioResult lost attrs used by this repo: {missing}"
