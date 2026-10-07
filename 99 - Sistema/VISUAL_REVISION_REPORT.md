# Revisão 1.5.0 — Direção visual semântica e espacial

## Base
Pacote recebido: claude-video-factory-v1.4.0.zip. O Roteirista Universal permanece separado:
estende-se o planejamento visual dele com o arquivo DIRECAO_VISUAL_PARA_AGENTES.md, sem
sobrescrever método, calibração ou rejeições de headlines. Não há vídeo real do usuário nesta
revisão. Não foi feita análise do cenário real dele.

## Acrescentado e integrado
- Leitura de todas as ideias com opção keep, não efeito obrigatório por frase.
- Fluxo de inspeção de frames, cenário, áreas protegidas, estilo, storyboard e briefs.
- Ferramenta tools/visual_direction.py: preparar, conferir e exportar. Trabalha localmente,
  sem instalar dependências, sem gerar imagem por API e sem chamadas de modelo.
- Exportação para quatro componentes JavaScript já existentes; conceito novo exige autoria
  de código/asset. Briefs para outras técnicas ficam explicitamente pendentes.
- Rotas Codex e Claude Code, usando o mesmo AGENTS.md; CLAUDE.md agora tem import explícito.
- Integração aos fluxos de edição, qualidade, personalização e contrato de entrada.
- Contratos para imagem gerada, máscara, tracking e VFX, com fallback honesto.

## Executado nesta construção
- 180 testes Python passaram (134 anteriores + 46 novos).
- 20 testes JavaScript passaram.
- 25 verificações de integração visual passaram. Foi criado vídeo sintético, extraídos
  frames reais, preparado mapa com retângulos e falas de teste escritos manualmente,
  exportados briefs/specs, renderizados dois componentes JS em 96 PNGs e feita composição
  MP4 preservando os 144 frames e o hash dos pacotes de áudio. Colisão, mistura de cliente
  e mudança da EDL foram rejeitadas. Um limite extra de cena e orçamento de frames foram testados.
- 16 verificações anteriores de roteiro/silêncio passaram novamente.
- Inspeção visual de um frame composto: retângulo protegido à esquerda, título à direita,
  área inferior livre. Trata-se de fixture técnica, não amostra de excelência artística.
- Uma execução combinada foi interrompida pelo timeout do ambiente; os testes foram repetidos
  separadamente e concluíram. Os resultados finais são os identificados como v1_5.

## Não executado / não fornecido
- Sessões reais de Codex ou Claude Code e julgamento semântico/espacial por esses agentes.
- ASR sobre fala humana desta solicitação ou revisão de uma gravação do cliente.
- Geração externa de ilustrações/vídeos; não há provedor conectado no pacote.
- Segmentação de pessoa, máscara temporal, tracking de câmera/superfície e reconstrução 3D.
- Renderização da rota Remotion; permanece opcional, conforme a revisão anterior.
- Avaliação artística pelo usuário ou teste de audiência.

## Limites que permanecem explícitos
A amostragem de frames não é tracking. O mapa é preenchido pelo agente após abrir imagens.
A validação de caixas não prova que a interpretação seja correta nem que nenhum gesto ficou
entre amostras. A exportação produz candidatos/briefs, nunca aprovação de publicação.
Qualidade exige examinar a composição e o movimento no vídeo, e respeitar contexto e feedback.
Os testes não demonstram o desempenho de um modelo, sua preferência estética ou viralidade.

## Preservação e uso
Fontes anteriores e YAMLs de padrões existentes foram preservados. O inventário de alterações
está em sources/V1_5_INPUT_AUDIT.json. Histórico de testes das versões anteriores não é
reapresentado como execução atual. ZIP não inclui caches Python, bancos de memória privados,
fontes tipográficas, chaves nem instalações locais.

Extraia em outra pasta e peça ao agente para mesclar a atualização preservando trabalhos,
clientes, memória e padrões personalizados. Não substituir uma instalação inteira pelo ZIP.
