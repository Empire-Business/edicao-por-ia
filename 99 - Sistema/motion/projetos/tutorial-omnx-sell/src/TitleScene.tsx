import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FONT, INK, MONO, useBrand} from './theme';

export const TitleScene: React.FC<{
  kicker?: string;
  title: string;
  subtitle: string;
  durationInFrames: number;
}> = ({kicker, title, subtitle, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const b = useBrand();

  const pop = spring({frame, fps, config: {damping: 200, mass: 0.7}});
  const out = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp'},
  );
  const lines = title.split('\n');

  return (
    <AbsoluteFill
      style={{
        fontFamily: FONT,
        alignItems: 'center',
        justifyContent: 'center',
        opacity: out,
      }}
    >
      <div
        style={{
          transform: `translateY(${interpolate(pop, [0, 1], [30, 0])}px)`,
          opacity: pop,
          textAlign: 'center',
          maxWidth: 1500,
        }}
      >
        <div
          style={{display: 'flex', justifyContent: 'center', marginBottom: 34}}
        >
          {b.logo}
        </div>

        {kicker ? (
          <div
            style={{
              fontFamily: MONO,
              color: b.accent,
              letterSpacing: 5,
              fontSize: 20,
              marginBottom: 22,
            }}
          >
            {kicker}
          </div>
        ) : null}

        {lines.map((l, i) => {
          const d = interpolate(frame, [6 + i * 6, 24 + i * 6], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.out(Easing.cubic),
          });
          return (
            <div
              key={i}
              style={{
                color: INK,
                fontSize: 82,
                fontWeight: 600,
                letterSpacing: -2,
                lineHeight: 1.08,
                opacity: d,
                transform: `translateY(${interpolate(d, [0, 1], [22, 0])}px)`,
              }}
            >
              {l}
            </div>
          );
        })}

        <div
          style={{
            color: b.muted,
            fontSize: 30,
            marginTop: 26,
            opacity: interpolate(frame, [22, 40], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          {subtitle}
        </div>

        <div
          style={{
            width: interpolate(frame, [16, 48], [0, 240], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.out(Easing.cubic),
            }),
            height: 3,
            background: `linear-gradient(90deg, transparent, ${b.accent}, transparent)`,
            margin: '38px auto 0',
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
