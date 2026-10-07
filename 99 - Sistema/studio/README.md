# Estúdio de motion — v1.7

O usuário continua pedindo em linguagem comum. O agente escolhe o caminho, executa comandos autorizados e mostra uma prévia.
Este módulo se soma à edição de fala da fábrica; não a substitui.

## Dois modos
**Fala primeiro (padrão para gravações):** roteiro como referência → erros/retomadas → silêncios → montagem fechada → transcrição retimada → ideias visuais → animações → som → revisão.
**Filme de motion:** referência/objetivo → linguagem → lista de estados → música/ritmo quando autorizados → quadros → animatic → cenas → revisão → exportação.

Nenhuma obrigação de ilustrar cada palavra, trocar de cena a cada dois segundos, ter música ou usar todos os materiais. `keep` é uma decisão válida.

## Entrada simples
> Edite minha gravação usando esta referência visual. Entenda o raciocínio das falas e crie cenas em código quando ajudarem. Não copie o conteúdo da referência. Mostre uma prévia antes de produzir o restante; preserve minhas preferências e o orçamento.

O agente carrega `workflows/MOTION_STUDIO.md`. Para configurações/contratos, lê `studio/CONTRACT.md`, não a biblioteca inteira.

## Comandos para o agente, não para o usuário leigo
- `python factory.py studio plan-check CAMINHO/plan.json`
- `python factory.py studio briefs CAMINHO/plan.json --outdir CAMINHO/briefs-v1`
- `python factory.py studio render CAMINHO/spec.json --inspect`
- Após revisar HTML, biblioteca e assets: `python factory.py studio render CAMINHO/spec.json --approve-bundle HASH --outdir CAMINHO/frames-v1 --frames 0,24,60`
- Render completo: mesmo comando sem `--frames`. Prever amostras e escolher explicitamente `--frame-budget`; não elevar limites sem decisão autorizada.
- Repetibilidade: `python factory.py studio render CAMINHO/spec.json --approve-bundle HASH --check-determinism`
- Revisão: `python factory.py studio sheets CAMINHO/draft.mp4 --outdir CAMINHO/evidence-v1 --max-samples 90 --strip-at 3.2`
- Batidas (opcional): `python factory.py studio beats CAMINHO/track.wav --output CAMINHO/beats.json`
- SFX (opcional): `python factory.py studio sfx CAMINHO/cues.json --output CAMINHO/sfx-v1.wav`
- Registro: `python factory.py studio review CAMINHO/plan.json CAMINHO/review.json --register`

`frames.json` completo é aceito por `tools/composite_motion.py` com o master/EDL corretos, a geometria compatível e a posição em frames. Isso mantém a voz. Uma prévia com poucos frames NÃO é compositável como se fosse completa.

`studio/examples/decision-flow.html` é uma demonstração conceitual original: fila de decisões → distribuição com critérios. Não é UI de produto, case real ou referência aprovada do cliente. O spec de exemplo contém o hash do HTML, que precisa ser atualizado e revisto quando o código muda.

## Instalação
O novo renderer usa Python + Playwright/Chromium + Pillow, com NumPy para subframes. Reutiliza o ambiente de motion, sem novo framework obrigatório. `factory.py dependencies --capability motion` mostra a preparação; `--apply` somente com autorização. Análise musical é opcional: `--capability studio-audio` propõe NumPy/librosa/soundfile. Não instala Remotion, HyperFrames ou plugins de posts.

## Limites reais
A revisão visual depende de o agente abrir as imagens e ter capacidade de ver o vídeo/trecho ou de solicitar revisão humana. O executor financeiro restrito da v1.6 continua sendo **texto/código**, não um adaptador de visão. Não o use para fingir que uma descrição de contact sheet foi vista. Consumo em sessões nativas fora desse executor não é coberto por seu teto monetário. O registro de crítica vincula arquivos e declarações, não prova que o modelo os examinou.

O renderer executa HTML/Canvas confiável/revisado, não vídeo gerativo nem máscaras/rastreamento 3D automáticos. Recursos externos e scripts importados são bloqueados; isso não o torna uma sandbox segura para código hostil. A renderização deve terminar antes de o arquivo `frames.json` completo existir. Pastas parciais indicam falha/pendência, não entrega.

## Teste local reproduzível
Sem instalar nada por conta própria: `python tests/smoke_studio.py --outdir CAMINHO-NOVO` depois de preparar as dependências autorizadas. O teste requer navegador, FFmpeg, NumPy, librosa, Pillow e Playwright. Em máquinas pequenas, limitar `OPENBLAS_NUM_THREADS=1` e `OMP_NUM_THREADS=1` no processo evita excesso de threads na análise numérica. O teste cria mídia sintética; não avalia fala real nem a qualidade artística de um modelo.
