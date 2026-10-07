# Adaptadores de host

Arquivos de papel em `roles/` são compartilhados; frontmatter Claude em `claude/` e TOML Codex em `.codex/agents/`. O setup gera as configurações específicas sem reescrever o método.

São sete papéis: triagem, montagem, QA, execução de motion, direção editorial, direção de motion e direção visual. O coordenador decide quando há trabalho real para delegar. Workers retornam texto/código; só coordenador persiste memória e aplica mudanças.

`config/model-catalog.json` tem nomes candidatos, não uma descoberta da conta. Vincular IDs e esforço confirmados com `model-bind`. Configuração antiga ou não suportada deve parar, não ser silenciosamente ignorada. Controles organizacionais do host podem prevalecer.

A descoberta das skills usa `.claude/skills/` e `.agents/skills/`. A mesma raiz `AGENTS.md` orienta ambos; `CLAUDE.md` a importa. Configuração de modelos não é garantia financeira: ler `method/EXECUTION_AND_COSTS.md`.

No executor textual isolado, ferramentas/delegação ficam desabilitadas. Inspecionar o código que o worker devolveu antes de executá-lo; resposta de modelo é dado, não comando de instalação.
