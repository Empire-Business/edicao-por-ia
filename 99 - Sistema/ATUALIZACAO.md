# Atualizar ou recuperar a fábrica sem perder trabalhos

**Se a sua pasta ficou uma bagunça depois de sincronizar, pare a sincronização automática e guarde uma cópia completa da pasta antes de continuar.** Inclua os itens ocultos nessa cópia. Não apague nenhuma das pastas duplicadas: elas podem conter trabalhos diferentes.

Você não precisa executar comandos. Abra a pasta no Codex ou Claude Code, copie o pedido correspondente abaixo e deixe a IA fazer a parte técnica.

## Minha pasta tem “99 - Sistema” e está organizada

1. Termine ou feche as edições em execução.
2. Faça uma cópia completa da pasta em outro local de backup.
3. Peça: **“Atualize esta fábrica com o atualizador seguro. Preserve vídeos, trabalhos, formatos, IDs, memória, configurações, chaves e gastos. Verifique a versão e me diga se houve conflito.”**
4. Aguarde a mensagem de conclusão. Abra `00 - COMECE AQUI.html` de novo. Se a IA indicar mudança de configuração do host, reabra a sessão.

A atualização é feita pela IA. Se faltar Python 3.11+ ou acesso ao repositório, ela explica a pendência e prepara o que for autorizado. O usuário não precisa abrir scripts nem executar comandos.

Se o atualizador antigo disser que o pacote é grande demais, peça à IA: **“Prepare o atualizador atual de forma verificada e temporária, sem alterar o código ativo, e depois aplique a atualização com todas as referências.”** A IA resolve essa etapa técnica; nada precisa ser executado manualmente.

**“Conflito” ou “precisa revisar” não significa atualização concluída.** A versão ativa permanece intacta e a recebida fica guardada para revisão. Peça: **“Revise o recibo da atualização e preserve minhas personalizações. Se não houver uma base confiável, use a recuperação em uma pasta nova.”**

## Minha versão é muito antiga ou não tem “99 - Sistema”

A estrutura mudou. Sincronizar Git ou extrair por cima pode misturar os arquivos antigos com os novos. Use uma recuperação em uma pasta separada:

1. Mantenha a pasta antiga e seu backup completos. Encerre as edições nela.
2. Baixe o ZIP atual em **Code → Download ZIP**. Extraia em uma pasta separada, por exemplo `edicao-por-ia-atual`. Não coloque dentro da pasta antiga.
3. Abra a pasta recém-baixada no Codex ou Claude Code.
4. Cole este pedido, substituindo os dois caminhos:

> Use a ferramenta de recuperação desta versão nova. Minha pasta antiga está em [caminho da pasta antiga]. Crie a instalação recuperada em [caminho de uma pasta nova que ainda não existe]. Primeiro confira a prévia, o espaço e os conflitos. Depois copie meus trabalhos, vídeos, formatos, IDs, memória, configurações, chaves e registros de gastos. Não altere nem apague a pasta antiga, não mescle bancos e não execute o código antigo. Prepare o ambiente da pasta recuperada e me mostre o relatório e as pendências.

A ferramenta cria a pasta recuperada completa. Não é necessário passar por todas as versões intermediárias. Ela reconhece a estrutura plana antiga, a estrutura atual e a presença das duas juntas. Somente o código verificado da versão baixada fica ativo.

Trabalhos e bancos mantêm seus arquivos originais. Código antigo e itens sem destino conhecido ficam em **99 - Sistema/arquivo/recuperacao**. Dois arquivos destinados ao mesmo lugar ficam separados e aparecem no relatório; a IA deve revisar qual corresponde ao trabalho que você quer continuar. A ferramenta não funde bancos nem garante que qualquer formato de arquivo histórico já seja compatível: trabalhos antigos ainda podem precisar de adaptação pela IA antes de editar.

O ambiente Python, programas e modelos são preparados novamente. Não se copia `.venv`, `node_modules` ou o histórico Git como ambiente executável. As configurações pessoais acompanham a recuperação; a IA verifica se precisam de adaptação ao host atual.

## Sincronizei e agora tenho duplicatas ou conflitos

Siga o mesmo processo de **recuperação em uma pasta nova**. No pedido, acrescente:

> Minha pasta foi misturada pela sincronização. Preserve todas as versões encontradas e compare-as no relatório. Não escolha por data de modificação, não apague pastas duplicadas e não reinicie os gastos das edições.

Quando existem `jobs` na raiz e em `99 - Sistema`, os trabalhos da estrutura atual ficam no destino principal e os da raiz também são copiados para o arquivo de recuperação. Isso preserva os dois conjuntos sem inventar que sejam o mesmo trabalho. Confira as pendências com a IA antes de continuar uma edição.

## Houve erro, falta de espaço ou arquivo fora da pasta

- **Falta de espaço:** a recuperação precisa de espaço para a nova cópia completa, mantendo a antiga. Escolha um destino com espaço e tente novamente.
- **Atalho para fora da fábrica:** importe o material para dentro da pasta com ajuda da IA. A recuperação bloqueia esse atalho; ela não pode prometer uma cópia portátil que dependa de outro disco.
- **Operação em execução:** espere a edição ou atualização terminar. Uma trava abandonada precisa de revisão do recibo, não de exclusão automática.
- **Python ou dependência ausente:** peça à IA para preparar o ambiente. A recuperação não instala programas automaticamente.
- **Conflito de código:** peça revisão ou recuperação em pasta nova. Não aceite instruções para apagar tudo e baixar novamente.
- **Arquivos já apagados por outra sincronização:** a ferramenta recupera o que ainda existe. A IA precisa procurar o backup para trazer os arquivos ausentes; o sistema não recria vídeos, memória ou gastos perdidos.

## Como conferir antes de abandonar a pasta antiga

Peça à IA: **“Confira os hashes dos materiais copiados, abra um trabalho antigo, confira seus gastos e etapas, liste meus formatos e IDs e verifique se as chaves foram preservadas sem mostrar os valores. Mostre também os itens arquivados e pendências de compatibilidade.”**

Abra as entregas e confira os projetos que você usa. Mantenha a pasta antiga até concluir essa revisão. Nenhuma etapa deste processo a apaga automaticamente. De agora em diante, atualize pedindo à IA, sem sincronizar arquivos de sistema por cima dos seus trabalhos.
