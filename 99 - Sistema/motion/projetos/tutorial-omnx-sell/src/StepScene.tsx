import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {
  CHROME_H,
  FONT,
  FRAME_H,
  FRAME_W,
  FRAME_X,
  FRAME_Y,
  IMG_H,
  IMG_W,
  INK,
  K,
  MONO,
  useBrand,
} from './theme';
import type {Focus} from './videos/types';

type Props = {
  step: number;
  totalSteps: number;
  image: string;
  title: string;
  caption: string;
  focus?: Focus;
  zoom?: number;
  durationInFrames: number;
};

export const StepScene: React.FC<Props> = ({
  step,
  totalSteps,
  image,
  title,
  caption,
  focus,
  zoom = 1.8,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const b = useBrand();

  const cx = focus ? focus.x + focus.w / 2 : IMG_W / 2;
  const cy = focus ? focus.y + focus.h / 2 : IMG_H / 2;

  const zStart = 18;
  const zEnd = 72;
  const p = focus
    ? interpolate(frame, [zStart, zEnd], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: Easing.bezier(0.33, 0, 0.12, 1),
      })
    : 0;

  // Nunca amplia além do que mantém a área destacada inteira dentro da moldura.
  const fit = focus
    ? Math.min(
        FRAME_W / (focus.w * K * 1.12),
        FRAME_H / (focus.h * K * 1.12),
        zoom,
      )
    : zoom;
  const sTarget = K * Math.max(1, fit);
  const s = K + (sTarget - K) * p;
  // Não deixa a imagem sair da moldura (evita faixas pretas nas bordas).
  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  const txT = clamp(FRAME_W / 2 - cx * sTarget, FRAME_W - IMG_W * sTarget, 0);
  const tyT = clamp(FRAME_H / 2 - cy * sTarget, FRAME_H - IMG_H * sTarget, 0);
  const tx = txT * p;
  const ty = tyT * p;
  const breathe = 1 + Math.sin(frame / 55) * 0.004 * p;

  const hi = focus
    ? interpolate(frame, [zStart + 8, zStart + 26], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  const pulse = 0.55 + 0.45 * Math.sin(frame / 7);
  const strokeW = 3 / (s / K);

  const appear = interpolate(frame, [0, 14], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const out = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp'},
  );
  const opacity = appear * out;
  const rise = interpolate(appear, [0, 1], [26, 0]);

  return (
    <AbsoluteFill style={{fontFamily: FONT, opacity}}>
      <div
        style={{
          position: 'absolute',
          left: FRAME_X,
          top: FRAME_Y + rise,
          width: FRAME_W,
          height: FRAME_H + CHROME_H,
          borderRadius: 16,
          overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.10)',
          boxShadow: `0 50px 120px rgba(0,0,0,0.65), 0 0 0 1px ${b.accent}1a, 0 0 90px ${b.accent}1a`,
          background: '#181818',
        }}
      >
        <div
          style={{
            height: CHROME_H,
            background: '#232323',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
            display: 'flex',
            alignItems: 'center',
            paddingLeft: 18,
            gap: 8,
          }}
        >
          {['#ff5f57', '#febc2e', '#28c840'].map((c) => (
            <div
              key={c}
              style={{width: 11, height: 11, borderRadius: 99, background: c}}
            />
          ))}
          <div
            style={{
              marginLeft: 18,
              height: 26,
              flex: 1,
              marginRight: 18,
              borderRadius: 7,
              background: '#171717',
              border: '1px solid rgba(255,255,255,0.07)',
              display: 'flex',
              alignItems: 'center',
              paddingLeft: 12,
              color: b.muted,
              fontFamily: MONO,
              fontSize: 14,
            }}
          >
            {b.domain}
          </div>
        </div>

        <div
          style={{
            position: 'relative',
            width: FRAME_W,
            height: FRAME_H,
            overflow: 'hidden',
            background: '#1c1c1c',
          }}
        >
          <div
            style={{
              position: 'absolute',
              width: IMG_W,
              height: IMG_H,
              transformOrigin: '0 0',
              transform: `translate(${tx}px, ${ty}px) scale(${s * breathe})`,
            }}
          >
            <Img
              src={staticFile(image)}
              style={{width: IMG_W, height: IMG_H, display: 'block'}}
            />
            {focus ? (
              <div
                style={{
                  position: 'absolute',
                  left: focus.x,
                  top: focus.y,
                  width: focus.w,
                  height: focus.h,
                  border: `${strokeW}px solid ${b.accent}`,
                  borderRadius: 8 / (s / K),
                  boxShadow: `0 0 ${18 / (s / K)}px ${b.accent}${Math.round(
                    170 * pulse,
                  )
                    .toString(16)
                    .padStart(2, '0')}, 0 0 0 9999px rgba(0,0,0,${0.34 * hi})`,
                  opacity: hi,
                }}
              />
            ) : null}
          </div>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: FRAME_X,
          right: FRAME_X,
          top: FRAME_Y + FRAME_H + CHROME_H + 24 + rise / 2,
          display: 'flex',
          gap: 22,
          alignItems: 'flex-start',
        }}
      >
        <div
          style={{
            flex: '0 0 auto',
            width: 62,
            height: 62,
            borderRadius: 16,
            background: `linear-gradient(160deg, ${b.accent}, ${b.accentDeep})`,
            color: b.bg,
            fontSize: 30,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 12px 34px ${b.accent}4d`,
          }}
        >
          {step}
        </div>
        <div style={{flex: 1}}>
          <div
            style={{
              color: INK,
              fontSize: 38,
              fontWeight: 600,
              letterSpacing: -0.6,
              lineHeight: 1.1,
            }}
          >
            {title}
          </div>
          <div
            style={{
              color: b.muted,
              fontSize: 25,
              lineHeight: 1.32,
              marginTop: 10,
              maxWidth: 1380,
            }}
          >
            {caption}
          </div>
        </div>
        <div
          style={{
            flex: '0 0 auto',
            color: b.muted,
            fontFamily: MONO,
            fontSize: 20,
            paddingTop: 14,
            opacity: 0.75,
          }}
        >
          {String(step).padStart(2, '0')} / {String(totalSteps).padStart(2, '0')}
        </div>
      </div>
    </AbsoluteFill>
  );
};
