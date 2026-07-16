"""
NIST TN 1822 Verif.1.1 - Pre-evacuation time distributions.

Thin wrapper around the upstream ``standards/utils/premovement_distributions``
module, which already ships the four NIST distributions and their canonical
parameters as ``PREMOVEMENT_PRESETS``. The base ZIP (Nist-1-1-premovement.zip)
ships the uniform case as the default; ``build_variants`` yields the three
other cases.

Source: NIST TN 1822 section 3.1.1 (Verif.1.1).
"""
from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

# standards/utils is two levels up from standards/nist/scenario_builders/.
_UTILS_PARENT = Path(__file__).resolve().parents[2]
if str(_UTILS_PARENT) not in sys.path:
    sys.path.insert(0, str(_UTILS_PARENT))

from utils.premovement_distributions import (  # type: ignore  # noqa: E402
    create_premovement_distribution,
)

DISTRIBUTION_ID = "jps-distributions_0"

# Distribution parameters for each case. NIST TN 1822 section 3.1.1 names
# only the distribution *types* (uniform / normal / log-normal / etc.), not
# numeric parameters - these values are the model's built-in premovement
# presets, hard-coded here so we never depend on upstream PREMOVEMENT_PRESETS
# defaults. Uniform is overridden to U(10, 100) (the upstream default is
# U(0, 60)); gamma/lognormal/weibull match the presets, listed for traceability.
NIST_CASES = {
    "uniform":   {"a": 10.0,    "b": 100.0,   "max_time_s": 180},
    "gamma":     {"a": 1.291,   "b": 103.901, "max_time_s": 1200},
    "lognormal": {"a": 4.586,   "b": 0.967,   "max_time_s": 2400},
    "weibull":   {"a": 139.285, "b": 1.195,   "max_time_s": 1200},
}


@dataclass(frozen=True)
class PreEvacCase:
    name: str
    params: dict
    max_simulation_time_s: int

    @property
    def param_a(self) -> float:
        return float(self.params["a"])

    @property
    def param_b(self) -> float:
        return float(self.params["b"])


def load_cases() -> list[PreEvacCase]:
    """Return the four pre-evac cases (distribution types per NIST TN 1822
    section 3.1.1; numeric parameters as configured in ``NIST_CASES``)."""
    return [
        PreEvacCase(
            name=name,
            params={"a": spec["a"], "b": spec["b"]},
            max_simulation_time_s=spec["max_time_s"],
        )
        for name, spec in NIST_CASES.items()
    ]


def build_variants(base_scenario):
    """Yield (case, scenario) - one per NIST distribution.

    The base scenario is deep-copied for each case so the loaded ZIP is never
    mutated in place. Premovement parameters are written straight onto the
    distribution parameters (see the note below) because ``set_agent_params``
    rejects the ``premovement_*`` kwargs.
    """
    for case in load_cases():
        variant = deepcopy(base_scenario)
        # Premovement is read straight from the distribution parameters at
        # simulation-init time; ``set_agent_params`` whitelists only movement
        # kwargs and rejects ``premovement_*``, so write them in directly.
        params = variant.distributions[DISTRIBUTION_ID]["parameters"]
        params["use_premovement"] = True
        params["premovement_distribution"] = case.name
        params["premovement_param_a"] = case.param_a
        params["premovement_param_b"] = case.param_b
        variant.max_simulation_time = case.max_simulation_time_s
        yield case, variant


def sample_reference(case: PreEvacCase, n: int, seed: int):
    """Sample n times from the case's analytic distribution (for fit-overlay plots)."""
    dist = create_premovement_distribution(case.name, case.params, seed=seed)
    return dist.sample(n)
