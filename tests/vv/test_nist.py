"""NIST TN 1822 - Verification and validation of building fire evacuation models.

Reference: Ronchi, Kuligowski, Reneke, Peacock, Nilsson (2013). NIST Technical
Note 1822. https://nvlpubs.nist.gov/nistpubs/technicalnotes/NIST.TN.1822.pdf

The contributions cover 9 of the 17 NIST verification tests. Tests blocked on
JuPedSim simulator features absent from CollisionFreeSpeedModel (Verif.2.5
visibility, Verif.2.6 FED, Verif.2.7 elevator, Verif.2.10 reduced mobility,
Verif.3.2 social influence, Verif.3.3 affiliation, Verif.4.1 dynamic exits)
are documented in standards/nist/README.md and not exercised here.

Per-scenario deviations from the NIST originals are logged in
standards/nist/MODIFICATIONS.md.
"""

from __future__ import annotations

import pathlib
import sys
from copy import deepcopy

import numpy as np
import pytest
from shapely.geometry import Point, Polygon
from vv_helpers import HAS_VV_DEPS

STANDARDS_DIR = pathlib.Path(__file__).resolve().parents[2] / "standards"
SCENARIO_FILES = STANDARDS_DIR / "nist" / "scenario_files"

for extra in (STANDARDS_DIR / "nist", STANDARDS_DIR):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from jupedsim_scenarios import load_scenario, run_scenario  # noqa: E402


def _load_builder(module_name: str):
    """Load standards/nist/scenario_builders/<module_name>.py by explicit
    file path. Avoids the package-name clash with
    standards/rimea/scenario_builders/ when vv.yml runs both test modules
    in the same pytest invocation (Python's import cache otherwise pins
    `scenario_builders` to whichever test loaded it first)."""
    import importlib.util

    path = STANDARDS_DIR / "nist" / "scenario_builders" / f"{module_name}.py"
    synthetic_name = f"_nist_{module_name}"
    spec = importlib.util.spec_from_file_location(synthetic_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before exec so @dataclass (which looks the module up in
    # sys.modules via __module__) can attach the class correctly.
    sys.modules[synthetic_name] = mod
    spec.loader.exec_module(mod)
    return mod


pytestmark = [
    pytest.mark.vv,
    pytest.mark.skipif(not HAS_VV_DEPS, reason="V&V runtime dependencies not installed"),
]


def _load(stem: str):
    return load_scenario(str(SCENARIO_FILES / f"{stem}.zip"))


def _trajectory_first_move_times(df, frame_rate, threshold_m=0.05):
    """Return per-agent observed start time = first frame where the agent has
    moved more than ``threshold_m`` (L1) from its spawn position."""
    starts = []
    for _agent_id, sub in df.sort_values(["id", "frame"]).groupby("id"):
        x0, y0 = sub.iloc[0][["x", "y"]]
        moved = sub[(sub.x - x0).abs() + (sub.y - y0).abs() > threshold_m]
        t = (moved.iloc[0]["frame"] / frame_rate) if len(moved) else float("nan")
        starts.append(t)
    return np.array(starts)


# ---------------------------------------------------------------------------
# Verif.1.1 - Pre-evacuation time distributions
# ---------------------------------------------------------------------------


class TestNist11Premovement:
    """NIST Verif.1.1 - 10 agents, four pre-evacuation distributions.

    Geometry: 8 m x 5 m room, 1 m exit centred on the 5 m wall.
    Acceptance: aggregated observed start times fit each NIST distribution
    (Kolmogorov-Smirnov, alpha = 0.05). Sample size per case in this test is
    n = 10 (one sim x 10 agents); the publishable n = 1000 (100 seeds) is
    available by wrapping the sweep loop.
    """

    def test_base_zip_loads(self):
        scenario = _load("Nist-1-1-premovement")
        assert scenario.model_type == "CollisionFreeSpeedModel"
        params = scenario.distributions["jps-distributions_0"]["parameters"]
        assert params["use_premovement"] is True
        # Base ZIP defaults to the uniform case.
        assert params["premovement_distribution"] == "uniform"

    @pytest.mark.parametrize("case_id", ["uniform", "gamma", "lognormal", "weibull"])
    def test_distribution_fits(self, case_id):
        build_variants = _load_builder("nist1_1_premovement").build_variants
        from scipy import stats as _stats

        base = _load("Nist-1-1-premovement")
        case, variant = next((c, s) for c, s in build_variants(base) if c.name == case_id)
        result = run_scenario(variant, seed=42)
        try:
            df = result.trajectory_dataframe()
            observed = _trajectory_first_move_times(df, result.frame_rate)
            observed = observed[~np.isnan(observed)]
            assert len(observed) > 0, f"{case_id}: no agents moved"
            # Build the analytic CDF for the active distribution.
            if case.name == "uniform":
                cdf = lambda v: _stats.uniform.cdf(v, case.param_a, case.param_b - case.param_a)
            elif case.name == "gamma":
                cdf = lambda v: _stats.gamma.cdf(v, case.param_a, scale=case.param_b)
            elif case.name == "lognormal":
                cdf = lambda v: _stats.lognorm.cdf(v, case.param_b, scale=np.exp(case.param_a))
            elif case.name == "weibull":
                cdf = lambda v: _stats.weibull_min.cdf(v, case.param_b, scale=case.param_a)
            else:
                pytest.fail(f"unknown distribution: {case.name}")
            p = _stats.kstest(observed, cdf).pvalue
            assert p > 0.05, f"{case_id}: KS p={p:.3f} below alpha=0.05"
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.2.1 - Speed in a corridor
# ---------------------------------------------------------------------------


class TestNist21CorridorSpeed:
    """NIST Verif.2.1 - single agent walks 40 m of corridor at v0 = 1.0 m/s.

    The corridor is extended to 60 m with 10 m buffers; speed is measured over
    the NIST 40 m segment (x = 10 .. 50).
    """

    MEAS_START_X = 10.0
    MEAS_END_X = 50.0
    TARGET_SPEED = 1.0
    TOL = 0.05

    def test_walking_speed(self):
        scenario = _load("Nist-2-1-corridor-speed")
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            sub = df.reset_index(drop=True)
            t_in_idx = sub[sub.x >= self.MEAS_START_X].index.min()
            t_out_idx = sub[sub.x >= self.MEAS_END_X].index.min()
            assert t_in_idx is not None and t_out_idx is not None
            t_in = sub.loc[t_in_idx, "frame"] / result.frame_rate
            t_out = sub.loc[t_out_idx, "frame"] / result.frame_rate
            speed = (self.MEAS_END_X - self.MEAS_START_X) / (t_out - t_in)
            assert abs(speed - self.TARGET_SPEED) <= self.TOL, (
                f"observed {speed:.3f} m/s, target {self.TARGET_SPEED} +/- {self.TOL}"
            )
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.2.2 - Speed on stairs (upward + downward)
# ---------------------------------------------------------------------------


class _StairSpeedBase:
    SCENARIO: str
    MEAS_START_X: float
    MEAS_END_X: float
    DIRECTION: str  # "right" or "left"
    TARGET_SPEED = 1.0
    TOL = 0.05

    def test_walking_speed(self):
        scenario = _load(self.SCENARIO)
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            sub = df.reset_index(drop=True)
            if self.DIRECTION == "right":
                t_in_idx = sub[sub.x >= self.MEAS_START_X].index.min()
                t_out_idx = sub[sub.x >= self.MEAS_END_X].index.min()
            else:
                t_in_idx = sub[sub.x <= self.MEAS_START_X].index.min()
                t_out_idx = sub[sub.x <= self.MEAS_END_X].index.min()
            assert t_in_idx is not None and t_out_idx is not None
            t_in = sub.loc[t_in_idx, "frame"] / result.frame_rate
            t_out = sub.loc[t_out_idx, "frame"] / result.frame_rate
            distance = abs(self.MEAS_END_X - self.MEAS_START_X)
            speed = distance / (t_out - t_in)
            assert abs(speed - self.TARGET_SPEED) <= self.TOL, (
                f"observed {speed:.3f} m/s, target {self.TARGET_SPEED} +/- {self.TOL}"
            )
        finally:
            result.cleanup()


class TestNist22StairsUp(_StairSpeedBase):
    """NIST Verif.2.2 (up) - 100 m measurement segment, 1 m/s target."""

    SCENARIO = "Nist-2-2-stairs-up"
    MEAS_START_X = 10.0
    MEAS_END_X = 110.0
    DIRECTION = "right"


class TestNist22StairsDown(_StairSpeedBase):
    """NIST Verif.2.2 (down) - same 100 m segment, traversed right-to-left."""

    SCENARIO = "Nist-2-2-stairs-down"
    MEAS_START_X = 110.0
    MEAS_END_X = 10.0
    DIRECTION = "left"


# ---------------------------------------------------------------------------
# Verif.2.3 - Movement around a corner
# ---------------------------------------------------------------------------


class TestNist23Corner:
    """NIST Verif.2.3 - 20 agents navigate an L-shaped corridor without
    penetrating the boundary."""

    def test_full_evacuation(self):
        scenario = _load("Nist-2-3-corner")
        result = run_scenario(scenario, seed=42)
        try:
            assert result.agents_remaining == 0
            assert result.evacuation_time < 60.0
        finally:
            result.cleanup()

    def test_no_boundary_penetration(self):
        scenario = _load("Nist-2-3-corner")
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe()
            walkable_with_tol = scenario.walkable_polygon.buffer(0.001)
            outside = sum(
                1 for row in df.itertuples() if not walkable_with_tol.contains(Point(row.x, row.y))
            )
            assert outside == 0, f"{outside} / {len(df)} trajectory points outside walkable area"
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.2.4 - Assigned agent demographics
# ---------------------------------------------------------------------------


class TestNist24Demographics:
    """NIST Verif.2.4 - 100 agents with Gaussian-distributed desired speed.

    The NIST test has no exit, so the loader refuses to start a simulation.
    We verify the config is wired up to sample from Gaussian(1.2, 0.2).
    """

    def test_gaussian_distribution_configured(self):
        scenario = _load("Nist-2-4-demographics")
        params = scenario.distributions["jps-distributions_0"]["parameters"]
        assert params["v0_distribution"] == "gaussian"
        assert abs(params["v0"] - 1.2) < 1e-6
        assert abs(params["v0_std"] - 0.2) < 1e-6
        assert int(params["number"]) == 100


# ---------------------------------------------------------------------------
# Verif.2.8 - Horizontal counter-flows
# ---------------------------------------------------------------------------


class TestNist28Counterflow:
    """NIST Verif.2.8 - 100 primary agents through a corridor against 0/10/50/100
    counterflow agents.

    Acceptance: as counterflow increases, the number of primary agents that
    complete the corridor must be non-increasing (the model deadlocks at high
    counterflow, which is consistent with NIST's expected trend taken to its
    limit case).
    """

    BUDGET_BY_CF = {0: 400, 10: 500, 50: 400, 100: 400}

    def test_evacuated_counts_monotonic(self):
        load_branches = _load_builder("nist2_8_counterflow").load_branches

        evacuated_counts = []
        for branch in load_branches():
            scenario = load_scenario(str(branch.scenario_zip))
            scenario.set_max_time(self.BUDGET_BY_CF[branch.counterflow_agents])
            result = run_scenario(scenario, seed=42)
            try:
                df = result.trajectory_dataframe()
                primary_ids = {
                    int(aid)
                    for aid, sub in df.sort_values(["id", "frame"]).groupby("id")
                    if sub.iloc[0].x < 5.0  # primary distribution spawns on the left
                }
                evac = sum(1 for aid in primary_ids if (df[df.id == aid].x >= 29.7).any())
                evacuated_counts.append(evac)
            finally:
                result.cleanup()

        deltas = np.diff(evacuated_counts)
        assert (deltas <= 0).all(), (
            f"evacuated counts not monotonic in counterflow: {evacuated_counts}"
        )


# ---------------------------------------------------------------------------
# Verif.2.9 - Group behaviours
# ---------------------------------------------------------------------------


class TestNist29Groups:
    """NIST Verif.2.9 - Group 1 (4 fast + 1 slow) and Group 2 (10 slow).

    The source ``group_id`` parameter was stripped (the JuPedSim loader has no
    native group cohesion). This test verifies the scenario loads, runs, and
    produces a trajectory; the qualitative "Group 1 stays together" property
    is not enforced by the simulator.
    """

    def test_runs_without_error(self):
        scenario = _load("Nist-2-9-groups")
        result = run_scenario(scenario, seed=42)
        try:
            assert result.total_agents == 15
            df = result.trajectory_dataframe()
            assert len(df) > 0
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.3.1 - Exit route allocation
# ---------------------------------------------------------------------------


class TestNist31RouteAllocation:
    """NIST Verif.3.1 - 12 rooms around a 1 m corridor; main exit serves rooms
    1-4 and 7-10, secondary exit serves rooms 5, 6, 11, 12.

    Acceptance: every agent must end at the exit allocated by its journey.
    The walkable polygon is rebuilt parametrically; see MODIFICATIONS.md
    section B12.
    """

    def test_each_agent_reaches_allocated_exit(self):
        """Every agent must end at the exit allocated by its journey. The
        ZIP carries both the legacy `journeys`/`stages` block (web-app
        export shape) and a derived `journeys_v2` + `journey_weights`
        block (the canonical loader's required shape); the latter is
        what makes the canonical loader enforce route allocation
        strictly. See MODIFICATIONS.md section A4.
        """
        scenario = _load("Nist-3-1-route-allocation")
        raw = scenario.raw
        if "journeys" in raw:
            journey_map = {j["stages"][0]: j["stages"][-1] for j in raw["journeys"]}
        else:
            j_to_exit = {j["id"]: j["sequence"][-1] for j in raw.get("journeys_v2", [])}
            journey_map = {}
            for did, d in scenario.distributions.items():
                jw = d.get("journey_weights", [])
                if jw:
                    journey_map[did] = j_to_exit.get(jw[0]["journey_id"], "")
        dist_polys = {did: Polygon(d["coordinates"]) for did, d in scenario.distributions.items()}
        exit_polys = {eid: Polygon(e["coordinates"]) for eid, e in scenario.exits.items()}
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            assert result.agents_remaining == 0, "not all agents evacuated"
            first = df.groupby("id").first().reset_index()
            last = df.groupby("id").last().reset_index()
            matches = 0
            total = 0
            mismatches = []
            for row_first, row_last in zip(first.itertuples(), last.itertuples()):
                p0 = Point(row_first.x, row_first.y)
                p1 = Point(row_last.x, row_last.y)
                home = next(
                    (did for did, poly in dist_polys.items() if poly.covers(p0)),
                    None,
                )
                assert home is not None, f"agent {row_first.id} did not spawn in any distribution"
                expected = journey_map[home]
                actual = min(exit_polys, key=lambda eid: exit_polys[eid].distance(p1))
                total += 1
                if actual == expected:
                    matches += 1
                else:
                    mismatches.append(
                        f"agent {row_first.id} from {home}: expected {expected}, got {actual}"
                    )
            match_rate = matches / total if total else 0.0
            assert match_rate == 1.0, (
                f"allocation match rate {match_rate:.1%} below 100%\n" + "\n".join(mismatches[:5])
            )
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.5.1 - Congestion
# ---------------------------------------------------------------------------


class TestNist51Congestion:
    """NIST Verif.5.1 - 100 agents in an 8 m x 5 m room with a 2 m corridor.

    Acceptance: peak density at the room exit > peak density in the corridor
    midsection (i.e. congestion forms at the room exit; flow is steadier in
    the corridor).
    """

    def test_peak_density_higher_at_room_exit(self):
        scenario = _load("Nist-5-1-congestion")
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe()
            area_room_exit = 2.0 * 0.5
            area_corridor = 2.0 * 2.0
            peak_room_exit = 0.0
            peak_corridor = 0.0
            for _frame, sub in df.groupby("frame"):
                room_count = ((sub.x.between(3.0, 5.0)) & (sub.y.between(4.5, 5.0))).sum()
                corr_count = ((sub.x.between(3.0, 5.0)) & (sub.y.between(15.0, 17.0))).sum()
                peak_room_exit = max(peak_room_exit, room_count / area_room_exit)
                peak_corridor = max(peak_corridor, corr_count / area_corridor)
            assert peak_room_exit > peak_corridor, (
                f"peak room-exit density {peak_room_exit:.2f} <= "
                f"peak corridor density {peak_corridor:.2f}"
            )
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.5.2 - Maximum flow rates (Mode B - emergent flow validation)
# ---------------------------------------------------------------------------


class TestNist52MaxFlow:
    """NIST Verif.5.2 - Mode B emergent-flow validation.

    The CollisionFreeSpeedModel has no built-in door-flow limiter. We record
    the peak emergent flow through the 1 m exit and verify it is positive +
    finite. The 1.33 p/m/s IMO reference is informational only at this stage.
    """

    EXIT_WIDTH_M = 1.0

    def test_emergent_flow_finite(self):
        scenario = _load("Nist-5-2-max-flow")
        result = run_scenario(scenario, seed=42)
        try:
            assert result.agents_evacuated > 0
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            exit_times = []
            for _aid, sub in df.groupby("id"):
                crossed = sub[sub.x <= 0.3]
                if len(crossed):
                    exit_times.append(crossed.iloc[0].frame / result.frame_rate)
            assert len(exit_times) > 0, "no agent crossed the exit"
            # 1 s sliding-window peak flow.
            exit_times = np.array(sorted(exit_times))
            peak = 0.0
            for t in np.arange(1.0, exit_times.max() + 1.0, 1.0):
                in_window = ((exit_times > t - 1.0) & (exit_times <= t)).sum()
                peak = max(peak, in_window / self.EXIT_WIDTH_M)
            assert peak > 0.0 and np.isfinite(peak)
        finally:
            result.cleanup()
