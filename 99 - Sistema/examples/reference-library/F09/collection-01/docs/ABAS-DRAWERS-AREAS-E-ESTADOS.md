# OMNX — Abas, drawers, áreas e estados

Este arquivo existe para evitar uma confusão comum em reunião: **nem tudo que aparece no produto é uma nova página**. Abaixo estão os elementos que vivem dentro das telas principais da V5.

## M00 — Base visual executável

- **Estados compartilhados** — *estado*. Exemplos de vazio, erro, sucesso e carregamento.

## M01 — Conversas

- **IA conduzindo** — *estado*. Mostra quando a IA está no controle e impede envio humano acidental.
- **Conversa assumida** — *estado*. Libera o compositor para o atendente humano após confirmação.
- **Ligação e gravação** — *área*. Permite ligar e consultar o histórico de chamadas quando elegível.
- **Info / Timeline / Anotações** — *área*. Mostra dados, histórico e notas sem sair da conversa.

## M02 — Acesso, primeiro uso e empresa

- **Convite expirado / acesso negado** — *estado*. Explica por que o acesso não pode continuar e qual o próximo passo.
- **Troca de empresa** — *área*. Alterna apenas entre empresas às quais o usuário tem acesso.

## M03 — Visão geral

- **Precisa de você** — *área*. Lista apenas pendências contextuais que exigem atenção.
- **Próximas conversas** — *área*. Antecipação dos contatos agendados ou esperados.
- **Saúde dos números** — *área*. Sinais rápidos sobre canais e indicadores operacionais.
- **Vazio / erro / desatualizado** — *estado*. Explica quando não há dados ou a informação não está atualizada.

## M04 — Contatos, ficha 360 e histórico

- **Cadastros / entradas** — *aba*. Mostra cada vez que a pessoa entrou por uma origem ou formulário.
- **Conversas** — *aba*. Lista as threads corretas sem fundi-las.
- **Timeline** — *área*. Ordena eventos relevantes do relacionamento.
- **Mesclagem de identidade** — *estado*. Une identidades quando há evidência de que são a mesma pessoa.

## M05 — Oportunidades e Pipelines

- **Detalhe da oportunidade** — *drawer*. Explica produto, origem, previsão e próximas ações.
- **Funil analítico** — *área*. Resume conversão entre marcos sem permitir edição manual de fatos.

## M06 — Pré-vendas / SDR

- **Qualificação** — *área*. Registra os critérios necessários para saber se o lead pode avançar.
- **Consulta de closers** — *área*. Mostra pessoas elegíveis e horários disponíveis.
- **Reserva confirmada** — *estado*. Confirma o agendamento de forma reconciliada com o Sell.
- **Exceções de agenda** — *estado*. Trata ausência de dados, conflito ou falta de horário.

## M07 — Vendas e contratos

- **Proposta comercial** — *aba*. Mostra versão, valor, validade e documentos.
- **Contrato** — *área*. Gera e revisa a minuta comercial autorizada.
- **Signatários** — *área*. Controla quem precisa assinar e o status de cada pessoa.
- **Registro de assinatura externa** — *estado*. Guarda evidência de assinatura sem fingir que o OMNX é o assinador.
- **Pagamento** — *área*. Registra condição e situação financeira sem confundir com ganho.

## M08 — Recuperação

- **Acordos / histórico** — *aba*. Registra compromissos e tentativas anteriores.
- **Reentrada** — *estado*. Devolve a oportunidade ao fluxo quando ela volta a avançar.
- **Opt-out / desfecho** — *estado*. Encerra a recuperação respeitando consentimento e motivo.

## M09 — Agenda Sell

- **Agendar reunião** — *drawer*. Drawer com contato, evento, data e horário.
- **Conflito / confirmação incerta** — *estado*. Impede afirmar reserva antes de confirmação real.
- **Remarcação / cancelamento / ausência** — *estado*. Mantém o histórico do evento sem apagar o que ocorreu.

## M10 — Painel comercial

- **Painel Pré-vendas** — *aba*. Acompanha geração, contato e qualificação.
- **Painel Vendas** — *aba*. Acompanha reunião, proposta, negociação e fechamento.
- **Painel Recuperação** — *aba*. Acompanha retomadas, reentradas e desfechos.
- **Consolidado** — *aba*. Une os recortes sem somar a mesma venda duas vezes.
- **Dicionário de métricas** — *área*. Explica fonte, unidade, numerador e denominador.

## M11 — Metas

- **Quem vê o quê** — *área*. Aplica as permissões definidas em M13.
- **Ajuste / histórico** — *estado*. Mantém rastreabilidade de alterações e lançamentos.

## M12 — Times, funções, distribuição e prioridade

- **Simulação** — *estado*. Mostra por que um lead iria para determinada pessoa.
- **Sem destino** — *estado*. Expõe a exceção quando nenhuma regra encontra responsável.

## M13 — Perfis e permissões

- **Permissões de campo** — *área*. Protege dados específicos dentro de um recurso.
- **Ver como** — *estado*. Simula a experiência sem assumir a identidade do usuário.
- **Acesso negado** — *estado*. Bloqueia ações não autorizadas com explicação clara.

## M14 — Agentes e prompts

- **Produtos e campos consultáveis** — *área*. Limita o que o agente pode usar.
- **Versões** — *aba*. Mantém histórico e permite comparar mudanças.
- **Saúde e custo** — *área*. Exibe sinais de operação e consumo do agente.

## M15 — Conhecimento

- **Ingestão / processamento** — *estado*. Explica o estado do conteúdo enquanto é preparado.
- **Conflito de informação** — *estado*. Sinaliza divergência com uma fonte estruturada mais autoritativa.
- **Revogação** — *estado*. Impede uso futuro de conteúdo retirado.

## M16 — Números, cobertura e copiloto

- **Saúde e capacidade** — *área*. Mostra disponibilidade e limites do canal.
- **Rota de ligação** — *área*. Indica se o número é elegível para chamadas.
- **Falha / indisponível** — *estado*. Impede prometer uma capacidade que não está conectada.

## M17 — Laboratório e publicação

- **Rascunho** — *estado*. Área de trabalho antes da validação.
- **Piloto / sombra** — *estado*. Testa com risco reduzido antes da produção.
- **Publicação e rollback** — *estado*. Coloca a versão no ar ou volta para a anterior.

## M18 — Cadências e modelos

- **Versões** — *aba*. Mantém histórico de alterações.
- **Bloqueio por opt-out/frequência** — *estado*. Impede uso quando a regra não permite contato.

## M19 — WhatsApp Marketing

- **Templates** — *aba*. Consulta situação e versões autorizadas.
- **Resposta recebida** — *estado*. Retorna para a thread correta no módulo Conversas.

## M20 — Captação e Entradas

- **UTMs e origem** — *área*. Preserva aquisição sem transformar campanha em entidade obrigatória.
- **Erro / duplicidade** — *estado*. Explica problemas de ingestão e como foram reconciliados.

## M21 — Loja de Apps

- **Categorias** — *aba*. Ajuda a encontrar apps por objetivo.
- **Meus apps** — *aba*. Mostra somente o que a empresa já instalou.
- **Detalhe do app** — *drawer*. Explica função, requisitos e ação principal.
- **Estados do app** — *estado*. Diferencia disponível, instalado, configurar, ativo e conectado.

## M22 — Central de Conexões

- **Conexões compartilhadas** — *aba*. Mostra recursos disponíveis para mais de um módulo.
- **Webhooks / API** — *aba*. Acompanha comunicação técnica autorizada.
- **Logs** — *aba*. Ajuda a diagnosticar falhas de sincronização.
- **Reconectar / indisponível** — *estado*. Mostra quando uma capacidade precisa de nova autorização.

## M23 — Exceções e ajuda contextual

- **Exceção contextual** — *estado*. Aviso no ponto exato onde a operação ficou bloqueada.
- **Detalhe da causa** — *drawer*. Explica o que faltou e qual impacto.
- **Ação recomendada** — *área*. Leva ao módulo correto para resolver.
- **Ajuda contextual** — *área*. Explica termos ou regras sem tirar o usuário do fluxo.

## M24 — Privacidade, auditoria e continuidade

- **Retenção / exportação** — *área*. Controla ciclo de vida e saída autorizada de informações.
- **Acesso restrito** — *estado*. Protege ações sensíveis por permissão.

## M25 — Automações

- **Teste / simulação** — *estado*. Permite validar antes de publicar.
- **Falha / retry** — *estado*. Explica erro e tentativa segura de recuperação.

## M26 — Créditos e consumo

- **Histórico** — *aba*. Lista lançamentos e períodos.
- **BYOK / governança** — *estado*. Restringe configurações sensíveis ao dono da plataforma.

## M27 — Produtos e ofertas

- **Publicação** — *estado*. Controla quando uma versão passa a valer.
- **Uso em outros módulos** — *área*. Mostra onde aquela oferta está sendo consultada.

## M99 — Integração final

- **Jornadas críticas** — *teste*. Valida fluxos ponta a ponta, como lead → venda → recuperação.
- **Matriz de contratos** — *teste*. Confere regras compartilhadas e limites entre módulos.
- **Resultado da validação** — *estado*. Resume o que passou, falhou ou ficou pendente.
