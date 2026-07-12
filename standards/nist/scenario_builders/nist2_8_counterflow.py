"""
NIST TN 1822 Verif.2.8 - Horizontal counter-flows.

100 agents move from room 1 to room 2 along a 10 m x 2 m corridor; a second
population moves simultaneously in the opposite direction. The test sweeps the
counterflow population size: 0, 10, 50, 100. The four base scenarios are
stored as separate ZIPs in scenario_files/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCENARIO_FILES = Path(__file__).resolve().parent.parent / "scenario_files"


@dataclass(frozen=True)
class CounterflowBranch:
    label: str
    counterflow_agents: int
    scenario_zip: Path


def load_branches() -> list[CounterflowBranch]:
    return [
        CounterflowBranch("counterflow=0", 0, SCENARIO_FILES / "Nist-2-8-counterflow-0.zip"),
        CounterflowBranch("counterflow=10", 10, SCENARIO_FILES / "Nist-2-8-counterflow-10.zip"),
        CounterflowBranch("counterflow=50", 50, SCENARIO_FILES / "Nist-2-8-counterflow-50.zip"),
        CounterflowBranch("counterflow=100", 100, SCENARIO_FILES / "Nist-2-8-counterflow-100.zip"),
    ]
