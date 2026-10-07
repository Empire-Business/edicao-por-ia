import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {useBrand} from './theme';

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const drift = Math.sin(frame / 90) * 40;
  const a = b.accent;

  return (
    <AbsoluteFill style={{backgroundColor: b.bg}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(900px 620px at ${18 + drift / 8}% -10%, ${a}26, transparent 70%),
             radial-gradient(760px 560px at 105% 115%, ${a}1a, transparent 68%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
          maskImage: 'radial-gradient(1400px 900px at 50% 40%, black, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(1400px 900px at 50% 40%, black, transparent 80%)',
        }}
      />
      <div style={{position: 'absolute', inset: 0, boxShadow: 'inset 0 0 260px rgba(0,0,0,0.85)'}} />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 0,
          height: 4,
          background: `linear-gradient(90deg, transparent, ${a}55, transparent)`,
        }}
      />
    </AbsoluteFill>
  );
};
