# Relatório de revisão — Video Factory 1.6.0

Data: 27/09/2026. Base: `claude-video-factory-v1.5.0.zip`.
SHA-256 do ZIP de entrada: `199faca7a1a35e9b7f029845b726d98effd038931c80cc8fde5328c4db4f021a`.

## Pedido atendido
Transformar a auditoria e a simulação de uso leigo em mecanismos executáveis: preparação assistida, adaptadores para os dois agentes, continuidade de trabalho e controle persistente de chamadas. Não se trata de outra revisão do Roteirista Universal.

## Implementado
- Entrada simples em `COMECE-AQUI.md` e interface `factory.py`. O agente preenche entradas e executa a parte técnica, com prévia e autorização antes das mudanças.
- Instalação de configuração com mesclagem de hooks/TOML, backups, recibo verificável, idempotência, detecção de conflitos e rollback que preserva edições posteriores.
- Atualizador baseado nos hashes do pacote anterior. Mantém arquivos personalizados e dados privados; versões conflitantes vão para `incoming/`, sem sobrescrever a atual.
- Preparação opcional de dependências em venv: base, transcrição, JS/navegador ou FFmpeg conforme o sistema. Não executada nesta construção; exige autorização local. Diagnóstico distingue presença de componentes de teste efetivo de fala/visão.
- Sete papéis nativos por host, com configurações próprias: `.claude/agents/*.md` e `.codex/agents/*.toml`. Skills de entrada nos dois locais. Modelo disponível na conta precisa ser confirmado; não há fallback automático de assinatura para API.
- Cadastro idempotente, um lote com vários vídeos-filhos, scripts e assets atribuídos sem presumir ordem. Padrão inexistente é rejeitado inclusive para trabalho anônimo.
- Etapas persistentes com artefatos, hashes, detecção de entradas modificadas, comparação de recortes e validação de EDL por vídeo. Prévia não avança para entrega final sem aprovação registrada.
- Alterações pontuais invalidam apenas dependências. Feedback novo aciona conferência e nova configuração efetiva; versões antigas ficam preservadas. Override explícito de legenda/silêncio prevalece sobre preferência do cliente.
- Executor de pacotes curtos de texto/código com conta do CLI, registro de uso e modelos reportados; limites de chamadas/tentativas/tempo/paralelismo. Não é um executor de geração visual ou de toda a edição por conta própria.
- Orçamento de lote em SQLite com reserva transacional antes de iniciar, reuso de resultados, saldo persistente entre processos, retenção de consumo desconhecido e congelamento após excesso.

## Testes executados nesta revisão

| Teste | Resultado | Alcance |
|---|---|---|
| Python — unitários/regressão | **268 passaram** | Inclui 88 testes do novo controlador e os 180 anteriores. Uma fixture antiga passou a incluir o padrão real exigido pelo criador de jobs. |
| JavaScript | **20 passaram** | Lógica de componentes e validações anteriores. |
| Nova integração assistida/controle | **25 verificações passaram** | Filesystem, setup, dois renders FFmpeg reais, jobs isolados, gate de aprovação, retomada em outro processo e contabilidade. Os dois provedores são CLIs FICTÍCIOS de teste. |
| Atualização v1.5 → v1.6 | **14 verificações passaram** | Cópia real do ZIP de entrada, cliente e trabalho fictícios, customizações preservadas, backup e configurações mescladas. Sem iniciar hosts. |
| Render original | **6 verificações passaram** | Decodificação, tamanho, SAR, retiming, SRT e original preservado. |
| Roteiro/silêncio | **16 verificações passaram** | Mídia sintética e timestamps escritos manualmente, render real. |
| Memória → alteração de corte | **18 verificações passaram** | Hooks chamados pelo teste, feedback sintético e render real. |
| JavaScript → composição | **19 verificações passaram** | Navegador/FFmpeg local, transparência, sincronização e áudio. |
| Direção visual → composição | **25 verificações passaram** | Frames extraídos e composição real; cenas/regiões/intenções foram definidas manualmente, não reconhecidas pelo modelo. |

Logs e JSONs desta rodada: `tests/results/v1_6-*`. O teste de memória teve uma execução interrompida por timeout do ambiente; a repetição limitada concluiu as 18 verificações. Não foi contado como sucesso o ensaio interrompido. Um bug de TOML sem newline e a fixture de padrão ausente foram corrigidos antes da rodada final.

## O que NÃO foi testado/garantido
- Não há Claude Code nem Codex CLI instalados neste ambiente. Não foram abertas sessões reais, confirmados modelos da conta nem geradas cobranças.
- Os processos do teste de adaptadores usam `tests/fixtures/fake_host.py`, explicitamente sintético. Testam argumentos, parsing, interrupção e livro de reservas, não autenticidade de respostas ou qualidade dos modelos.
- Não foram instalados transcritores nem baixados pesos. Não houve transcrição real, avaliação semântica de uma gravação sua, reconhecimento automático de cenário, rastreamento, segmentação ou geração externa.
- Instaladores específicos de Windows/macOS não foram executados. Planos e manipulação de arquivos/configurações foram testados no container Linux; implantação em máquina nova ainda pede verificação local.
- Aprovação artística e entendimento do feedback livre continuam dependendo do agente e do usuário. Testes mecânicos não são teste de audiência.

## Alcance financeiro exato
No Claude compatível, o executor integra a parada monetária nativa e o saldo persistente. Não oferece garantia de centavos exatos nem controla a conta inteira. No Codex, o modo monetário nativo é bloqueado; modo de estimativa exige autorização explícita e não limita o preço dentro de uma chamada. Assinatura não é convertida em fatura fictícia. Conversa principal, visão nativa, subagentes fora do executor e serviços externos permanecem fora do saldo automático.

O controlador não é uma fronteira de segurança contra um agente com acesso ao disco/shell. Não foi adicionado nenhum gerador de imagem/vídeo pago ou mecanismo de compra de créditos.

## Preservação e migração
Todos os **188 arquivos** da base continuam presentes. **11 arquivos de padrões** mantidos byte a byte. Fontes/metodologia e ferramentas de edição foram preservadas, exceto os pontos explicitamente atualizados de integração/diagnóstico/criação/validação.
`README` anterior também está em `sources/README_V1_5.md`. Relatórios anteriores permanecem históricos; não são apresentados como novos testes.

A estrutura genérica entregue não contém bancos de cliente, caches, credenciais, modelos, fontes ou vídeos dos testes. A instalação anterior do usuário não foi alterada nesta conversa.

## Conferência de integridade e uso
O pacote contém `PACKAGE_MANIFEST.json`. Em extração nova, `python tools/verify_package.py` deve passar sem diferenças. Após personalizar/instalar, `--installed` diferencia customização local de erro de sintaxe/arquivo ausente.
Use o atualizador a partir da pasta nova apontando para a instalação anterior, como descrito em `workflows/ASSISTED_START.md`. Não basta substituir o diretório inteiro.
