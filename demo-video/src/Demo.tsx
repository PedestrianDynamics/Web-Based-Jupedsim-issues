import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { TitleScene } from "./scenes/TitleScene";
import { AppScene, APP_SCENE_SECS } from "./scenes/AppScene";
import { CodeScene } from "./scenes/CodeScene";
import { SweepScene } from "./scenes/SweepScene";
import { PlotScene } from "./scenes/PlotScene";
import { ClosingScene } from "./scenes/ClosingScene";
import { theme } from "./theme";

// Scene durations in seconds. Total = 78s @ 30fps = 2340 frames.
export const SCENE_SECS = {
  title: 6,
  app: APP_SCENE_SECS,
  code: 16,
  sweep: 12,
  plot: 22,
  closing: 10,
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

  const title = at(SCENE_SECS.title);
  const app = at(SCENE_SECS.app);
  const code = at(SCENE_SECS.code);
  const sweep = at(SCENE_SECS.sweep);
  const plot = at(SCENE_SECS.plot);
  const closing = at(SCENE_SECS.closing);

  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <Sequence from={title.from} durationInFrames={title.durationInFrames} layout="none">
        <TitleScene />
      </Sequence>
      <Sequence from={app.from} durationInFrames={app.durationInFrames} layout="none">
        <AppScene />
      </Sequence>
      <Sequence from={code.from} durationInFrames={code.durationInFrames} layout="none">
        <CodeScene />
      </Sequence>
      <Sequence from={sweep.from} durationInFrames={sweep.durationInFrames} layout="none">
        <SweepScene />
      </Sequence>
      <Sequence from={plot.from} durationInFrames={plot.durationInFrames} layout="none">
        <PlotScene />
      </Sequence>
      <Sequence from={closing.from} durationInFrames={closing.durationInFrames} layout="none">
        <ClosingScene />
      </Sequence>
    </AbsoluteFill>
  );
};

export const TOTAL_SECONDS =
  SCENE_SECS.title + SCENE_SECS.app + SCENE_SECS.code + SCENE_SECS.sweep + SCENE_SECS.plot + SCENE_SECS.closing;
