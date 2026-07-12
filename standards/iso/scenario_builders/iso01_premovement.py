"""
ISO 20414:2020 Test 1 - Pre-evacuation time assignment.

Thin wrapper around ``standards/utils/premovement_distributions``. The base
ZIP (Iso-01-premovement.zip) ships the uniform case as the default; the
``build_variants`` helper yields one variant per distribution ISO names
explicitly in Test 1 ("uniform, normal, log-normal, etc.").

Source: ISO 20414:2020(E) Table 2 (Test 1).
"""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

# standards/utils is two levels up from standards/iso/scenario_builders/.
_UTILS_PARENT = Path(__file__).resolve().parents[2]
if str(_UTILS_PARENT) not in sys.path:
    sys.path.insert(0, str(_UTILS_PARENT))

from utils.premovement_distributions import (  # type: ignore  # noqa: E402
    create_premovement_distribution,
)

DISTRIBUTION_ID = "jps-distributions_0"

# ISO 20414 Test 1 names "uniform, normal, log-normal" as examples. Parameters
# are chosen to produce a realistic pre-evacuation window for the 10-occupant
# 8 m x 5 m room; uniform matches the value shipped in the base ZIP.
ISO_CASES = {
    "uniform": {"a": 10.0, "b": 100.0, "max_time_s": 180},
    "normal": {"a": 60.0, "b": 20.0, "max_time_s": 180},
    "lognormal": {"a": 4.586, "b": 0.967, "max_time_s": 2400},
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
    return [
        PreEvacCase(
            name=name,
            params={"a": spec["a"], "b": spec["b"]},
            max_simulation_time_s=spec["max_time_s"],
        )
        for name, spec in ISO_CASES.items()
    ]


def build_variants(base_scenario):
    """Yield (case, scenario) - one per ISO distribution.

    The base scenario is deep-copied for each case so the loaded ZIP is never
    mutated in place.
    """
    for case in load_cases():
        variant = deepcopy(base_scenario)
        # set_agent_params()'s kwarg allow-list dropped the premovement_*
        # keys, but simulation_init.py still reads them straight out of
        # the distribution's raw parameters dict, so write there directly.
        params = variant.raw["distributions"][DISTRIBUTION_ID]["parameters"]
        params.update(
            use_premovement=True,
            premovement_distribution=case.name,
            premovement_param_a=case.param_a,
            premovement_param_b=case.param_b,
        )
        variant.max_simulation_time = case.max_simulation_time_s
        yield case, variant


def sample_reference(case: PreEvacCase, n: int, seed: int):
    """Sample n times from the case's analytic distribution (for fit-overlay plots)."""
    dist = create_premovement_distribution(case.name, case.params, seed=seed)
    return dist.sample(n)
