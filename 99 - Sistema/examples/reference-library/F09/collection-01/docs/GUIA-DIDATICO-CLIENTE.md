# OMNX — Guia didático tela por tela

Este guia foi escrito para responder às perguntas mais comuns de uma reunião: **para que serve, onde fica, quem usa, como chega e o que acontece depois**.

## Como explicar a arquitetura

- **Tela/página**: destino real que merece uma visualização própria.
- **Aba, drawer ou estado**: aparece dentro de uma tela; não é contado artificialmente como outra página.
- **Prancha do módulo**: reúne as principais telas e relações para explicar o fluxo sem perder contexto.

## M00 — Base visual executável

**Em uma frase:** Base que garante que todas as partes do OMNX falem a mesma linguagem visual.
**Onde fica:** Base / catálogo do produto
**Quem usa:** Produto, design e desenvolvimento.

### Catálogo do produto

**Para que serve:** Mostra os módulos e permite navegar entre eles.
**Explicação simples:** Base que garante que todas as partes do OMNX falem a mesma linguagem visual.
**Como chegar:** Acesse Base / catálogo do produto e abra “Catálogo do produto”.
**Quando aparece/é usada:** Sempre: é a fundação usada pelos outros módulos.
**Depois:** Os módulos reutilizam estes componentes e padrões, evitando telas desconectadas.
**Não confundir com:** Não é uma área de negócio para o usuário final; é a base do produto.

### Base visual

**Para que serve:** É o mostruário dos componentes usados no sistema inteiro.
**Explicação simples:** Serve para conferir botões, campos, tabelas, mensagens e padrões antes de criar novas telas.
**Como chegar:** Acesse Base / catálogo do produto e abra “Base visual”.
**Quando aparece/é usada:** Sempre: é a fundação usada pelos outros módulos.
**Depois:** Os módulos reutilizam estes componentes e padrões, evitando telas desconectadas.
**Não confundir com:** Não é uma área de negócio para o usuário final; é a base do produto.

**Elementos que aparecem dentro dessas telas:** Estados compartilhados (estado).

## M01 — Conversas

**Em uma frase:** Central de atendimento onde IA e equipe humana trabalham sobre a mesma conversa.
**Onde fica:** Operação › Conversas
**Quem usa:** SDRs, closers, recuperação e gestores autorizados.

### Inbox / fila

**Para que serve:** Organiza as conversas que precisam de atenção.
**Explicação simples:** Central de atendimento onde IA e equipe humana trabalham sobre a mesma conversa.
**Como chegar:** Acesse Operação › Conversas e abra “Inbox / fila”.
**Quando aparece/é usada:** Quando chega uma mensagem, é preciso responder, ligar, revisar ou assumir o atendimento.
**Depois:** O atendimento pode qualificar, agendar, vender, recuperar ou ser concluído sem criar outra conversa.
**Não confundir com:** Não é um inbox diferente para Marketing e não duplica conversas por canal.

### Thread da conversa

**Para que serve:** É onde o atendimento realmente acontece.
**Explicação simples:** Aqui ficam mensagens, áudio, ligação, contexto do lead e a troca de controle entre IA e humano.
**Como chegar:** Acesse Operação › Conversas e abra “Thread da conversa”.
**Quando aparece/é usada:** Quando chega uma mensagem, é preciso responder, ligar, revisar ou assumir o atendimento.
**Depois:** O atendimento pode qualificar, agendar, vender, recuperar ou ser concluído sem criar outra conversa.
**Não confundir com:** Não é um inbox diferente para Marketing e não duplica conversas por canal.

**Elementos que aparecem dentro dessas telas:** IA conduzindo (estado), Conversa assumida (estado), Ligação e gravação (área), Info / Timeline / Anotações (área).

## M02 — Acesso, primeiro uso e empresa

**Em uma frase:** Entrada no sistema, convites e configuração da empresa.
**Onde fica:** Configuração › Empresa / acesso
**Quem usa:** Dono, administrador e usuários convidados.

### Configuração da empresa

**Para que serve:** Cadastra dados institucionais e mantém rascunho.
**Explicação simples:** Entrada no sistema, convites e configuração da empresa.
**Como chegar:** Acesse Configuração › Empresa / acesso e abra “Configuração da empresa”.
**Quando aparece/é usada:** No primeiro acesso, ao aceitar convite, trocar de empresa ou ajustar preferências.
**Depois:** Depois da empresa configurada, o usuário segue para os módulos que sua permissão libera.
**Não confundir com:** Não substitui os editores de IA, times ou integrações; apenas direciona para eles.

### Login

**Para que serve:** É a porta de entrada segura do OMNX.
**Explicação simples:** O usuário informa seus dados e entra somente nas empresas e áreas para as quais tem permissão.
**Como chegar:** Aparece antes de entrar no sistema.
**Quando aparece/é usada:** No primeiro acesso, ao aceitar convite, trocar de empresa ou ajustar preferências.
**Depois:** Depois da empresa configurada, o usuário segue para os módulos que sua permissão libera.
**Não confundir com:** Não substitui os editores de IA, times ou integrações; apenas direciona para eles.

### Recuperação de acesso

**Para que serve:** Ajuda quem esqueceu a senha a voltar ao sistema.
**Explicação simples:** Envia um processo seguro de redefinição sem expor informações da conta.
**Como chegar:** Na tela Login, use “Esqueci minha senha”.
**Quando aparece/é usada:** No primeiro acesso, ao aceitar convite, trocar de empresa ou ajustar preferências.
**Depois:** Depois da empresa configurada, o usuário segue para os módulos que sua permissão libera.
**Não confundir com:** Não substitui os editores de IA, times ou integrações; apenas direciona para eles.

### Convite e aceite

**Para que serve:** É como uma pessoa entra na equipe de uma empresa.
**Explicação simples:** O convite confirma a empresa, o papel e o acesso antes de liberar o uso.
**Como chegar:** Aparece ao abrir um convite válido recebido por link.
**Quando aparece/é usada:** No primeiro acesso, ao aceitar convite, trocar de empresa ou ajustar preferências.
**Depois:** Depois da empresa configurada, o usuário segue para os módulos que sua permissão libera.
**Não confundir com:** Não substitui os editores de IA, times ou integrações; apenas direciona para eles.

**Elementos que aparecem dentro dessas telas:** Convite expirado / acesso negado (estado), Troca de empresa (área).

## M03 — Visão geral

**Em uma frase:** Resumo do que está acontecendo agora e do que precisa de atenção.
**Onde fica:** Operação › Início
**Quem usa:** Qualquer usuário operacional, dentro do seu escopo de acesso.

### Visão geral

**Para que serve:** Resumo executivo da operação no período.
**Explicação simples:** Resumo do que está acontecendo agora e do que precisa de atenção.
**Como chegar:** Acesse Operação › Início e abra “Visão geral”.
**Quando aparece/é usada:** Ao iniciar o dia ou quando alguém precisa entender rapidamente a situação da operação.
**Depois:** Cada bloco abre o registro ou módulo correto para a pessoa agir.
**Não confundir com:** Não é o painel comercial completo e não vira uma central genérica de tarefas.

**Elementos que aparecem dentro dessas telas:** Precisa de você (área), Próximas conversas (área), Saúde dos números (área), Vazio / erro / desatualizado (estado).

## M04 — Contatos, ficha 360 e histórico

**Em uma frase:** Cadastro único do cliente com histórico completo.
**Onde fica:** Operação › CRM › Contatos
**Quem usa:** Atendimento, comercial, recuperação e gestores autorizados.

### Ficha 360

**Para que serve:** Concentra identificação, classificação e dados governados.
**Explicação simples:** Cadastro único do cliente com histórico completo.
**Como chegar:** Acesse Operação › CRM › Contatos e abra “Ficha 360”.
**Quando aparece/é usada:** Quando alguém precisa entender quem é o contato e tudo o que já aconteceu com ele.
**Depois:** A partir da ficha é possível abrir a conversa correta, consultar entradas e oportunidades ou revisar o histórico.
**Não confundir com:** Um contato não é a mesma coisa que uma conversa, cadastro ou oportunidade.

### Lista de contatos

**Para que serve:** É a agenda central de pessoas do OMNX.
**Explicação simples:** Permite localizar contatos e abrir a ficha completa sem duplicar a pessoa por campanha ou canal.
**Como chegar:** Acesse Operação › CRM › Contatos e abra “Lista de contatos”.
**Quando aparece/é usada:** Quando alguém precisa entender quem é o contato e tudo o que já aconteceu com ele.
**Depois:** A partir da ficha é possível abrir a conversa correta, consultar entradas e oportunidades ou revisar o histórico.
**Não confundir com:** Um contato não é a mesma coisa que uma conversa, cadastro ou oportunidade.

**Elementos que aparecem dentro dessas telas:** Cadastros / entradas (aba), Conversas (aba), Timeline (área), Mesclagem de identidade (estado).

## M05 — Oportunidades e Pipelines

**Em uma frase:** Organização das oportunidades e do andamento comercial.
**Onde fica:** Operação › Comercial › Oportunidades e Pipelines
**Quem usa:** SDRs, closers, gestores e recuperação conforme permissão.

### Lista de oportunidades

**Para que serve:** Mostra oportunidades, valores, etapa e responsável.
**Explicação simples:** Organização das oportunidades e do andamento comercial.
**Como chegar:** Acesse Operação › Comercial › Oportunidades e Pipelines e abra “Lista de oportunidades”.
**Quando aparece/é usada:** Quando é preciso acompanhar o avanço das oportunidades e entender o funil.
**Depois:** A oportunidade segue de etapa conforme fatos reais do processo, e pode abrir contato, conversa ou detalhes.
**Não confundir com:** Funil analítico não é um quadro manual de arrastar cards; campanha é dimensão de aquisição, não entidade obrigatória.

### Pipeline operacional

**Para que serve:** Mostra em que etapa operacional cada oportunidade está.
**Explicação simples:** As etapas refletem fatos reais do processo e não dependem de arrastar cards para “forçar” um status.
**Como chegar:** Acesse Operação › Comercial › Oportunidades e Pipelines e abra “Pipeline operacional”.
**Quando aparece/é usada:** Quando é preciso acompanhar o avanço das oportunidades e entender o funil.
**Depois:** A oportunidade segue de etapa conforme fatos reais do processo, e pode abrir contato, conversa ou detalhes.
**Não confundir com:** Funil analítico não é um quadro manual de arrastar cards; campanha é dimensão de aquisição, não entidade obrigatória.

**Elementos que aparecem dentro dessas telas:** Detalhe da oportunidade (drawer), Funil analítico (área).

## M06 — Pré-vendas / SDR

**Em uma frase:** Espaço de trabalho do SDR para qualificar e agendar.
**Onde fica:** Operação › Conversas › contexto Pré-vendas / SDR
**Quem usa:** SDRs e gestores de pré-vendas.

### Fila do SDR

**Para que serve:** Prioriza os leads sob responsabilidade da pré-venda.
**Explicação simples:** Espaço de trabalho do SDR para qualificar e agendar.
**Como chegar:** Acesse Operação › Conversas › contexto Pré-vendas / SDR e abra “Fila do SDR”.
**Quando aparece/é usada:** Quando um lead novo precisa ser entendido e, se qualificado, encaminhado para reunião.
**Depois:** Com a reserva confirmada, o SDR volta ao chat e a oportunidade segue para a próxima função conforme a regra.
**Não confundir com:** Agendar não significa vender e não transfere automaticamente a carteira.

**Elementos que aparecem dentro dessas telas:** Qualificação (área), Consulta de closers (área), Reserva confirmada (estado), Exceções de agenda (estado).

## M07 — Vendas e contratos

**Em uma frase:** Área do closer para conduzir proposta, contrato e assinatura.
**Onde fica:** Operação › Comercial › Vendas e contratos
**Quem usa:** Closers, comercial, financeiro e revisores autorizados.

### Negócio / visão geral

**Para que serve:** Reúne contexto, etapa atual e responsáveis.
**Explicação simples:** Área do closer para conduzir proposta, contrato e assinatura.
**Como chegar:** Acesse Operação › Comercial › Vendas e contratos e abra “Negócio / visão geral”.
**Quando aparece/é usada:** Depois da reunião, durante proposta, negociação, conferência e formalização.
**Depois:** O processo separa proposta, contrato, assinatura e pagamento para que cada marco seja verificável.
**Não confundir com:** Venda ganha, contrato assinado e valor recebido são coisas diferentes.

**Elementos que aparecem dentro dessas telas:** Proposta comercial (aba), Contrato (área), Signatários (área), Registro de assinatura externa (estado), Pagamento (área).

## M08 — Recuperação

**Em uma frase:** Fluxo para retomar oportunidades que esfriaram ou venceram.
**Onde fica:** Operação › Conversas / Comercial › Recuperação
**Quem usa:** Equipe de recuperação e gestores.

### Detalhe da recuperação

**Para que serve:** Explica motivo, prazo, equipe anterior e objetivo.
**Explicação simples:** Fluxo para retomar oportunidades que esfriaram ou venceram.
**Como chegar:** Acesse Operação › Conversas / Comercial › Recuperação e abra “Detalhe da recuperação”.
**Quando aparece/é usada:** Quando uma regra ou prazo indica que a oportunidade saiu do fluxo normal e precisa ser retomada.
**Depois:** A recuperação pode resultar em reentrada, agendamento, retorno ao time anterior, opt-out ou encerramento.
**Não confundir com:** Não é pós-venda e não cria uma nova pessoa ou uma nova oportunidade artificial.

### Fila de recuperação

**Para que serve:** Organiza quem precisa ser retomado.
**Explicação simples:** Prioriza clientes ou oportunidades que saíram do fluxo normal e precisam de nova tentativa.
**Como chegar:** Acesse Operação › Conversas / Comercial › Recuperação e abra “Fila de recuperação”.
**Quando aparece/é usada:** Quando uma regra ou prazo indica que a oportunidade saiu do fluxo normal e precisa ser retomada.
**Depois:** A recuperação pode resultar em reentrada, agendamento, retorno ao time anterior, opt-out ou encerramento.
**Não confundir com:** Não é pós-venda e não cria uma nova pessoa ou uma nova oportunidade artificial.

**Elementos que aparecem dentro dessas telas:** Acordos / histórico (aba), Reentrada (estado), Opt-out / desfecho (estado).

## M09 — Agenda Sell

**Em uma frase:** Agenda comercial espelhada do Sell para reuniões e compromissos.
**Onde fica:** Operação › Comercial › Agenda Sell
**Quem usa:** SDRs, closers e gestores autorizados.

### Agenda semanal

**Para que serve:** Mostra compromissos e disponibilidade por horário.
**Explicação simples:** Agenda comercial espelhada do Sell para reuniões e compromissos.
**Como chegar:** Acesse Operação › Comercial › Agenda Sell e abra “Agenda semanal”.
**Quando aparece/é usada:** Ao agendar, remarcar, cancelar ou consultar compromissos comerciais.
**Depois:** Uma confirmação reconciliada volta para o atendimento e atualiza o contexto da oportunidade.
**Não confundir com:** A agenda não transfere titularidade do lead e não inventa calendários fora do Sell.

### Agenda diária / lista

**Para que serve:** É uma leitura rápida dos compromissos do dia.
**Explicação simples:** Ajuda SDRs e closers a enxergar horários, conflitos, reuniões e lembretes sem navegar pela semana inteira.
**Como chegar:** Acesse Operação › Comercial › Agenda Sell e abra “Agenda diária / lista”.
**Quando aparece/é usada:** Ao agendar, remarcar, cancelar ou consultar compromissos comerciais.
**Depois:** Uma confirmação reconciliada volta para o atendimento e atualiza o contexto da oportunidade.
**Não confundir com:** A agenda não transfere titularidade do lead e não inventa calendários fora do Sell.

**Elementos que aparecem dentro dessas telas:** Agendar reunião (drawer), Conflito / confirmação incerta (estado), Remarcação / cancelamento / ausência (estado).

## M10 — Painel comercial

**Em uma frase:** Painel de desempenho de pré-vendas, vendas e recuperação.
**Onde fica:** Operação › Painéis › Painel comercial
**Quem usa:** Gestores de pré-vendas, vendas, recuperação e direção.

### Painel comercial

**Para que serve:** É o painel que explica o desempenho comercial do início ao fim, com filtros e métricas auditáveis.
**Explicação simples:** Painel de desempenho de pré-vendas, vendas e recuperação.
**Como chegar:** Acesse Operação › Painéis › Painel comercial.
**Quando aparece/é usada:** Para acompanhar resultado, diagnosticar gargalos e comparar recortes de desempenho.
**Depois:** Os números podem ser abertos nos registros e analisados por fonte, período, pipeline, produto e aquisição.
**Não confundir com:** Cohort e produtividade são análises diferentes; potencial, contratado e recebido também.

**Elementos que aparecem dentro dessas telas:** Painel Pré-vendas (aba), Painel Vendas (aba), Painel Recuperação (aba), Consolidado (aba), Dicionário de métricas (área).

## M11 — Metas

**Em uma frase:** Metas da empresa e do colaborador com fonte e prazo claros.
**Onde fica:** Operação › Metas
**Quem usa:** Gestores e cada colaborador dentro do que pode visualizar.

### Metas por área

**Para que serve:** Resume metas de uma equipe ou área autorizada.
**Explicação simples:** Metas da empresa e do colaborador com fonte e prazo claros.
**Como chegar:** Acesse Operação › Metas e abra “Metas por área”.
**Quando aparece/é usada:** Ao definir metas ou acompanhar progresso ao longo do período.
**Depois:** O progresso é atualizado pela fonte aprovada ou manualmente quando a fonte ainda não está homologada.
**Não confundir com:** A visão individual não precisa expor ranking de colegas; R$ e % podem continuar manuais até homologação.

### Configurar meta

**Para que serve:** É onde o gestor cria ou altera uma meta.
**Explicação simples:** Define indicador, período, responsável, alvo e fonte de medição em um fluxo guiado.
**Como chegar:** Acesse Operação › Metas e abra “Configurar meta”.
**Quando aparece/é usada:** Ao definir metas ou acompanhar progresso ao longo do período.
**Depois:** O progresso é atualizado pela fonte aprovada ou manualmente quando a fonte ainda não está homologada.
**Não confundir com:** A visão individual não precisa expor ranking de colegas; R$ e % podem continuar manuais até homologação.

### Minhas metas

**Para que serve:** Mostra ao colaborador apenas os objetivos que dizem respeito a ele.
**Explicação simples:** Exibe realizado, alvo, falta e prazo sem ranking indevido de colegas.
**Como chegar:** Acesse Operação › Metas e abra “Minhas metas”.
**Quando aparece/é usada:** Ao definir metas ou acompanhar progresso ao longo do período.
**Depois:** O progresso é atualizado pela fonte aprovada ou manualmente quando a fonte ainda não está homologada.
**Não confundir com:** A visão individual não precisa expor ranking de colegas; R$ e % podem continuar manuais até homologação.

**Elementos que aparecem dentro dessas telas:** Quem vê o quê (área), Ajuste / histórico (estado).

## M12 — Times, funções, distribuição e prioridade

**Em uma frase:** Regras de times, distribuição de trabalho e prioridade.
**Onde fica:** Configuração › Times e prioridade
**Quem usa:** Administradores e gestores operacionais.

### Times e funções

**Para que serve:** Organiza pessoas e responsabilidades.
**Explicação simples:** Regras de times, distribuição de trabalho e prioridade.
**Como chegar:** Acesse Configuração › Times e prioridade e abra “Times e funções”.
**Quando aparece/é usada:** Ao montar times, regras de distribuição e critérios de prioridade.
**Depois:** As regras passam a orientar a fila e o encaminhamento, com fallback quando ninguém é elegível.
**Não confundir com:** Reatribuir não reinicia artificialmente prazos e exceção sem destino não vira tarefa genérica.

### Distribuição

**Para que serve:** Define como novos atendimentos encontram a pessoa certa.
**Explicação simples:** Controla elegibilidade, capacidade e fallback para evitar filas sem responsável.
**Como chegar:** Acesse Configuração › Times e prioridade e abra “Distribuição”.
**Quando aparece/é usada:** Ao montar times, regras de distribuição e critérios de prioridade.
**Depois:** As regras passam a orientar a fila e o encaminhamento, com fallback quando ninguém é elegível.
**Não confundir com:** Reatribuir não reinicia artificialmente prazos e exceção sem destino não vira tarefa genérica.

### Prioridade

**Para que serve:** Define quais sinais tornam um atendimento mais urgente.
**Explicação simples:** Pesos, teto, decaimento e expiração ajudam a ordenar a fila com regras transparentes.
**Como chegar:** Acesse Configuração › Times e prioridade e abra “Prioridade”.
**Quando aparece/é usada:** Ao montar times, regras de distribuição e critérios de prioridade.
**Depois:** As regras passam a orientar a fila e o encaminhamento, com fallback quando ninguém é elegível.
**Não confundir com:** Reatribuir não reinicia artificialmente prazos e exceção sem destino não vira tarefa genérica.

**Elementos que aparecem dentro dessas telas:** Simulação (estado), Sem destino (estado).

## M13 — Perfis e permissões

**Em uma frase:** Controle central de perfis e permissões.
**Onde fica:** Configuração › Perfis e permissões
**Quem usa:** Dono, administradores e responsáveis por governança.

### Perfis

**Para que serve:** Lista papéis e escopos de acesso.
**Explicação simples:** Controle central de perfis e permissões.
**Como chegar:** Acesse Configuração › Perfis e permissões e abra “Perfis”.
**Quando aparece/é usada:** Ao criar perfis, limitar dados sensíveis ou definir ações permitidas.
**Depois:** A mesma regra é respeitada na interface, API, exportações, IA, automações e logs.
**Não confundir com:** Não é apenas esconder botão; a autorização precisa valer em todas as camadas.

### Matriz de permissões

**Para que serve:** Define exatamente o que cada perfil pode fazer.
**Explicação simples:** Permite controlar visualização, edição, exportação e ações sensíveis por recurso.
**Como chegar:** Acesse Configuração › Perfis e permissões e abra “Matriz de permissões”.
**Quando aparece/é usada:** Ao criar perfis, limitar dados sensíveis ou definir ações permitidas.
**Depois:** A mesma regra é respeitada na interface, API, exportações, IA, automações e logs.
**Não confundir com:** Não é apenas esconder botão; a autorização precisa valer em todas as camadas.

**Elementos que aparecem dentro dessas telas:** Permissões de campo (área), Ver como (estado), Acesso negado (estado).

## M14 — Agentes e prompts

**Em uma frase:** Configuração dos agentes de IA e suas versões.
**Onde fica:** IA › Agentes e prompts
**Quem usa:** Administradores, especialistas de IA e revisores autorizados.

### Lista de agentes

**Para que serve:** Mostra agentes, função, status e versão.
**Explicação simples:** Configuração dos agentes de IA e suas versões.
**Como chegar:** Acesse IA › Agentes e prompts e abra “Lista de agentes”.
**Quando aparece/é usada:** Ao criar, ajustar ou versionar um agente antes de publicá-lo.
**Depois:** A versão segue para validação e publicação no laboratório, respeitando conhecimento e permissões.
**Não confundir com:** Prompt não vira tabela de preço nem pode ampliar o que o usuário não tem permissão de acessar.

### Editor do agente

**Para que serve:** É o local de configuração de um agente de IA.
**Explicação simples:** Define função, instruções, comportamento e limites antes de publicar uma nova versão.
**Como chegar:** Acesse IA › Agentes e prompts e abra “Editor do agente”.
**Quando aparece/é usada:** Ao criar, ajustar ou versionar um agente antes de publicá-lo.
**Depois:** A versão segue para validação e publicação no laboratório, respeitando conhecimento e permissões.
**Não confundir com:** Prompt não vira tabela de preço nem pode ampliar o que o usuário não tem permissão de acessar.

**Elementos que aparecem dentro dessas telas:** Produtos e campos consultáveis (área), Versões (aba), Saúde e custo (área).

## M15 — Conhecimento

**Em uma frase:** Fontes de conhecimento que alimentam IA e operação.
**Onde fica:** IA › Conhecimento
**Quem usa:** Administradores, operação e responsáveis por conteúdo.

### Biblioteca

**Para que serve:** Lista documentos e fontes disponíveis.
**Explicação simples:** Fontes de conhecimento que alimentam IA e operação.
**Como chegar:** Acesse IA › Conhecimento e abra “Biblioteca”.
**Quando aparece/é usada:** Ao adicionar documentos, revisar fontes ou controlar o que a IA pode usar.
**Depois:** Conteúdo aprovado fica disponível aos agentes autorizados; conteúdo revogado deixa de ser usado no futuro.
**Não confundir com:** Preço, prazo e garantia estruturados em Produtos/Ofertas não devem ser sobrescritos por um PDF divergente.

### Detalhe da fonte

**Para que serve:** Mostra de onde uma informação veio e quem pode usá-la.
**Explicação simples:** Ajuda a manter conhecimento versionado, auditável e com autoridade clara.
**Como chegar:** Acesse IA › Conhecimento e abra “Detalhe da fonte”.
**Quando aparece/é usada:** Ao adicionar documentos, revisar fontes ou controlar o que a IA pode usar.
**Depois:** Conteúdo aprovado fica disponível aos agentes autorizados; conteúdo revogado deixa de ser usado no futuro.
**Não confundir com:** Preço, prazo e garantia estruturados em Produtos/Ofertas não devem ser sobrescritos por um PDF divergente.

**Elementos que aparecem dentro dessas telas:** Ingestão / processamento (estado), Conflito de informação (estado), Revogação (estado).

## M16 — Números, cobertura e copiloto

**Em uma frase:** Números, canais e limites de atuação de IA, copiloto e humano.
**Onde fica:** Configuração › Números e cobertura
**Quem usa:** Administradores de operação e integrações.

### Números e canais

**Para que serve:** Lista identidades de contato e seu estado.
**Explicação simples:** Números, canais e limites de atuação de IA, copiloto e humano.
**Como chegar:** Acesse Configuração › Números e cobertura e abra “Números e canais”.
**Quando aparece/é usada:** Ao ativar um número, revisar saúde do canal ou definir cobertura da IA.
**Depois:** As regras passam a valer nas conversas, respeitando a capacidade real do canal e a autoridade do atendimento.
**Não confundir com:** Número, WABA e rota de ligação são objetos diferentes; configurar um não garante os outros.

### Cobertura

**Para que serve:** Mostra onde IA, copiloto e humano podem atuar.
**Explicação simples:** Evita que a automação aja em canais ou contextos nos quais não está autorizada.
**Como chegar:** Acesse Configuração › Números e cobertura e abra “Cobertura”.
**Quando aparece/é usada:** Ao ativar um número, revisar saúde do canal ou definir cobertura da IA.
**Depois:** As regras passam a valer nas conversas, respeitando a capacidade real do canal e a autoridade do atendimento.
**Não confundir com:** Número, WABA e rota de ligação são objetos diferentes; configurar um não garante os outros.

**Elementos que aparecem dentro dessas telas:** Saúde e capacidade (área), Rota de ligação (área), Falha / indisponível (estado).

## M17 — Laboratório e publicação

**Em uma frase:** Ambiente seguro para testar e publicar mudanças de IA.
**Onde fica:** IA › Laboratório e publicação
**Quem usa:** Equipe de IA, produto e aprovadores.

### Validação

**Para que serve:** Executa cenários e checagens obrigatórias.
**Explicação simples:** Ambiente seguro para testar e publicar mudanças de IA.
**Como chegar:** Acesse IA › Laboratório e publicação e abra “Validação”.
**Quando aparece/é usada:** Antes de publicar uma nova versão de agente, prompt ou comportamento.
**Depois:** Depois de validar, a versão pode ir para sombra, piloto e produção, sempre com possibilidade de reversão.
**Não confundir com:** Fallback nunca deve ignorar segurança ou permissões.

### Simulação

**Para que serve:** Permite testar uma configuração antes de colocá-la em produção.
**Explicação simples:** Mostra resposta, evidências, custo e resultado esperado em cenários controlados.
**Como chegar:** Acesse IA › Laboratório e publicação e abra “Simulação”.
**Quando aparece/é usada:** Antes de publicar uma nova versão de agente, prompt ou comportamento.
**Depois:** Depois de validar, a versão pode ir para sombra, piloto e produção, sempre com possibilidade de reversão.
**Não confundir com:** Fallback nunca deve ignorar segurança ou permissões.

**Elementos que aparecem dentro dessas telas:** Rascunho (estado), Piloto / sombra (estado), Publicação e rollback (estado).

## M18 — Cadências e modelos

**Em uma frase:** Modelos reutilizáveis e sequências de contato.
**Onde fica:** Operação › Cadências e modelos
**Quem usa:** Marketing, pré-vendas e operação autorizada.

### Modelos

**Para que serve:** Biblioteca de mensagens reutilizáveis.
**Explicação simples:** Modelos reutilizáveis e sequências de contato.
**Como chegar:** Acesse Operação › Cadências e modelos e abra “Modelos”.
**Quando aparece/é usada:** Ao preparar modelos ou cadências que serão usados em conversas e automações.
**Depois:** Os ativos podem ser usados por M19 e M25, sempre respeitando opt-out, frequência e autoridade da conversa.
**Não confundir com:** Não é E-mail Marketing e não pode disparar ignorando consentimento ou controle da conversa.

### Editor de modelo

**Para que serve:** É onde uma mensagem reutilizável é preparada.
**Explicação simples:** Define texto, variáveis e regras para que a equipe reutilize conteúdo sem perder controle.
**Como chegar:** Acesse Operação › Cadências e modelos e abra “Editor de modelo”.
**Quando aparece/é usada:** Ao preparar modelos ou cadências que serão usados em conversas e automações.
**Depois:** Os ativos podem ser usados por M19 e M25, sempre respeitando opt-out, frequência e autoridade da conversa.
**Não confundir com:** Não é E-mail Marketing e não pode disparar ignorando consentimento ou controle da conversa.

### Cadências

**Para que serve:** Organiza uma sequência de contatos ao longo do tempo.
**Explicação simples:** Define mensagens, intervalos e condições para continuar ou interromper os próximos passos.
**Como chegar:** Acesse Operação › Cadências e modelos e abra “Cadências”.
**Quando aparece/é usada:** Ao preparar modelos ou cadências que serão usados em conversas e automações.
**Depois:** Os ativos podem ser usados por M19 e M25, sempre respeitando opt-out, frequência e autoridade da conversa.
**Não confundir com:** Não é E-mail Marketing e não pode disparar ignorando consentimento ou controle da conversa.

**Elementos que aparecem dentro dessas telas:** Versões (aba), Bloqueio por opt-out/frequência (estado).

## M19 — WhatsApp Marketing

**Em uma frase:** Gestão de envios de WhatsApp pela API oficial.
**Onde fica:** Marketing › WhatsApp Marketing
**Quem usa:** Marketing e gestores autorizados.

### Campanhas de WhatsApp

**Para que serve:** Lista iniciativas de envio e seu status.
**Explicação simples:** Gestão de envios de WhatsApp pela API oficial.
**Como chegar:** Acesse Marketing › WhatsApp Marketing e abra “Campanhas de WhatsApp”.
**Quando aparece/é usada:** Ao criar uma comunicação ativa para uma audiência permitida.
**Depois:** O envio gera execuções rastreáveis e respostas retornam para a conversa correta, sem criar um inbox paralelo.
**Não confundir com:** Disparo de Marketing não cria oportunidade automaticamente e não substitui o atendimento 1:1.

### Criar envio

**Para que serve:** É o fluxo para preparar um disparo oficial de WhatsApp.
**Explicação simples:** Escolhe público, template, variáveis e horário e faz checagens antes de enviar.
**Como chegar:** Acesse Marketing › WhatsApp Marketing e abra “Criar envio”.
**Quando aparece/é usada:** Ao criar uma comunicação ativa para uma audiência permitida.
**Depois:** O envio gera execuções rastreáveis e respostas retornam para a conversa correta, sem criar um inbox paralelo.
**Não confundir com:** Disparo de Marketing não cria oportunidade automaticamente e não substitui o atendimento 1:1.

### Execução

**Para que serve:** Mostra o que aconteceu depois de um disparo.
**Explicação simples:** Separa entregues, falhas, respostas e opt-outs para que a operação saiba o resultado real.
**Como chegar:** Acesse Marketing › WhatsApp Marketing e abra “Execução”.
**Quando aparece/é usada:** Ao criar uma comunicação ativa para uma audiência permitida.
**Depois:** O envio gera execuções rastreáveis e respostas retornam para a conversa correta, sem criar um inbox paralelo.
**Não confundir com:** Disparo de Marketing não cria oportunidade automaticamente e não substitui o atendimento 1:1.

**Elementos que aparecem dentro dessas telas:** Templates (aba), Resposta recebida (estado).

## M20 — Captação e Entradas

**Em uma frase:** Entradas vindas de formulários, webhooks, APIs e importações.
**Onde fica:** Marketing › Captação e entradas
**Quem usa:** Marketing, operações e administradores.

### Fontes de captação

**Para que serve:** Lista origens conectadas ou disponíveis.
**Explicação simples:** Entradas vindas de formulários, webhooks, APIs e importações.
**Como chegar:** Acesse Marketing › Captação e entradas e abra “Fontes de captação”.
**Quando aparece/é usada:** Ao conectar formulários, Type, páginas, anúncios ou outras fontes de captação.
**Depois:** Cada nova entrada é vinculada ao contato canônico e pode alimentar oportunidade conforme as regras do produto.
**Não confundir com:** Uma pessoa pode ter várias entradas; isso não significa criar várias pessoas.

### Entradas / cadastros

**Para que serve:** Mostra cada submissão recebida pelo sistema.
**Explicação simples:** Preserva origem e dados de entrada sem confundir cadastro com contato ou oportunidade.
**Como chegar:** Acesse Marketing › Captação e entradas e abra “Entradas / cadastros”.
**Quando aparece/é usada:** Ao conectar formulários, Type, páginas, anúncios ou outras fontes de captação.
**Depois:** Cada nova entrada é vinculada ao contato canônico e pode alimentar oportunidade conforme as regras do produto.
**Não confundir com:** Uma pessoa pode ter várias entradas; isso não significa criar várias pessoas.

### Mapeamento de campos

**Para que serve:** Liga os campos de uma fonte externa aos campos corretos do OMNX.
**Explicação simples:** Evita que telefone, e-mail, UTM e respostas entrem no lugar errado.
**Como chegar:** Acesse Marketing › Captação e entradas e abra “Mapeamento de campos”.
**Quando aparece/é usada:** Ao conectar formulários, Type, páginas, anúncios ou outras fontes de captação.
**Depois:** Cada nova entrada é vinculada ao contato canônico e pode alimentar oportunidade conforme as regras do produto.
**Não confundir com:** Uma pessoa pode ter várias entradas; isso não significa criar várias pessoas.

**Elementos que aparecem dentro dessas telas:** UTMs e origem (área), Erro / duplicidade (estado).

## M21 — Loja de Apps

**Em uma frase:** Catálogo das capacidades e aplicativos disponíveis.
**Onde fica:** Operação › Apps
**Quem usa:** Dono e administradores autorizados.

### Todos os apps

**Para que serve:** Catálogo geral de capacidades disponíveis.
**Explicação simples:** Catálogo das capacidades e aplicativos disponíveis.
**Como chegar:** Acesse Operação › Apps e abra “Todos os apps”.
**Quando aparece/é usada:** Quando a empresa quer habilitar uma capacidade nova ou revisar apps já instalados.
**Depois:** Ao escolher um app, o usuário segue para instalar, configurar ou conectar, conforme o estado real.
**Não confundir com:** Disponível, instalado, ativo, configurar e conectado são estados diferentes.

**Elementos que aparecem dentro dessas telas:** Categorias (aba), Meus apps (aba), Detalhe do app (drawer), Estados do app (estado).

## M22 — Central de Conexões

**Em uma frase:** Lugar único para conectar provedores e integrações.
**Onde fica:** Configuração › Integrações
**Quem usa:** Administradores e responsáveis por integrações.

### Provedores

**Para que serve:** Visão principal das conexões externas.
**Explicação simples:** Lugar único para conectar provedores e integrações.
**Como chegar:** Acesse Configuração › Integrações e abra “Provedores”.
**Quando aparece/é usada:** Ao conectar WhatsApp, voz, Type, Sell, Meta, storage, IA ou revisar uma falha.
**Depois:** A conexão habilita as capacidades correspondentes nos módulos que dependem dela.
**Não confundir com:** A tela comum não expõe tokens nem detalhes técnicos sensíveis; isso fica na área de desenvolvedor.

**Elementos que aparecem dentro dessas telas:** Conexões compartilhadas (aba), Webhooks / API (aba), Logs (aba), Reconectar / indisponível (estado).

## M23 — Exceções e ajuda contextual

**Em uma frase:** Pendências que exigem uma ação humana, sempre ligadas ao contexto de origem.
**Onde fica:** Ajuda contextual / exceções operacionais
**Quem usa:** Usuários operacionais e administradores, conforme o problema.

### Precisa de você

**Para que serve:** Mostra problemas operacionais exatamente onde eles acontecem e orienta a pessoa sobre o que fazer.
**Explicação simples:** Pendências que exigem uma ação humana, sempre ligadas ao contexto de origem.
**Como chegar:** Acesse Ajuda contextual / exceções operacionais.
**Quando aparece/é usada:** Quando falta dado, integração, permissão, responsável, capacidade ou alguma condição necessária.
**Depois:** A pessoa resolve a causa ou segue para o módulo responsável; o item desaparece quando a condição é corrigida.
**Não confundir com:** Não é uma central genérica de tarefas nem uma caixa onde tudo vira pendência.

**Elementos que aparecem dentro dessas telas:** Exceção contextual (estado), Detalhe da causa (drawer), Ação recomendada (área), Ajuda contextual (área).

## M24 — Privacidade, auditoria e continuidade

**Em uma frase:** Privacidade, auditoria e mecanismos de continuidade.
**Onde fica:** Configuração › Privacidade e auditoria
**Quem usa:** Dono, administradores, segurança, compliance e auditoria.

### Auditoria

**Para que serve:** Lista ações relevantes com autor, data e contexto.
**Explicação simples:** Privacidade, auditoria e mecanismos de continuidade.
**Como chegar:** Acesse Configuração › Privacidade e auditoria e abra “Auditoria”.
**Quando aparece/é usada:** Ao revisar acesso a dados, rastrear alterações, atender solicitações de privacidade ou verificar continuidade.
**Depois:** As evidências ficam registradas para investigação, prestação de contas e cumprimento das políticas.
**Não confundir com:** Auditoria não deve permitir que a própria pessoa aprove sua exceção ou apague evidências indevidamente.

### Privacidade

**Para que serve:** É a área para tratar solicitações e políticas de dados pessoais.
**Explicação simples:** Centraliza retenção, exportação autorizada e pedidos relacionados à privacidade.
**Como chegar:** Acesse Configuração › Privacidade e auditoria e abra “Privacidade”.
**Quando aparece/é usada:** Ao revisar acesso a dados, rastrear alterações, atender solicitações de privacidade ou verificar continuidade.
**Depois:** As evidências ficam registradas para investigação, prestação de contas e cumprimento das políticas.
**Não confundir com:** Auditoria não deve permitir que a própria pessoa aprove sua exceção ou apague evidências indevidamente.

### Continuidade

**Para que serve:** Mostra como o serviço se recupera de falhas.
**Explicação simples:** Apresenta backups, recuperação e situação operacional sem misturar isso com tarefas comerciais.
**Como chegar:** Acesse Configuração › Privacidade e auditoria e abra “Continuidade”.
**Quando aparece/é usada:** Ao revisar acesso a dados, rastrear alterações, atender solicitações de privacidade ou verificar continuidade.
**Depois:** As evidências ficam registradas para investigação, prestação de contas e cumprimento das políticas.
**Não confundir com:** Auditoria não deve permitir que a própria pessoa aprove sua exceção ou apague evidências indevidamente.

**Elementos que aparecem dentro dessas telas:** Retenção / exportação (área), Acesso restrito (estado).

## M25 — Automações

**Em uma frase:** Criação e acompanhamento de automações.
**Onde fica:** Operação › Automações
**Quem usa:** Administradores e operação autorizada.

### Lista de automações

**Para que serve:** Mostra regras, status e última execução.
**Explicação simples:** Criação e acompanhamento de automações.
**Como chegar:** Acesse Operação › Automações e abra “Lista de automações”.
**Quando aparece/é usada:** Quando uma atividade repetitiva pode ser automatizada sem perder controle e rastreabilidade.
**Depois:** Cada execução registra entrada, decisão, ação, resultado e falha para que seja possível entender o que ocorreu.
**Não confundir com:** Automação não pode ampliar permissão, ignorar opt-out ou executar efeitos externos sem reconciliação.

### Construtor

**Para que serve:** É onde uma automação é montada visualmente.
**Explicação simples:** Combina gatilho, condições, esperas e ações para executar um processo de forma controlada.
**Como chegar:** Acesse Operação › Automações e abra “Construtor”.
**Quando aparece/é usada:** Quando uma atividade repetitiva pode ser automatizada sem perder controle e rastreabilidade.
**Depois:** Cada execução registra entrada, decisão, ação, resultado e falha para que seja possível entender o que ocorreu.
**Não confundir com:** Automação não pode ampliar permissão, ignorar opt-out ou executar efeitos externos sem reconciliação.

### Execuções

**Para que serve:** É o histórico de cada vez que uma automação rodou.
**Explicação simples:** Permite descobrir se deu certo, onde falhou e qual versão foi usada.
**Como chegar:** Acesse Operação › Automações e abra “Execuções”.
**Quando aparece/é usada:** Quando uma atividade repetitiva pode ser automatizada sem perder controle e rastreabilidade.
**Depois:** Cada execução registra entrada, decisão, ação, resultado e falha para que seja possível entender o que ocorreu.
**Não confundir com:** Automação não pode ampliar permissão, ignorar opt-out ou executar efeitos externos sem reconciliação.

**Elementos que aparecem dentro dessas telas:** Teste / simulação (estado), Falha / retry (estado).

## M26 — Créditos e consumo

**Em uma frase:** Saldo, consumo, limites e conciliação de créditos.
**Onde fica:** Configuração › Créditos e consumo
**Quem usa:** Dono, administradores e responsáveis financeiros autorizados.

### Resumo de créditos

**Para que serve:** Mostra saldo, uso e tendência.
**Explicação simples:** Saldo, consumo, limites e conciliação de créditos.
**Como chegar:** Acesse Configuração › Créditos e consumo e abra “Resumo de créditos”.
**Quando aparece/é usada:** Para acompanhar uso, saldo, limites e custo por recurso ou período.
**Depois:** O usuário pode ajustar limites ou revisar consumo, de acordo com a política e permissão da conta.
**Não confundir com:** Crédito e BYOK têm regras de governança próprias e não devem ser alterados por perfis comuns.

### Consumo por recurso

**Para que serve:** Explica onde os créditos estão sendo usados.
**Explicação simples:** Separa IA, voz e outros recursos para que custos não apareçam como um número sem origem.
**Como chegar:** Acesse Configuração › Créditos e consumo e abra “Consumo por recurso”.
**Quando aparece/é usada:** Para acompanhar uso, saldo, limites e custo por recurso ou período.
**Depois:** O usuário pode ajustar limites ou revisar consumo, de acordo com a política e permissão da conta.
**Não confundir com:** Crédito e BYOK têm regras de governança próprias e não devem ser alterados por perfis comuns.

### Limites / alertas

**Para que serve:** Evita surpresas de consumo.
**Explicação simples:** Define limites e avisos antes que uma equipe ultrapasse o orçamento planejado.
**Como chegar:** Acesse Configuração › Créditos e consumo e abra “Limites / alertas”.
**Quando aparece/é usada:** Para acompanhar uso, saldo, limites e custo por recurso ou período.
**Depois:** O usuário pode ajustar limites ou revisar consumo, de acordo com a política e permissão da conta.
**Não confundir com:** Crédito e BYOK têm regras de governança próprias e não devem ser alterados por perfis comuns.

**Elementos que aparecem dentro dessas telas:** Histórico (aba), BYOK / governança (estado).

## M27 — Produtos e ofertas

**Em uma frase:** Catálogo de produtos e condições comerciais.
**Onde fica:** Operação › Produtos e ofertas
**Quem usa:** Comercial, marketing, IA e administradores conforme permissão.

### Catálogo

**Para que serve:** Lista produtos e ofertas disponíveis.
**Explicação simples:** Catálogo de produtos e condições comerciais.
**Como chegar:** Acesse Operação › Produtos e ofertas e abra “Catálogo”.
**Quando aparece/é usada:** Ao cadastrar uma oferta ou quando outro módulo precisa consultar condições comerciais confiáveis.
**Depois:** Produtos e ofertas ficam disponíveis para conversa, proposta, agentes de IA e análises sem copiar preço em vários lugares.
**Não confundir com:** Documento ou prompt não deve sobrescrever uma condição comercial estruturada e vigente.

### Detalhe do produto

**Para que serve:** Mostra tudo o que define um produto.
**Explicação simples:** Reúne descrição, atributos e condições-base que podem ser usadas nas ofertas.
**Como chegar:** Acesse Operação › Produtos e ofertas e abra “Detalhe do produto”.
**Quando aparece/é usada:** Ao cadastrar uma oferta ou quando outro módulo precisa consultar condições comerciais confiáveis.
**Depois:** Produtos e ofertas ficam disponíveis para conversa, proposta, agentes de IA e análises sem copiar preço em vários lugares.
**Não confundir com:** Documento ou prompt não deve sobrescrever uma condição comercial estruturada e vigente.

### Oferta / versão

**Para que serve:** É onde preço e condições comerciais ganham uma versão controlada.
**Explicação simples:** Define valor, validade, prazo, garantia e outras condições sem sobrescrever o histórico.
**Como chegar:** Acesse Operação › Produtos e ofertas e abra “Oferta / versão”.
**Quando aparece/é usada:** Ao cadastrar uma oferta ou quando outro módulo precisa consultar condições comerciais confiáveis.
**Depois:** Produtos e ofertas ficam disponíveis para conversa, proposta, agentes de IA e análises sem copiar preço em vários lugares.
**Não confundir com:** Documento ou prompt não deve sobrescrever uma condição comercial estruturada e vigente.

**Elementos que aparecem dentro dessas telas:** Publicação (estado), Uso em outros módulos (área).

## M99 — Integração final

**Em uma frase:** Mapa final que mostra como as partes do OMNX se conectam.
**Onde fica:** Integração final / validação transversal
**Quem usa:** Produto, QA, design e desenvolvimento.

### Mapa de integração

**Para que serve:** Mostra como os módulos se conectam.
**Explicação simples:** Mapa final que mostra como as partes do OMNX se conectam.
**Como chegar:** Acesse Integração final / validação transversal e abra “Mapa de integração”.
**Quando aparece/é usada:** Antes de considerar uma versão do produto pronta para demonstração ou entrega.
**Depois:** Problemas encontrados voltam para o módulo responsável; o pacote só é considerado integrado quando os contratos passam.
**Não confundir com:** Não é uma tela comercial do usuário final; é uma validação transversal do produto.

**Elementos que aparecem dentro dessas telas:** Jornadas críticas (teste), Matriz de contratos (teste), Resultado da validação (estado).
