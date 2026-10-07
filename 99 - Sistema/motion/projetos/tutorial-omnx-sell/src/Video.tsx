import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Background} from './Background';
import {NoteScene} from './NoteScene';
import {StepScene} from './StepScene';
import {TitleScene} from './TitleScene';
import {BrandContext, MONO, type Brand} from './theme';
import {stepsOf, type Scene} from './videos/types';

export const Tutorial: React.FC<{brand: Brand; scenes: Scene[]}> = ({
  brand,
  scenes,
}) => {
  const total = stepsOf(scenes);
  let cursor = 0;

  return (
    <BrandContext.Provider value={brand}>
      <AbsoluteFill style={{backgroundColor: brand.bg}}>
        <Background />

        {scenes.map((scene, i) => {
          const from = cursor;
          cursor += scene.durationInFrames;
          return (
            <Sequence
              key={i}
              from={from}
              durationInFrames={scene.durationInFrames}
              layout="none"
            >
              {scene.kind === 'title' ? (
                <TitleScene
                  kicker={scene.kicker}
                  title={scene.title}
                  subtitle={scene.subtitle}
                  durationInFrames={scene.durationInFrames}
                />
              ) : scene.kind === 'note' ? (
                <NoteScene
                  title={scene.title}
                  bullets={scene.bullets}
                  durationInFrames={scene.durationInFrames}
                />
              ) : (
                <StepScene
                  step={scene.step}
                  totalSteps={total}
                  image={scene.image}
                  title={scene.title}
                  caption={scene.caption}
                  focus={scene.focus}
                  zoom={scene.zoom}
                  durationInFrames={scene.durationInFrames}
                />
              )}
            </Sequence>
          );
        })}

        <div
          style={{
            position: 'absolute',
            right: 40,
            bottom: 26,
            fontFamily: MONO,
            fontSize: 17,
            color: brand.muted,
            opacity: 0.45,
            letterSpacing: 1.5,
          }}
        >
          <span style={{color: brand.accent}}>{brand.watermark}</span> · tutorial
        </div>
      </AbsoluteFill>
    </BrandContext.Provider>
  );
};
