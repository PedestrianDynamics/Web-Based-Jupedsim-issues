import "./index.css";
import { Composition } from "remotion";
import { Demo, TOTAL_SECONDS } from "./Demo";
import { Thumbnail } from "./scenes/Thumbnail";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="FasterIsSlowerDemo"
        component={Demo}
        durationInFrames={Math.round(TOTAL_SECONDS * FPS)}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Thumbnail"
        component={Thumbnail}
        durationInFrames={30}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
