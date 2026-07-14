"""NIST TN 1822 - Verification and validation of building fire evacuation models.

Reference: Ronchi, Kuligowski, Reneke, Peacock, Nilsson (2013). NIST Technical
Note 1822. https://nvlpubs.nist.gov/nistpubs/technicalnotes/NIST.TN.1822.pdf

The contributions cover 10 of the 17 NIST verification tests. Tests blocked on
JuPedSim simulator features absent from CollisionFreeSpeedModel (Verif.2.5
visibility, Verif.2.6 FED, Verif.2.7 elevator, Verif.2.10 reduced mobility,
Verif.3.2 social influence, Verif.3.3 affiliation, Verif.4.1 dynamic exits)
are documented in standards/nist/README.md and not exercised here.

Two shipped tests exercise NIST's numeric criterion but xfail because it needs a
CollisionFreeSpeedModel capability the model lacks: Verif.2.9 (no group-cohesion
model) and Verif.5.2 (no door-flow limiter). See issue #151.

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
    pytest.mark.skipif(
        not HAS_VV_DEPS, reason="V&V runtime dependencies not installed"
    ),
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
        case, variant = next(
            (c, s) for c, s in build_variants(base) if c.name == case_id
        )
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
                1
                for row in df.itertuples()
                if not walkable_with_tol.contains(Point(row.x, row.y))
            )
            assert outside == 0, (
                f"{outside} / {len(df)} trajectory points outside walkable area"
            )
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
    """NIST Verif.2.8 - 100 primary agents cross a 10 m x 2 m corridor against
    0/10/50/100 counterflow agents in the far room.

    NIST criterion: the completion time (last primary agent to reach the far
    room) increases with counterflow. Under CollisionFreeSpeedModel the high
    counterflow branches deadlock, so a last-arrival *time* is undefined; the
    equivalent monotone quantity is the number of primary agents that reach the
    far room within a fixed, *equal* time budget, which must be non-increasing
    as counterflow grows. Observed on seed 42: [100, 100, 1, 0].
    """

    BUDGET_S = 400
    # The two 10 m rooms bracket a 10 m corridor, so the far room starts at
    # x = 20 m. An agent that reaches it is absorbed at the far exit (x >= 29.7),
    # so its *last* recorded position lies in the far room - counting a fixed
    # crossing frame (x >= 29.7) misses every absorbed agent and reads 0.
    FAR_ROOM_X = 20.0

    def test_completion_non_increasing_with_counterflow(self):
        load_branches = _load_builder("nist2_8_counterflow").load_branches

        reached = []
        for branch in load_branches():
            scenario = load_scenario(str(branch.scenario_zip))
            scenario.max_simulation_time = self.BUDGET_S
            result = run_scenario(scenario, seed=42)
            try:
                df = result.trajectory_dataframe().sort_values(["id", "frame"])
                grouped = df.groupby("id")
                first_x = grouped.first().x
                last_x = grouped.last().x
                # Primary population spawns in the near room (x < 5).
                primary = first_x[first_x < 5.0].index
                reached.append(
                    sum(1 for aid in primary if last_x[aid] >= self.FAR_ROOM_X)
                )
            finally:
                result.cleanup()

        deltas = np.diff(reached)
        assert (deltas <= 0).all(), (
            f"primary completions not non-increasing in counterflow: {reached}"
        )


# ---------------------------------------------------------------------------
# Verif.2.9 - Group behaviours
# ---------------------------------------------------------------------------


class TestNist29Groups:
    """NIST Verif.2.9 - Group 1 (4 @1.25 m/s + 1 @0.5 m/s) must reach the exit
    together (arrival spread <= 10 s); Group 2 (10 @0.2 m/s) shares the room.
    """

    GROUP1_SIZE = 5
    MAX_SPREAD_S = 10.0  # NIST TN 1822 section 3.1.2, Verif.2.9.

    def test_runs_without_error(self):
        scenario = _load("Nist-2-9-groups")
        result = run_scenario(scenario, seed=42)
        try:
            assert result.total_agents == 15
            df = result.trajectory_dataframe()
            assert len(df) > 0
        finally:
            result.cleanup()

    @pytest.mark.xfail(
        reason="CollisionFreeSpeedModel has no group-cohesion model, so the "
        "0.5 m/s member of Group 1 lags the 1.25 m/s members (spread ~24 s > "
        "10 s). Needs a group sub-model; tracked in issue #151.",
        raises=AssertionError,
        strict=True,
    )
    def test_group1_arrives_together(self):
        scenario = _load("Nist-2-9-groups")
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            grouped = df.groupby("id")
            first_y = grouped.first().y
            # Exit time per agent = last recorded frame (absorbed at the exit).
            exit_time = grouped.frame.max() / result.frame_rate
            # Group 1 spawns in the top zone (y ~16-19.5); Group 2 sits lower
            # (y ~8-12), so the five highest spawn-y agents are exactly Group 1.
            group1 = first_y.sort_values(ascending=False).head(self.GROUP1_SIZE).index
            spread = exit_time[group1].max() - exit_time[group1].min()
            assert spread <= self.MAX_SPREAD_S, (
                f"Group 1 arrival spread {spread:.1f} s exceeds {self.MAX_SPREAD_S} s"
            )
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
            journey_map = {
                j["stages"][0]: j["stages"][-1] for j in raw["journeys"]
            }
        else:
            j_to_exit = {
                j["id"]: j["sequence"][-1] for j in raw.get("journeys_v2", [])
            }
            journey_map = {}
            for did, d in scenario.distributions.items():
                jw = d.get("journey_weights", [])
                if jw:
                    journey_map[did] = j_to_exit.get(jw[0]["journey_id"], "")
        dist_polys = {
            did: Polygon(d["coordinates"])
            for did, d in scenario.distributions.items()
        }
        exit_polys = {
            eid: Polygon(e["coordinates"]) for eid, e in scenario.exits.items()
        }
        result = run_scenario(scenario, seed=42)
        try:
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            assert result.agents_remaining == 0, "not all agents evacuated"
            first = df.groupby("id").first().reset_index()
            last = df.groupby("id").last().reset_index()
            matches = 0
            total = 0
            mismatches = []
            for row_first, row_last in zip(
                first.itertuples(), last.itertuples()
            ):
                p0 = Point(row_first.x, row_first.y)
                p1 = Point(row_last.x, row_last.y)
                home = next(
                    (did for did, poly in dist_polys.items() if poly.covers(p0)),
                    None,
                )
                assert home is not None, (
                    f"agent {row_first.id} did not spawn in any distribution"
                )
                expected = journey_map[home]
                actual = min(
                    exit_polys, key=lambda eid: exit_polys[eid].distance(p1)
                )
                total += 1
                if actual == expected:
                    matches += 1
                else:
                    mismatches.append(
                        f"agent {row_first.id} from {home}: "
                        f"expected {expected}, got {actual}"
                    )
            match_rate = matches / total if total else 0.0
            assert match_rate == 1.0, (
                f"allocation match rate {match_rate:.1%} below 100%\n"
                + "\n".join(mismatches[:5])
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

    NIST also expects congestion at the base of the stairs, but this ZIP models
    a plain room -> corridor -> exit with no stair speed-factor zone, so that
    half of the expected result is not exercised. Adding a stair zone (JuPedSim
    supports it) is scope-deferred; see issue #151.
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
                room_count = (
                    (sub.x.between(3.0, 5.0)) & (sub.y.between(4.5, 5.0))
                ).sum()
                corr_count = (
                    (sub.x.between(3.0, 5.0)) & (sub.y.between(15.0, 17.0))
                ).sum()
                peak_room_exit = max(peak_room_exit, room_count / area_room_exit)
                peak_corridor = max(peak_corridor, corr_count / area_corridor)
            assert peak_room_exit > peak_corridor, (
                f"peak room-exit density {peak_room_exit:.2f} <= "
                f"peak corridor density {peak_corridor:.2f}"
            )
        finally:
            result.cleanup()


# ---------------------------------------------------------------------------
# Verif.5.2 - Maximum flow rates
# ---------------------------------------------------------------------------


class TestNist52MaxFlow:
    """NIST Verif.5.2 - 100 agents evacuate an 8 m x 5 m room through a 1 m exit.

    For an emergent-flow model NIST section 3.1.5 reads this as a non-exceedance
    check: the sustained specific flow through the exit must not exceed the IMO
    MSC/Circ.1238 reference of 1.33 p/m/s.
    """

    EXIT_WIDTH_M = 1.0
    IMO_MAX_FLOW = 1.33  # p/m/s, IMO MSC/Circ.1238 (via NIST TN 1822 section 3.1.5).

    @pytest.mark.xfail(
        reason="CollisionFreeSpeedModel has no door-flow limiter, so the "
        "emergent specific flow through the 1 m exit (~5 p/m/s on seed 42) "
        "exceeds the IMO 1.33 p/m/s reference. Needs a flow-limiting exit "
        "model; tracked in issue #151.",
        raises=AssertionError,
        strict=True,
    )
    def test_flow_within_imo_reference(self):
        scenario = _load("Nist-5-2-max-flow")
        result = run_scenario(scenario, seed=42)
        try:
            assert result.agents_evacuated > 0
            df = result.trajectory_dataframe().sort_values(["id", "frame"])
            grouped = df.groupby("id")
            # Exit time per agent = last recorded frame (absorbed at the exit);
            # an agent that evacuated ends within a door-width of the exit.
            last = grouped.last()
            evac = last[last.x <= 0.6].index
            exit_times = np.sort(
                (grouped.frame.max()[evac] / result.frame_rate).values
            )
            assert len(exit_times) > 0, "no agent reached the exit"
            # Sustained specific flow over the egress period.
            span = exit_times.max() - exit_times.min()
            flow = len(exit_times) / span / self.EXIT_WIDTH_M
            assert flow <= self.IMO_MAX_FLOW, (
                f"specific flow {flow:.2f} p/m/s exceeds IMO {self.IMO_MAX_FLOW} p/m/s"
            )
        finally:
            result.cleanup()
