# NIST scenario files

Each ZIP here is a JuPedSim web-editor export. The ZIP contains exactly two
files at its root:

- `config.json` — simulation settings, distributions, exits, journeys.
- `geometry.wkt` — walkable area as a single WKT `POLYGON`, with optional
  interior rings encoding internal walls.

## Naming convention

```
Nist-<section>-<descriptor>[-<branch>].zip
```

- `<section>` is the NIST TN 1822 verification id with dots replaced by
  dashes (`Verif.2.1` -> `2-1`, `Verif.2.8` -> `2-8`).
- `<descriptor>` is a short kebab-case label for the test.
- `<branch>` (optional) distinguishes variants of the same test:
  parameter-sweep values, scenario branches (up/down, baseline/with-X), etc.

Examples:

| ZIP                                  | NIST id     | Variant            |
|--------------------------------------|-------------|--------------------|
| `Nist-1-1-premovement.zip`           | Verif.1.1   | base scenario      |
| `Nist-2-1-corridor-speed.zip`        | Verif.2.1   | -                  |
| `Nist-2-2-stairs-up.zip`             | Verif.2.2   | upward branch      |
| `Nist-2-2-stairs-down.zip`           | Verif.2.2   | downward branch    |
| `Nist-2-8-counterflow-0.zip`         | Verif.2.8   | 0 counterflow      |
| `Nist-2-8-counterflow-100.zip`       | Verif.2.8   | 100 counterflow    |

For the workflow that consumes these ZIPs see
[`../../README.md`](../../README.md).
