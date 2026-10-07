# Fábrica de vídeos — v2

Uma pasta local para editar vídeos por conversa, com dados separados do código.

- F01, F02…: formato de edição, sem cor/fonte obrigatória.
- ID01, ID02…: paleta e tipografia, escolhidas separadamente.
- E01, E02…: trabalho de edição; V1, V2…: revisões.

Antes de editar, o usuário escolhe F e ID. Não há dupla padrão. Novos formatos precisam de um link de exemplo; cada pasta tem guia HTML detalhado e prints locais quando disponíveis. Logos não entram automaticamente.

Abra `00 - COMECE AQUI.html` na raiz visível. No novo computador, peça a preparação da fábrica. Peça “Atualize esta fábrica” para receber a main sem substituir seus dados.

O atualizador usa revisão GitHub fixada por SHA, integridade, backup, journal, mescla de código local quando possível e rollback. Conflitos preservam a versão ativa. Migrações devem ser declaradas e testadas; operações desconhecidas são bloqueadas.

Dados do usuário ficam em jobs/context/.factory e pastas de materiais. Defaults de instalação ficam em config e não sobrescrevem catálogo, IDs ou memória locais. Não publicar trabalhos reais, mídia de clientes, chaves ou bancos privados em releases de código.

Regras permanentes: AGENTS.md. Atualização: workflows/UPDATE_FACTORY.md.
