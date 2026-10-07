import React from 'react';

export const INK = '#f4f6f5';
export const MUTED = '#93a29b';

export const FONT =
  'Inter, "Helvetica Neue", -apple-system, BlinkMacSystemFont, sans-serif';
export const MONO = 'ui-monospace, SFMono-Regular, Menlo, monospace';

// Dimensões do vídeo e do print normalizado
export const VW = 1920;
export const VH = 1080;
export const IMG_W = 1280;
export const IMG_H = 657;

// Moldura do navegador
export const K = 1.2;
export const FRAME_W = IMG_W * K; // 1536
export const FRAME_H = IMG_H * K; // 788.4
export const FRAME_X = (VW - FRAME_W) / 2; // 192
export const FRAME_Y = 44;
export const CHROME_H = 46;

export type Brand = {
  accent: string; // cor de destaque e dos números
  accentDeep: string; // variante escura para gradientes
  bg: string; // fundo do vídeo
  muted: string; // cor do texto secundário
  domain: string; // o que aparece na barra do "navegador"
  watermark: string; // marca d'água do canto
  logo: React.ReactNode; // marca da abertura
};

export const BrandContext = React.createContext<Brand | null>(null);

export const useBrand = (): Brand => {
  const b = React.useContext(BrandContext);
  if (!b) throw new Error('BrandContext ausente');
  return b;
};
