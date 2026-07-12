import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CodeScene } from "./scenes/CodeScene";
import { PlotScene } from "./scenes/PlotScene";
import { theme } from "./theme";

export const SCENE_SECS = {
  code: 9,
  plot: 9,
} as const;

export const Demo: React.FC = () => {
  const { fps } = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);

  let cursor = 0;
  const at = (s: number) => {
    const start = cursor;
    cursor += f(s);
    return { from: start, durationInFrames: f(s) };
  };

  const code = at(SCENE_SECS.code);
  const plot = at(SCENE_SECS.plot);

  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <Sequence from={code.from} durationInFrames={code.durationInFrames} layout="none">
        <CodeScene />
      </Sequence>
      <Sequence from={plot.from} durationInFrames={plot.durationInFrames} layout="none">
        <PlotScene />
      </Sequence>
    </AbsoluteFill>
  );
};

export const TOTAL_SECONDS = SCENE_SECS.code + SCENE_SECS.plot;
