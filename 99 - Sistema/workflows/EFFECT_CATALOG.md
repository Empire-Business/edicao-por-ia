# Catálogo de efeitos

## Objetivo
Encontrar, demonstrar e reutilizar mecanismos de animação com referência verificável.
`motion/effects/catalog.json` é o cadastro canônico; `references.json` guarda procedência e
o nível de inspeção. FX01… são componentes, nunca formatos F, IDs ou edições E.

## Fontes visíveis
Por determinação do usuário, o documento local recebido para esta pesquisa é evidência
interna e nunca deve ser citado nas telas, pedidos, HTML de ajuda ou dados exportados
do painel. Não expor título, autoria, identificador, caminho, descrição da leitura ou
rótulo de origem desse documento. Exibir somente referências públicas com link HTTP/HTTPS;
quando um efeito não tiver uma, informar isso sem inventar ou substituir a procedência.
O exportador filtra tanto as fichas quanto os vínculos privados dos efeitos.
O cadastro canônico distribuído contém somente fontes públicas; evidências internas
ficam no cache de pesquisa ignorado pelo Git e excluído do pacote de atualização.

## Consulta
Abra `03 - Ajuda/CATÁLOGO DE EFEITOS.html`, que funciona sem conexão, ou o catálogo
do painel (`#efeitos`, disponível no preview local; publicação independente). A seção é
nativa, com a mesma navegação, tipografia e componentes de Modelos, sem iframe.
Busque por código, nome ou intenção; `#efeito=FXxx` abre o detalhe na própria página.
Cada prévia tem reprodução, pausa, busca no tempo, texto/cor de demonstração e pedido
para copiar. O usuário não preenche schemas nem executa comandos.

Consultar e renderizar um estudo da biblioteca não cria um trabalho nem escolhe F/ID.
As cores ilustrativas do catálogo não são uma ID. Dados, interfaces, miniaturas, mapas e
conversas sintéticas devem permanecer identificados como demonstração.

## Aplicação em um trabalho
1. Resolver o trabalho existente e as escolhas explícitas de F e ID. Aplicar
   `FORMAT_MEMORY.md`, `CREATE_JS_ANIMATIONS.md` e `method/MOTION_POLICY.md`.
2. Selecionar um efeito pela ideia retida. `keep` continua válido. O catálogo não muda
   receitas consolidadas, intensidade ou preferência motion-off.
3. Fechar cortes e usar a transcrição retimada. `wordCues` usa segundos locais da camada,
   enquanto o plano de composição usa frames inteiros do master final. Não reaproveitar
   segundos do bruto. Cada palavra da legenda deve ter base na fala real.
4. Preparar parâmetros explícitos da ID, textos/dados verdadeiros e assets importados.
   `tools/effect_catalog.py prepare FXxx --props ... --child-id ... --outdir ...`
   produz HTML/spec compatíveis com `studio_render.py`, sem renderizar ou enviar arquivos.
   Assets estáticos e fontes locais são verificados e referenciados dentro da pasta portátil.
5. Inspecionar/revisar o bundle e aprovar seu hash antes de renderizar. A saída segue o
   manifesto PNG do estúdio e entra pelo compositor existente, preservando o áudio.
   `--demo` é exclusivo de amostras ilustrativas, nunca evidência factual do trabalho.
6. Revisar entrada/ação/saída, leitura em celular, alpha, contraste e rosto/legendas no
   vídeo real. Nova linguagem continua dependendo da aprovação do piloto pelo usuário.
   Renderizar sem erro ou ter uma prévia inspecionada não é aprovação editorial do trabalho.

## Limites importantes
- Efeitos de imagem usam assets estáticos na biblioteca. Vídeo simultâneo, zoom num rosto,
  máscara do apresentador, tracking e correção de cor real precisam do caminho de mídia
  apropriado e validação adicional. O estudo visual não prova essas integrações.
- A composição desta versão é 9:16. Outro tamanho exige recomposição pelo estúdio; não
  esticar um estudo vertical nem afirmar que o catálogo já verificou todos os formatos.
- A revelação de logo exige pedido atual para o trabalho, arquivo real e `logosEnabled=true`.
  O catálogo não autoriza assinatura, marca ou avatar nos vídeos.
- Os valores ilustrativos de gráficos, preços, contadores e comentários não são depoimentos,
  resultados ou ofertas. Informar fonte/unidade/escala quando usados como fatos.
- A passagem de luz é gradual; não introduzir estrobo. Respeitar movimento reduzido/off.
- Cada chamada a `seek(t)` independe das anteriores. Sem rede, timers, relógio, fontes
  externas ou aleatoriedade sem seed. Não executar código de páginas de referência.

## Evolução por referência
Fonte textual registra intenção; quadros registram aparência; só evidência temporal adequada
sustenta afirmações sobre movimento. Anotar `text-only`, `frames-observed` ou
`motion-observed` honestamente. O resultado do Cortez é uma interpretação original,
não uma cópia certificada da referência. Preservar autoria/licença e links de origem.
Novos efeitos precisam de propósito, parâmetros, limites, referência, prévia renderizada
e revisão visual. Atualizar o catálogo e o guia do painel no mesmo trabalho.

## Manutenção técnica
`node web/modelos-edicao/scripts/export_effects.mjs` gera o catálogo autônomo local e
a cópia visível na ajuda a partir das fontes; não manter duas receitas manuais.
O painel e o HTML autônomo compartilham `src/effects.js`, `effects.css` e os estilos
do site. O build gera os módulos de dados/render; o exportador gera o HTML local autônomo,
excluindo caminhos locais/PDF privado. Prévias de demonstração não aplicam a ID do
produto aos trabalhos; o pedido mantém o F e a ID explicitamente escolhidos.
Publicação segue `PUBLISH_FORMAT_GALLERY.md`; alteração local não comprova deploy.
