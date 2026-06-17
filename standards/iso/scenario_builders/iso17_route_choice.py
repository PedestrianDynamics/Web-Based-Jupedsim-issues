"""
ISO 20414:2020 Test 17 - Route choice based on geometric layout.

The aim of the test is to confirm that agents choose the geometrically
shorter route to their target when two route alternatives are available:
(a) staying on the upper floor and walking the long way around a ring
corridor, or (b) branching off the ring, descending a staircase, crossing a
short lower-floor corridor, and ascending a second staircase back to the
upper floor near the target.

JuPedSim's walkable area is a single flattened 2D polygon - there is no
native concept of floor elevation. Both floors are therefore "unfolded" into
one plane: the upper-floor ring corridor is drawn where it is, and the
lower-floor connecting corridor is drawn as a separate strip offset below the
ring (so the two never overlap), joined to the ring by two stair strips.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
RING_OUTER = 20.0            # outer side length of the square upper-floor ring (m)
CORR_WIDTH = 2.0              # corridor width, both upper ring and lower shortcut (m)
STAIR_WIDTH = 1.5             # stair width (m)
STAIR_LENGTH = 6.0            # flat-corridor proxy for the real stair incline walking
                               # distance (riser/going derived), not floor-to-floor height
LOWER_GAP = 3.0                # vertical plan-offset gap between the ring and the lower
                                # floor corridor strip, purely so the two polygons never
                                # overlap on the canvas (has no effect on route length)
BRANCH_OFFSET = 7.0            # distance from the bottom-left ring corner to the
                                # down-stair branch point, measured along the bottom
                                # corridor (m)
START_MARGIN = 1.0             # distance from the bottom-left corner to the start area
TARGET_MARGIN = 1.0            # distance from the bottom-right corner to the target/exit

STAIR_SPEED_FACTOR = 0.5       
N_AGENTS = 10
WALKING_SPEED = 1.2
AGENT_RADIUS = 0.15

JOURNEY_ID = "jps-journeys_0"

# Derived geometry anchors -----------------------------------------------------
INNER = CORR_WIDTH                                  # inner ring boundary offset
DOWN_STAIR_X = BRANCH_OFFSET                         # centerline x of the down-stair
UP_STAIR_X = RING_OUTER - BRANCH_OFFSET              # centerline x of the up-stair
LOWER_Y_TOP = -STAIR_LENGTH - LOWER_GAP              # top edge of the lower corridor
LOWER_Y_BOTTOM = LOWER_Y_TOP - CORR_WIDTH            # bottom edge of the lower corridor
START_POS = (START_MARGIN, CORR_WIDTH / 2.0)
TARGET_POS = (RING_OUTER - TARGET_MARGIN, CORR_WIDTH / 2.0)


def stair_x_bounds(center_x: float) -> tuple[float, float]:
    """Left/right x of a stair strip centred on center_x."""
    return center_x - STAIR_WIDTH / 2.0, center_x + STAIR_WIDTH / 2.0


def build_geometry_wkt() -> str:
    """Single connected walkable polygon with the direct bottom corridor blocked.

    The previous geometry left the full bottom corridor open from the start to
    the target. Then the shortest-path triangulation quite correctly sent agents
    straight along y ~= 1, which is not one of the intended ISO 17 alternatives.

    This geometry keeps only:
      - the upper-floor U-shaped long route: left side -> top -> right side,
      - short bottom stubs from the start to the down-stair and from the up-stair
        to the target,
      - the lower-floor shortcut connected by the two stair strips.

    The middle part of the bottom corridor is removed by the interior ring, so a
    trajectory from start to target must either go around the upper ring or use
    the lower shortcut.
    """
    down_xl, down_xr = stair_x_bounds(DOWN_STAIR_X)
    up_xl, up_xr = stair_x_bounds(UP_STAIR_X)

    exterior = [
        (up_xl, LOWER_Y_BOTTOM),
        (down_xr, LOWER_Y_BOTTOM),
        (down_xl, LOWER_Y_BOTTOM),
        (down_xl, LOWER_Y_TOP),
        (down_xl, 0.0),
        (INNER, 0.0),
        (0.0, 0.0),
        (0.0, RING_OUTER),
        (RING_OUTER, RING_OUTER),
        (RING_OUTER, 0.0),
        (RING_OUTER - INNER, 0.0),
        (up_xr, 0.0),
        (up_xr, LOWER_Y_BOTTOM),
        (up_xl, LOWER_Y_BOTTOM),
    ]

    blocked_middle = [
        (down_xr, CORR_WIDTH),
        (down_xr, LOWER_Y_TOP),
        (up_xl, LOWER_Y_TOP),
        (up_xl, CORR_WIDTH),
        (RING_OUTER - INNER, CORR_WIDTH),
        (RING_OUTER - INNER, RING_OUTER - INNER),
        (INNER, RING_OUTER - INNER),
        (INNER, CORR_WIDTH),
        (down_xr, CORR_WIDTH),
    ]

    def ring(points: list[tuple[float, float]]) -> str:
        return "(" + ", ".join(f"{x:g} {y:g}" for x, y in points) + ")"

    return "POLYGON (" + ring(exterior) + ", " + ring(blocked_middle) + ")"


def build_raw_scenario(seed: int = 42, max_simulation_time: float = 200.0) -> dict:
    down_xl, down_xr = stair_x_bounds(DOWN_STAIR_X)
    up_xl, up_xr = stair_x_bounds(UP_STAIR_X)

    return {
        "config": {
            "simulation_settings": {
                "baseSeed": seed,
                "simulationParams": {
                    "model_type": "CollisionFreeSpeedModel",
                    "max_simulation_time": max_simulation_time,
                },
            }
        },
        "distributions": {
            "jps-distributions_0": {
                "type": "polygon",
                "coordinates": [
                    [START_POS[0] - 0.5, 0.2],
                    [START_POS[0] + 0.5, 0.2],
                    [START_POS[0] + 0.5, CORR_WIDTH - 0.2],
                    [START_POS[0] - 0.5, CORR_WIDTH - 0.2],
                    [START_POS[0] - 0.5, 0.2],
                ],
                "parameters": {
                    "number": N_AGENTS,
                    "radius": AGENT_RADIUS,
                    "v0": WALKING_SPEED,
                    "distribution_mode": "by_number",
                    "radius_distribution": "constant",
                    "v0_distribution": "constant",
                    "use_flow_spawning": False,
                },
                "journey_weights": [{"journey_id": JOURNEY_ID, "weight": 100}],
            }
        },
        "exits": {
            "jps-exits_0": {
                "type": "polygon",
                "coordinates": [
                    [TARGET_POS[0] - 0.5, 0.2],
                    [TARGET_POS[0] + 0.5, 0.2],
                    [TARGET_POS[0] + 0.5, CORR_WIDTH - 0.2],
                    [TARGET_POS[0] - 0.5, CORR_WIDTH - 0.2],
                    [TARGET_POS[0] - 0.5, 0.2],
                ],
                "enable_throughput_throttling": False,
                "max_throughput": 0,
            }
        },
        "zones": {
            # Down-stair: agents descend from the upper ring's bottom corridor to
            # the lower corridor. Same speed-factor convention as iso12.
            "jps-zones_0": {
                "type": "polygon",
                "coordinates": [
                    [down_xl + 0.05, LOWER_Y_BOTTOM + 0.05],
                    [down_xr - 0.05, LOWER_Y_BOTTOM + 0.05],
                    [down_xr - 0.05, 0.0 - 0.05],
                    [down_xl + 0.05, 0.0 - 0.05],
                    [down_xl + 0.05, LOWER_Y_BOTTOM + 0.05],
                ],
                "speed_factor": STAIR_SPEED_FACTOR,
            },
            # Up-stair: agents ascend from the lower corridor back to the upper
            # ring's bottom corridor, near the target.
            "jps-zones_1": {
                "type": "polygon",
                "coordinates": [
                    [up_xl + 0.05, LOWER_Y_BOTTOM + 0.05],
                    [up_xr - 0.05, LOWER_Y_BOTTOM + 0.05],
                    [up_xr - 0.05, 0.0 - 0.05],
                    [up_xl + 0.05, 0.0 - 0.05],
                    [up_xl + 0.05, LOWER_Y_BOTTOM + 0.05],
                ],
                "speed_factor": STAIR_SPEED_FACTOR,
            },
        },
        "journeys_v2": [
            {
                "id": JOURNEY_ID,
                "name": JOURNEY_ID,
                "color": "#3b82f6",
                # Single stage straight to the exit:
                # this lets CollisionFreeSpeedModel's default shortest-path
                # triangulation routing decide between the long way around the
                # ring and the shortcut via the stairs. 
                "sequence": ["jps-exits_0"],
            }
        ],
    }


def route_length_reference() -> dict:
    """Rough straight-line reference lengths for the two route alternatives.

    Useful as a sanity check against simulated trajectories: the long way
    should measure close to `long_way_m`, the shortcut close to `shortcut_m`.
    Test 17 passes if agents are observed taking the shorter of the two.
    """
    long_way_m = 3 * (RING_OUTER - CORR_WIDTH)
    shortcut_m = (
        (DOWN_STAIR_X - START_POS[0])
        + STAIR_LENGTH
        + (UP_STAIR_X - DOWN_STAIR_X)
        + STAIR_LENGTH
        + (TARGET_POS[0] - UP_STAIR_X)
    )
    return {"long_way_m": long_way_m, "shortcut_m": shortcut_m}


def measure_route_choice(traj_df, frame_rate: float) -> dict:
    """Classify each agent's path as 'shortcut' or 'long_way' from its trajectory.

    An agent is classified as having taken the shortcut if it ever enters either
    stair zone's y-range (y < 0, i.e. below the ring's bottom corridor). Agents
    that never go below y = 0 stayed on the upper floor and took the long way.
    Returns counts and fractions.
    """
    if traj_df.empty:
        return {"n_shortcut": 0, "n_long_way": 0, "frac_shortcut": float("nan")}

    took_shortcut = 0
    took_long_way = 0
    for _, sub in traj_df.sort_values(["id", "frame"]).groupby("id"):
        if (sub.y < 0.0).any():
            took_shortcut += 1
        else:
            took_long_way += 1

    total = took_shortcut + took_long_way
    return {
        "n_shortcut": took_shortcut,
        "n_long_way": took_long_way,
        "frac_shortcut": took_shortcut / total if total else float("nan"),
    }
