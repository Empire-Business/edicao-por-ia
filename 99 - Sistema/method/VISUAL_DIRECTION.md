# Direção visual semântica e espacial — v1.5

## Missão
Examinar TODA a fala retida como matéria-prima de direção, não como uma ordem para gerar
uma imagem por frase. Cada unidade recebe uma decisão: preservar o apresentador, mostrar
material real, ilustrar uma relação, demonstrar um processo, animar ou compor uma cena.
Uma decisão `keep` fundamentada conta como cobertura. Não há cota de efeitos.

Este módulo amplia a produção visual. Não substitui o método de roteiros, nem aprova headlines
rejeitadas. A intenção é tornar perceptível o que a fala entrega, sem fabricar evidências.

## Três leituras separadas
1. **Sentido:** o que foi efetivamente dito, com contexto anterior/posterior; negações, comparação,
   metáfora, exemplo, números e intenção narrativa. O roteiro auxilia; a transcrição real manda.
2. **Imagem observada:** enquadramento, cenário visível, fundo, objetos, rosto, mãos, ação,
   movimento, iluminação aparente e espaço disponível. Só registrar como observado o que foi
   visto em frames identificados. Não inferir identidade, emoções íntimas, endereço ou medidas
   físicas pela aparência. Uma imagem não reconstrói a sala oculta.
3. **Direção proposta:** o que acrescentar, com função, estilo, posição, tempo, movimento,
   orçamento e fallback. Proposta não é observação nem material já produzido.

## Do significado ao visual, não da palavra ao ícone
Durante esta leitura, usar `method/EDITORIAL_REASONING.md` para nomear a forma da informação
e ligá-la ao mecanismo permitido pela receita. A classificação organiza o plano existente;
não impõe blocos, cadência, densidade, efeitos ou alteração de formato. `keep` continua válido.

“Tudo depende da aprovação do dono” pode pedir uma sequência de tarefas convergindo para um
único ponto e ficando em espera. Não pede automaticamente foto genérica de executivo nem
três ícones de dinheiro. Construir visualmente a RELAÇÃO descrita: causa, dependência,
transformação, proporção, contraste, sequência, descoberta ou uso de uma resposta.

Agrupar falas consecutivas que desenvolvem a mesma ideia. Uma composição pode evoluir ao
longo de várias falas. Evitar colagem de estilos e troca de cena a cada substantivo.
Preservar o rosto quando o valor estiver no depoimento, expressão ou demonstração do autor.
Não decidir esse valor por diagnóstico de emoção feito de uma imagem.

## Percepção de cenário
Por plano, inspecionar começo, meio e fim; adicionar frames em mudança de câmera, gestos,
oclusão, pessoa atravessando a composição e entrada de objetos. O utilitário prepara amostras
pelos cortes da EDL; não detecta automaticamente todas as mudanças visuais dentro de um take.
Separar planos adicionais quando a observação revelar necessidade.

Registrar: câmera estática/móvel/incerta; fundo descritivo; paleta observada; direção aparente
da luz; perspectiva aproximada; regiões ocupadas; espaço negativo; áreas de legenda e interface.
Uma parede lisa não é automaticamente espaço livre durante todo o take. Verificar mãos e
movimento. Uma região candidata é hipótese; uma região protegida deve ser conservadora.

Coordenadas internas: `[x,y,width,height]`, normalizadas no MASTER FINAL decodificado,
origem superior esquerda. Quem usa um modelo que retorna pixels deve converter usando as
DIMENSÕES DA IMAGEM EFETIVAMENTE ANALISADA. Não confundir coordenadas da folha de miniaturas
com as do frame. Refazer o mapa depois de crop, zoom, rotação ou mudança de proporção.

## Composição em níveis — não fingir uma capacidade instalada
- **Overlay 2D:** ilustração ao lado, sem cobrir rosto, mãos relevantes, demonstração, legendas
  ou áreas de interface. Usar o envelope máximo do movimento, incluindo sombra/escala/entrada,
  não somente o retângulo em repouso. O validador confere retângulos declarados, não o alfa real.
- **Cutaway:** ocupar a imagem mantendo a voz. Legendas entram depois dos visuais. Não aumentar
  a duração do vídeo inserindo um clipe silencioso entre frases.
- **Atrás do apresentador:** exige máscara por frame, bordas temporais estáveis e compositor que
  suporte essa máscara. Cabelo, óculos, mãos e objetos devem ser inspecionados em movimento.
- **Preso à parede/tela/mesa:** exige rastreamento de superfície/câmera, transformação de perspectiva,
  tratamento de oclusão e revisão. Coordenadas sugeridas pelo modelo não equivalem a tracking.
- **Reconstrução/alteração de cenário:** opt-in separado. Não trocar o fundo por padrão, modificar
  um produto como prova, nem apresentar uma reconstrução como local real. Falta de geometria,
  máscara ou rastreamento → overlay simples, cutaway ou keep, com motivo registrado.

O pacote leve implementa preparação, contratos, validação e exportação de specs 2D/briefs.
Segmentação, tracking, reconstrução 3D e geração neural são rotas com ferramentas externas
ou código adicional, NÃO serviços incluídos e já conectados. `behind_subject` e `tracked_surface`
ficam pendentes até a rota avançada existir; o exportador leve nunca os transforma em 2D silenciosamente.

## Direção de arte
Selecionar referências visuais reais aprovadas para o formato ativo; se não houver, apresentar uma proposta
como proposta. Definir materialidade (vetorial, editorial, fotografia, 3D etc.), paleta, tipografia,
espessura de traço, iluminação, perspectiva, textura, hierarquia e movimento. Não basta escrever
“premium”, “cinematográfico”, “8K” ou “de primeira linha”.

Produzir um trecho representativo antes de fabricar o vídeo inteiro num estilo novo. A aprovação
do usuário é distinta da revisão técnica. Não inventar que houve aprovação porque o usuário não respondeu.
Respeitar autorização prévia para trabalhar com autonomia, sem perguntar sobre cada frase.
Usar uma linguagem visual consistente; alternar técnica só com função editorial explícita.

## Seleção de ferramenta
1. Material real adequado já fornecido: preservar integridade e usar onde sustenta a fala.
2. Componente aprovado: reaplicar com dados locais. Mais barato que redesenhar.
3. Diagrama, rótulos, processo e números exatos: JS/SVG/Canvas; cenas maiores em React/Remotion.
4. Ilustração original/fotografia conceitual: ferramenta de geração realmente disponível e autorizada.
   A skill produz o brief; Claude com saída textual não se torna gerador de imagem por instrução.
5. Clipe generativo ou VFX: avaliar custo, continuidade, artefatos e necessidade. Não usar por prestígio.

O prompt de imagem especifica assunto, RELAÇÃO, composição, áreas vazias, estilo de referência,
iluminação, perspectiva, fundo/alpha, resolução de entrega e o que evitar. O prompt de animação
acrescenta estados inicial/final, eventos por frame, easing, entrada, saída e loop (se necessário).
Textos, logos e números precisos devem ser aplicados em camada determinística, não confiados à
imagem gerada. Não usar ilustrações sintéticas como prints, depoimentos ou prova de resultados.

## Qualidade e orçamento
Sempre revisar no contexto do vídeo: sentido, leitura pequena, rosto livre, sincronismo,
legendas, transições, continuidade, movimento e áudio. Não declarar alta qualidade estética
por um teste de sintaxe. Se a animação compete com a fala, simplificar. Sem flashes/strobe.

Reusar componentes/assets por hash + versão + props + formato. Cache não dispensa revisão de
posicionamento em outro plano. Agrupar decisões semelhantes numa chamada; enviar só contexto
ativo, fala próxima e frames relevantes. Modelo forte para conceitos novos/ambíguos; modelo
mais barato para adaptar um sistema aprovado; execução local para extração, matemática e render.
Não prometer troca de modelo se o host não oferece delegação. Chamadas pagas, uploads e instalações
exigem autorização. Orçamento de geração externa padrão = zero até o usuário autorizar.

## Feedback
Preferências explícitas e aprovação/rejeição de um visual entram no mecanismo de memória do
formato com o trecho/versão e alcance correto. “Esse gráfico cobriu minha mão” não significa
“não use gráficos”. “Só neste vídeo” não altera o padrão permanente. Métrica de publicação
não é necessária para respeitar gosto; é necessária para alegar desempenho observado.
