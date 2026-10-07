# Auditoria da versão anterior — base do pedido

Origem: `claude-video-factory.zip` fornecido nesta conversa; inspeção do conteúdo extraído, não suposição a partir da resposta anterior.

## Roteiro de referência
`method/INPUT_CONTRACT.md` enumerava entradas como fonte, padrão, erros de fala e trechos obrigatórios, mas não definia o roteiro opcional e seu modo flexível. `method/SPEECH_ERROR_POLICY.md` tratava de tentativas, correções e conflitos, sem um fluxo roteiro × gravação. `workflows/ANALYZE_REFERENCE.md` era voltado à referência visual de edição, não à comparação do texto pretendido com a fala real.

Conclusão: a limpeza de fala existia, mas a comparação semântica com roteiro não estava especificada operacionalmente. Isso foi acrescentado; não é apresentado como recurso já completo da v1.0.

## Silêncios
`patterns/*-v1.yaml` continham `max_unmotivated_silence_seconds`, `tools/detect_silence.py` gerava intervalos e `workflows/EDIT_VIDEO.md` incluía a detecção. `tools/render_edl.py` conseguia renderizar intervalos de uma EDL.
Não havia uma ferramenta dedicada que convertesse a detecção em cortes sincronizados, com proteção de palavras/pausas, preservação da montagem anterior e relatório específico.

Conclusão: estava parcialmente previsto. Não se deve confundir detectar silêncio com ter executado sua remoção. A revisão conecta essas etapas com `plan_silence_cuts.py` e um workflow explícito.

## Preservação
Os três arquivos de padrão v1 foram comparados byte a byte com o ZIP anterior e preservados. Os starters v2 são novas versões. A arquitetura multiagente e demais workflows foram mantidos, com mudanças relacionadas aos dois pontos pedidos.

## Limites desta auditoria
Não revalida nomes/preços de modelos da pesquisa anterior. Não testa qualidade editorial humana nem comportamento real dos modelos com gravações do usuário. A revisão limita seus resultados executados aos testes registrados.

SHA-256 do ZIP auditado: `c895282be4142e31b9af79f038fdd556d55abff934d929fcc28adb5c008c1037`.
