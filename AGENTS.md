# Fábrica de vídeos — entrada do projeto

A parte técnica foi movida fisicamente para `99 - Sistema/`.
Leia `99 - Sistema/AGENTS.md` como regras permanentes. Os caminhos dos workflows,
methods, jobs, tools, context e patterns ali e nas skills são relativos a esse motor.
Trabalhe nesse diretório ao executar ferramentas. `factory.py` na raiz é uma ponte
para o motor. Não use atalhos antigos como destinos de escrita. Ao preparar uma cópia nova,
o setup também aplica a apresentação da raiz; use os caminhos reais do motor.

O uso diário está na raiz: `00 - COMECE AQUI.html`, `01 - Enviar vídeos/`,
`02 - Ver vídeos/`, `03 - Ajuda/`, `04 - Formatos/` e `05 - IDs Visuais/`. Crie e altere formatos pelo
fluxo de memória existente, com recibo, e atualize as pastas visíveis com
`99 - Sistema/tools/format_catalog.py refresh`. Não coloque comandos para leigos.

As pastas visíveis de formatos são identificações do cadastro; os bancos originais
permanecem em `99 - Sistema/context/clients/`, sem mescla ou alteração de registros.
A camada de caminhos legados não edita a evidência armazenada nem reinicia orçamento.

Configuração nativa `.agents/`, `.claude/` e `.codex/`, Git, segredos e ambiente
Python permanecem na raiz do projeto. Nunca leia segredos sem pedido explícito.

Mantenha a raiz simples. Atualizações são pedidas à IA; ela opera o atualizador seguro.
Não crie atalhos visíveis de atualização, instaladores ou arquivos técnicos extras na raiz.
Documentação técnica fica em `99 - Sistema/` ou `03 - Ajuda/`.
