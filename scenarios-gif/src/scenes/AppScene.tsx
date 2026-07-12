import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig, staticFile, Easing } from "remotion";
import { Video } from "@remotion/media";
import { theme } from "../theme";
import { Caption } from "../components/Caption";

// Each clip plays inside the same browser-chrome frame. playbackRate
// compresses long screen-recordings into the demo's beat without
// losing the "real recording" feel.
type Clip = {
  src: string;
  durationSec: number;
  playbackRate: number;
  trimBeforeSec?: number;
  caption: string;
};

const CLIPS: Clip[] = [
  { src: "01_create_scenario.mov", durationSec: 4, playbackRate: 3.4, caption: "Create a new scenario." },
  { src: "02_draw_elements.mov", durationSec: 7, playbackRate: 4.4, caption: "Sketch the geometry — walkable area, exits, agents." },
  { src: "03_setup_model.mov", durationSec: 7, playbackRate: 2.0, caption: "Pick a model, tune its parameter and run a simulation." },
  // Clip 04 split: skip ahead through the setup, then near-normal speed for the actual simulation.
  { src: "04_run_simulation_with_analysis.mov", durationSec: 4, playbackRate: 7.5, caption: "" },
  { src: "04_run_simulation_with_analysis.mov", durationSec: 19, playbackRate: 1.5, trimBeforeSec: 30, caption: "Watch the simulation. Inspect the in-app analysis." },
];

const SAVE_CLIP: Clip = {
  src: "05_save_scenario.mov",
  durationSec: 3,
  playbackRate: 5.2,
  caption: "Save and download the scenario as a zip.",
};

const BRIDGE_SECS = 4;

export const APP_SCENE_SECS =
  CLIPS.reduce((s, c) => s + c.durationSec, 0) + BRIDGE_SECS + SAVE_CLIP.durationSec;

export const AppScene: React.FC = () => {
  const { fps } = useVideoConfig();

  let cursor = 0;
  const at = (s: number) => {
    const start = cursor;
    cursor += Math.round(s * fps);
    return { from: start, durationInFrames: Math.round(s * fps) };
  };

  const segments = [
    ...CLIPS.map((c) => ({ kind: "clip" as const, clip: c, range: at(c.durationSec) })),
    { kind: "bridge" as const, range: at(BRIDGE_SECS) },
    { kind: "clip" as const, clip: SAVE_CLIP, range: at(SAVE_CLIP.durationSec) },
  ];

  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      {segments.map((seg, i) => (
        <Sequence
          key={i}
          from={seg.range.from}
          durationInFrames={seg.range.durationInFrames}
          layout="none"
        >
          {seg.kind === "clip" ? (
            <ClipScene clip={seg.clip} />
          ) : (
            <BridgeCard />
          )}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const ClipScene: React.FC<{ clip: Clip }> = ({ clip }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const trimBefore = clip.trimBeforeSec ? Math.round(clip.trimBeforeSec * fps) : 0;
  const fadeIn = interpolate(frame, [0, 0.3 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 0.3 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity: fadeIn * fadeOut }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <BrowserFrame>
          <Video
            src={staticFile(clip.src)}
            playbackRate={clip.playbackRate}
            trimBefore={trimBefore}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </BrowserFrame>
      </AbsoluteFill>
      {clip.caption && <Caption text={clip.caption} appearAt={Math.floor(0.2 * fps)} />}
    </AbsoluteFill>
  );
};

const BridgeCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 0.45 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(frame, [durationInFrames - 0.45 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dy = interpolate(frame, [0, 0.45 * fps], [16, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 30% 70%, #1a2233 0%, ${theme.bg} 65%)`,
        opacity: fadeIn * fadeOut,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: 1500, transform: `translateY(${dy}px)` }}>
        <div
          style={{
            fontFamily: theme.mono,
            color: theme.warn,
            fontSize: 24,
            letterSpacing: 4,
            textTransform: "uppercase",
            marginBottom: 32,
          }}
        >
          From qualitative to quantitative
        </div>
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 72,
            fontWeight: 700,
            color: theme.text,
            letterSpacing: -1.2,
            lineHeight: 1.15,
          }}
        >
          A single in-app run validates the setup.
        </div>
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 72,
            fontWeight: 700,
            color: theme.accent,
            letterSpacing: -1.2,
            lineHeight: 1.15,
            marginTop: 16,
          }}
        >
          Quantitative results require repeated trials.
        </div>
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 30,
            color: theme.textDim,
            marginTop: 48,
            lineHeight: 1.4,
          }}
        >
          Export the scenario. Parameterize it in Python. Sweep across seeds and parameters.
        </div>
      </div>
    </AbsoluteFill>
  );
};

const BrowserFrame: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      width: 1700,
      height: 920,
      borderRadius: 18,
      border: `1px solid ${theme.grid}`,
      overflow: "hidden",
      background: theme.panel,
      boxShadow: "0 30px 80px rgba(0,0,0,0.55)",
    }}
  >
    <div
      style={{
        height: 44,
        background: "#0b0f17",
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "0 16px",
        borderBottom: `1px solid ${theme.grid}`,
      }}
    >
      <span style={dot("#ff5f57")} />
      <span style={dot("#febc2e")} />
      <span style={dot("#28c840")} />
      <div style={{ marginLeft: 18, fontFamily: theme.mono, color: theme.textDim, fontSize: 16 }}>
        app.jupedsim.org
      </div>
    </div>
    <div style={{ width: "100%", height: "calc(100% - 44px)" }}>{children}</div>
  </div>
);

const dot = (c: string) => ({ width: 12, height: 12, borderRadius: 6, background: c });
