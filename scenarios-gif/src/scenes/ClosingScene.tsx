import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { theme } from "../theme";
import { Logo } from "../components/Logo";

export const ClosingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const inAt = (d: number) =>
    interpolate(frame, [d, d + 0.6 * fps], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
  const yAt = (d: number) =>
    interpolate(frame, [d, d + 0.6 * fps], [20, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });

  const out = interpolate(frame, [durationInFrames - 0.6 * fps, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const STATS = [
    ["1", "scenario drawn in the browser"],
    ["75", "simulations, run in parallel"],
    ["17", "clogging events (22.7%)"],
    ["5", "desired speeds compared"],
  ];

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 70% 70%, #18253a 0%, ${theme.bg} 65%)`,
        opacity: out,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Logo />
      <div style={{ textAlign: "center", maxWidth: 1500 }}>
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 84,
            fontWeight: 700,
            color: theme.text,
            letterSpacing: -1.5,
            opacity: inAt(0),
            transform: `translateY(${yAt(0)}px)`,
            lineHeight: 1.1,
          }}
        >
          Interactive scenario setup,
        </div>
        <div
          style={{
            fontFamily: theme.sans,
            fontSize: 84,
            fontWeight: 700,
            color: theme.accent,
            letterSpacing: -1.5,
            opacity: inAt(0.4 * fps),
            transform: `translateY(${yAt(0.4 * fps)}px)`,
            lineHeight: 1.1,
          }}
        >
          programmatic stochastic analysis.
        </div>
        <div
          style={{
            display: "flex",
            gap: 32,
            justifyContent: "center",
            marginTop: 80,
            opacity: inAt(0.9 * fps),
            transform: `translateY(${yAt(0.9 * fps)}px)`,
          }}
        >
          {STATS.map(([n, label]) => (
            <div
              key={label}
              style={{
                background: theme.panel,
                border: `1px solid ${theme.grid}`,
                borderRadius: 14,
                padding: "26px 34px",
                minWidth: 240,
              }}
            >
              <div
                style={{
                  fontFamily: theme.mono,
                  color: theme.accent,
                  fontSize: 72,
                  fontWeight: 700,
                  lineHeight: 1,
                }}
              >
                {n}
              </div>
              <div
                style={{
                  fontFamily: theme.sans,
                  color: theme.textDim,
                  fontSize: 20,
                  marginTop: 12,
                  lineHeight: 1.3,
                }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: 100,
            display: "flex",
            gap: 56,
            justifyContent: "center",
            opacity: inAt(1.5 * fps),
            transform: `translateY(${yAt(1.5 * fps)}px)`,
          }}
        >
          <Pill label="app" value="app.jupedsim.org" />
          <Pill label="pypi" value="pip install jupedsim-scenarios" />
          <Pill label="github" value="PedestrianDynamics/jupedsim-web-community" />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Pill: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div
    style={{
      fontFamily: theme.mono,
      color: theme.text,
      fontSize: 26,
      display: "flex",
      alignItems: "center",
      gap: 16,
    }}
  >
    <span
      style={{
        color: theme.textDim,
        textTransform: "uppercase",
        fontSize: 16,
        letterSpacing: 3,
        background: theme.panel,
        border: `1px solid ${theme.grid}`,
        padding: "6px 12px",
        borderRadius: 6,
      }}
    >
      {label}
    </span>
    {value}
  </div>
);
