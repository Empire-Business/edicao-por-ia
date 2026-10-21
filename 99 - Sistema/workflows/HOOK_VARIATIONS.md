# Workflow — variações de gancho para teste (qualquer formato)

Pedido do autor (20/10/2026): "no final me entrega 5 variações de edição com 5 ganchos visuais diferentes. Eu quero
testar qual vai funcionar melhor (para o Instagram não reconhecer que é o mesmo vídeo, sugiro mudar detalhes de legenda
e edição no resto dos vídeos das variações também)".

## Quando usar
Somente quando o usuário pedir variações/testes de gancho. Não é padrão de nenhum formato e não muda o F nem a ID.

## O que muda e o que não muda
- Igual em todas: voz, cortes, roteiro, fatos, F e ID escolhidos, CTA.
- Diferente em cada uma, desde o 1º quadro: o gancho visual (os primeiros segundos até a primeira virada da fala).
  Exemplos já usados: tela dividida com tarja-pergunta; react com o apresentador recortado sobre o vídeo; anel/seta
  "QUEM É ELA?" sobre a prova; scanner/HUD com a revelação escrita; "ache a diferença" lado a lado; contagem
  regressiva; manchetes reais empilhando; expectativa × realidade.
- Diferente também no resto: estilo e tamanho de legenda (palavras por grupo, caixa, karaokê, monoespaçada),
  transição entre cenas, ponto de entrada de B-roll equivalente, rótulos/chips, cor (ajuste leve), trilha (um par de
  atos por variação), texto da cartela final. Tudo dentro da ID.

## Processo
1. Montar a edição base uma vez (voz, EDL, legendas, cenas do corpo).
2. Parametrizar o build por variação (ex.: `build.py <N>` → `comp/v<N>.html`, arquivos de cache com nome por variação
   ou por hash do conteúdo — nunca o mesmo nome com conteúdo diferente).
3. Renderizar uma por vez (`hyperframes render comp -c v<N>.html`) com `TMPDIR` na pasta `tmp/` do trabalho.
4. QA de cada uma (`method/QUALITY_BAR.md`): quadro 0 do gancho, rosto/apresentador, comparações, B-roll de
   terceiros, legenda e áudio (−16 LUFS). Um defeito do corpo comum corrige-se no build e vale para todas.
5. Entregar lado a lado: `…_VAR1-<gancho>_PREVIEW_Vn.mp4` … `VAR5`, com o nome do gancho no arquivo. Revisões
   anteriores vão para `anteriores/`.
6. Registrar no `edit/decision_log.md` a tabela gancho × legenda × transição × trilha × cor de cada variação.

## Cuidados
- Ganchos novos podem esconder defeitos que a base não tinha (mídia de terceiros com rosto de comentarista em outro
  recorte, quadro escuro, trecho errado). Revisar o gancho de cada variação no arquivo final.
- Não inventar fato, número ou montagem de pessoas reais para deixar o gancho "mais forte".
