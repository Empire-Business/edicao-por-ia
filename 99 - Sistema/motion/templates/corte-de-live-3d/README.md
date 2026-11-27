# F22 Corte de Live 3D — modelo de composição

Código-base do formato **F22 Corte de Live 3D** (receita `patterns/f22-corte-de-live-3d-v1.yaml`), derivado da edição de
exemplo E119 (prévia aprovada pelo autor em 27/11/2026; vídeo em
`examples/reference-library/F22/corte-de-live-3d/reference.mp4`).
Os textos, tempos, falas, provas, paleta e fontes que aparecem nos arquivos são **do exemplo**: cada trabalho troca por
seus próprios. Pessoas, nomes e assunto do exemplo não são padrões; cores e fontes vêm da ID escolhida.

## Como usar num trabalho

Copiar estes arquivos para `jobs/<trabalho>/src/` e preencher, nesta ordem:

| Arquivo | O que faz | O que o trabalho preenche |
|---|---|---|
| `make_edl.py` | EDL a partir das palavras reais da transcrição da fonte; bordas ajustadas pela energia da voz (sem cortar sílabas), pausas internas > 0,15 s cortadas, tudo quantizado a 30 fps | Fonte (`SRC`), transcrição (`analysis/source.transcript.json`), áudio limpo para o envelope, `TAKES` (quem fala, cena, primeira/última palavra e o texto conferido) |
| `make_voice.py` | Voz: corte pelo EDL com fades curtos, mesmo nível por pessoa, HPF + EQ de clareza + compressão suave, −16 LUFS, limitador | Janela de áudio isolada (`audio/<janela>-el.wav`) e o deslocamento `OFF` em segundos da fonte |
| `make_media.py` | Masters dos quadros da live (recorte por pessoa, ampliação lanczos, redução de blocos, nitidez suave, quadros exatos do EDL) e quadros de vitrine | Recortes (`CROPS`) de cada pessoa na live e as entregas próprias usadas como prova |
| `make_assets.py` | Texturas determinísticas (sequências JPG por quadro) das provas, fontes da ID, fonte *typeface* para texto 3D (fontTools) e cópia local do three.js r186 + addons e do GSAP | Provas (vídeo longo 16:9 e vídeos curtos 9:16 **do próprio usuário, editados pelo Cortez, sem logotipos de terceiros**) e os caracteres do texto 3D |
| `index.tpl.html` | Composição HyperFrames: GSAP pausado em `window.__timelines.main`; cena three.js (ESM, importmap) com EffectComposer (RenderPass, UnrealBloom, Bokeh, Output) guiada pelo evento `hf-seek` — parede viva de provas, tela 3D com reflexo, celulares em leque, palavra-chave em texto 3D, CTA com celulares | Paleta/fontes da ID, nomes e papéis de quem fala, cenas e rótulos honestos ("editado pelo Cortez") |
| `build.py` | Gera `comp/index.html`, `analysis/motion_plan.json`, `scene_plan.json` e `caption_groups.json` a partir do EDL e da transcrição da voz final (tempos = palavras faladas) | Âncoras de cena (`W('palavra')`), títulos (`HEADS`), *punch-ins*, correções de transcrição (`FIXES`) e o texto do CTA |
| `mix.py` | Trilha editada em compassos com a virada no momento-chave, ~22 dB abaixo da voz com compressão lateral, CTA mais alto, efeitos discretos; final −15 LUFS | Trilha (própria/licenciada), deslocamento da virada e lista de efeitos |

Ordem de execução (a partir de `jobs/<trabalho>`): `make_edl.py` → `make_voice.py` → `make_media.py` → `make_assets.py` →
transcrever `renders/voice.wav` com `tools/transcribe.py` (→ `analysis/transcript_final_voice.json`) → `build.py` →
`npx -y hyperframes@0.8.92 render comp -o renders/picture.mp4 -w 4 --video-frame-format png --crf 12` → `mix.py` →
juntar imagem e mix com `ffmpeg` e nomear com `tools/output_naming.py`.

## Armadilhas já resolvidas no exemplo

- O filtro `volume` do ffmpeg com expressão usa ganho **linear**, não dB: converter (`10 ** (dB / 20)`) e conferir o nível
  da trilha sozinha (≈ −37/−38 LUFS sob a fala).
- Câmera three.js em escala de pixels (fov 30, distância = 960 / tan 15°): 1 unidade = 1 px no plano z = 0. A abertura do
  Bokeh precisa ser minúscula nessa escala (≈ 2e-5 no fundo, ≈ 3,5e-6 quando a prova está em foco), senão a prova borra.
- Tudo é função do tempo do quadro: sem relógio, sem `requestAnimationFrame` próprio; `Math.random` com semente fixa;
  vídeos dentro do 3D são sequências JPG indexadas por `floor(t * 30)`.
- Vídeos `<video class="clip">` precisam de quadros-chave densos (`-g 15`) e de 1 s extra no fim (`tpad`) para não
  ficarem pretos no CTA.
- Em GSAP 3, não somar `transform` de CSS com `y/yPercent` no mesmo elemento; estados iniciais com `gsap.set` fora da
  linha do tempo; cada entrada termina antes da saída.
- O Whisper erra nomes em áudio cortado: a legenda usa o texto conferido na transcrição contínua da fonte.
- CTA: a fala termina, a mensagem inteira fica escrita no cartão final com o botão "Saiba mais" e o vídeo acaba ali.
