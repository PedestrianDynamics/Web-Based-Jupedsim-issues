import { AbsoluteFill, Img, staticFile } from "remotion";
import { theme } from "../theme";
import { FIS_DATA } from "../data";

const W = 1920;
const H = 1080;

// Reuse the plot layout, slightly compacted for thumbnail.
const PAD_L = 140;
const PAD_R = 120;
const PAD_T = 360;
const PAD_B = 220;
const PLOT_W = W - PAD_L - PAD_R;
const PLOT_H = H - PAD_T - PAD_B;
const Y_MIN = 0;
const Y_MAX = 500;
const X_MIN = 1.05;
const X_MAX = 2.15;

const xScale = (v: number) => PAD_L + ((v - X_MIN) / (X_MAX - X_MIN)) * PLOT_W;
const yScale = (t: number) => PAD_T + (1 - (Math.max(Math.min(t, Y_MAX), Y_MIN) - Y_MIN) / (Y_MAX - Y_MIN)) * PLOT_H;

const agg = FIS_DATA.map((p) => {
  const n = p.evac_times.length;
  const mean = p.evac_times.reduce((a, b) => a + b, 0) / n;
  const variance = p.evac_times.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);
  const ci = (1.96 * std) / Math.sqrt(n);
  return { v0: p.v0, mean, lower: Math.max(0, mean - ci), upper: mean + ci };
});

export const Thumbnail: React.FC = () => {
  const meanPath = agg.map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.v0)} ${yScale(p.mean)}`).join(" ");
  const upperPts = agg.map((p) => `${xScale(p.v0)},${yScale(p.upper)}`).join(" ");
  const lowerPtsRev = [...agg].reverse().map((p) => `${xScale(p.v0)},${yScale(p.lower)}`).join(" ");
  const ribbon = `${upperPts} ${lowerPtsRev}`;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 30% 25%, #1a2233 0%, ${theme.bg} 60%)`,
      }}
    >
      {/* Logo top-left */}
      <Img
        src={staticFile("jupedsim_logo.svg")}
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          width: 360,
          height: "auto",
          filter: "brightness(0) invert(1)",
          opacity: 0.92,
        }}
      />

      {/* Headline */}
      <div
        style={{
          position: "absolute",
          top: 140,
          left: 80,
          right: 80,
          fontFamily: theme.sans,
          textAlign: "left",
        }}
      >
        <div
          style={{
            fontSize: 32,
            color: theme.warn,
            letterSpacing: 6,
            fontFamily: theme.mono,
            textTransform: "uppercase",
            marginBottom: 24,
          }}
        >
          Pedestrian Dynamics · Monte Carlo
        </div>
        <div
          style={{
            fontSize: 180,
            fontWeight: 800,
            color: theme.text,
            lineHeight: 0.95,
            letterSpacing: -4,
          }}
        >
          FASTER <span style={{ color: theme.danger }}>≠</span> FASTER
        </div>
      </div>

      {/* Plot */}
      <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {/* axes */}
        <line x1={PAD_L} y1={PAD_T} x2={PAD_L} y2={PAD_T + PLOT_H} stroke={theme.textDim} strokeWidth={3} />
        <line x1={PAD_L} y1={PAD_T + PLOT_H} x2={PAD_L + PLOT_W} y2={PAD_T + PLOT_H} stroke={theme.textDim} strokeWidth={3} />

        {/* CI ribbon */}
        <polygon points={ribbon} fill={theme.danger} fillOpacity={0.22} />

        {/* mean line */}
        <path d={meanPath} fill="none" stroke={theme.danger} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />

        {/* markers + labels */}
        {agg.map((p) => (
          <g key={p.v0}>
            <circle cx={xScale(p.v0)} cy={yScale(p.mean)} r={14} fill={theme.danger} stroke={theme.bg} strokeWidth={4} />
            <text
              x={xScale(p.v0)}
              y={yScale(p.mean) - 26}
              fill={theme.danger}
              fontFamily={theme.mono}
              fontSize={28}
              fontWeight={700}
              textAnchor="middle"
            >
              {p.mean.toFixed(0)}
            </text>
          </g>
        ))}

        {/* x labels */}
        {agg.map((p) => (
          <text
            key={p.v0}
            x={xScale(p.v0)}
            y={PAD_T + PLOT_H + 50}
            fill={theme.textDim}
            fontFamily={theme.mono}
            fontSize={26}
            textAnchor="middle"
          >
            {p.v0.toFixed(1)}
          </text>
        ))}
        <text
          x={PAD_L + PLOT_W / 2}
          y={PAD_T + PLOT_H + 110}
          fill={theme.text}
          fontFamily={theme.sans}
          fontSize={30}
          textAnchor="middle"
        >
          desired speed v₀ [m/s]
        </text>
      </svg>

      {/* Bottom-right callout */}
      <div
        style={{
          position: "absolute",
          right: 80,
          bottom: 80,
          fontFamily: theme.sans,
          textAlign: "right",
        }}
      >
        <div style={{ fontSize: 28, color: theme.textDim, letterSpacing: 2, fontFamily: theme.mono, textTransform: "uppercase" }}>
          75 simulations · 17 clogs
        </div>
      </div>
    </AbsoluteFill>
  );
};
