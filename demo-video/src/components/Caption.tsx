import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { theme } from "../theme";

export const Caption: React.FC<{
  text: string;
  position?: "top" | "bottom";
  appearAt?: number;
}> = ({ text, position = "bottom", appearAt = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - appearAt;
  const opacity = interpolate(t, [0, 0.4 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const dy = interpolate(t, [0, 0.4 * fps], [12, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          [position]: position === "bottom" ? 20 : 80,
          display: "flex",
          justifyContent: "center",
          opacity,
          transform: `translateY(${dy}px)`,
        }}
      >
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 36,
            fontWeight: 500,
            color: theme.text,
            background: "rgba(13, 17, 23, 0.78)",
            backdropFilter: "blur(8px)",
            padding: "16px 28px",
            borderRadius: 12,
            border: `1px solid ${theme.grid}`,
            maxWidth: "78%",
            textAlign: "center",
            lineHeight: 1.3,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
