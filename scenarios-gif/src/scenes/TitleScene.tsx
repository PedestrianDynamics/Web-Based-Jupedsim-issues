import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing, spring } from "remotion";
import { theme } from "../theme";
import { LogoIntro } from "../components/LogoIntro";

// Beats (seconds): scatter → assemble → wordmark fade-in → shrink to corner → title text.
const LETTER_REVEAL = 0.85;
const SHRINK_START = 1.4;
const SHRINK_END = 2.2;
const TEXT_DELAY = 2.2;

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const textStart = TEXT_DELAY * fps;

  const lineIn = (extra: number) =>
    interpolate(frame, [textStart + extra, textStart + extra + 0.7 * fps], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
  const lineY = (extra: number) =>
    interpolate(frame, [textStart + extra, textStart + extra + 0.7 * fps], [24, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });

  const out = interpolate(frame, [durationInFrames - 0.5 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const dotScale = spring({
    frame: frame - textStart - 0.2 * fps,
    fps,
    config: { damping: 12, stiffness: 120 },
  });

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 30% 30%, #1a2233 0%, ${theme.bg} 60%)`,
        opacity: out,
      }}
    >
      <LogoIntro
        letterRevealSec={LETTER_REVEAL}
        shrinkStartSec={SHRINK_START}
        shrinkEndSec={SHRINK_END}
      />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center", maxWidth: 1500 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 16,
              opacity: lineIn(0),
              transform: `translateY(${lineY(0)}px)`,
              marginBottom: 40,
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 7,
                background: theme.ok,
                transform: `scale(${dotScale})`,
                boxShadow: `0 0 24px ${theme.ok}`,
              }}
            />
            <div
              style={{
                fontFamily: theme.mono,
                color: theme.textDim,
                fontSize: 26,
                letterSpacing: 4,
                textTransform: "uppercase",
              }}
            >
              JuPedSim Web + jupedsim-scenarios
            </div>
          </div>
          <div
            style={{
              fontFamily: theme.sans,
              fontSize: 124,
              fontWeight: 700,
              color: theme.text,
              lineHeight: 1.05,
              letterSpacing: -2,
              opacity: lineIn(0.4 * fps),
              transform: `translateY(${lineY(0.4 * fps)}px)`,
            }}
          >
            Faster-is-slower effect
          </div>
          <div
            style={{
              fontFamily: theme.sans,
              fontSize: 124,
              fontWeight: 700,
              color: theme.accent,
              lineHeight: 1.05,
              letterSpacing: -2,
              opacity: lineIn(0.8 * fps),
              transform: `translateY(${lineY(0.8 * fps)}px)`,
            }}
          >
            in 90 seconds.
          </div>
          <div
            style={{
              fontFamily: theme.sans,
              fontSize: 32,
              color: theme.textDim,
              marginTop: 56,
              opacity: lineIn(1.3 * fps),
              transform: `translateY(${lineY(1.3 * fps)}px)`,
            }}
          >
            5 desired speeds × 15 random seeds = 75 stochastic simulations.
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
