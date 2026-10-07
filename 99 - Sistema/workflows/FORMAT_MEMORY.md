# Workflow — formato F e ID visual

## Entrada

1. Sem hook, iniciar um token de turno com `format_memory.py begin`. Com hook, usar o token atual, sem iniciar outro.
2. Para editar, resolver as duas escolhas atuais: F e ID. Perguntar somente pelo que falta; não adivinhar. O usuário pode dizer “Use F01 com ID03”.
3. Vincular a sessão ao F com `format_memory.py bind --format F01 ...`. Ler `context --format F01` e a receita versionada. Ler a ID separadamente com `visual_identity.py show --code ID03`.
4. Registrar feedback de edição no F/trabalho correto com `capture`, usando o schema de memória e recibo. Feedback de cor/fonte vira revisão em `visual_identity.py update`. Nunca mover paleta para F.
5. Sem informação a guardar ou em pedido exclusivamente global de sistema, usar um skip honesto; regras globais ficam em AGENTS/métodos. Nunca fingir captura.

## Cadastro

Usar `format_catalog.py create --name "Nome simples" --example-url URL`; o próximo FP é gerado automaticamente nas cópias de uso. Apenas o autor/mantenedor autenticado usa --official para cadastrar o menor F livre; a ferramenta confere a permissão de escrita no repositório central. Link de exemplo é obrigatório em novos cadastros. A exceção é apenas para os cadastros antigos marcados `legacy_exempt`.
O cadastro novo fica reference_analysis_pending: não editar com a receita genérica de entrada. Inspecionar o exemplo real e salvar uma análise com UID, URL original, mecanismo/etapas, observações e referências locais hashadas. Usar format_catalog.py set-recipe para associar essa análise a uma receita específica e versionada; essa operação completa um cadastro pendente, não altera os formatos consolidados.
Analisar a referência, criar uma receita sem paleta/fontes fixas, salvar a direção e atualizar `format_catalog.py refresh`. A pasta tem COM O USAR/GUIA DA EDIÇÃO em HTML; incluir prints locais quando disponíveis.
No catálogo deste autor, cadastrar o formato também exige publicá-lo em `https://modelos-edicao.empirebusiness.com.br`, seguindo `PUBLISH_FORMAT_GALLERY.md`. Não encerrar a criação antes de conferir o cartão, o exemplo, o guia e a busca na página publicada. Renomes e descartes precisam atualizar essa mesma galeria. Bloqueio concreto de publicação fica registrado como pendência, sem declarar conclusão.
IDs visuais são cadastradas separadamente com `visual_identity.py create`, com nome, paleta e tipografia/arquivos locais. Não criar uma associação automática F–ID.

## Trabalho

Criar com `factory.py intake`, informando `format: F01` e `visual_identity: ID03`, ou usar `make_job.py --format F01 --visual-id ID03`.
O manifesto guarda `format_code`, `visual_identity`, `edition_code` e a compatibilidade interna. O resolvedor combina as regras de F com a aparência de ID e produz recibos independentes. Overrides explícitos do trabalho prevalecem; logotipos só se pedidos para aquele vídeo.

Trabalho anterior: usar `resume --job E01`. Se não tem as escolhas novas, usar `assign-design --job E01 --format F01 --visual-id ID03 --note "Escolha atual"`. Não zerar orçamento, apagar originais ou substituir aprovação sem nova revisão.

Antes da entrega, `resolve_format_context.py --check` verifica o contexto e a ID. QA confere a execução real: fala, leitura, cortes, cores/fontes da ID, ausência de logos automáticas e sincronização.

## Nomes e histórico

Renomear com `format_catalog.py rename`, com recibo. O F não muda e os bancos originais não são mesclados. Nomes curtos descrevem o mecanismo; nomes de pessoa/cliente/produto não são nomes de formato.
Os bancos anteriores e as referências mantêm seus IDs e evidência; são acervo, não uma rota automática de identidade para outro usuário.
