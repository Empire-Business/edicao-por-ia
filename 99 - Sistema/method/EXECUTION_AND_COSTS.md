# Execução, orçamento e alcance dos controles

## Não confundir quatro coisas
1. Ferramenta local sem chamada ao modelo: não gasta tokens por si só.
2. Conversa principal e subagentes nativos: usam a conta do host e têm consumo próprio.
3. Assinatura: pode ter franquias/créditos extras; custo equivalente de API não é a fatura do assinante.
4. API/serviço adicional: cobrança separada só com autorização e condições conhecidas.

O usuário não precisa escolher IDs técnicos. O coordenador verifica configuração, pergunta apenas o indispensável e registra consentimento real. Flags de autorização são recibos da decisão, não substitutos para pedi-la.

## Perfis operacionais
| Perfil | Chamadas por lote | Tentativas do mesmo pacote/tarefa | Paralelismo | Pacote de entrada | Espera por chamada |
|---|---:|---:|---:|---:|---:|
| Econômico | 12 | 2 | 1 | 24.000 caracteres | 240 s |
| Equilibrado | 24 | 2 | 2 | 48.000 caracteres | 420 s |
| Elaborado | 40 | 3 | 2 | 64.000 caracteres | 600 s |

São limites de engenharia ajustáveis, não previsões de preço ou qualidade. Não degradar sentido, áudio, fatos ou aprovação para caber. Premium requer permissão no econômico/equilibrado; o elaborado permite a função, mas não dispensa o orçamento. O limite global também conta chamadas canceladas, conservadoramente.

## Fluxo controlado
`factory.py run` faz prévia por padrão. Só `--execute` inicia uma chamada, após:
- modelo confirmado pelo usuário/host em `model-bind`, CLI compatível e pacote dentro do limite;
- orçamento e autorização de envio remotos definidos para o lote;
- saldo/concorrência/tentativas verificados em transação SQLite;
- reserva registrada antes da inicialização do processo.

Usa a conta configurada no CLI, não lê credenciais nem ativa API alternativa. O worker recebe texto/código explicitamente selecionado em diretório temporário, com ferramentas/delegação desabilitadas. A visão nativa do coordenador é **fora** desta contabilidade; não prometer que ela ficou limitada por `run`.

Concluído: salvar texto final, uso reportado, modelo solicitado versus modelos reportados e referência do artefato. Não persistir fluxo interno de raciocínio. Se o host não informa modelo ou custo, marcar desconhecido.

Se cair, exceder tempo ou retornar algo não conciliável: manter reserva, marcar pendência, não repetir. `settle` exige consumo apurado e origem. Não cancelar custo de processo que já iniciou. Reuso de chamada concluída evita gasto; retry é explícito e limitado.

## Teto em dólares
**Uma reserva por chamada, um orçamento compartilhado por lote.** Dois vídeos não multiplicam a verba; retomar não apaga gastos. Chamadas concorrentes disputam o mesmo saldo transacional.

**Claude Code:** em modo USD, passa a reserva a `--max-budget-usd` no modo não interativo. O registro da fábrica acompanha várias execuções. Exige CLI compatível com modo restrito; a v1.6 pede 2.1.248+. A parada nativa não deve ser apresentada como uma garantia de centavos exatos: uma chamada em andamento ou mudança de cobrança pode gerar excesso. Qualquer excesso reportado congela o lote até conciliar e autorizar continuação.

**Codex:** não há teto nativo em USD implementado neste adaptador. O modo padrão `cap_mode=native` **bloqueia a execução monetária** em vez de inventar uma flag. O usuário pode autorizar `cap_mode=estimate`; haverá reserva/limites operacionais, mas não teto dentro da chamada. Se só vierem tokens, o saldo permanece pendente até conciliação. Não deduzir preço sem uma tabela vigente e aplicável, nem assumir custo zero.

**Assinatura:** contabilizar tentativas e uso disponível, não anunciar dinheiro economizado nem “custo zero”. O controlador não verifica a configuração de créditos extras nem consegue proibir cobranças em toda a conta. Confirme isso no host com o usuário.

## Escopo real da proteção
Protege chamadas que passam pelo controlador. Não governa conversa principal, subagentes nativos fora dele, outros comandos do agente, geradores externos, assinaturas ou faturamento do provedor. Um agente com escrita e shell pode contornar controles; isto não é uma fronteira de segurança contra código malicioso. Para teto empresarial rígido, acrescente limites no próprio provedor/conta quando disponíveis, verificados na implantação.

Serviços externos de imagem/vídeo não são conectados automaticamente. A versão não contém adaptador de faturamento desses serviços: apresentar proposta e consentimento separado, nunca alegar cobertura do saldo local para uma ferramenta não integrada.

## Quando parar
Saldo insuficiente, gasto desconhecido, modelo ausente, CLI incompatível, necessidade de envio não autorizado ou repetição sem melhora: explicar a pendência em linguagem comum. Oferecer uma alternativa concreta de produção ou aguardar decisão. Não gastar nem baixar a qualidade silenciosamente.
