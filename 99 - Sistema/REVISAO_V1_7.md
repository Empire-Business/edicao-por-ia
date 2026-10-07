# Revisão v1.7.0 — Estúdio de motion com referências e crítica verificável

**Data de construção: 27 de setembro de 2026.** Base: ZIP v1.6.0 fornecido na conversa. Melhoria motivada pelo curso de Movez colado pelo usuário. O texto do curso é uma referência de processo, não uma comprovação de todos os resultados sociais que relata.

## Entrega
A edição de fala continua sendo o centro da fábrica. O novo caminho integra referência → linguagem visual → estados por cena → stills → animatic/piloto → código → evidência → reparo pontual → exportação. Os dois agentes acessam o mesmo workflow; o usuário continua pedindo em linguagem natural.

### Executável agora
- Renderer de HTML/Canvas revisado, com `window.seek(t)`, arquivos autorizados por SHA-256, recursos locais explícitos, saída PNG completa e integração ao compositor existente. Não se limita aos quatro componentes SVG anteriores.
- Biblioteca JavaScript de mola analítica nos três regimes, superposição de alvos, indicadores com bordas diferentes, seed reproduzível e layout por formato.
- Teste de repetibilidade por pixels RGBA: repetição, ordem inversa e novo contexto do navegador. Teste amostrado; não é certificação entre máquinas nem teste de emenda.
- Subframes opcionais com alpha premultiplicado, sem cruzar cortes declarados e com limite de amostras. Não é motion blur fisicamente correto em luz linear.
- Validador de plano com estados observáveis, contexto por vídeo, dependências e recomposição de formato. Briefs individuais para delegação seletiva.
- Evidências paginadas, amostragem distribuída por toda a duração, imagens em 360px e sequência de frames perto de uma ação. IDs, tempos e hashes evitam aprovar outra versão sem perceber.
- Registro de revisão com gates e até três problemas prioritários, bloqueio de aprovação sem evidência do tipo adequado e limite de 2/3/4 registros. Ausência de resposta não é consentimento.
- Análise local de batidas/onsets e geração determinística de efeitos sonoros simples. Sem inferir compasso por contar quatro batidas; sem mudar palavras para combinar com música.

### Instruções editoriais, dependentes do agente/revisor
Analisar estética/referência, perceber gestos/fundo, decidir onde uma cena agrega, julgar beleza e assistir/ouvir trechos continuam tarefas do agente com ferramentas adequadas ou de um humano. O validador verifica arquivos e declarações; não consegue provar que alguém realmente os abriu nem que a peça ficou excelente. Um exemplo pode passar em mecânica e continuar fraco artisticamente.

O workflow exige registrar “observado / inferido / proposto”, preservar marca real, não inventar telas e não promover frames de demonstração a referência aprovada do cliente. Nova linguagem pede piloto, sem deixar o usuário escrever JSON ou configurar cada etapa.

## O que foi preservado
Memória por cliente, feedback com alcance, scripts de referência flexíveis, erros de fala, remoção de silêncio, materiais de apoio, animações anteriores, visuais por fala, instalador/atualizador, checkpoints, modelos e controle de custos da v1.6. Arquivos de padrões anteriores não foram reescritos. Relatórios antigos permanecem como histórico datado, não como testes desta edição.

## Custo e instalação
Reutiliza Python + Playwright/Chromium; acrescenta Pillow à preparação de motion que estava incompleta. NumPy atende o blur opcional; o instalador de análise musical é opt-in (`studio-audio`). Não foram instaladas bibliotecas, plugins, vozes ou APIs nesta construção: as dependências disponíveis no ambiente foram reutilizadas.

Os perfis monetários/modelos anteriores não foram substituídos por “Opus max em tudo”. Tarefas de planejar e revisar notas de motion têm rotas de texto/código; render, frames, beats e SFX são locais. Premium e maior esforço só quando necessários e autorizados. Aprovação antecipada encerra revisões; orçamento esgotado mantém o rascunho não aprovado.

**Limite mantido e explícito:** o executor financeiro restrito continua texto/código, sem entrada visual. Abertura de imagens/playback na sessão nativa não é incluída por mágica no teto monetário desse executor. Ele não controla toda a conta nem chamadas feitas fora dele. O novo histórico de revisão limita o ciclo no diretório do job; não é uma nova barreira universal de cobrança.

## Adoção crítica do curso
A matriz completa em `sources/MOVEZ_ADOPTION.md` acompanha suas 12 partes. Adaptamos em vez de copiar: fala antes da música; nenhuma cena obrigatória a cada 2 segundos; sem nota autodeclarada 8 como prova; nenhuma revisão infinita/três rodadas obrigatórias; sem seguir após dez minutos; dados e UI reais; referência não é licença de cópia; opcionalidade de Remotion/HyperFrames.

O fichamento em `sources/MOVEZ_COURSE_NOTES.md` não é o artigo integral. As legendas “Imagem” e os vídeos embutidos no texto não constituem arquivos que tenhamos assistido. Não auditamos métricas de audiência, preços, todos os posts ou os resultados atribuídos aos modelos. Consulta técnica externa focal, separada, em `sources/STUDIO_RESEARCH_V1_7.md`.

## Testes realmente executados
- **331 testes Python**, incluindo 63 novos do estúdio.
- **42 testes JavaScript**, incluindo 22 novos para o movimento analítico.
- **38 verificações na integração nova**, com renderizações reais: 144 frames de uma cena original em HTML/Canvas, subframes opcionais, adaptação vertical/quadrada, asset local, composição com FFmpeg, 192 frames de master preservados e igualdade do bitstream de áudio.
- Dentro da integração, **12 comparações de repetibilidade** de pixels em ordens/sessões diferentes. Um renderer intencionalmente dependente de estado foi detectado; `Math.random` foi bloqueado; prévia incompleta foi recusada pelo compositor.
- Detector musical executado sobre cliques sintéticos de 120 BPM: estimou aproximadamente 117,45 BPM, resultado tratado como estimativa e dentro da tolerância do teste. Downbeats permaneceram desconhecidos. Áudio silencioso produziu lista vazia.
- Regressão de roteiro/silêncio: **16 verificações**. Regressão de memória: **18 verificações**. Regressão das animações anteriores: **19 verificações**. Todas passaram na execução concluída.
- Os registros de “revisor” usados na integração são **declarações simuladas para testar o fluxo**, claramente identificadas. Não são inferência visual ou avaliação artística real.

Os logs ficam em `tests/results/v1.7-*`. Chromium 144.0.7559.96; FFmpeg 7.1.5 no ambiente de construção. Processos numéricos de integração foram executados com limites de threads para evitar sobrecarga; tentativas interrompidas não foram contadas como passagens.

## Integridade e atualização
O verificador estrutural passou com 159 arquivos obrigatórios e sem erros de JSON/YAML/TOML ou hashes. Foram executadas 14 verificações de atualização em uma cópia da v1.6: prévia sem mudança, backup, skills dos dois agentes, novo renderer, preservação de cliente/job/padrão e conflito explícito de um agente personalizado. Configurações nativas ficaram intactas para mesclagem posterior.

Nenhum arquivo da base foi removido. Todos os padrões anteriores foram mantidos byte a byte. Arquivos de execução criados pelos testes, incluindo banco SQLite temporário, foram removidos e não fazem parte do ZIP.

## Inspeção visual realmente feita
Foram abertos quadros renderizados do exemplo. Havia uma conexão cruzando a palavra central: corrigimos a ordem de desenho dos nós em relação às linhas. Os quadros horizontal e vertical foram abertos novamente; o texto central ficou livre. Essa observação é inspeção dos frames, não avaliação de playback, locução, criatividade de outro modelo ou resultado de cliente.

## Não testado / não implementado
Nenhuma sessão real de Codex/Claude Code, chamada cobrada ou identificação de modelos da conta do usuário. Nenhuma nova transcrição real, compreensão semântica de gravação, análise de fundo/gestos pelo modelo, geração externa de imagem/vídeo, locução, máscara/rastreamento 3D, geração-para-traçado ou composição musical sofisticada. Remotion e HyperFrames foram apenas documentados como opções: não instalados/renderizados.

O renderer aceita código revisado, não código hostil. Executá-lo com rede bloqueada não cria uma sandbox universal. A saída convencional é um único Canvas; misturar DOM sobre ele precisa de outro contrato. FPS fracionário exige outro adaptador ou normalização aprovada, não arredondamento silencioso. A revisão final de movimento/áudio permanece pendente quando a ferramenta do agente não permite assistir/ouvir.

## Atualização para quem já usa
Extraia o ZIP em outra pasta e peça ao agente para atualizar a instalação antiga pelo atualizador com backup, preservando clientes, trabalhos e padrões personalizados. Revise conflitos e depois mescle as configurações nativas pelo setup. Não substitua a pasta de trabalho inteira manualmente.

Pedido possível: “Atualize minha fábrica com esta versão, preservando tudo que já foi aprovado. Nas próximas edições, use referências reais, proponha estados visuais, faça um piloto e examine os frames antes de concluir. Mantenha a fala natural e respeite meu orçamento.”
