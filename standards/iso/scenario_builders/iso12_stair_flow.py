"""
ISO 20414:2020 Test 12 - Stair flow rates.

The aim of the test is to confirm that an increase in stair width leads to an
increase in agent flow rate. ISO Test 12 specifies five widths
(1.0, 1.2, 1.4, 1.6, 1.8 m) and 100 occupants per width.

The stair is a planar strip carrying a user-defined speed-reduction zone
(speed_factor = 0.5, so agents walk it at 0.5 m/s) - the convention ISO Test 3/12
describe for representing stair movement. The speed factor is constant across
runs, so the only driver of the difference in emergent flow is the opening
width. A feeding room funnels the crowd into the stair; flow is measured where
agents cross the middle of the stair.

Source: ISO 20414:2020(E) Table 13 (Test 12).
"""

from __future__ import annotations

ROOM_WIDTH = 10.0
ROOM_DEPTH = 8.0
STAIR_LENGTH = 6.0  # flat-corridor proxy for the 4.24 m incline + landings
STAIR_TOP_Y = ROOM_DEPTH + STAIR_LENGTH  # 14.0
MEASURE_Y = ROOM_DEPTH + STAIR_LENGTH / 2.0  # 11.0 - mid-stair flow line

STAIR_WIDTHS = [1.0, 1.2, 1.4, 1.6, 1.8]
N_AGENTS = 100
WALKING_SPEED = 1.0
# ISO Test 3/12 note that stair movement is represented by a user-defined speed
# factor. Agents walk the stair zone at WALKING_SPEED * STAIR_SPEED_FACTOR
# (0.5 m/s here, a realistic ascent speed) instead of the flat free speed.
STAIR_SPEED_FACTOR = 0.5
AGENT_RADIUS = 0.15

JOURNEY_ID = "jps-journeys_0"


def stair_bounds(width: float) -> tuple[float, float]:
    """Left/right x of a centred stair of the given width."""
    return (ROOM_WIDTH - width) / 2.0, (ROOM_WIDTH + width) / 2.0


def build_geometry_wkt(width: float) -> str:
    """Room (10 x 8) with a centred stair of the given width rising to y = 14."""
    xl, xr = stair_bounds(width)
    pts = [
        (0.0, 0.0),
        (ROOM_WIDTH, 0.0),
        (ROOM_WIDTH, ROOM_DEPTH),
        (xr, ROOM_DEPTH),
        (xr, STAIR_TOP_Y),
        (xl, STAIR_TOP_Y),
        (xl, ROOM_DEPTH),
        (0.0, ROOM_DEPTH),
        (0.0, 0.0),
    ]
    return "POLYGON ((" + ", ".join(f"{x:g} {y:g}" for x, y in pts) + "))"


def build_raw_scenario(width: float, seed: int = 42, max_simulation_time: float = 200.0) -> dict:
    xl, xr = stair_bounds(width)
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
                    [0.3, 0.3],
                    [ROOM_WIDTH - 0.3, 0.3],
                    [ROOM_WIDTH - 0.3, ROOM_DEPTH - 0.3],
                    [0.3, ROOM_DEPTH - 0.3],
                    [0.3, 0.3],
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
                    [xl, STAIR_TOP_Y - 0.3],
                    [xr, STAIR_TOP_Y - 0.3],
                    [xr, STAIR_TOP_Y],
                    [xl, STAIR_TOP_Y],
                    [xl, STAIR_TOP_Y - 0.3],
                ],
                "enable_throughput_throttling": False,
                "max_throughput": 0,
            }
        },
        "zones": {
            "jps-zones_0": {
                "type": "polygon",
                "coordinates": [
                    [xl + 0.05, ROOM_DEPTH],
                    [xr - 0.05, ROOM_DEPTH],
                    [xr - 0.05, STAIR_TOP_Y - 0.1],
                    [xl + 0.05, STAIR_TOP_Y - 0.1],
                    [xl + 0.05, ROOM_DEPTH],
                ],
                "speed_factor": STAIR_SPEED_FACTOR,
            }
        },
        "journeys_v2": [
            {
                "id": JOURNEY_ID,
                "name": JOURNEY_ID,
                "color": "#3b82f6",
                "sequence": ["jps-exits_0"],
            }
        ],
    }


def measure_flow(traj_df, frame_rate: float, width: float) -> dict:
    """Flow of agents across the mid-stair line y = MEASURE_Y.

    Returns absolute flow (p/s) and specific flow (p/m/s). ISO expects the
    absolute flow to increase with stair width.
    """
    crossings = []
    for _, sub in traj_df.sort_values(["id", "frame"]).groupby("id"):
        below = sub[sub.y < MEASURE_Y]
        above = sub[sub.y >= MEASURE_Y]
        if len(below) and len(above):
            crossings.append(above.iloc[0].frame / frame_rate)
    crossings.sort()
    n = len(crossings)
    if n < 2:
        return {
            "width": width,
            "crossed": n,
            "flow_p_s": float("nan"),
            "specific_flow_p_m_s": float("nan"),
        }
    duration = crossings[-1] - crossings[0]
    flow = (n - 1) / duration if duration > 0 else float("nan")
    return {
        "width": width,
        "crossed": n,
        "flow_p_s": flow,
        "specific_flow_p_m_s": flow / width,
    }
