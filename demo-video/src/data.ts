// Real numbers from examples/cookbook/faster_is_slower.ipynb,
// CollisionFreeSpeedModel, 60 agents, 0.75 m doorway, max_time=1000s.
// 5 desired speeds × 15 seeds = 75 trials; 17 of them clogged.
export type FISPoint = {
  v0: number;
  evac_times: number[];
};

export const MAX_TIME = 1000;
export const SEEDS = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54];

export const FIS_DATA: FISPoint[] = [
  { v0: 1.2, evac_times: [66.83, 67.29, 72.27, 66.77, 66.63, 64.35, 69.46, 67.4, 69.17, 63.68, 68.4, 67.8, 71.49, 1000.0, 69.08] },
  { v0: 1.4, evac_times: [65.24, 1000.0, 67.82, 62.26, 1000.0, 64.35, 1000.0, 64.79, 61.33, 61.55, 1000.0, 66.72, 67.43, 1000.0, 64.11] },
  { v0: 1.6, evac_times: [63.44, 62.22, 1000.0, 63.5, 1000.0, 1000.0, 1000.0, 62.94, 63.16, 60.55, 57.24, 1000.0, 64.04, 62.63, 61.09] },
  { v0: 1.8, evac_times: [63.79, 58.93, 61.3, 59.0, 58.63, 55.54, 1000.0, 1000.0, 59.0, 1000.0, 1000.0, 61.67, 55.85, 56.18, 59.01] },
  { v0: 2.0, evac_times: [57.03, 1000.0, 58.71, 54.37, 56.18, 52.79, 57.34, 54.42, 55.38, 57.24, 56.68, 57.11, 1000.0, 54.07, 54.03] },
];

export type TrialPoint = { v0: number; seed: number; t: number; clogged: boolean };

export const TRIALS: TrialPoint[] = FIS_DATA.flatMap((p) =>
  p.evac_times.map((t, i) => ({
    v0: p.v0,
    seed: SEEDS[i],
    t,
    clogged: t >= MAX_TIME,
  })),
);

export const TOTAL_TRIALS = TRIALS.length;
export const CLOG_COUNT = TRIALS.filter((t) => t.clogged).length;
export const CLOG_PCT = (CLOG_COUNT / TOTAL_TRIALS) * 100;
