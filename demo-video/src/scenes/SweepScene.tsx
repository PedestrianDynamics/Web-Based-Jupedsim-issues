import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { theme } from "../theme";
import { Caption } from "../components/Caption";
import { FIS_DATA, SEEDS, MAX_TIME } from "../data";

export const SweepScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 0.4 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 0.5 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const total = FIS_DATA.length * SEEDS.length;
  const sweepProgress = interpolate(frame, [0.4 * fps, durationInFrames - 1.2 * fps], [0, total], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  const cellW = 240;
  const cellH = 44;
  const padX = 360;
  const padY = 240;
  const cols = FIS_DATA.length;
  const rows = SEEDS.length;

  let done = 0;
  let cloggedCount = 0;
  for (let c = 0; c < cols; c++) {
    for (let r = 0; r < rows; r++) {
      const idx = c * rows + r;
      if (idx < Math.floor(sweepProgress)) {
        done++;
        if (FIS_DATA[c].evac_times[r] >= MAX_TIME) cloggedCount++;
      }
    }
  }

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity: fadeIn * fadeOut }}>
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: theme.sans,
          fontSize: 42,
          fontWeight: 600,
          color: theme.text,
        }}
      >
        run_sweep · {cols} desired speeds [m/s] × {rows} seeds = {total} simulations
      </div>
      <div
        style={{
          position: "absolute",
          top: 150,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: theme.mono,
          fontSize: 26,
          color: theme.textDim,
        }}
      >
        {done}/{total} complete · {cloggedCount} clogged
      </div>

      <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        {/* x labels: v0 */}
        {FIS_DATA.map((p, c) => (
          <text
            key={`xl-${c}`}
            x={padX + c * cellW + cellW / 2}
            y={padY - 28}
            fill={theme.textDim}
            fontFamily={theme.mono}
            fontSize={22}
            textAnchor="middle"
          >
            {p.v0.toFixed(1)}
          </text>
        ))}

        {/* y labels: seed */}
        {SEEDS.map((s, r) => (
          <text
            key={`yl-${r}`}
            x={padX - 18}
            y={padY + r * cellH + cellH / 2 + 6}
            fill={theme.textDim}
            fontFamily={theme.mono}
            fontSize={18}
            textAnchor="end"
          >
            seed={s}
          </text>
        ))}

        {FIS_DATA.flatMap((p, c) =>
          SEEDS.map((_, r) => {
            const idx = c * rows + r;
            const cellState = sweepProgress - idx;
            if (cellState <= 0) {
              return (
                <rect
                  key={`c-${c}-${r}`}
                  x={padX + c * cellW + 4}
                  y={padY + r * cellH + 4}
                  width={cellW - 8}
                  height={cellH - 8}
                  rx={8}
                  fill={theme.bgSoft}
                  stroke={theme.grid}
                />
              );
            }
            const reveal = Math.min(1, cellState);
            const clogged = p.evac_times[r] >= MAX_TIME;
            const t = p.evac_times[r];
            const fillColor = clogged ? theme.danger : theme.ok;
            return (
              <g key={`c-${c}-${r}`} opacity={reveal}>
                <rect
                  x={padX + c * cellW + 4}
                  y={padY + r * cellH + 4}
                  width={cellW - 8}
                  height={cellH - 8}
                  rx={8}
                  fill={fillColor}
                  fillOpacity={clogged ? 0.32 : 0.18}
                  stroke={fillColor}
                  strokeOpacity={0.85}
                />
                <text
                  x={padX + c * cellW + cellW / 2}
                  y={padY + r * cellH + cellH / 2 + 6}
                  fill={theme.text}
                  fontFamily={theme.mono}
                  fontSize={20}
                  fontWeight={600}
                  textAnchor="middle"
                >
                  {clogged ? "CLOG" : `${t.toFixed(1)}s`}
                </text>
              </g>
            );
          }),
        )}
      </svg>

      <Caption text="17 of 75 trials hit max_time. Clogging is rare per cell — and invisible to a single seed." appearAt={Math.floor(durationInFrames - 2.6 * fps)} />
    </AbsoluteFill>
  );
};
