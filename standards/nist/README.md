# NIST TN 1822 — JuPedSim verification scenarios

Scenarios and notebooks based on **NIST Technical Note 1822** (Ronchi,
Kuligowski, Reneke, Peacock, Nilsson, 2013 — *The process of verification and
validation of building fire evacuation models*). Reference:
<https://nvlpubs.nist.gov/nistpubs/technicalnotes/NIST.TN.1822.pdf>.

Notebooks live alongside this README; scenario ZIPs live in
`scenario_files/`; parameter-sweep helpers live in `scenario_builders/`;
reference data lives in CSVs at this folder's root.

For deviations from the NIST original specifications see
[`MODIFICATIONS.md`](MODIFICATIONS.md).

## Coverage

| NIST id    | Title                                  | Status   | ZIP / notebook |
|------------|----------------------------------------|----------|----------------|
| Verif.1.1  | Pre-evacuation time distributions      | covered  | `Nist-1-1-premovement.zip` + `nist1_1_premovement.ipynb` (sweeps the 4 NIST distributions via `standards/utils/premovement_distributions`) |
| Verif.2.1  | Speed in a corridor                    | covered  | `Nist-2-1-corridor-speed.zip` |
| Verif.2.2  | Speed on stairs (upward)               | covered  | `Nist-2-2-stairs-up.zip` |
| Verif.2.2  | Speed on stairs (downward)             | covered  | `Nist-2-2-stairs-down.zip` |
| Verif.2.3  | Movement around a corner               | covered  | `Nist-2-3-corner.zip` |
| Verif.2.4  | Assigned agent demographics            | covered  | `Nist-2-4-demographics.zip` |
| Verif.2.5  | Reduced visibility vs walking speed    | pending  | requires smoke / extinction-coefficient handling |
| Verif.2.6  | Agent incapacitation (FED)             | pending  | requires FED sub-model |
| Verif.2.7  | Elevator usage                         | pending  | requires elevator component |
| Verif.2.8  | Horizontal counter-flows               | covered  | `Nist-2-8-counterflow-{0,10,50,100}.zip` + `scenario_files/nist2_8_counterflow_reference.csv` |
| Verif.2.9  | Group behaviours                       | covered* | `Nist-2-9-groups.zip` |
| Verif.2.10 | Agents with movement disabilities      | pending  | requires reduced-mobility / agent-size profiles |
| Verif.3.1  | Exit route allocation                  | covered  | `Nist-3-1-route-allocation.zip` |
| Verif.3.2  | Social influence                       | pending  | requires social-influence component |
| Verif.3.3  | Affiliation                            | pending  | requires affiliation component |
| Verif.4.1  | Dynamic availability of exits          | pending  | requires runtime exit toggling |
| Verif.5.1  | Congestion                             | covered  | `Nist-5-1-congestion.zip` |
| Verif.5.2  | Maximum flow rates                     | covered  | `Nist-5-2-max-flow.zip` (NIST Mode B - emergent flow) |

\* Verif.2.9 ships geometry + journeys but the original config used a custom
`group_id` parameter that was stripped during cleaning; the notebook will need
to apply group behaviour through whatever mechanism the loader supports.

## Modification highlights vs NIST originals

See [`MODIFICATIONS.md`](MODIFICATIONS.md) for the full audit trail. Summary:

- **Exit-capture polygon thickness** normalised to 0.3 m across every scenario
  for consistency with `Nist-1-1-premovement.zip`. The exit opening width
  (along the wall) follows the NIST figures unchanged.
- **Single-agent speed tests** (Verif.2.1, 2.2, 2.5) extend the corridor or
  stair by 10 m at each end (upstream acceleration buffer + downstream
  isolation buffer). The measurement segment length remains exactly as NIST
  specifies.
- **Verif.3.1 (S12)** geometry was rebuilt to NIST Figure 8 (12 rooms around a
  1 m corridor + vestibule); the previous tree had a bare 18 m x 11 m
  rectangle.
- **Verif.5.2 (S17)** uses NIST's Mode B (emergent-flow validation), because
  the JuPedSim CollisionFreeSpeedModel has no built-in door-flow limiter. The
  1.33 p/m/s value (IMO MSC/Circ.1238) is a post-run comparison threshold,
  not an input cap applied to the exit.
- **Terminology**: "pre-evacuation time" used throughout in place of mixed
  "pre-movement / immediate response / instant response / response time 0"
  wording from earlier V&V iterations. NIST TN 1822 uses "pre-evacuation
  time" as the canonical term.
- **Schema cleanup**: every `config.json` has been filtered to canonical
  JuPedSim-scenarios loader fields (verified against
  `src/jupedsim_scenarios/simulation_init.py` and
  `rimea/scenario_files/rimea-12d-bottleneck/config.json`). Custom non-loader
  keys (`group_id`, `room_number`, `desired_speed_distribution`,
  `desired_speed_std`, `premovement_cases_file`, top-level `metadata`
  blocks) were removed from the ZIPs and either moved to reference CSVs /
  `scenario_builders/` modules or scheduled for re-injection inside the
  notebooks. Loader-canonical fields (`use_premovement`, `premovement_*`,
  `max_throughput`, `enable_throughput_throttling`) are kept in the ZIPs.

## Pending NIST tests

The "pending" rows above are blocked on simulator features that are not yet
in the JuPedSim CollisionFreeSpeedModel. Each will be added in a follow-up
PR once the corresponding feature lands.

## Citation

Ronchi, E., Kuligowski, E. D., Reneke, P. A., Peacock, R. D., & Nilsson, D.
(2013). *The process of verification and validation of building fire
evacuation models.* NIST Technical Note 1822.
