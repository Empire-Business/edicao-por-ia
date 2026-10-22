# Publicar e manter o catálogo visual

Todo novo formato criado no catálogo deste autor deve aparecer em **https://cortez.highticketai.com.br**. A criação só está concluída depois da publicação e conferência da página. Isso também vale para renomes e descartes. Não transferir esta autorização a catálogos privados de outras pessoas que usam cópias da fábrica.

## Fonte e seleção

1. Consultar o código ativo em `context/catalog/registry.json` pelo fluxo normal de formato/memória. Não usar `config/design-defaults.json` para restaurar descartes. Preservar o F e os bancos originais.
2. Criar ou revisar a receita e o guia sem fixar a ID visual. Formato, identidade e código da edição continuam separados.
3. Adicionar à seleção explícita em `web/modelos-edicao/publication.json` somente os campos públicos. Atualizar nome, descrição e receita do código correto. Retirar códigos descartados e mantê-los em `excluded_codes`.

## Exemplo e busca

4. Procurar primeiro as referências e entregas/previews locais correspondentes ao mecanismo. Importar para dentro da fábrica qualquer material externo e conferir o hash. Inspecionar metadados e cenas reais; nome de arquivo ou perfil histórico não prova qual formato o vídeo demonstra.
5. Escolher um exemplo real disponível. Uma prévia pode ser publicada com rótulo de prévia; uma referência parcial deve dizer o que demonstra e o que falta. Não atribuir animação de foto a uma gravação sem evidência. Se só houver imagem ou esquema, a criação permanece pendente de um exemplo real em vídeo.
6. Usar Vimeo quando a conexão e o upload estiverem disponíveis. Enquanto houver bloqueio concreto, a cópia local otimizada do exemplo pode ser servida pela galeria, preservando o original. Não inventar IDs, URLs ou recibos de upload. Não publicar o trabalho inteiro, dados pessoais, arquivos de memória ou chaves.
7. Escrever descritores úteis: para que usar, como o vídeo é construído, se há apresentador, o que enviar e palavras/sinônimos que uma pessoa procuraria. Exemplos: “sem aparecer”, “mensagens”, “foto falando”, “tutorial”, “notícias”, “mapas”, “comparação”. Cores e fontes pertencem à ID, não aos descritores de mecânica do formato.

## Publicação e recibo

8. Exportar o catálogo sanitizado e as mídias selecionadas, testar a busca, os filtros, áudio/autoplay, guia e seleção explícita de F/ID. O build precisa rejeitar códigos descartados e arquivos fora da seleção pública.
9. Publicar somente os arquivos revisados no GitHub e acompanhar a implantação da galeria no Vercel. Verificar o modelo na página do domínio oficial, inclusive em celular. Não mudar segredos nem publicar dados privados para resolver um bloqueio.
10. Guardar um recibo em `.factory/gallery-publications/` com F, ação, hashes, commit, URL do cartão, implantação e verificação real. Se o domínio, upload ou implantação estiver inacessível, guardar `pending_publication` com o motivo e o que já está comprovado. Não dizer que a criação terminou por ter apenas um commit ou uma prévia local.
11. Executar `tools/format_catalog.py refresh` para manter as pastas locais e os guias coerentes. O nome muda com recibo; o código e a história não mudam.

O assistente executa a manutenção técnica. O visitante escolhe na página e copia o pedido para sua pasta; não recebe comandos ou etapas de implantação.

## Conferência de importações

Inventariar cada pasta do ZIP solicitado e registrar seu destino: código novo, variação existente ou pendência explícita. Usar somente os arquivos desse ZIP e os links de referência nele contidos. Não recorrer a outro arquivo, prévia local, busca em rede social ou receita genérica para preencher material ausente, salvo autorização explícita do autor para essa fonte. Um pedido para “se virar” ou preservar um cadastro não autoriza inventar seu mecanismo ou substituir seu exemplo. Manter os materiais originais e indicar o que falta, sem apresentar uma adaptação como formato recebido. Uma retirada explícita atual prevalece sobre pedidos anteriores para preservar. Conferir o inventário completo antes de declarar a importação concluída; não publicar bancos importados nem mesclar memórias.

## Ordem, autoria e gerações
A galeria mantém ordem numérica de F, sem renomear/renumerar os atuais. FP/IDP são particulares e não entram automaticamente no catálogo do autor. Novos F usam o menor número livre entre ativos e um UID/loja novos; nunca recuperar referência rejeitada só porque o número foi reaproveitado. Conferir locks dos consolidados. A origem ativa é o novo Empire-Business/edicao-por-ia público independente, ID 1408655066, main. O anterior foi renomeado para edicao-por-ia-antigo-nao-usar e permanece privado como arquivo; não é fonte de instalação ou publicação.

A lista de formatos do README público deve refletir apenas os cadastros ativos e seus nomes atuais, em ordem numérica. Atualizar essa lista ao criar, renomear ou retirar um formato; códigos antigos não retornam por documentação desatualizada.

## Painel de instruções (sempre atualizado)
A galeria é também o painel geral da fábrica: a tela inicial (`#inicio`) explica o uso, destaca a biblioteca de modelos (`#modelos`) e lista todas as funções em `#funcoes`, com a frase curta para dizer e o prompt completo para copiar. A fonte é `web/modelos-edicao/src/guide.js`.
Ao criar, renomear, mudar ou retirar um workflow ou uma capacidade que o usuário pede (inclusive pedidos novos que viraram rotina, como as variações de teste), atualizar no mesmo trabalho a função correspondente e `guideUpdated`. `tests/guide.test.mjs` falha se um arquivo de `workflows/` não estiver documentado nem listado em `internalWorkflows`, e se um prompt trouxer comando de terminal. O painel nunca entrega comandos técnicos ao usuário: só frases para a IA. Publicar pelo mesmo fluxo da galeria e conferir a página no domínio.

## Conferir o destino de hospedagem

`web/modelos-edicao/publication-target.json` registra o projeto que atende ao domínio oficial. Antes de publicar, conferir o alias exato pelo serviço: em 21/10/2026 `cortez.highticketai.com.br` (domínio principal por ordem de 22/10/2026) e o alias anterior `modelos-edicao.empirebusiness.com.br` pertencem ao projeto Vercel `prj_UqbYeafa2wgEhdt1nj6jeuxbgGsy`, equipe `team_FujSZEiwGJtiMygV3DlMCYyY`. O projeto `prj_4Zt3yYpNuCQaOFFC1E4ETJGRgs4p` atende outro endereço; um READY nele não comprova publicação no painel oficial.

O nome legado do projeto de hospedagem, `edicao-por-ia-dist1`, não é uma fonte GitHub. Usar exclusivamente `gitSource` do repositório público ativo, ID 1408655066, com SHA da main verificada. Não recorrer ao repositório arquivado nem a um segundo repositório de distribuição. Conferir SHA, projeto, estado READY e atribuição do domínio no recibo. Se o projeto do alias mudar, revisar o destino antes de publicar, sem mover domínios ou alterar DNS por suposição.

## Marca do produto
O painel e as instruções públicas usam Cortez, “o agente que edita seus vídeos”. Marca e personagem são da interface; as IDs dos vídeos permanecem independentes. Manter a função de contribuição e o tutorial de uso visíveis no painel. O vídeo específico sobre PR só pode ser listado quando houver um arquivo real produzido e revisado; não confundi-lo com a aula de uso enviada pelo autor.
