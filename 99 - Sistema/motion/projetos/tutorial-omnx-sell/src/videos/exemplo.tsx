import React from 'react';
import type {Brand} from '../theme';
import {S, type Scene} from './types';

// ---------------------------------------------------------------------------
// MODELO. Duplique este arquivo para cada vídeo, registre em videos/index.ts
// e apague este exemplo quando não precisar mais dele.
//
// `accent` é a cor da marca do produto que aparece no vídeo — ela pinta o
// número do passo, o retângulo de destaque, o brilho da moldura e o fundo.
// Pegue a cor do botão primário da própria interface: o vídeo passa a parecer
// uma extensão do produto em vez de um template genérico.
// ---------------------------------------------------------------------------

export const exemploBrand: Brand = {
  accent: '#3ECF8E',
  accentDeep: '#22a06b', // variante escura, para o gradiente do número
  bg: '#0b0f0d', // fundo do vídeo: quase preto, puxando para o accent
  muted: '#93a29b', // texto secundário — precisa ler bem sobre o bg
  domain: 'exemplo.com', // aparece na barra do "navegador" desenhado
  watermark: 'exemplo', // marca d'água discreta no canto
  logo: (
    <svg width="78" height="78" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="#3ECF8E" />
    </svg>
  ),
};

const P = 'exemplo/'; // pasta dentro de public/

export const exemploScenes: Scene[] = [
  {
    kind: 'title',
    durationInFrames: S(4),
    kicker: 'TUTORIAL PASSO A PASSO',
    title: 'Título em até duas linhas\ncom quebra manual',
    subtitle: 'a promessa do vídeo em uma frase',
  },
  {
    kind: 'step',
    durationInFrames: S(7),
    step: 1,
    image: P + '01-primeira-tela.jpg',
    title: 'O que fazer neste passo',
    caption:
      'Uma ou duas frases dizendo exatamente onde clicar e por quê. Cabem duas linhas — passou disso, corte.',
    // Coordenadas em pixels do print normalizado (1280x657).
    // Pegue com getBoundingClientRect() na hora da captura — ver references/captura.md.
    focus: {x: 100, y: 200, w: 300, h: 40},
    zoom: 1.8, // teto de zoom; o componente reduz sozinho se o destaque não couber
  },
  {
    kind: 'note',
    durationInFrames: S(7),
    title: 'Um alerta que vale a pena reter',
    bullets: [
      'Três itens no máximo — mais que isso ninguém lê.',
      'Cada um em uma linha, direto ao ponto.',
      'Use para segurança, custo ou pegadinha comum.',
    ],
  },
  {
    kind: 'title',
    durationInFrames: S(4),
    kicker: 'PRONTO',
    title: 'O que a pessoa conseguiu',
    subtitle: 'e qual é o próximo passo dela.',
  },
];
