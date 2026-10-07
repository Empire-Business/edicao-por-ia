import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {FONT, INK, MONO, useBrand} from './theme';

export const NoteScene: React.FC<{
  title: string;
  bullets: string[];
  durationInFrames: number;
}> = ({title, bullets, durationInFrames}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const out = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp'},
  );
  const inn = interpolate(frame, [0, 16], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill
      style={{
        fontFamily: FONT,
        alignItems: 'center',
        justifyContent: 'center',
        opacity: out * inn,
      }}
    >
      <div style={{width: 1420}}>
        <div
          style={{
            fontFamily: MONO,
            color: b.accent,
            letterSpacing: 5,
            fontSize: 19,
            marginBottom: 18,
          }}
        >
          ATENÇÃO
        </div>
        <div
          style={{
            color: INK,
            fontSize: 62,
            fontWeight: 600,
            letterSpacing: -1.4,
            marginBottom: 52,
            transform: `translateY(${interpolate(inn, [0, 1], [20, 0])}px)`,
          }}
        >
          {title}
        </div>

        {bullets.map((t, i) => {
          const d = interpolate(frame, [14 + i * 12, 34 + i * 12], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.out(Easing.cubic),
          });
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 22,
                alignItems: 'center',
                padding: '22px 28px',
                marginBottom: 16,
                borderRadius: 14,
                background: 'rgba(255,255,255,0.035)',
                border: '1px solid rgba(255,255,255,0.07)',
                opacity: d,
                transform: `translateX(${interpolate(d, [0, 1], [-24, 0])}px)`,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 99,
                  background: b.accent,
                  boxShadow: `0 0 18px ${b.accent}`,
                  flex: '0 0 auto',
                }}
              />
              <div style={{color: b.muted, fontSize: 32, lineHeight: 1.35}}>
                {t}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
