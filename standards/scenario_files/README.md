# Scenarios

Example scenarios grouped by which standard / category they belong to.

```
scenarios/
├── general/   # Generic dynamics demos used by the notebooks (bottleneck,
│              # faster-is-slower, waiting stages, etc.)
├── rimea/     # RiMEA verification & validation cases
├── iso/       # ISO 20414 / 20415 (planned)
├── nist/      # NIST egress benchmarks (planned)
└── imo/       # IMO MSC.1/Circ.1533 cases (planned; current IMO V&V
               # scenarios are authored inline in tests/vv/test_imo_*.py)
```

## Adding a new scenario

- One zip per scenario (containing `config.json` + `geometry.wkt`),
  OR a directory containing the same two files.
- Use the modern `journeys_v2` schema + per-distribution
  `journey_weights`. The legacy `journeys` / `transitions` /
  `waypoint_routing` schema is no longer supported.
- Drop the zip / dir into the right subdirectory and reference it via
  `load_scenario("scenarios/<subdir>/<name>")` from notebooks or tests.

## Inspecting in the app

Any zip here can be dragged into the web editor at
[app.jupedsim.org](https://app.jupedsim.org). The editor reads
`journeys_v2` + `journey_weights` directly, so what you see in the app
is what `load_scenario()` will simulate.
