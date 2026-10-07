# Protocolo de limpeza de armazenamento

## Objetivo

Liberar espaço sem tocar em gravações originais, assets enviados, memória, banco de andamento, EDLs, código de cena, análises, evidências de QA, prévias ou finais. A limpeza é por trabalho; nenhuma pasta `jobs/` inteira é descartada automaticamente.

## O que ocupa espaço

Priorizar os segmentos de render `jobs/<id>/studio/parts-*/part_*.mov` e `jobs/<id>/renders/m4k/s*.mov`. Eles são componentes técnicos usados para compor uma exportação. `proxy/`, masters, stems de áudio, versões de prévia e outros renders não entram na remoção automática: podem ser insumos de uma revisão ou a única cópia de trabalho.

## Portão de segurança

1. Conferir que `final`, `qa` e `delivery` constam como `completed` em `.factory/state.sqlite3` e que a evidência registrada do final ainda existe. Trabalho ativo, estágio `stale`, pendente ou legado sem registro fica protegido.
2. Fazer prévia: `python3.12 factory.py cleanup` para todos os trabalhos, ou `python3.12 factory.py cleanup --job ID` para um.
3. Conferir total, quantidade e amostra dos caminhos. Verificar que nenhum renderizador está escrevendo no trabalho.
4. Após a entrega, para o trabalho escolhido: `python3.12 factory.py cleanup --job ID --apply --confirm ID`. O comando remove somente segmentos com os nomes e locais acima e preserva qualquer arquivo registrado como evidência de checkpoint. Um recibo `qa/cleanup-*.json` registra os caminhos removidos e o total de bytes.
5. Se houver nova revisão, os segmentos removidos terão de ser renderizados de novo. As fontes e os planos permanecem para essa reconstrução. Não marque uma etapa como concluída só porque um vídeo antigo ainda existe.

## Limites

- A prévia nunca apaga nada. A remoção exige ID explícito e confirmação igual ao ID; não há `--apply` global.
- Cache de bytecode `.venv/**/__pycache__/*.pyc` pode ser apagado separadamente após conferir que nenhuma instalação ou execução Python está em andamento; Python o recria quando necessário. Isso costuma liberar bem menos espaço que os segmentos de vídeo.
- Não limpar arquivos dentro de `assets/`, `analysis/`, `edit/`, `memory/`, `.factory/`, nem a pasta `renders/` inteira.
- Para recuperar mais espaço em masters, trilhas, versões antigas ou trabalhos incompletos, fazer revisão manual de dependências e cópias antes de decidir. Não ampliar o filtro automático por extensão genérica.
- Se o usuário pedir apenas um diagnóstico, entregar a prévia e parar antes de `--apply`.
