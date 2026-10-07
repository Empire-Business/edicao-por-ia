# Relatório da atualização — Claude Video Factory 1.4.0

## Diagnóstico verificado
O ZIP recebido da v1.3.0 tinha templates de cliente, pastas de memória e um workflow de resultados,
mas não um sistema executável de captura/releitura por turno. `make_job.py` também não recebia
cliente/projeto nem aplicava preferências salvas. O diagnóstico é do pacote inspecionado,
não da instalação, permissões ou versão do Claude Code no computador do usuário.

## Implementado
- Cadastro isolado por cliente e vínculo por sessão, projeto, padrão e job.
- Captura proativa de fatos/preferências/feedbacks, com histórico e recibo lido após escrita.
- Estados separados: regra explícita, candidato, aprovação, rejeição e resultado observado.
- Um ajuste local não é promovido automaticamente a regra global; gosto não exige métrica.
- Consulta limitada a exemplos aprovados/rejeitados do mesmo cliente para trabalhos semelhantes.
- Resolvedor de preferências mecânicas, preservando overrides explícitos e jobs legados.
- Configuração de hooks para pasta nova e utilitário de mesclagem com backup para instalação existente.
- Inspeção seletiva, revogação, restauração autorizada e esquecimento por chave.
- Proteções contra paths inseguros, símbolos de credencial comuns, conflitos, duplicação por retry
  e gravação de um job na sessão de outro cliente.
- QA de personalização: fatos salvos não bastam; verificar a aplicação no corte real.

## Ferramentas novas
`client_memory.py`: armazenamento SQLite local, sem API ou dependência de serviço externo.
`resolve_client_context.py`: novo job efetivo, resumo Markdown, recibo e parâmetros de silêncio.
`memory_hook.py`: lembrete por turno e verificação de revisão, sem salvar o prompt completo.
`install_memory_hooks.py`: preview/mesclagem local, sem expandir permissões.
`make_job.py` foi integrado a essas ferramentas. Renderers e arquivos de padrões foram preservados.
O resolvedor lê YAML com a dependência opcional PyYAML já prevista pelo pacote; JSON também é lido.

## Testes realmente executados nesta revisão
**134 testes Python passaram, sendo 81 novos sobre memória/personalização e 53 anteriores.**
Log: `tests/results/v1_4-python-tests.txt`.

**20 testes JavaScript anteriores passaram novamente.**
Log: `tests/results/v1_4-motion-js-tests.txt`.

**18 verificações do fluxo integrado de memória passaram**, incluindo processos separados,
protocolo sintético de hooks, recibo, isolamento de clientes, herança em um novo job, invalidação
de snapshot antigo e renderização real por FFmpeg. Uma preferência sintética de pausa de 0,42 s
foi substituída por 0,70 s. O plano mudou de 6,42 s para 6,70 s e o vídeo renderizado teve 6,70 s.
A imagem e o áudio eram sintéticos; os tempos foram escritos para a fixture, não transcritos.
Log: `tests/results/v1_4-memory-integration.json`.

**16 verificações anteriores de roteiro/silêncio passaram novamente**, incluindo render,
proteção de pausas, seleção de áudio, retiming e preservação do original.
Log: `tests/results/v1_4-script-silence-regression.json`.

Teste de falha de escrita: simulação controlada de erro SQLite, não ensaio de todas as permissões
de sistemas operacionais. Concorrência: 12 escritas com 4 workers em uma fixture local.
Portabilidade: uma cópia do cadastro foi lida numa pasta nova. Isso não testa todas as máquinas.
Verificação estrutural/integridade e preservação de componentes: arquivos em `tests/results/v1_4-*`.

## Não executado / limites
Não houve sessão real autenticada de Claude Code ou Codex. Os hooks foram chamados como
processos Python com o protocolo documentado, não acionados por um host instalado do usuário.
Não houve teste da compreensão semântica de feedback livre, nem avaliação de uma gravação do usuário.
Não foi reexecutado o caminho React/Remotion; a revisão preserva seus arquivos e limitações.
Nenhum modelo foi treinado. Os hooks verificam que o agente revisou o turno, não que interpretou
corretamente o feedback ou que justificou bem um skip. Há proteção contra loop infinito.
Uma configuração existente, política de organização ou falta de escrita pode impedir o fluxo;
o agente deve dizer que não salvou. Não há garantia de observância perfeita de instruções.

## Dados e migração
Este ZIP genérico não contém cadastros reais do usuário, banco SQLite de teste, caches ou conversas.
Os dados locais surgem quando o agente identifica o cliente e registra informações realmente fornecidas.
Não importamos biografias ou preferências de PDFs de metodologia que não pertencem a este ajuste.
Para migrar uma instalação existente, preserve clients/jobs/padrões e mescle a configuração;
não substitua a pasta antiga cegamente. Use `MEMORIA-COMO-USAR.md`.
O comando esquecer remove a chave da base viva, não de cópias de segurança ou conversas do host.

## Fontes
Auditoria do ZIP: `sources/MEMORY_AUDIT_V1_3.md`.
Documentação oficial consultada: `sources/MEMORY_RESEARCH.md`.
As regras editoriais de memória e os utilitários são implementação desta revisão, não promessa
atribuída à Anthropic nem comportamento cientificamente validado.
