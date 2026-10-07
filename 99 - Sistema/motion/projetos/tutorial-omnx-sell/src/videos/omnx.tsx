import React from 'react';
import type {Brand} from '../theme';
import {S, type Scene} from './types';

export const omnxBrand: Brand = {
  accent: '#C9A24B',
  accentDeep: '#8A6A2A',
  bg: '#0d0b08',
  muted: '#a39a86',
  domain: 'sell.omnx.pro',
  watermark: 'omnx sell',
  logo: (
    <svg width="78" height="78" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="#C9A24B" />
      <path d="M8 12h8M12 8v8" stroke="#0d0b08" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
};

const P = 'analise/';

export const omnxScenes: Scene[] = [
  {
    kind: 'title',
    durationInFrames: S(4),
    kicker: 'OMNX SELL · PILOTO',
    title: 'Análise de Conversas',
    subtitle: 'veja como cada call vira nota, dores e plano de ação',
  },
  {
    kind: 'step',
    durationInFrames: S(6),
    step: 1,
    image: P + '01-lista.jpg',
    title: 'Abra "Análise de Conversas"',
    caption: 'No menu lateral, em "Operação", clique em "Análise de Conversas" para ver todas as calls já analisadas.',
    focus: {x: 9, y: 276, w: 160, h: 24},
    zoom: 1.25,
  },
  {
    kind: 'step',
    durationInFrames: S(7),
    step: 2,
    image: P + '01-lista.jpg',
    title: 'Confira o resumo do período',
    caption: 'Quatro cartões mostram quantas conversas foram analisadas, a nota média, as boas (8,0+) e as abaixo de 7,0.',
    focus: {x: 254, y: 154, w: 953, h: 77},
    zoom: 1.6,
  },
  {
    kind: 'step',
    durationInFrames: S(7),
    step: 3,
    image: P + '01-lista.jpg',
    title: 'Filtre do jeito que precisar',
    caption: 'Busque por lead ou vendedor e filtre por "Cargo", "Formato", "Período" e "Nota".',
    focus: {x: 254, y: 94, w: 953, h: 47},
    zoom: 1.6,
  },
  {
    kind: 'step',
    durationInFrames: S(8),
    step: 4,
    image: P + '01-lista.jpg',
    title: 'Leia a lista de conversas',
    caption: 'Cada linha traz título, objeções e dores encontradas, duração, data, participantes, tipo, desfecho e nota.',
    focus: {x: 254, y: 262, w: 953, h: 240},
    zoom: 1.6,
  },
  {
    kind: 'step',
    durationInFrames: S(6),
    step: 5,
    image: P + '01-lista.jpg',
    title: 'Traga uma gravação nova',
    caption: 'Use "Importar gravação" para enviar uma call que aconteceu fora da plataforma e analisá-la também.',
    focus: {x: 1064, y: 31, w: 143, h: 28},
    zoom: 1.9,
  },
  {
    kind: 'step',
    durationInFrames: S(7),
    step: 6,
    image: P + '02-detalhe.jpg',
    title: 'Abra uma conversa',
    caption: 'Ao clicar numa linha, você vê a análise em quatro abas: "Análise", "Transcrição", "Oráculo" e "Plano de ação".',
    focus: {x: 254, y: 111, w: 953, h: 27},
    zoom: 1.8,
  },
  {
    kind: 'step',
    durationInFrames: S(8),
    step: 7,
    image: P + '02-detalhe.jpg',
    title: 'Veja nota, dores e objeções',
    caption: 'Aqui aparecem a "Nota da reunião" e os contadores de "Dores", "Objeções", "Próximos passos" e "Fora da faixa".',
    focus: {x: 254, y: 223, w: 953, h: 78},
    zoom: 1.7,
  },
  {
    kind: 'step',
    durationInFrames: S(8),
    step: 8,
    image: P + '02-detalhe.jpg',
    title: 'Leia o "Resumo da IA"',
    caption: 'A IA resume o contexto do cliente e o que ele quer resolver, sem você precisar rever a gravação inteira.',
    focus: {x: 254, y: 323, w: 953, h: 235},
    zoom: 1.3,
  },
  {
    kind: 'note',
    durationInFrames: S(7),
    title: 'Bom saber',
    bullets: [
      'Reunião sem lead vinculado fica "Sem nota" e não afeta a média.',
      'A nota de venda só existe para calls ligadas a um lead.',
      'Use os filtros de período para comparar semanas.',
    ],
  },
  {
    kind: 'title',
    durationInFrames: S(4),
    kicker: 'PRONTO',
    title: 'Toda call, analisada',
    subtitle: 'do resumo ao plano de ação, em um só lugar.',
  },
];
