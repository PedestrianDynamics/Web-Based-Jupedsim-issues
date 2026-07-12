import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

const LINES: Array<{ text: string; color?: string }> = [
  { text: "from jupedsim_scenarios import load_scenario, run_sweep", color: theme.textDim },
  { text: "" },
  { text: "scenario = load_scenario(\"faster-is-slower.zip\")" },
  { text: "" },
  { text: "sweep = run_sweep(", color: theme.accent },
  { text: "    scenario,", color: theme.text },
  { text: "    axes={\"v0\": [1.2, 1.4, 1.6, 1.8, 2.0]},", color: theme.warn },
  { text: "    apply={\"v0\": lambda s, v: s.set_agent_params(desired_speed=v)},", color: theme.text },
  { text: "    seeds=list(range(40, 55)),  # 15 seeds", color: theme.warn },
  { text: "    workers=4,", color: theme.text },
  { text: ")", color: theme.accent },
  { text: "df = sweep.to_dataframe()", color: theme.ok },
  { text: "plot_evacuation_time(df)", color: theme.ok },
];

const LINE_HEIGHT = 50;
const PANEL_PAD_TOP = 40;

export const CodeScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const charsPerSec = 120;
  const typed = Math.floor((frame / fps) * charsPerSec);

  const fadeIn = interpolate(frame, [0, 0.4 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // No fadeOut: hard cut into PlotScene so the curve appears the instant
  // typing finishes.
  const fadeOut = 1;
  void durationInFrames;

  let consumed = 0;
  const rendered = LINES.map((line) => {
    const remaining = Math.max(0, typed - consumed);
    const shown = line.text.slice(0, remaining);
    consumed += line.text.length + 1;
    return { ...line, shown };
  });

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity: fadeIn * fadeOut, padding: 100 }}>
      <div
        style={{
          fontFamily: theme.sans,
          fontSize: 30,
          color: theme.textDim,
          letterSpacing: 3,
          textTransform: "uppercase",
          marginBottom: 30,
        }}
      >
        A few lines of Python
      </div>
      <div
        style={{
          background: theme.panel,
          border: `1px solid ${theme.grid}`,
          borderRadius: 14,
          padding: `${PANEL_PAD_TOP}px 56px`,
          fontFamily: theme.mono,
          fontSize: 32,
          lineHeight: `${LINE_HEIGHT}px`,
          color: theme.text,
          position: "relative",
          overflow: "hidden",
        }}
      >
        {rendered.map((line, i) => (
          <div key={i} style={{ color: line.color ?? theme.text, minHeight: LINE_HEIGHT, whiteSpace: "pre" }}>
            {line.shown || " "}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
