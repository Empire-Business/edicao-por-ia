import React from 'react';
import {Composition} from 'remotion';
import {Tutorial} from './Video';
import {VH, VW, type Brand} from './theme';
import {totalOf, type Scene} from './videos/types';
import {videos} from './videos';

// Cada vídeo vira um componente próprio via closure. Não dá para passar `brand`
// por defaultProps: o brand carrega o logo, que é um elemento React, e
// defaultProps é serializado para JSON pelo Remotion — elemento React quebra.
const make = (brand: Brand, scenes: Scene[]): React.FC =>
  function Video() {
    return <Tutorial brand={brand} scenes={scenes} />;
  };

export const RemotionRoot: React.FC = () => (
  <>
    {videos.map((v) => (
      <Composition
        key={v.id}
        id={v.id}
        component={make(v.brand, v.scenes)}
        durationInFrames={totalOf(v.scenes)}
        fps={30}
        width={VW}
        height={VH}
      />
    ))}
  </>
);
