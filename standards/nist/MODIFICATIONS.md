# Modifications relative to NIST TN 1822

This file lists every change applied to the original NIST TN 1822
verification scenarios in producing this contribution. Reviewers should
treat each entry as the *minimum* delta needed to make the test runnable in
the JuPedSim CollisionFreeSpeedModel via the jupedsim-web-community
workflow.

The original V&V tree (Codex-produced, audited locally) lives separately and
is not part of this PR; it is referenced here as "source tree".

NIST source: <https://nvlpubs.nist.gov/nistpubs/technicalnotes/NIST.TN.1822.pdf>

## A. Project-wide normalisations

These apply uniformly to every scenario in this PR.

### A1. Exit-capture polygon thickness = 0.3 m

NIST figures specify exit *width* (opening length along the wall) but not the
solver-side capture thickness, which is an implementation detail. In the
source tree this thickness varied from 0.25 m to 1.0 m. **All exit polygons
have been normalised to 0.3 m thickness**, matching the value used in S1
(Verif.1.1).

Exit opening width (along the wall) is **unchanged** and continues to follow
each NIST figure.

### A2. Terminology: "pre-evacuation time"

The source tree used several near-synonyms inconsistently ("immediate
response", "response time 0", "instant response", "pre-movement"). All
human-readable strings (READMEs, notebook prose, CSV labels) now use the
canonical NIST TN 1822 term **"pre-evacuation time"**.

Note: any custom JSON keys named `premovement_*` were *removed* during
schema cleanup (see section A3), so this terminology change has no effect on
machine-readable artifacts shipped in the ZIPs.

### A3. config.json schema cleanup

Every `config.json` was filtered to canonical JuPedSim-web-editor fields
only. Per-ZIP the following custom keys were stripped (full list in
`_staging/conversion_report.txt` of the upload package):

| Scenario           | Stripped key(s)                                                       |
|--------------------|-----------------------------------------------------------------------|
| Verif.1.1          | `parameters.premovement_cases_file` (custom file pointer; the four NIST distributions are stored in the reference CSV + builder instead) |
| Verif.2.1, 2.2     | top-level `metadata` (corridor-extension explanation)                 |
| Verif.2.4          | `parameters.desired_speed_distribution`, `desired_speed_std`          |
| Verif.2.9          | `parameters.group_id` (all 3 distributions), top-level `metadata`     |
| Verif.3.1          | `parameters.room_number` (all 12 distributions), top-level `metadata` |
| Verif.5.1          | `parameters.desired_speed_distribution`, `desired_speed_std`, `metadata` |
| Verif.5.2          | top-level `metadata`                                                  |

Note: `use_premovement`, `premovement_distribution`, `premovement_param_a`,
`premovement_param_b`, `max_throughput`, and `enable_throughput_throttling`
are **kept** in the ZIPs — they are part of the canonical JuPedSim-scenarios
loader schema (verified against `src/jupedsim_scenarios/simulation_init.py`
and against `rimea/scenario_files/rimea-12d-bottleneck/config.json`).

Stripped semantics are preserved by:

- `Verif.1.1`: `nist1_1_premovement_reference.csv` +
  `scenario_builders/nist1_1_premovement.py` enumerate the 4 distributions
  and provide a `sample_pre_evac_times` helper.
- `Verif.2.8` (no keys stripped from JSON but conceptually a sweep): the 4
  counterflow values are captured in `scenario_files/nist2_8_counterflow_reference.csv` +
  `scenario_builders/nist2_8_counterflow.py`.
- `Verif.2.9`, `Verif.5.2`, etc.: the notebook is expected to re-apply the
  removed semantics through whatever loader API exists. The mapping from
  removed key to expected notebook behaviour will be in the notebook prose.

## B. Per-scenario modifications

### B1. Verif.1.1 — Pre-evacuation time distributions

- **Schema cleanup** (A3): the custom `premovement_cases_file` pointer was
  removed (the loader has no such hook). The base ZIP keeps the uniform
  U(10, 100) case as default.
- **Reuse**: the three additional NIST distributions (gamma, lognormal,
  weibull) come from `standards/utils/premovement_distributions`'s
  `PREMOVEMENT_PRESETS`, which already encode the canonical NIST
  parameters (Gamma a=1.291 b=103.901, Lognormal a=4.586 b=0.967,
  Weibull a=139.285 b=1.195). The local reference CSV that previously held
  these values was removed as redundant.
- `scenario_builders/nist1_1_premovement.build_variants(base)` deep-copies
  the base scenario and applies each case via `set_agent_params(..., 
  use_premovement=True, premovement_distribution=..., premovement_param_a=...,
  premovement_param_b=...)` — the loader's documented override API.
- **Exit thickness** (A1): already 0.3 m in the source tree, no change.

### B2. Verif.2.1 — Speed in a corridor (S2)

- **Geometry extended** from NIST's 40 m measurement corridor to 60 m total:
  10 m upstream acceleration buffer + 40 m measurement segment +
  10 m downstream isolation buffer. Measurement-segment length is unchanged.
- **Exit thickness** (A1): 0.5 m -> 0.3 m.
- **Schema cleanup** (A3): `metadata` block removed.

### B3. Verif.2.2 — Speed on stairs (S3.1, S3.2)

- **Geometry extended** from NIST's 100 m measurement stair to 120 m total
  (10 m + 100 m + 10 m). Same upstream/downstream rationale as Verif.2.1.
- **Exit thickness** (A1): 0.5 m -> 0.3 m on both branches.
- **Schema cleanup** (A3): `metadata` block removed on both branches.

### B4. Verif.2.3 — Movement around a corner (S4)

- **Exit thickness** (A1): 1.0 m -> 0.3 m. Exit opening width (2 m along the
  corridor head) unchanged.

### B5. Verif.2.4 — Assigned agent demographics (S5)

- **No exit polygon**: NIST's test is a pure demographic-distribution check;
  agents do not need to evacuate, so the scenario has no `exits` block.
- **Schema cleanup** (A3): `desired_speed_distribution` and
  `desired_speed_std` removed (duplicates of `v0_distribution` and `v0_std`).

### B6. Verif.2.5 — Reduced visibility (S6) — PENDING

Not shipped in this PR. NIST's smoke / extinction-coefficient correlation
requires features (visibility-driven speed reduction) absent from
CollisionFreeSpeedModel. Stays in source tree until those features land.

### B7. Verif.2.6 — Agent incapacitation (S7.x) — PENDING

Not shipped. NIST's FED-based incapacitation needs an FED sub-model.

### B8. Verif.2.7 — Elevator usage (S8) — PENDING

Not shipped. Requires elevator component (no 2D geometry can express this
test alone).

### B9. Verif.2.8 — Horizontal counter-flows (S9.1-S9.4)

- **Exit thickness** (A1): 1.0 m -> 0.3 m on both exits across all four
  branches.
- **No semantic changes**.

### B10. Verif.2.9 — Group behaviours (S10)

- **Schema cleanup** (A3): `group_id` parameter stripped from each of the 3
  distributions. The notebook will need to re-introduce group cohesion
  through the loader's group-behaviour API (when available) or by post-hoc
  analysis of trajectory bunching.

### B11. Verif.2.10 — Movement disabilities (S11.x) — PENDING

Not shipped. Requires reduced-mobility / per-agent size profiles.

### B12. Verif.3.1 — Exit route allocation (S12)

- **Geometry rebuilt** to NIST Figure 8. The source tree had a bare 18 m x 11
  m rectangle with no walls; the new geometry is a T-intersection of two 1 m
  corridors (horizontal east-west at y = 5..6, vertical south-north at
  x = 6..7) with 12 attached rooms. The outer ring + 26 interior wall rings
  encode 6 doors of 0.9 m on each long corridor wall, the vertical-corridor
  mouth, and inter-room walls. Distribution polygons inside each room are
  unchanged from the source tree.
- **Geometry rebuilt parametrically at conversion time**. The source WKT
  defined walls as 27 separate interior rings, two of which (vertical
  inter-room walls and the horizontal corridor walls) overlapped at the
  T-junctions, producing a shapely `TopologyException: side location
  conflict at (12.05, 6.05)` when the loader clipped exits to the
  walkable area. An initial fix that shrank the vertical walls by 0.01 m
  removed the topology error but left a tiny gap at every T-junction;
  agents (radius 0.15 m) couldn't pass through, but the JuPedSim
  pathfinder still routed them toward the gaps and they piled up at the
  corners (evacuation rate dropped to 11/23). The final fix
  (`_staging/convert.py::build_s12_walkable_wkt`) rebuilds the walkable
  polygon from a parametric NIST Figure 8 spec using
  `shapely.ops.unary_union`: each wall is a thin box extending into the
  horizontal corridor walls, so unioning them merges the overlaps into
  clean T-junctions with no gap. After the rebuild the test runs
  correctly: 23/23 agents evacuate in 18.6 s (vs 180 s timeout previously).
- **Exit thickness** (A1): 0.25 m -> 0.3 m on both main and secondary
  exits. Exit opening widths (1 m each) unchanged.
- **Schema cleanup** (A3): `room_number` parameter stripped from all 12
  distributions; `metadata` block removed.

### B13. Verif.3.2 — Social influence (S13.x) — PENDING

Not shipped. Requires social-influence component.

### B14. Verif.3.3 — Affiliation (S14.x) — PENDING

Not shipped. Requires affiliation component.

### B15. Verif.4.1 — Dynamic exit availability (S15) — PENDING

Not shipped. Requires runtime exit toggling (NIST closes Exit 1 at t = 1 s).

### B16. Verif.5.1 — Congestion (S16)

- **Exit thickness** (A1): 0.5 m -> 0.3 m. Exit opening width (2 m at top of
  vertical corridor) unchanged.
- **Schema cleanup** (A3): `desired_speed_distribution`,
  `desired_speed_std`, and `metadata` removed.

### B17. Verif.5.2 — Maximum flow rates (S17)

- **NIST Mode B (emergent-flow validation)** is the default because the
  CollisionFreeSpeedModel has no built-in door-flow limiter. NIST TN 1822
  Verif.5.2 explicitly offers two interpretations: (A) verification of a
  restricted-flow model — set the exit cap and check it is enforced; or (B)
  validation of emergent flow — let flow emerge and check it stays below
  the threshold. The notebook compares the recorded flow against the
  1.33 p/m/s reference (IMO MSC/Circ.1238) as a post-run threshold.
- The exit retains the canonical loader fields `max_throughput: 1.33` and
  `enable_throughput_throttling: false`. To switch to Mode A (when the
  runner under test supports throttled exits), the notebook can flip
  `enable_throughput_throttling` to `true` after loading.
- **Schema cleanup** (A3): only the top-level `metadata` block was removed.

## C. Items intentionally NOT changed

To make reviewer audit easier, these stayed identical to the source tree:

- All NIST-figure geometry dimensions (room sizes, corridor widths, stair
  lengths, opening widths) except S12's interior walls (B12) and the
  upstream/downstream buffers on single-agent speed tests (B2/B3).
- All journey definitions (distribution -> exit mappings).
- Distribution polygon shapes and agent counts.
- Agent radius (0.15 m) and configured walking speeds.
- Model type (`CollisionFreeSpeedModel`) and base seed (42).
