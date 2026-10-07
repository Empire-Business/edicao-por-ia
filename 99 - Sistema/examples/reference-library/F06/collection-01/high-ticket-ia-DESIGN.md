# DESIGN.md — Design System do site High Ticket IA

**Atualizado em:** 15/09/2026 às 14h06 BRT
**Status:** Aprovado (decisão do usuário: "Nubank roxo, fundo claro")

Referência estética: deck comercial v24 (roxo Nubank, Manrope, kickers mono, itálico roxo, sombras roxas) + estrutura de seções e prova quantificada de viverdeia.ai. Fonte de verdade visual deste projeto — nenhum componente usa cor, fonte ou espaçamento fora daqui.

---

## 1. Regras inegociáveis

1. **Roxo `#820AD1` é a cor de ação e de marca.** Botões primários, links de destaque, selos. Nunca como fundo de seção inteira em texto longo.
2. **Sem gradientes de texto.** Sem glassmorphism pesado. **Sombras sempre tingidas de roxo** (`rgba(130,10,209,…)`), nunca cinza/preto neutro.
3. **Sem exclamações na copy.** Tom editorial, direto, confiante.
4. **Fundo claro por padrão** (`#FFFFFF` / `#F7F4FB`). Seções escuras (`#17092C`) são exceção pontual para contraste (ex: bloco OMNX Clone e/ou footer) — no máximo 2 por página.
5. **Um destaque por seção** (palavra em itálico roxo, número grande ou selo). Nunca dois competindo.
6. Toda cor vem dos tokens abaixo via Tailwind (`@theme`) — proibido hex arbitrário no código.

## 2. Cores (tokens)

| Token | Hex | Uso |
|-------|-----|-----|
| `brand` | `#820AD1` | Cor primária: CTAs, links, selos, ícones de destaque, itálico de ênfase |
| `brand-deep` | `#5C0F8B` | Base do gradiente do CTA, hover/ativo do primário |
| `brand-ink` | `#3E1874` | Texto forte em seções tint, detalhes |
| `brand-soft` | `#D2A5FF` | Ilustrações, gráficos, detalhes em fundo escuro |
| `brand-tint` | `#E9DFF6` | Fundos de destaque suaves (cards, eyebrow chips, faixas) |
| `brand-dim` | `rgba(130,10,209,0.08)` | Callouts, banners, card em destaque (fundo roxo 8%) |
| `ink` | `#17092C` | Ultraviolet: texto principal (quase-preto roxo) + fundo das seções escuras |
| `bg` | `#FFFFFF` | Fundo padrão |
| `bg-subtle` | `#F7F4FB` | Fundo alternado de seções (tinta roxa sutil, não cinza neutro) |
| `card` | `#FFFFFF` | Cards em fundo subtle |
| `line` | `rgba(23,9,44,0.10)` | Hairlines/bordas (1px) |
| `text` | `#17092C` | Texto primário |
| `text-secondary` | `#5A4A6E` | Texto secundário (contraste AA sobre branco) |
| `success` | `#0C7A3A` | Checks de "incluso" |
| `danger` | `#D01D1C` | Preço riscado, "não incluso" |
| `on-dark` | `#FFFFFF` | Texto em seções escuras |
| `on-dark-secondary` | `#C9B8DB` | Texto secundário em seções escuras |

Sombras (tokens `--shadow-*`): `card` `0 2px 12px rgba(130,10,209,0.08)` · `card-hover` `0 12px 32px rgba(130,10,209,0.12)` · `glow` `0 0 32px rgba(130,10,209,0.18)`.

## 2.1 Slogan

**"Operada por IA. Feita para humanos."** Definido pelo usuário em 29/08/2026 como título da seção "como funciona" e candidato a slogan da marca. Sempre nas duas frases, com a segunda em destaque roxo.

## 3. Tipografia

- **Fonte principal: Manrope** (next/font/google), pesos 300–800. **JetBrains Mono** para microcopy (kickers, labels, footnotes), números de métricas e preços.
- Escala fluida tokenizada no `@theme` (utilitários `text-display`, `text-h2`, etc. — proibido clamp arbitrário repetido no código):

| Estilo | Utilitário | Tamanho | Peso | Line-height | Tracking |
|--------|-----------|---------|------|-------------|----------|
| Display (H1) | `text-display` | `clamp(2.75rem, 6.5vw, 5rem)` | 800 | 1.02 | -0.035em |
| Display hero (H1 da home) | `text-display-hero` | `clamp(2.5rem, 4.6vw, 4rem)` | 800 | 1.05 | -0.035em |
| H2 | `text-h2` | `clamp(2rem, 4.5vw, 3.25rem)` | 800 | 1.06 | -0.03em |
| H3 | `text-h3` | `clamp(1.25rem, 2vw, 1.5rem)` | 700 | 1.3 | -0.01em |
| Lead | `text-lead` | `clamp(1.05rem, 1.6vw, 1.32rem)` | 400 | 1.6 | 0 |
| Métrica | `text-metric` | `clamp(2.2rem, 5vw, 3.6rem)` | 800 (mono) | 1 | -0.03em |
| Kicker/eyebrow | componente `Eyebrow` | 11px mono | 500 | 1 | +0.34em, uppercase |
| Body | `text-base` | 16px | 400 | 1.6 | 0 |
| Footnote | — | 11px mono | 400 | — | +0.06em |

- **Ênfase em títulos: uma palavra em itálico roxo** (componente `Mark`) — assinatura do deck oficial.
- O hero da home usa `text-display-hero` (não `text-display`) sobre a arte própria do ecossistema HTAI. Em `lg+`, a ilustração preenche o fundo e preserva o respiro à esquerda para a copy; no mobile, a versão vertical entra abaixo da copy, sem disputar leitura com título e CTA. O teto de 4rem mantém cada linha do `LineMask` inteira em desktops.
- Medida máxima de texto corrido: **68ch**. Nunca linha de texto corrido full-width.

## 4. Espaçamento e layout

- Base 4px. Seções: `py-20 md:py-32` (80px/128px).
- Container: máx **1240px**, padding lateral `px-5 md:px-8`.
- Hairlines 1px `line` como separadores ("réguas de revista").
- **Atmosfera roxa** (prop `atmosfera` do `Section`): radiais roxos suaves fixos no hero e no CTA final — `ellipse 55% 40% at 12% 8%` 7% e `ellipse 45% 35% at 90% 85%` 5%.
- Grid de cards: 12 colunas desktop, gap 24px; bento permitido na seção de pilares/plataformas.
- Breakpoints: mobile 375 (base), `md` 768, `lg` 1024, `xl` 1280.

## 5. Componentes base

- **Button primário:** pill (`border-radius: 999px`), gradiente vertical `brand` → `brand-deep`, highlight inset `0 1px rgba(255,255,255,0.18)`, sombra roxa `0 4px 16px rgba(130,10,209,0.28)`, texto branco, padding `14px 28px`, peso 600; hover → sobe 2px e sombra cresce; focus ring `brand-soft`.
- **Button secundário:** pill, transparente, borda 1px `line` → hover borda `brand`, texto `brand`, sobe 2px com `shadow-card`.
- **Eyebrow (kicker):** JetBrains Mono 11px/500, uppercase, tracking 0.34em, `text-secondary`, traço roxo 34px×1px à esquerda. Variante chip: pill `brand-tint`/`brand-ink`, tracking 0.22em.
- **Card:** bg `card`, borda 1px `line`, radius **24px**, padding 32px, `shadow-card`; hover: borda `brand` 35%, translateY(-4px), `shadow-card-hover`.
- **Callout:** barra esquerda 2px `brand`, fundo `brand-dim`, radius 16px só à direita (citações e frases-chave).
- **Inputs (quando houver):** radius **12px**, borda `line`, focus ring `brand`.
- **Badge/selo:** pill mono 11px uppercase tracking 0.22em, `brand-tint` + `brand-ink`.
- **Header:** fixo, bg `rgba(255,255,255,0.85)` + `backdrop-blur`, hairline inferior; logo à esquerda, nav centro, CTA pill à direita; barra de scroll-progress em gradiente `brand-deep` → `brand`. Menu mobile: sheet lateral.
- **Footer:** fundo `ink` (seção escura), texto `on-dark-secondary`, logo oficial sobre seu fundo claro, hairlines.
- **PlanCard (v24):** cartão em cópia integral da apresentação comercial v24 (decisão do usuário em 15/09/2026): kicker mono "preço normal", preço em Manrope 800 com os centavos em `<small>`, lista com marcador `+` (`✓` no destaque), raio 36px, altura mínima 620px no desktop e sombra `0 22px 70px rgba(44,21,72,.09)`. O plano em destaque usa gradiente `#1A0828 → #56118C → #8A18D7`, elevação de 10px e selo preto "destaque", sem CTA dentro do card.
- **Faixa de lançamento (LaunchOffer):** palco em gradiente `#0E0715 → #2A0A45 → #7A16C4` com círculo claro no canto, cards em vidro (blur 8px) e o Company em branco elevado, seguido da âncora escura. Cards e palco usam 1224px de largura (saída de 24px além do container) a partir de 1240px de viewport, que é a largura do v24 e evita a quebra de linha dos preços; abaixo disso voltam ao container padrão.

## 6. Motion (CSS-only — sem framer-motion/GSAP)

- Easing único: `cubic-bezier(0.16, 1, 0.3, 1)` (token `--ease-editorial`).
- Só `transform`, `opacity` e `filter`. Durações: 200–300ms (micro), 950ms (reveals).
- **Reveal:** IntersectionObserver, fade + translateY(38px→0) + blur(8px→0), dispara uma vez a 15% visível, stagger 75–140ms entre irmãos.
- **Máscara de linha (componente `LineMask`, hero da home):** cada linha do título sobe de translateY(112%) dentro de overflow hidden, 1050ms, delay 180ms + 140ms por linha.
- **Marquee** (logo wall / lista de ferramentas substituídas): CSS puro, conteúdo duplicado com `aria-hidden`, pausa no hover.
- **CountUp** para métricas (easeOutCubic, rAF).
- `prefers-reduced-motion`: desliga tudo globalmente. `animation-timeline: view()`/`scroll-timeline` com fallback `@supports`.

## 7. Iconografia e imagens

- Ícones: `lucide-react` apenas, traço 1.5px, cor `brand` ou `ink`.
- Logo oficial: `public/brand/high-ticket-ia.png`, fornecido pelo usuário. É usado no cabeçalho e no rodapé, preservando o fundo claro da arte original.
- Plataformas: mini-mockups de UI desenhados em CSS (estilo bento do viverdeia.ai) na v1 — nunca ilustração genérica de stock.
- Fotos: permitidas apenas no bloco do fundador (`src/components/site/founder.tsx`), servidas por `next/image` com `width`/`height` explícitos. Exceção autorizada pelo usuário em 29/08/2026; fora dessa seção, a regra de não usar foto continua valendo.
- **Hero da home:** a mídia proprietária do ecossistema HTAI fica em `public/hero/high-ticket-ia-hero-desktop.webp` (1672×941) e `public/hero/high-ticket-ia-hero-mobile.webp` (941×1672), exportadas das artes entregues pelo usuário. São decorativas, portanto usam `alt` vazio; título, descrição e CTA seguem no HTML para leitores de tela e SEO.
- Logos de marca do portfólio EMPIRE ficam em `public/brand/`. Marca sem arquivo de logo cai no tratamento tipográfico do `BrandGrid`, nunca em logo improvisado.

## 8. Tom visual por seção da Home (mapa claro/escuro)

Atualizado em 29/08/2026, com a reconstrução da home sobre a copy base da EMPIRE:

Header claro → Hero claro (sem eyebrow) com faixa de autoridade → Marquee `bg-subtle` → Diagnóstico `bg-subtle` → Origem claro (sem os cards do portfólio) → Diferencial `bg-subtle` → **OMNX Clone (ESCURO `ink`)** → Três pilares claro → Componentes da plataforma `bg-subtle` (linhas alternadas) → Como funciona claro → Planos claro (com o card High Ticket IA Partner em `ink`) → Tabela de substituição `bg-subtle` → Garantia claro com card `brand-tint` → Marcas claro → **Fundador (ESCURO `ink`)** → FAQ `bg-subtle` → CTA final claro → **Footer (ESCURO `ink`)**.

O limite de duas seções escuras por página conta OMNX Clone e Fundador. O card do High Ticket IA Partner é um bloco `ink` dentro de uma seção clara, não uma seção escura, e existe para o programa de revenda ler como categoria separada, não como o degrau de cima da escada de planos.
