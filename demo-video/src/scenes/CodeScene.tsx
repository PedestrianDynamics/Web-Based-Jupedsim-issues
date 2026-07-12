import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
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
];

const LINE_HEIGHT = 50;
const PANEL_PAD_TOP = 40;

// Indices of the lines we want to highlight in order.
const AXES_LINE = 6;
const SEEDS_LINE = 8;
const WORKERS_LINE = 9;

type Highlight = {
  line: number;
  start: number; // seconds
  end: number;   // seconds
  keyword: string;
  text: string;
};

export const CodeScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const charsPerSec = 120;
  const typed = Math.floor((frame / fps) * charsPerSec);

  const fadeIn = interpolate(frame, [0, 0.4 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 0.5 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  let consumed = 0;
  const rendered = LINES.map((line) => {
    const remaining = Math.max(0, typed - consumed);
    const shown = line.text.slice(0, remaining);
    consumed += line.text.length + 1;
    return { ...line, shown };
  });

  // Highlight timeline (seconds). Typing finishes around 4.5 s.
  const HIGHLIGHTS: Highlight[] = [
    { line: AXES_LINE, start: 5.0, end: 8.0, keyword: "axes", text: "the parameter grid. Here: five desired speeds." },
    { line: SEEDS_LINE, start: 8.0, end: 11.5, keyword: "seeds", text: "each combination is repeated 15 times for statistical power." },
    { line: WORKERS_LINE, start: 11.5, end: 14.5, keyword: "workers", text: "four trials run in parallel on this machine." },
  ];

  // Pick the active highlight by current frame. Box snaps between rows
  // with a short eased slide rather than a piecewise-linear interpolate.
  let activeLine = HIGHLIGHTS[0].line;
  let activeStartFrame = HIGHLIGHTS[0].start * fps;
  for (const h of HIGHLIGHTS) {
    if (frame >= h.start * fps) {
      activeLine = h.line;
      activeStartFrame = h.start * fps;
    }
  }
  const targetTop = PANEL_PAD_TOP + activeLine * LINE_HEIGHT - 6;

  // Slide from previous position over ~0.35 s when the active stop changes.
  const slideDuration = 0.35 * fps;
  const slideT = Math.min(1, Math.max(0, (frame - activeStartFrame) / slideDuration));
  const eased = Easing.inOut(Easing.cubic)(slideT);
  // We don't track the "previous" target across renders, so just snap to
  // target — a clean discrete move reads better than mid-slide artifacts.
  void eased;
  const boxTop = targetTop;

  const showBox = frame >= HIGHLIGHTS[0].start * fps;
  const boxOpacity = showBox
    ? interpolate(
        frame,
        [HIGHLIGHTS[0].start * fps - 0.3 * fps, HIGHLIGHTS[0].start * fps],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
      )
    : 0;

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
        <div
          style={{
            position: "absolute",
            left: 30,
            right: 30,
            top: boxTop,
            height: LINE_HEIGHT + 12,
            background: theme.accent,
            opacity: boxOpacity * 0.12,
            borderRadius: 8,
            border: `1px solid rgba(88, 166, 255, ${boxOpacity * 0.65})`,
          }}
        />
        {rendered.map((line, i) => (
          <div key={i} style={{ color: line.color ?? theme.text, minHeight: LINE_HEIGHT, whiteSpace: "pre" }}>
            {line.shown || " "}
          </div>
        ))}
      </div>

      <HighlightCaptions highlights={HIGHLIGHTS} />
    </AbsoluteFill>
  );
};

const HighlightCaptions: React.FC<{ highlights: Highlight[] }> = ({ highlights }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 80,
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div style={{ position: "relative", height: 100, width: "78%" }}>
        {highlights.map((h, i) => {
          const fadeIn = 0.3;
          const fadeOut = 0.3;
          const opacity = interpolate(
            frame,
            [
              (h.start - fadeIn) * fps,
              h.start * fps,
              (h.end - fadeOut) * fps,
              h.end * fps,
            ],
            [0, 1, 1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );
          if (opacity <= 0) return null;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                justifyContent: "center",
                opacity,
              }}
            >
              <div
                style={{
                  fontFamily: theme.sans,
                  fontSize: 32,
                  fontWeight: 500,
                  color: theme.text,
                  background: "rgba(13, 17, 23, 0.78)",
                  backdropFilter: "blur(8px)",
                  padding: "16px 28px",
                  borderRadius: 12,
                  border: `1px solid ${theme.grid}`,
                  textAlign: "center",
                  lineHeight: 1.3,
                  maxWidth: "100%",
                }}
              >
                <span style={{ color: theme.warn, fontWeight: 700, fontFamily: theme.mono }}>
                  {h.keyword}
                </span>
                {" — "}
                {h.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
