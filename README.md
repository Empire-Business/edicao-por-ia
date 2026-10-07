# Fábrica de vídeos

Edite vídeos conversando com a IA, escolhendo **um formato de edição (F)** e **uma identidade visual (ID)**. Trabalhos, arquivos e memória ficam na sua pasta local.

**Já usa uma versão antiga ou sua pasta ficou misturada após sincronizar? Leia [Atualizar e recuperar a pasta](99%20-%20Sistema/ATUALIZACAO.md) antes de baixar algo por cima.**

## Primeira instalação

1. No GitHub, escolha **Code → Download ZIP** e extraia em uma pasta nova chamada `edicao-por-ia`. Não extraia dentro de uma instalação existente.
2. Abra essa pasta no Codex ou Claude Code e peça: **“Prepare esta fábrica para usar neste computador. Verifique o que falta e me explique antes de instalar programas.”**
3. Abra `00 - COMECE AQUI.html`. A preparação cria o catálogo legível, as IDs e o arquivo de chaves. Python 3.11 ou mais recente é necessário; a IA prepara as dependências de acordo com o trabalho pedido.
4. Coloque gravações e materiais em `01 - Enviar vídeos`. Você encontra entregas em `02 - Ver vídeos`.

A pasta pode ser copiada para outro computador. Os materiais acompanham a cópia; programas e ambiente Python precisam ser preparados na nova máquina.

## Escolher a edição

Em `04 - Formatos`, cada pasta tem um código F, instruções e **GUIA DA EDIÇÃO.html**. Em `05 - IDs Visuais`, escolha as cores e fontes.

Exemplo de pedido: **“Edite esta gravação com F02 e ID03.”** Nenhum formato escolhe cores, fontes, pessoa ou logo automaticamente. Logotipos só entram quando pedidos para aquele vídeo.

| Código | Formato | Código | Formato |
| --- | --- | --- | --- |
| F01 | Chat | F07 | Tela Animada |
| F02 | Dinâmico | F08 | Camadas |
| F03 | Foto Falante | F09 | Conversa e Tela |
| F04 | Gancho e Animação | F10 | Pessoa e Tela |
| F05 | Editorial | F11 | Formulários |
| F06 | Diagramas | F12 | Documentário |

Veja a [biblioteca de referências dos 12 formatos](99%20-%20Sistema/examples/reference-library/README.md), com vídeos, fotos, pranchas e análises disponíveis. Ela acompanha o download e a atualização. As [ilustrações didáticas](99%20-%20Sistema/examples/formats/README.md) também continuam disponíveis. As ilustrações demonstram a sequência de edição; os materiais reais e as prévias históricas são identificados separadamente. Toda ID pode ser combinada com todo F. A IA atribui um código E a cada trabalho: **“Na E01, aos 12 segundos, tire o texto.”**

## Integrações

A preparação cria **CHAVES DAS INTEGRAÇÕES.txt** na raiz, visível e fora do Git. Cole as chaves nos campos ScrapeCreators e ElevenLabs e salve. Não envie esse arquivo para outras pessoas.

Cenas pedidas de TikTok e YouTube são pesquisadas e obtidas exclusivamente pelo ScrapeCreators. Se a API não disponibilizar a mídia, a IA informa a pendência sem trocar de serviço. ElevenLabs é usado quando solicitado; as integrações dependem das chaves e dos créditos da sua conta.

## Atualizar sem perder trabalhos

Feche as edições em andamento e peça à IA: **“Atualize esta fábrica pelo atualizador seguro, preservando meus trabalhos e configurações.”**

O atualizador baixa apenas o código declarado no pacote, verifica os arquivos e mantém backup. Trabalhos, originais, memória, IDs, catálogo, chaves e gastos são preservados. Conflitos precisam de revisão; não são resolvidos apagando suas alterações.

**Não use sincronização do GitHub Desktop, `git pull`, reset ou extração de ZIP por cima como instalador.** Quem tem versão muito antiga, conflitos ou pastas duplicadas deve seguir o [guia de recuperação](99%20-%20Sistema/ATUALIZACAO.md). O caminho assistido cria outra pasta completa e mantém a antiga intacta.

## Novos formatos

Peça o cadastro com nome simples e um link HTTP/HTTPS de exemplo (Instagram, Drive, X ou outro). A fábrica cria um código estável, guarda a descrição da edição e atualiza as pastas visíveis. Cor e fonte são cadastradas separadamente como ID visual.

## Versões e dados

Veja o [histórico de mudanças](99%20-%20Sistema/CHANGELOG.md). A parte técnica fica em `99 - Sistema`. O GitHub distribui todos os formatos padrão, receitas, ferramentas, fontes, exemplos e referências disponíveis selecionadas pelo autor; cada usuário mantém seus trabalhos e aprendizados localmente. A cópia da pasta e o backup dos dados continuam necessários: o GitHub não é o backup dos seus vídeos.
