# Kit — motion de plataforma (UI recriada)

Origem: `jobs/omnx-sell-motion` (aprovado). Método: `workflows/PRODUCT_MOTION.md`. Prompt: `PROMPT_MODELO.md`.

- `kit/src/` — o que `tools/product_motion.py new` copia para o job: `build.mjs` (uma fonte de cenas → `build/h` 1920×1080 e `build/v` 1080×1920), `base.css` (moldura papel/grade, legenda `.cap`, janela `.win`/`.cam`, sidebar, cards, badges, botões, tabs, cursor), `brand.json` (tokens reais do produto → `:root` + `@font-face`), `icons.mjs` (Lucide, só acrescentar), `partials/` (logo, sidebar, cursor), `scenes/s01-intro.html`, `make_music.sh`, `SCENE_GUIDE.md`.
- `reference/omnx-sell-scenes/` — padrão de qualidade a igualar: mecanismos históricos de abertura (logo não é herdada), agenda (cursor+modal), sala escura com Copiloto (câmera/painéis), análise (contagens/barras), `scenes.json`, `job.yaml`, `qa.json` e o `SCENE_GUIDE.md` original. Leia no máximo 2 cenas.
- Fluxo: `new` → preencher `brand.json`/assets → storyboard + cenas-modelo → `build`/`snap` (iterar) → ondas paralelas → `check` → `music` → `render` → `sheet` → `qa.json`.
