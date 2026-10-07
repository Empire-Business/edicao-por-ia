# Documentação consultada para a revisão 1.6

Data da consulta: 27/09/2026. Fontes primárias; estas notas descrevem documentação, não execução numa conta do usuário. Não contêm comparação de qualidade artística nem tabela de preço fabricada.

- OpenAI — Subagents: https://developers.openai.com/codex/subagents (redireciona para ChatGPT Learn). Agentes de projeto em `.codex/agents/*.toml`; campos name, description, developer_instructions, model e model_reasoning_effort; concorrência em `[agents]`. Os modelos indicados são candidatos, não disponibilidade confirmada na conta.
- OpenAI — CLI reference: https://developers.openai.com/codex/cli/reference . `exec --json`, `--ephemeral`, `--ignore-user-config`, sandbox e configuração por `-c`. O adaptador verifica CLI local e não inventa `--max-budget-usd` para Codex.
- OpenAI — Non-interactive mode: https://developers.openai.com/codex/noninteractive . Eventos de saída e usage de `turn.completed`; tokens não devem ser tratados como dólares sem dados de cobrança aplicáveis.
- OpenAI — Configuration reference: https://developers.openai.com/codex/config-reference . Desabilitação de shell/delegação/web no worker isolado. Configurações de conta/organização precisam ser conferidas no ambiente real.
- Anthropic — CLI reference: https://code.claude.com/docs/en/cli-reference . `--max-budget-usd` em modo print; limitação por execução; `--bare`, `--restricted`, ferramentas, `--no-session-persistence` e resultados JSON. O executor exige versão compatível, em vez de remover restrições silenciosamente.
- Anthropic — Subagents: https://code.claude.com/docs/en/sub-agents . Modelos por subagente, aliases e turnos. Limitar turnos não equivale a orçamento monetário.
- Anthropic — Costs: https://code.claude.com/docs/en/costs . Consumo equivalente em dólares e faturamento de assinatura são conceitos diferentes.

## Decisões de engenharia desta revisão (não afirmações dos fornecedores)
Saldo em SQLite, reserva anterior à chamada, retenção de custo desconhecido, suspensão após excesso, recorte por filho, limites dos perfis e backup com conflito preservado são implementações deste pacote. Os testes locais estão no relatório. Não houve chamada real a modelo nem confirmação de autenticação, licença, crédito extra ou disponibilidade de conta.
