import "./index.css";
import { Composition } from "remotion";
import { Demo, TOTAL_SECONDS } from "./Demo";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ScenariosGif"
      component={Demo}
      durationInFrames={Math.round(TOTAL_SECONDS * FPS)}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
