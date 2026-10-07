# Referências técnicas externas — consultadas em 26/09/2026

Estas fontes sustentam capacidades/ferramentas, não validam qualidade artística da skill.

1. Anthropic, Vision: https://platform.claude.com/docs/en/build-with-claude/vision
   Entrada de imagens para análise; limitações de precisão/localização. Motivo para inspecionar
   frames reais e não tratar regiões estimadas como rastreamento exato.
2. Anthropic, Coordinates and bounding boxes:
   https://platform.claude.com/docs/en/build-with-claude/vision-coordinates
   Pixels retornados referem-se à imagem processada; converter após considerar redimensionamento.
3. Anthropic, Models overview: https://platform.claude.com/docs/en/models/overview
   A página consultada lista entrada de texto/imagem e saída de texto nos modelos atuais.
   Escrever código/brief não equivale a gerar vídeo ou imagem nativamente. Verificar capacidades
   e disponibilidade no host antes de despachar. Não fixar nova promessa de modelo/preço.
4. Remotion, Animating properties: https://www.remotion.dev/docs/animating-properties
   Animação controlada por useCurrentFrame; mudanças fora do relógio dos frames podem tremular.
5. Google MediaPipe, Image segmentation:
   https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter
   Máscaras de regiões, incluindo pessoa/fundo, em imagens/frames/vídeo. É opção externa para
   recorte; não foi instalado ou testado neste pacote. Não equivale a tracking 3D de câmera.
6. OpenAI, AGENTS.md: https://developers.openai.com/codex/guides/agents-md
   Instruções locais descobertas pelo Codex; a configuração/permissão do ambiente ainda importa.
7. Claude Code, Memory: https://code.claude.com/docs/en/memory
   Leitura de AGENTS.md depende de versão/configuração/presença de CLAUDE.md. O import
   @AGENTS.md continua sendo um mecanismo documentado para compartilhar as mesmas regras.

## Material do usuário relevante (não pesquisa externa)
Metodologia de Headlines, v4.2, seção 4 (três canais, pp.15–16) e seção 10.6 (p.47):
visual tem função e deve sustentar a entrega; não acrescentar complexidade sem necessidade.
Esses princípios foram usados como ponte editorial. O novo módulo de direção espacial,
contratos de coordenadas e ferramentas são desenvolvimento desta revisão, não transcrição
nem capacidade comprovada pelos documentos de headlines.
