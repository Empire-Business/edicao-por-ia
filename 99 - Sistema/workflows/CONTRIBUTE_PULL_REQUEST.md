# Sugerir um formato ou uma melhoria ao Cortez

## Para quem nunca abriu um PR

Um **PR** (pull request) é uma proposta de alteração enviada para revisão. Pense em uma sugestão com as mudanças anexadas. A versão usada por todos continua igual até um mantenedor aprovar e integrar a proposta.

Você descreve a ideia; o Cortez cuida da parte técnica. Peça:

> Cortez, prepare um PR com esta sugestão: [explique o formato novo ou a melhoria].

Para um formato novo, inclua um vídeo de exemplo que possa ser compartilhado e explique o que ele faz: cortes, ritmo, cenas e legendas. Pessoa, cores e fontes do exemplo não se tornam padrões do formato.

Para uma melhoria, conte o que aconteceu, o que esperava e como repetir o problema. Não precisa saber programar. O Cortez pode pedir uma informação que esteja faltando.

## Processo do assistente

1. **Entender a proposta.** Identificar objetivo e resultado esperado. Verificar se já existe um formato equivalente ou um PR aberto sobre a mesma mudança. Mostrar em linguagem simples o que será proposto. Não ampliar o escopo.
2. **Confirmar a conta.** Usar a sessão oficial da própria pessoa no GitHub. Não pedir senhas, tokens ou chaves na conversa. Autenticação e consentimentos ficam no fluxo oficial. Sem autenticação ou acesso, preparar o rascunho local e informar o bloqueio.
3. **Separar a mudança.** Usar uma cópia de código limpa baseada na main atual de `Empire-Business/edicao-por-ia`, ID 1408655066. Preservar a instalação, trabalhos e alterações locais. Conferir os hooks antes de executar. Nunca enviar o histórico de um repositório privado antigo.
4. **Escolher o caminho de contribuição.** Com escrita no central, criar uma branch de contribuição; sem escrita, usar um fork na conta da pessoa, sem pedir elevação de permissão. Conferir colisões antes de criar. A solicitação explícita para abrir o PR autoriza o envio somente dos arquivos revisados desta proposta ao GitHub; não autoriza outros destinatários, convites ou mudanças de visibilidade.
5. **Preparar e conferir.** Alterar apenas o necessário e executar verificações proporcionais, após inspecionar scripts e hooks. Não criar bancos de teste, preparar infraestrutura, executar migrations ou usar serviços pagos sem autorização específica. Não desativar proteções nem ocultar falhas. Se uma checagem obrigatória depender de operação não autorizada, informar a pendência e manter o PR em rascunho.
6. **Conferir o material público.** Mostrar a lista exata de arquivos e revisar o diff. Nunca incluir trabalhos, originais de clientes, exports, memória, bancos, chaves, `.env`, credenciais, caches, dados pessoais ou configuração local. Não usar `git add -A` na instalação do usuário. Pedir confirmação específica quando não estiver claro se uma referência pode ser publicada. Um link recebido não autoriza divulgar todos os arquivos da pessoa.
7. **Abrir o rascunho.** Criar o PR contra a main, com título claro, problema, comportamento proposto, exemplo autorizado quando houver, verificações realizadas e pendências. Reutilizar a mesma branch/PR em revisões relacionadas. Entregar o link e explicar: “Sua proposta foi enviada para revisão; a versão oficial ainda não mudou.”
8. **Acompanhar correções.** Quando a pessoa pedir, ler o feedback e atualizar a proposta no mesmo PR, preservando mudanças de outros colaboradores. Nunca aprovar, integrar, publicar na galeria ou fazer deploy automaticamente como consequência de abrir um PR.

## Formatos novos

- Visitantes podem propor formatos, mas não reservar nem cadastrar códigos F oficiais. Identificar a proposta pelo nome e pela receita candidata; o mantenedor atribui o menor F livre e um UID novo na integração.
- Usar apenas referências explicitamente autorizadas para publicação. Não incluir uma gravação particular para preencher um exemplo ausente.
- Descrever o mecanismo sem fixar marca, apresentador, paleta ou fontes. Preservar todos os formatos existentes, sem renumerar nem substituir receitas consolidadas.
- Incluir análise da referência e uma receita específica. Material incompleto deve aparecer como pendência, sem apresentar o formato como concluído.
- Na revisão do mantenedor, conferir análise, receita, catálogo, guias, referências, busca, publicação e manifesto pelo fluxo existente. Abrir o PR não equivale a publicar o formato.

## Melhorias

Preservar compatibilidade com trabalhos, memória, códigos, permissões e escolhas de modelo. Mudanças no comportamento devem trazer um exemplo concreto de antes/depois e verificações diretamente relacionadas. Se houver SQL necessário, preparar e revisar estaticamente sem executar; registrar: “Migration preparada e revisada estaticamente; execução e validação em banco não realizadas.”

## Depois do envio

O GitHub mostra a conversa e o andamento da proposta. Os mantenedores podem pedir ajustes, aprovar ou encerrar o PR. Encerrar uma proposta não apaga os vídeos nem a instalação da pessoa. A atualização oficial continua sendo solicitada ao Cortez pelo atualizador seguro, depois da integração.
