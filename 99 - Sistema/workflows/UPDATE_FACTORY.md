# Atualizar a fábrica sem substituir os dados

## Pedido do usuário

“Atualize esta fábrica” autoriza a atualização do código desta instalação. Faça a parte técnica; não peça comandos ao usuário.
Use `factory.py update --check` para consultar a main configurada. A revisão do GitHub é congelada por SHA; o manifesto confere todos os bytes do pacote antes da aplicação.
Use `update --apply` quando não houver edição em execução. A atualização é solicitada à IA; não criar atalhos, instaladores visíveis ou comandos para o usuário executar.

## O que é preservado

Nunca substituir trabalhos, mídia, exportações, bancos de memória, catálogo do usuário, IDs visuais/revisões, chaves, modelos vinculados, configurações locais ou gastos. Não usar git reset/clean/pull como instalador de uma pasta de usuário.
Arquivos desconhecidos permanecem. Código gerenciado sem alteração local é atualizado. Código modificado é mesclado em três vias quando existe uma base verificada e a mescla não conflita. Conflito mantém toda a versão ativa intacta e guarda a versão recebida em um recibo para revisão do assistente.

## Recuperação

Cada escrita tem backup e journal antes de mudar o arquivo. Falha recupera o código já aplicado; migrações são aditivas e preservam os dados originais. Remoções do código publicado só retiram arquivos gerenciados que continuam idênticos à base conhecida. Não apagar personalizações desconhecidas.
`update --rollback RECIBO` restaura o código somente se ninguém alterou esses arquivos depois. Não reverter edições ou gastos. Se a recuperação detectar alteração concorrente, manter a trava e pedir revisão dos arquivos concretos do recibo.

## Mudanças grandes

Todo release incompatível deve declarar migrações conhecidas, manter adaptadores para trabalhos antigos e testar atualização a partir de instalações anteriores. Migração desconhecida/schema não suportado é bloqueado antes de ativar código.
Os defaults distribuídos ficam em config; o catálogo/IDs locais ficam em context. Defaults faltantes podem ser acrescentados, mas não sobrescrevem definições locais. Formatos particulares novos usam FP e oficiais usam F; conflitos legados são relatados sem renumerar ou mesclar cadastros. Um F retirado pode ser ocupado por uma geração nova autorizada, com UID e loja de memória diferentes. Bancos antigos são preservados; preferências mecânicas podem ser projetadas em novos F, sem herdar cor/fonte/pessoa.

## Publicação

Antes de subir mudanças à main: executar regressão, testes de upgrade/rollback/mescla e construir o manifesto com `build_release.py`. Não incluir trabalhos reais, vídeos de clientes, bancos privados, chaves ou repositórios de produto nos arquivos publicados. Receitas aprovadas que mudam de comportamento recebem nova versão.

## Muito antiga / sem manifesto / pasta misturada

Não executar código da instalação antiga como instalador da versão nova. Não tentar resolver com Git, reset ou extração sobreposta. Ler `ATUALIZACAO.md` no motor da versão nova e usar `tools/recover_installation.py` da cópia nova verificada.

A recuperação faz prévia por padrão. Usar `--old PASTA_ANTIGA --destination PASTA_NOVA --package PACOTE_NOVO`, revisar bloqueios, espaço e conflitos; a autorização do pedido de recuperar permite `--apply`. O destino deve ser novo e fora da origem. O pacote precisa de manifesto válido. Trabalhos, memória, IDs, configurações e gastos são copiados sem editar seus arquivos de evidência; as chaves viajam opacas, sem análise ou saída dos valores. A origem não muda. Código antigo/itens desconhecidos/duplicatas vão para `99 - Sistema/arquivo/recuperacao` e constam do recibo. Dados da estrutura física atual são o conjunto principal quando a raiz também contém `jobs`; o conjunto da raiz é preservado separadamente, nunca mesclado. Antes de retomar uma edição, o assistente deve conferir seu ID, mídia, ledger e compatibilidade.

Não copiar o ambiente executável `.venv`/`node_modules` ou `.git`. Preparar dependências na nova máquina por `ASSISTED_START.md`. Atalhos externos, diretórios simbólicos sem migração conhecida, trabalhos/updates ativos, espaço insuficiente ou pacote inválido bloqueiam antes de publicação. Atalhos internos de arquivo tornam-se arquivos reais. Não prometer recuperar dados já ausentes sem backup.

Depois: conferir hashes e relatório, abrir um trabalho antigo, verificar gastos/etapas e listar formatos/IDs. Não apagar a origem. Referências legadas são resolvidas por um mapa interno de caminhos hashados, sem reescrever os registros originais. Links ilustrativos dos presets só completam URLs ausentes; links fornecidos por usuários e cadastros customizados permanecem intactos.

Se faltam arquivos após uma sincronização, procurar primeiro o backup. Para um arquivo específico anteriormente rastreado, o histórico Git da origem pode fornecer uma cópia: inspecionar e restaurar em local separado dentro da fábrica, sem reset/clean/checkout por cima dos dados existentes. Nunca inferir que o Git contém vídeos, memória ou ledger ignorados. Não reconstruir gastos inventados.

## Referências distribuídas pelo autor

O release inclui todos os formatos do catálogo padrão e suas referências disponíveis, indexadas em `config/reference-library.json`. A biblioteca fica em `examples/reference-library/Fxx`, sem acrescentar entradas na raiz. O builder aceita somente arquivos desse índice, verifica seus hashes e os inclui no manifesto. A atualização baixa/valida a biblioteca junto com as receitas; referências e guias ficam disponíveis na instalação nova. Não publicar bancos privados, trabalhos completos ou credenciais. Vídeos finais selecionados como referência pelo autor são copiados para a biblioteca, sem seus manifests, ledgers ou demais arquivos do trabalho. Não substituir links próprios do usuário por links padrão.

## Atualizador antigo / biblioteca grande

O comando assistido `factory.py update` prepara uma cópia temporária do atualizador atual, fixada por commit e conferida pelo hash declarado no manifesto. Isso não altera o motor ativo; só a transação final ativa o pacote. A biblioteca é preservada como parte do pacote. Nada novo fica na raiz.
Se uma instalação anterior a 2.1 bloquear um pacote acima do seu limite antigo de download, o assistente deve obter `tools/bootstrap_update.py` da revisão atual verificada do repositório e executá-lo em `.factory/bootstrap`, indicando a raiz antiga. O helper é standalone e só usa stdlib. Conferir seu SHA contra `PACKAGE_MANIFEST.json` da MESMA revisão antes de executar. Não editar o atualizador antigo por cima, não resetar o Git, não passar comandos ao usuário. Uma instalação sem estrutura/manifesto confiável continua usando recuperação em pasta nova.

## Repositório ativo público independente
A decisão atual usa o novo Empire-Business/edicao-por-ia público independente, ID 1408655066, como origem da main. O anterior foi renomeado para edicao-por-ia-antigo-nao-usar e permanece privado como arquivo, sem participar da distribuição. O fluxo de instalação exige login antes de baixar/aplicar setup. O visitante público pode obter a versão, mas não publicar mudanças no código central. A IA autentica o acesso usando a sessão própria do usuário no GitHub, sem copiar credenciais do autor. O atualizador fixa um commit da main e verifica o manifesto; sincronização significa receber esse código com backup e preservação dos dados, não executar pull/reset/clean sobre a pasta de trabalho. Se gh estiver ausente ou sem sessão própria confirmada, informar a pendência de autenticação e preparar a ferramenta oficial; não contornar o fluxo guiado com download anônimo. Referências continuam incluídas: downloads seletivos e outro repositório foram adiados.

## Após a limpeza autorizada do histórico de outubro/2026
A main passou a ter uma nova raiz de histórico. Cópias Git antigas continuam privadas e não devem ser mescladas à main, reenviadas com force/mirror ou usadas como base de publicação; isso poderia recolocar registros de trabalhos no GitHub. Nunca usar `--allow-unrelated-histories` para uma atualização. O usuário recebe código pelo atualizador seguro, com SHA e manifesto atuais, preservando os dados locais. Para publicar como mantenedor, usar um checkout de código separado criado a partir da main limpa atual, sem copiar a pasta `.git` antiga, jobs, memória ou credenciais. Verificar a ancestralidade e os caminhos da história da branch antes do push. Backups e o repositório antigo permanecem privados. O novo público é independente; não importar objetos, branches ou caches do arquivo antigo.
