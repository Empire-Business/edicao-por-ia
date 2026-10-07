> Revisão atual: `REVISAO_V1_6.md`. O relatório abaixo é histórico e mantém seu escopo original.

# Relatório de revisão — Claude Video Factory 1.1.0

## Pedido
Verificar se a skill aceita um roteiro de referência flexível para comparar a gravação e orientar erros/cortes, e se remove silêncios automaticamente.

## O que havia na 1.0
- Roteiro: não existia contrato/workflow dedicado; havia limpeza genérica de erros de fala.
- Silêncio: havia detecção, limites nos padrões e renderização por EDL, mas não uma ponte determinística completa detecção → cortes protegidos → render.

Detalhes e identificação do ZIP inspecionado em `sources/REVISION_AUDIT_V1.md`.

## O que mudou
- Roteiro opcional, modo flexível como padrão, alinhamento por ideias e preservação de paráfrases.
- Tratamento explícito de tentativas abandonadas, versões com significados diferentes, palavras críticas, linhas não gravadas e instruções de cena.
- Associação do roteiro a cada vídeo/escopo, sem misturar conteúdos de gravações compostas.
- Contrato de entrada, schemas, gerador de jobs, templates e instruções para os subagentes atualizados.
- Utilitário local `prepare_script_comparison.py` para recuperação compacta de candidatos; não é um avaliador semântico nem cria cortes sozinho.
- Utilitário `plan_silence_cuts.py` para transformar silêncio detectado em EDL sincronizada, com proteção de fala, pausas marcadas, fontes, hashes e montagem anterior.
- Detector revisado: falhas explícitas, áudio ausente, final silencioso, seleção de faixa e origem temporal.
- Renderizador recusa sobrescrever fontes/renders e respeita a faixa de áudio selecionada na EDL.
- Três starters v2 e exemplo anotado explicitamente simulado. Padrões v1 preservados byte a byte.
- Sem instalação, download de modelos ou chamadas a APIs de modelos nesta revisão.

## Testes executados
- **37 testes unitários: PASS.** Incluem campos temporais inválidos, proteção de palavras, pausas marcadas, associação de fonte/faixa, conflitos de hash, isolamento de escopo, preservação de montagem, bloqueios de sobrescrita e recuperação de referências sem julgamento semântico automático.
- **Integração com FFmpeg, 16 verificações: PASS.** Vídeo/tons sintéticos de 6 s com pausas conhecidas → EDL de aproximadamente 3,30 s; 2,70 s de tempo morto removidos. Vídeo renderizado: 3,300 s; áudio: 3,316 s. Quatro palavras simuladas tiveram tempos recalculados; SRT gerado. Fonte preservada por SHA-256. Proteção de pausa testada em EDL separada. Seleção correta entre uma faixa vazia e uma faixa sonora também testada.
- **Smoke test original, 6 verificações: PASS.** Render, geometria, SAR, retiming, SRT e integridade da fonte.
- Sintaxe Python, verificação estrutural, JSON/YAML e integridade do pacote são verificados na finalização. Evidências em `tests/results/`.

## O que NÃO foi validado
Os tempos de palavras da integração foram escritos manualmente para mídia sintética. Não houve transcrição real, julgamento semântico por Sonnet/Opus/Haiku nem escuta/percepção humana de uma gravação do usuário. Os cenários de paráfrases, erro real, intenção da pausa e fidelidade editorial estão especificados para testes de aceitação, mas não são apresentados como aprovados por modelos.

## Limitações importantes
O utilitário de comparação usa similaridade lexical para localizar possíveis trechos; o agente precisa avaliar o sentido. O utilitário de silêncio não entende intenção retórica, não garante limites perfeitos de ASR e exige fala protegida por timestamps/VAD. Música/ruído podem ocultar pausas; ASR pode omitir fala baixa. Não se deve fabricar conteúdo ausente nem encurtar só o áudio. A reprodução/avaliação dos cortes reais segue sendo um gate antes de chamar um vídeo de final.

## Uso
Leia `START-HERE.md`. Extraia a atualização numa pasta nova e compare antes de migrar jobs, contextos ou padrões personalizados. Escolha um starter v2 para defaults explícitos novos, ou mantenha seu v1: seus limites anteriores são respeitados.

## v1.2.0 revision
- Added explicit support for user-provided insertion assets (images/videos/B-roll/cutaways/proof assets).
- Added `method/INSERTION_ASSETS_POLICY.md` and `workflows/USE_INSERTION_ASSETS.md`.
- Extended job schema/template with `supporting_assets`.
- Added `tools/prepare_supporting_assets.py` for conservative local preparation of still-image clips.
- Updated router, input contract, patterns, and acceptance criteria.

## v1.3.0 — JavaScript motion

Ver `MOTION_REVISION_REPORT.md` para as mudanças, testes realmente executados, correção de fps e limitações. O caminho React/Remotion permanece não testado; a rota JS/browser/FFmpeg foi renderizada e composta de fato.

## v1.4.0 — memória proativa
Acrescentado fluxo executável de cadastro, captura, recuperação e aplicação de feedbacks.
Ver `MEMORY_REVISION_REPORT.md` e `MEMORIA-COMO-USAR.md`. Preservadas as ferramentas de
roteiro, silêncios, assets e animação. Testes de host real/entendimento semântico seguem pendentes.


## v1.7.0 — motion studio
Revisão atual em `REVISAO_V1_7.md`. O material de Movez motivou a ampliação do motor, a crítica vinculada a evidências, planos por estados e áudio opcional. Relatórios desta versão em `tests/results/v1.7-*`; resultados antigos permanecem históricos.
