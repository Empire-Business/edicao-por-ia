# Raciocínio editorial: da informação ao mecanismo do formato

## Alcance e precedência

Esta orientação organiza decisões e revisões; não cria um formato nem altera uma receita
consolidada. Pedido atual e integridade > exceções autorizadas do trabalho > preferências do
formato > receita fixada > este método > exemplos. Cores e fontes vêm do ID escolhido. Regras
de legenda, áudio, layout, apresentador, persistência de itens e movimento continuam valendo.

Aplicar durante o planejamento visual existente, usando os mesmos beats, shots e IDs. Em
edições sem visuais adicionais, basta o registro editorial atual. Não criar etapa obrigatória,
cota de efeitos, migração nem exigência retroativa para jobs antigos. `keep` fundamentado
continua sendo uma decisão completa; não é falta de edição.

## 1. Ler a relação antes de escolher o bloco

Ler a fala retida inteira e o contexto adjacente. Agrupar a mesma ideia, preservando negações,
condições, exemplos e distinções. Classificar a forma da informação quando isso ajudar:

| Forma | Relação a tornar clara | Verificação editorial |
| --- | --- | --- |
| Lista | Conjunto de itens | Não transformar itens em etapas; preservar acúmulo quando exigido pela receita. |
| Sequência/processo | Ordem, dependência ou mudança de estado | Não inventar etapas nem trocar sua ordem. |
| Comparação/classificação | Critério e relação entre os lados | Não inventar vencedor, equivalência ou causalidade. |
| Quantidade/escala | Valor, unidade, período e referência | Preservar "até" e "mais de"; número não exige contador. |
| Tendência/proporção | Direção ou distribuição | Não inventar série, escala ou porcentagens; identificar ilustração quando aplicável. |
| Definição | Termo e significado | Resumir sem mudar o conceito nem retirar condições. |
| Causa/dependência | O que depende de quê | Não promover correlação ou hipótese a causa comprovada. |
| Demonstração | Ação, objeto ou estado observável | Material genérico não comprova uma ação real. |
| Contexto/narrativa | Situação, mudança ou consequência | Preservar progressão quando presente, sem impor arco obrigatório. |
| Pergunta/conclusão/ênfase | Foco e sentido da frase | Não inventar resposta, promessa ou CTA; respeitar a presença da pessoa prevista pela receita. |

Estas formas são vocabulário de análise, não componentes obrigatórios. Um beat pode ter várias
formas; uma composição pode evoluir por várias falas. Não dividir para atingir duração fixa,
variedade mínima ou ocupação percentual da tela.

## 2. Traduzir a informação para a receita escolhida

Responder de forma curta no plano existente:
1. Qual relação ou ideia esta fala entrega?
2. Qual mecanismo PERMITIDO pela receita a esclarece, ou por que manter a cena?
3. Que material real, dado ou representação conceitual sustenta a escolha?
4. Quando cada parte fica compreensível, e o que deve continuar visível?

Usar o bloco do formato, não transportar o componente de outro exemplo. Uma lista pode aparecer
em mensagens, módulos, itens acumulados ou fala sem inserção, conforme a receita. Não adicionar
gráfico, janela, zoom, B-roll ou metáfora só porque a classificação sugere essa possibilidade.
Se a execução necessária faltar, registrar dependência/exceção no fluxo existente; não reduzir
silenciosamente o formato. Escolher tomadas pela fidelidade, completude e execução, não por
serem as últimas. Pausas, cortes e proteção de palavras seguem a política do formato.

## 3. Ancorar significado, tempo e evidência

Usar o master limpo e a transcrição retimada, depois dos cortes de fala e silêncio. Quando uma
entrada depende de palavra/item, registrar a ocorrência específica: utterance, índice da palavra
no transcript retimado e frame final, conferindo o contexto. Proximidade de QUALQUER palavra
não valida a correspondência semântica. ASR suspeito exige confirmação da fonte, conforme
`method/FACTUALITY.md`; não inventar tempo exato nem afirmar escuta não realizada.

Antecipação de contexto, entrada gradual ou manutenção após a fala são possíveis quando a
receita e a leitura justificarem, com motivo registrado. Não impor tolerância temporal universal,
retimar voz para encaixar efeito/trilha ou substituir tempos finais pelos tempos da fonte.

Separar o papel do material: **demonstração/evidência real**, **contexto**, **conceito** ou
**simulação identificada**. Isso complementa, sem substituir, `evidence`, origem, licença,
hashes e rótulos dos contratos. Print real deve mostrar tela, ação e elemento citados; sem a
captura adequada, registrar pendência ou usar representação permitida que não finja comprovar
a ação. Uma etiqueta "ilustrativo" não autoriza dados inventados.

## 4. Registrar sem duplicar os contratos

Usar `meaning`, `purpose`, `utterance_ids`, tempos e decisões atuais. Quando útil, acrescentar
`editorial_reasoning` ao beat com as chaves de `beat_annotation` em
`visual/EDITORIAL_REASONING_TEMPLATE.json`. Essa anotação opcional não controla renderer,
componentes, aprovação ou timing. Planos antigos continuam válidos sem ela.

Consultar `method/examples/EDITORIAL_DECISIONS.md` para exemplos didáticos. Ao analisar uma
referência real, reunir fala, forma, mecanismo, tempo, frame/hash e razão na nota existente.
Vincular ao UID/receita corretos; separar observação de interpretação. Não afirmar movimento
ou áudio vistos a partir de uma folha estática. Exemplo comentado não aprova formato nem
cria preferência permanente.

## 5. Revisar a decisão no resultado

Manter os gates de `method/QUALITY_BAR.md`, `visual/VISUAL_QA.md` e fidelidade ao formato.
Para cada problema, registrar **tempo/frame + fala/ID + beat/shot + problema + correção +
resultado esperado**, citando render e evidência realmente vistos. Corrigir relação, leitura
ou composição; não preencher intervalos automaticamente com efeitos.

No estúdio, manter os campos de `issues[]` (`gate`, `shot_id`, `start_frame`, `end_frame`,
`fix` e severidade adequada). Pode acrescentar `editorial_context` com `issue_context` do
template. Fora do estúdio, usar o mesmo conteúdo no QA existente. Sem fala, marcar o contexto
de fala como não aplicável; não fabricar trecho. Frames usam a timebase identificada do
relatório, com fim exclusivo; não arredondar FPS fracionário sem autorização. Hash/estrutura
validam integridade, não compreensão.

Após ajuste, rever cenas afetadas e transições; mudança de master, EDL, crop ou plano invalida
evidências dependentes. Preservar limites de rodadas, orçamento, status e histórico. Anotação
não resolve problema, não aprova gate pendente, não substitui playback nem comparação com
a referência real do formato.
