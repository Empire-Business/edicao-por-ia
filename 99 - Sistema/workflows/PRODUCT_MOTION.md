# Workflow — Motion de produto/plataforma (UI recriada, proporções 16:9 + 9:16)

Receita extraída do job `jobs/omnx-sell-motion` (sessão de 2026-09-30, aprovada pelo usuário como padrão).
Resultado de referência: 19 cenas, 2min06s, 30 fps, duas proporções, lint zerado. Kit: `studio/product-motion/`.
Ferramenta: `python3 tools/product_motion.py` (new · build · check · snap · sheet · music · render).

## Quando usar
Pedido de "motion/vídeo da plataforma X mostrando as funções", sem filmagem de origem. Para motion sobre
fala gravada use `CREATE_JS_ANIMATIONS.md`; para linguagem nova com referência use `MOTION_STUDIO.md`.

## O que o usuário entrega (e como o prompt original foi lido)
Prompt-modelo: `studio/product-motion/PROMPT_MODELO.md`. Os seis ingredientes que fizeram dar certo:
1. **Fonte da verdade = repositório** do produto (GitHub; achar clone local ou `gh repo clone` com autorização). Telas e textos vêm do JSX, não dos prints.
2. **Identidade visual do produto** (DESIGN.md/tokens do repo) — fidelidade de marca é regra do formato e do pedido.
3. **Prints anexados** = ajuda de fidelidade (layout, dados, ordem). Vão para `assets/refs/`. Só entram como imagem no vídeo o que não dá para recriar (ex.: câmeras da call), recortado e limpo.
4. **"Motion bem feito, não compilação de prints"** → UI recriada em HTML/CSS e animada. Registrar em memória do formato (`motion.product_demo_style`).
5. **Cobertura**: "mostrar TUDO" → inventário completo de funções, depois cena por função. Registrar `content.coverage` no job.
6. **Duas proporções** (16:9 e 9:16) a partir da mesma fonte de cenas.
Se faltar o repositório ou o design, é a única pergunta essencial.

## Etapas
1. **Memória do formato** (`FORMAT_MEMORY.md`): salvar estilo/fidelidade/proporções/cobertura com a citação do usuário. Carregar o que já existe do formato.
2. **Inventário** (agente `Explore`, "very thorough", modelo barato): lista de cada item de menu, tela, abas, cards, KPIs, botões, badges, estados vazios, com **textos exatos em pt-BR** e caminho do arquivo. Pedir também tokens de design, tabs/rótulos truncados nos prints, lista de apps/arquétipos/etapas nomeadas, e o posicionamento do produto (PRD). Corrigir divergência print × código a favor do **código atual** (ex.: aba "Fala"/"Agente" mudou) e anotar em `decision_log.md`.
3. **Scaffold**: `product_motion.py new --format <id> --job-id <id>-motion --name "<Produto>" --video-name "<Nome do vídeo>" --repo <path> --fonts-from <dir>`. `--name` identifica a marca do produto; `--video-name` aparece no nome dos arquivos exportados e, se omitido, usa o ID do job. Preencher `src/brand.json` com os tokens REAIS (cores claro + escuro, fonte), copiar fontes woff2 e refs para dentro do trabalho. Logotipo/wordmark/monograma desligados por padrão; criar `partials/logo.html` somente se houver pedido explícito para esse vídeo. `partials/sidebar.html` usa identificação genérica de painel quando a logo estiver desligada (menu real, mesma ordem/seções).
4. **Roteiro/storyboard** (coordenador, não delegar): lista de cenas `sNN-id` com duração (4,5–10 s; total ≈ 1 min por 8–10 funções), headline de 1 linha com `<em>` dourado, e a ação que anima cada função (cursor clica, número conta, barra cresce, texto digita, aba troca, câmera aproxima). Agrupar por jornada do usuário: abertura → navegação → operação → análise → desenvolvimento → configuração → encerramento. Cenas escuras (`cls: dark-scene`) para telas escuras do produto. Preencher `scenes.json`.
5. **Cena-modelo antes de paralelizar.** O coordenador escreve 1–2 cenas completas (abertura + a mais complexa), roda `build` + `snap` nas duas proporções e corrige até ficar premium. Elas fixam o padrão que os outros copiam (ver `reference/omnx-sell-scenes/` para o nível esperado). Escrever/ajustar `SCENE_GUIDE.md` com as regras aprendidas.
6. **Cenas em ondas paralelas** (agentes `fork`/`motion-builder`, 3–5 cenas por agente, 4 agentes): cada um recebe o prompt com (a) o storyboard das suas cenas com labels e dados de exemplo, (b) caminhos dos JSX reais, (c) `SCENE_GUIDE.md`, (d) `SCENES=a,b OUT=build-fN` e pasta `qa/fN-*`, (e) "iterar com snapshots nas DUAS proporções até ficar premium", (f) relatório curto: arquivos, `check`, ressalvas. Cada agente só escreve as próprias cenas; não toca `base.css`/`build.mjs`/`scenes.json`/partials. Respeitar `method/EXECUTION_AND_COSTS.md` (orçamento/consentimento) antes de disparar.
7. **Integração (coordenador)**: `build` completo, `check` nas duas proporções, corrigir regras de estilo vertical entre cenas, abrir contact sheets de TODA a duração nas duas proporções (`snap --at` a cada ~3 s).
8. **Áudio**: sem narração por padrão (a headline carrega a história). Música: checar a preferência do formato/job antes. O usuário autorizou ElevenLabs → trilha original (`method/EXTERNAL_SERVICES.md`, sem citar artista/música no prompt). Senão, trilha licenciada em loop no compasso (`make_music.sh`: constantes BPM/primeiro tempo da faixa), duração = duração do filme, fade-out ≥ 3 s, `loudnorm` −16 LUFS. **Recalcular a trilha sempre que a duração mudar** (erro real: trilha de 129,8 s para filme de 125,8 s). Trilha foi o ponto fraco do v1: oferecer ajuste de música/SFX na revisão.
9. **Render**: `product_motion.py render <job> --kind preview` (qualidade `looks`; `delivery` só pedido). Os nomes incluem vídeo, proporção, formato e `PREVIEW_V<n>`. Depois `sheet` no MP4 real: o render pode divergir da prévia (câmeras que medem layout, fontes). Medir áudio (LUFS, pico, fade chega ao fim) e duração.
10. **QA**: preencher `qa/qa.json` (lint para 16:9/9:16, layout, contraste, revisão visual com frames, correções, áudio, cobertura × não mostrado) e `edit/decision_log.md`. Declarar o que não foi mostrado. Status "rascunho aguardando revisão"; sem ouvir/ver playback não afirmar aprovação.
11. **Aprender**: feedback do usuário → memória do formato (escopo job; promover ao formato só com aprovação explícita). Versão aprovada vira `approval.*` e referência para o próximo motion do mesmo formato.

Depois que os gates passarem e o usuário aprovar, exporte a entrega com `product_motion.py render <job> --kind final --version <n>`. O número deve coincidir com o preview aprovado; arquivos de preview e finais não são sobrescritos.

## Regras duras aprendidas (HyperFrames + GSAP)
- Nunca animar left/top/width/height; só x/y/scale/opacity/clipPath/filter. Barras: `scaleX` com `transform-origin:0 50%`.
- Todo CSS escopado por `[data-composition-id="<id>"]`; vertical: `.fmt-v [data-composition-id=...] .x` (nunca forma composta no mesmo elemento).
- Um `gsap.timeline({paused:true})` por cena, registrado em `window.__timelines[id]`. Sem `repeat:-1`, `Date`, `Math.random`. Texto que muda: `tl.call` ou onUpdate de objeto tweenado.
- Cena que mede layout deve chamar `window.__omnxShow(el)` (cena ainda inativa tem `display:none`).
- Espaço entre palavras de headline = `column-gap` flex (espaço final colapsa). Sem `<br>`.
- 16:9: telas de app autoradas em 1440 px, câmera ×1,2; texto efetivo ≥ 16 px. 9:16: **reorganizar** (painel inferior, cards empilhados, texto ≥ 26 px), nunca encolher o desktop.
- Movimento contínuo: nenhuma tela parada > ~1 s. Entrada 0,6 s, saída 0,5 s, cenas sobrepostas 0,4 s. Ease expo.out/power3.out; nada elástico exceto badges. Última cena sem fade de saída; encerramento limpo; logo final apenas se solicitada explicitamente para esse vídeo.
- Dados fictícios coerentes (empresa, pessoas, números); **nunca inventar função que não existe no código**; strings exatamente como na UI.
- `snapshot` sempre com `--describe false` (não enviar imagens a serviço externo). Avisos aceitáveis: sobreposição nos crossfades, texto cortado pela janela durante push-in intencional, rótulos muted ~3,4:1 fiéis ao produto.
- Node ≥ 22 (o job usou Node 24 via nvm); HyperFrames fixado em `0.8.92`.

## Aprendizados do segundo job (`jobs/omnx-gt3-motion`, 2026-10-01)
- **Dados privados nos prints**: quando o usuário pede dados fictícios, definir um ELENCO único no `SCENE_GUIDE.md` (empresa, usuário logado, pessoas com iniciais/cor, projetos, grupos, data do filme) antes de paralelizar; avatares de iniciais, nunca fotos; `assets/refs/` fica fora do git (`jobs/*/assets/refs/` no `.gitignore`).
- **Paleta: medir nos prints.** O código pode definir uma cor e a produção mostrar outra (branding por tenant sobrescreve `--primary`). Amostrar pixels dos prints (botão, item ativo, fundo, badges) e usar a aparência de produção; registrar a divergência e avisar o usuário.
- **Ícones**: `tools/lucide_extract.py <node_modules/lucide-react> src/lucide.json` dá o conjunto Lucide completo; `{{icon:nome}}` aceita qualquer ícone (sem desenhar à mão).
- **`src/lib.js` (`window.__pm`)**: helpers compartilhados (enter/exit/swap/click/focus/count/type, item ativo + scroll da sidebar). Reduz erro repetido nos agentes. Limites: `pt/click/focus` ignoram transforms → posicionar popovers com `left/top`; `focus` pode tirar a tela do quadro no 9:16 (limitar às bordas).
- **Canvas fixo**: 16:9 = 1440×704 (janela inteira visível, escala 1,2); 9:16 = 560×829 com o layout MOBILE real do app (barra inferior), não o desktop encolhido.
- **IDs de SVG únicos por cena** (`id="g-{{ARG}}-{{ID}}"`): gradiente/máscara com id repetido em duas cenas some quando a primeira está oculta.
- **Stacking**: elemento tweenado ganha `transform` → cria contexto de empilhamento; card arrastado precisa de `position:relative; z-index` na coluna de origem. `fromTo` manual em anel de clique: `immediateRender:false`.
- **Fonte de marca extra** (ex.: wordmark): declarar `@font-face` em `base.css` e usar por classe; declarar `font-family` nova dentro da cena dá erro de lint.
- **Marcar camadas intencionais**: `data-layout-allow-occlusion data-layout-allow-overlap` em modais/painéis; sobras de overlap sob modal são aceitas.
- **Pedir ao agente a lista do que divergiu** do roteiro e do código; revisar esses pontos (ex.: painel inventado) antes do render. 5 agentes × ~4 cenas levaram ~18 min.
- **Trilha**: `make_music.sh` agora repete o miolo da faixa quantas vezes for preciso para cobrir a duração.

## Aprendizados do terceiro job (`jobs/omnx-sdrai-motion`, 2026-10-01) — produto inacabado (código + mockups)
- **Duas fontes, um contrato**: quando o produto não está pronto, o VISUAL vem do mockup aprovado e os TEXTOS DE COMPORTAMENTO vêm do código quando o fluxo real é mais rico (ex.: diálogos de assumir/devolver conversa). O inventário marca cada tela como implementada / parcial / só mockup e isso vai para `analysis/feature_inventory.md` e `qa/qa.json`.
- **Mockup pode ser raster**: HTMLs que usam um PNG de fundo para o shell não trazem sidebar/topbar; ler o shell dos PNGs e amostrar cores em pixels. Mockups mobile "explicativos" não são UI: derivar o 9:16 do desktop.
- **Não promover promessa de mockup a fato**: percentuais de confiabilidade (uptime, RPO/RTO, "100% auditado") que o próprio repositório marca como não verificados ficam fora. Restos de anonimização (nomes de produto/segmento antigos) são trocados por descrições neutras.
- **Clone próprio do repositório** em `sources/repos/` (fora do git) em vez de mexer no clone de desenvolvimento do usuário, que pode estar atrás do remoto.
- **Elenco**: resolver colisões de nomes dos mockups (mesma pessoa como lead e como vendedor) no `SCENE_GUIDE.md` antes de paralelizar.
- **Efeitos inventados**: agentes tendem a criar "consequências" (número que sobe após um clique, selo de sucesso, toast). Pedir a lista no relatório e remover o que altera dados/afirma resultado sem fonte; estados de UI óbvios (botão vira "Inscrito") podem ficar se marcados como ilustrativos no QA.
- `pm.focus` agora limita a câmera às bordas da janela (três agentes tinham criado o mesmo helper local).

## Parada
Sem repositório/design acessível → pergunta única. Dependência ausente (Node/ffmpeg/hyperframes) → informar, não instalar sem autorização. Não usar prints como cenas; não copiar a marca de outro formato (cada plataforma usa a própria identidade).
