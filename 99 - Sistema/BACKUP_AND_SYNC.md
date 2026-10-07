# Backup e sincronização

Este projeto usa um repositório GitHub privado. O hook local `.githooks/post-commit`
envia automaticamente para `origin/main` cada commit feito na branch `main`.
Commits em outras branches não são enviados. O hook não cria commits por conta
própria: alterações precisam ser commitadas. Se o push falhar, o commit continua
local e o hook informa o comando para tentar novamente.

O backup inclui código, métodos, workflows, padrões, templates e configurações do
projeto. Ficam fora renders, mídia original, arquivos de entrada e saída,
ambientes locais, credenciais, estado de instalação e memória privada de clientes.
Essas regras estão em `.gitignore`.

Depois de clonar este repositório em outra pasta, ative o hook nesse clone uma vez:

```sh
git config core.hooksPath .githooks
```

O hook depende de autenticação GitHub válida no computador. Não armazene tokens no
repositório.
