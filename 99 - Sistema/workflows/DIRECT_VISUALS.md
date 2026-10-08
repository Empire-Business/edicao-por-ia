# Workflow — Dirigir visuais a partir da fala e do cenário

## Entrada e saída
Entrada: pedido, formato ativo, padrão, master limpo com cortes aprovados, EDL, transcrição
retida com tempos finais, assets e referências acessíveis. Roteiro sem vídeo: entregar somente
storyboard provisório, sem afirmar posição, cor de luz ou timestamps observados.
Saída: mapa de cena, storyboard, briefs/specs, rascunho revisado quando as ferramentas existem,
pendências reais e registro de aprendizado. Não exigir formulário longo.

## Fluxo
1. Recuperar formato/feedback. Ler `method/VISUAL_DIRECTION.md`. Confirmar limites de geração,
   autonomia, orçamento e padrão. Não perguntar o que já está definido.
2. Fechar correção de fala, múltiplos vídeos e silêncios; renderizar um master limpo por filho.
   Recalcular transcrição com identificação correta das fontes. Conferir tempos e frases antes
   de declarar que a transcrição corresponde ao master. Manter referências ao material original.
3. Preparar evidência local (o agente preenche os caminhos existentes):
   ```bash
   python3 tools/visual_direction.py prepare --master jobs/ID/renders/clean.mp4 --edl jobs/ID/edit/edl.json --transcript jobs/ID/analysis/retimed.json --format FORMATO --child VIDEO --outdir jobs/ID/visual/context-v1 --confirm-final-timestamps
   ```
   `--confirm-final-timestamps` é uma confirmação operacional, não um alinhador automático.
   O programa recusa sobrescritas, tempos inválidos e frame budget excedido. Requer FFmpeg,
   FFprobe e Pillow instalados; não instala nada. Os limites são do lote, não da edição inteira.
   Se a inspeção detectar mudança dentro de um take, repetir `prepare` em pasta nova com
   `--extra-cut-frame N` para cada novo limite observado. Isso amplia o mapa sem mudar a EDL
   de fala nem inventar que a detecção foi automática.
4. Abrir realmente os frames com a capacidade visual do agente. A saída `scene-map.json` começa
   não revisada e SEM interpretação inventada. Produzir `scene-map-reviewed-v1.json`, usando o
   contrato de `visual/SPEC.md`. Identificar áreas a preservar e envelopes das inserções. Para
   gesto/movimento difícil, inspeção mais densa ou rastreamento externo; não extrapolar uma foto.
5. Ler TODAS as unidades de fala no contexto. Agrupar ideias, determinar função visual e decidir
   `keep` ou visual. Usar `visual/PLAN_TEMPLATE.json` como estrutura; todos os IDs precisam vir
   do contexto. O bloco pode ilustrar várias falas sem mudar a cena a cada frase. Uma inserção
   não cruza planos sem novo mapa de composição.
   Aplicar `method/EDITORIAL_REASONING.md`: forma da informação → mecanismo permitido pela
   receita → material correspondente → cue semântico no master final. Registrar no plano
   existente; `editorial_reasoning` é anotação opcional, não um requisito para jobs antigos.
6. Escolher arte e execução. Para estilo novo, criar um trecho piloto; para estilo aprovado,
   reutilizar. Escrever prompts concretos, não “faça uma ilustração incrível”. Materiais gerados
   e simulações não se tornam provas. Confirmar ferramenta existente antes de invocar.
7. Conferir plano e exportar briefs/specs locais:
   ```bash
   python3 tools/visual_direction.py check --context jobs/ID/visual/context-v1/context.json --scenes jobs/ID/visual/scene-map-reviewed-v1.json --plan jobs/ID/visual/plan-v1.json
   python3 tools/visual_direction.py export --context jobs/ID/visual/context-v1/context.json --scenes jobs/ID/visual/scene-map-reviewed-v1.json --plan jobs/ID/visual/plan-v1.json --outdir jobs/ID/visual/production-v1
   ```
   Exportar não gera uma ilustração neural nem renderiza os specs. Ler `pending`: briefs de VFX,
   imagem/vídeo generativo e componentes novos precisam da rota correspondente. Nunca tratar
   `structural_ok` como aprovação semântica, artística ou de publicação.
8. Specs suportados → `tools/render_motion.py` → `tools/composite_motion.py`, conforme
   `CREATE_JS_ANIMATIONS.md`. Posição usa o envelope máximo declarado; conferir alfa renderizado.
   Imagem gerada → verificar arquivo, registrar hash/proveniência → `proof-frame` ou composição
   autoral, sem chamar a ilustração de prova. Remotion/VFX → caminho separado, com mesma base,
   fps, áudio, duração e contratos de QA. Não afirmar execução de rota não disponível.
9. Reservar áreas para legenda desde o mapa; queimar legendas depois de visuais quando se usa
   cutaway. Verificar camada textual em cima da imagem. Se o master já tem legendas queimadas,
   usar uma cópia limpa ou ficar em overlay que respeite a região; não apagá-las acidentalmente.
10. Rever começo/meio/fim e momentos de movimento de CADA inserção no vídeo renderizado. Revisão
    em velocidade normal é obrigatória para qualidade de movimento; stills não comprovam ausência
    de tremulação. Verificar também sentido, dados, continuidade, áudio e legibilidade no celular.
    Localizar problemas por tempo/frame, fala/ID e beat/shot; registrar correção e resultado
    esperado no QA existente. Não usar cotas de movimento para substituir revisão semântica.
11. Registrar feedback e versões aprovadas. Corrigir somente cenas afetadas. Mudança de EDL,
    crop ou master invalida o plano espacial/temporal, mesmo se a duração não mudar.

## Critérios de parada
Dependência ausente: preservar corte limpo e produzir brief pendente; não simular sucesso.
Ambiguidade editorial relevante: uma pergunta objetiva. Efeito opcional ruim: retirar ou usar
fallback sem esconder downgrade. Não reduzir o padrão de qualidade só para preencher cenas.
Sem vídeo real: análise espacial pendente; storyboard pode continuar normalmente.

## Compatibilidade
AGENTS.md orienta Codex. CLAUDE.md importa as mesmas regras para Claude Code. Ambos utilizam
os mesmos arquivos e utilitários. A instalação do host ainda precisa oferecer leitura de imagem,
execução local e quaisquer geradores autorizados. Este workflow não cria essas permissões.

## Reference-driven studio extension (v1.7)
For supplied visual references, bespoke scenes, state lists or a showreel, route through `workflows/MOTION_STUDIO.md`. It adds a style guide, state list, reusable seek renderer, paginated evidence and bounded review. Do not skip locked speech timing, format context or costs.
