# Faster-Is-Slower Demo Video

A 78-second Remotion video that tells the story:

1. **Title** (6 s) — JuPedSim Web + jupedsim-scenarios
2. **App** (16 s) — your screen recording of drawing the geometry and downloading the zip
3. **Code** (12 s) — the 8 lines of Python that drive a 40-trial sweep
4. **Sweep grid** (12 s) — all 40 (v₀ × seed) trials filling in, clogs in red
5. **Plot** (22 s) — scatter of evacuation times, clogged trials pinned above, mean curve
6. **Closing** (10 s) — the takeaway and links

The numbers shown in the sweep grid and plot are real, from a fresh run of
`standards/general/faster_is_slower.ipynb` (8 desired speeds × 5 seeds = 40 trials,
3 of which clogged at 1000 s).

## Preview

```
npm run dev
```

## Drop in your screen recording

1. Record drawing the geometry, placing agents/exit, and downloading the zip in
   the app.
2. Save it to `public/app-recording.mp4` (~16 s; the scene plays it at native
   rate with `objectFit: cover`).
3. Open `src/scenes/AppScene.tsx` and set `HAS_RECORDING = true`.

Without a recording, an animated SVG mockup of the drawing step plays as a
fallback so the project always renders.

## Render

```
npx remotion render FasterIsSlowerDemo out/demo.mp4
```

## Refresh the data

The sweep results live in `src/data.ts`. To regenerate from a fresh run of the
notebook, rerun the sweep and copy the per-`v0` evacuation-time arrays.
