# OMNX — Cola de reunião com o cliente

Use estas respostas quando o cliente perguntar **“onde fica?”** ou **“para que serve?”**. O `index.html` permite pesquisar qualquer tela pelo nome.

## M00 — Base visual executável
- **Serve para:** É a base que mantém todas as telas com a mesma cara, navegação e comportamento.
- **Fica em:** Base / catálogo do produto
- **Telas mostradas:** Catálogo do produto, Base visual
- **Depois:** Os módulos reutilizam estes componentes e padrões, evitando telas desconectadas.

## M01 — Conversas
- **Serve para:** É a caixa de entrada central onde a equipe e a IA atendem clientes sem separar o histórico.
- **Fica em:** Operação › Conversas
- **Telas mostradas:** Inbox / fila, Thread da conversa
- **Depois:** O atendimento pode qualificar, agendar, vender, recuperar ou ser concluído sem criar outra conversa.

## M02 — Acesso, primeiro uso e empresa
- **Serve para:** Cuida da entrada no OMNX e da configuração básica da empresa e do usuário.
- **Fica em:** Configuração › Empresa / acesso
- **Telas mostradas:** Configuração da empresa, Login, Recuperação de acesso, Convite e aceite
- **Depois:** Depois da empresa configurada, o usuário segue para os módulos que sua permissão libera.

## M03 — Visão geral
- **Serve para:** É a página inicial que resume o que está acontecendo e mostra o que precisa de atenção agora.
- **Fica em:** Operação › Início
- **Telas mostradas:** Visão geral
- **Depois:** Cada bloco abre o registro ou módulo correto para a pessoa agir.

## M04 — Contatos, ficha 360 e histórico
- **Serve para:** É a ficha completa de cada pessoa, reunindo cadastro, origem, histórico e relacionamento com a empresa.
- **Fica em:** Operação › CRM › Contatos
- **Telas mostradas:** Ficha 360, Lista de contatos
- **Depois:** A partir da ficha é possível abrir a conversa correta, consultar entradas e oportunidades ou revisar o histórico.

## M05 — Oportunidades e Pipelines
- **Serve para:** Organiza as oportunidades comerciais e mostra em que etapa operacional cada uma está.
- **Fica em:** Operação › Comercial › Oportunidades e Pipelines
- **Telas mostradas:** Lista de oportunidades, Pipeline operacional
- **Depois:** A oportunidade segue de etapa conforme fatos reais do processo, e pode abrir contato, conversa ou detalhes.

## M06 — Pré-vendas / SDR
- **Serve para:** É o ambiente de pré-vendas onde o SDR conversa, qualifica o lead e encontra um horário com o closer.
- **Fica em:** Operação › Conversas › contexto Pré-vendas / SDR
- **Telas mostradas:** Fila do SDR
- **Depois:** Com a reserva confirmada, o SDR volta ao chat e a oportunidade segue para a próxima função conforme a regra.

## M07 — Vendas e contratos
- **Serve para:** É onde o time transforma uma oportunidade qualificada em proposta, contrato e registro comercial consistente.
- **Fica em:** Operação › Comercial › Vendas e contratos
- **Telas mostradas:** Negócio / visão geral
- **Depois:** O processo separa proposta, contrato, assinatura e pagamento para que cada marco seja verificável.

## M08 — Recuperação
- **Serve para:** Reúne oportunidades que precisam de uma nova tentativa de contato antes de serem consideradas perdidas.
- **Fica em:** Operação › Conversas / Comercial › Recuperação
- **Telas mostradas:** Detalhe da recuperação, Fila de recuperação
- **Depois:** A recuperação pode resultar em reentrada, agendamento, retorno ao time anterior, opt-out ou encerramento.

## M09 — Agenda Sell
- **Serve para:** É a agenda comercial do Sell dentro do OMNX, usada para consultar e confirmar reuniões reais.
- **Fica em:** Operação › Comercial › Agenda Sell
- **Telas mostradas:** Agenda semanal, Agenda diária / lista
- **Depois:** Uma confirmação reconciliada volta para o atendimento e atualiza o contexto da oportunidade.

## M10 — Painel comercial
- **Serve para:** É o painel que explica o desempenho comercial do início ao fim, com filtros e métricas auditáveis.
- **Fica em:** Operação › Painéis › Painel comercial
- **Telas mostradas:** Painel comercial
- **Depois:** Os números podem ser abertos nos registros e analisados por fonte, período, pipeline, produto e aquisição.

## M11 — Metas
- **Serve para:** Transforma objetivos comerciais em metas claras, mostrando quanto já foi feito, quanto falta e até quando.
- **Fica em:** Operação › Metas
- **Telas mostradas:** Metas por área, Configurar meta, Minhas metas
- **Depois:** O progresso é atualizado pela fonte aprovada ou manualmente quando a fonte ainda não está homologada.

## M12 — Times, funções, distribuição e prioridade
- **Serve para:** Define quem recebe cada atendimento e em que ordem, considerando disponibilidade, capacidade e prioridade.
- **Fica em:** Configuração › Times e prioridade
- **Telas mostradas:** Times e funções, Distribuição, Prioridade
- **Depois:** As regras passam a orientar a fila e o encaminhamento, com fallback quando ninguém é elegível.

## M13 — Perfis e permissões
- **Serve para:** Controla exatamente quem pode ver ou fazer cada coisa no sistema.
- **Fica em:** Configuração › Perfis e permissões
- **Telas mostradas:** Perfis, Matriz de permissões
- **Depois:** A mesma regra é respeitada na interface, API, exportações, IA, automações e logs.

## M14 — Agentes e prompts
- **Serve para:** É onde a empresa configura os agentes de IA, suas funções e as instruções que orientam cada comportamento.
- **Fica em:** IA › Agentes e prompts
- **Telas mostradas:** Lista de agentes, Editor do agente
- **Depois:** A versão segue para validação e publicação no laboratório, respeitando conhecimento e permissões.

## M15 — Conhecimento
- **Serve para:** É a biblioteca de informações confiáveis que a IA pode consultar para responder e trabalhar.
- **Fica em:** IA › Conhecimento
- **Telas mostradas:** Biblioteca, Detalhe da fonte
- **Depois:** Conteúdo aprovado fica disponível aos agentes autorizados; conteúdo revogado deixa de ser usado no futuro.

## M16 — Números, cobertura e copiloto
- **Serve para:** Configura os números e canais usados no atendimento e define quando IA, copiloto ou humano pode atuar.
- **Fica em:** Configuração › Números e cobertura
- **Telas mostradas:** Números e canais, Cobertura
- **Depois:** As regras passam a valer nas conversas, respeitando a capacidade real do canal e a autoridade do atendimento.

## M17 — Laboratório e publicação
- **Serve para:** É o ambiente seguro para testar mudanças de IA antes de colocá-las em produção.
- **Fica em:** IA › Laboratório e publicação
- **Telas mostradas:** Validação, Simulação
- **Depois:** Depois de validar, a versão pode ir para sombra, piloto e produção, sempre com possibilidade de reversão.

## M18 — Cadências e modelos
- **Serve para:** Guarda mensagens e sequências reutilizáveis para contatos recorrentes no WhatsApp.
- **Fica em:** Operação › Cadências e modelos
- **Telas mostradas:** Modelos, Editor de modelo, Cadências
- **Depois:** Os ativos podem ser usados por M19 e M25, sempre respeitando opt-out, frequência e autoridade da conversa.

## M19 — WhatsApp Marketing
- **Serve para:** É a área para preparar e acompanhar disparos de WhatsApp com governança de templates, público e consentimento.
- **Fica em:** Marketing › WhatsApp Marketing
- **Telas mostradas:** Campanhas de WhatsApp, Criar envio, Execução
- **Depois:** O envio gera execuções rastreáveis e respostas retornam para a conversa correta, sem criar um inbox paralelo.

## M20 — Captação e Entradas
- **Serve para:** Mostra de onde as pessoas estão entrando no OMNX e como cada entrada é registrada sem duplicar o contato.
- **Fica em:** Marketing › Captação e entradas
- **Telas mostradas:** Fontes de captação, Entradas / cadastros, Mapeamento de campos
- **Depois:** Cada nova entrada é vinculada ao contato canônico e pode alimentar oportunidade conforme as regras do produto.

## M21 — Loja de Apps
- **Serve para:** É a loja onde o cliente descobre recursos e integrações que podem ser adicionados ao OMNX.
- **Fica em:** Operação › Apps
- **Telas mostradas:** Todos os apps
- **Depois:** Ao escolher um app, o usuário segue para instalar, configurar ou conectar, conforme o estado real.

## M22 — Central de Conexões
- **Serve para:** É a central onde o OMNX mostra quais serviços externos estão conectados e se estão funcionando.
- **Fica em:** Configuração › Integrações
- **Telas mostradas:** Provedores
- **Depois:** A conexão habilita as capacidades correspondentes nos módulos que dependem dela.

## M23 — Exceções e ajuda contextual
- **Serve para:** Mostra problemas operacionais exatamente onde eles acontecem e orienta a pessoa sobre o que fazer.
- **Fica em:** Ajuda contextual / exceções operacionais
- **Telas mostradas:** Precisa de você
- **Depois:** A pessoa resolve a causa ou segue para o módulo responsável; o item desaparece quando a condição é corrigida.

## M24 — Privacidade, auditoria e continuidade
- **Serve para:** É a área de governança que registra ações importantes, protege dados e ajuda a manter o serviço confiável.
- **Fica em:** Configuração › Privacidade e auditoria
- **Telas mostradas:** Auditoria, Privacidade, Continuidade
- **Depois:** As evidências ficam registradas para investigação, prestação de contas e cumprimento das políticas.

## M25 — Automações
- **Serve para:** Permite montar regras automáticas do tipo “quando isso acontecer, faça aquilo”, com histórico e segurança.
- **Fica em:** Operação › Automações
- **Telas mostradas:** Lista de automações, Construtor, Execuções
- **Depois:** Cada execução registra entrada, decisão, ação, resultado e falha para que seja possível entender o que ocorreu.

## M26 — Créditos e consumo
- **Serve para:** Mostra quanto a empresa está consumindo de recursos de IA e outros serviços medidos por crédito.
- **Fica em:** Configuração › Créditos e consumo
- **Telas mostradas:** Resumo de créditos, Consumo por recurso, Limites / alertas
- **Depois:** O usuário pode ajustar limites ou revisar consumo, de acordo com a política e permissão da conta.

## M27 — Produtos e ofertas
- **Serve para:** É o catálogo oficial do que a empresa vende, com preço, condição e versão controlados.
- **Fica em:** Operação › Produtos e ofertas
- **Telas mostradas:** Catálogo, Detalhe do produto, Oferta / versão
- **Depois:** Produtos e ofertas ficam disponíveis para conversa, proposta, agentes de IA e análises sem copiar preço em vários lugares.

## M99 — Integração final
- **Serve para:** É a checagem final que garante que os módulos funcionem juntos como um único sistema.
- **Fica em:** Integração final / validação transversal
- **Telas mostradas:** Mapa de integração
- **Depois:** Problemas encontrados voltam para o módulo responsável; o pacote só é considerado integrado quando os contratos passam.
