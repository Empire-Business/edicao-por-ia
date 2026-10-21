# Workflow — variações de reel para teste (qualquer formato, qualquer quantidade)

Pedido do autor (20/10/2026): "no final me entrega 5 variações de edição com 5 ganchos visuais diferentes… para o
Instagram não reconhecer que é o mesmo vídeo, mude detalhes de legenda e edição no resto também" e, depois, "cria um
processo de criar variações para reels de teste, assim como você fez 5 reels do Felca. Qualquer pessoa pode querer
fazer algo semelhante na quantidade que quiser."

## Quando usar
Quando o usuário pedir variações, testes A/B, "versões diferentes do mesmo reel", "N ganchos" ou "postar de novo sem
parecer repetido". Funciona com qualquer F/FP e qualquer ID. Não é padrão de nenhum formato e não muda receitas.
Quantidade: a que o usuário pedir. Se ele não disser, propor 5 (bom equilíbrio entre teste e custo de render).

## Duas estratégias (podem ser misturadas)
1. **Gancho re-editado (`hook`)** — a edição é refeita: um gancho visual diferente desde o 1º quadro até a primeira
   virada da fala, e detalhes diferentes no resto (estilo de legenda, transições, ponto de entrada de B-roll
   equivalente, rótulos/chips, cor leve, trilha, texto da cartela final). Exemplos de gancho: tarja-pergunta em tela
   dividida, react com a pessoa recortada, anel/seta "QUEM É ELA?", revelação escrita grande, "ache a diferença",
   contagem regressiva, manchetes empilhando, expectativa × realidade, número gigante, pergunta direta.
2. **Post com foto (`post`)** — o vídeo pronto (de qualquer formato) é embalado como print de post, a mecânica do
   F19 Print Repost: cabeçalho com foto, nome e @ da conta que vai postar, frase-gancho com destaque na cor da ID e uma
   foto chamativa parada ao lado do vídeo. Cada variação troca a foto e/ou a frase. É rápido e barato; o tempo vai
   para escolher a foto e escrever a frase.
Para muitas variações, combinar: K ganchos re-editados × M posts por gancho (ex.: 5 edições × 2 posts = 10 reels).

## O que nunca muda
Voz, cortes, fatos, CTA, F e ID escolhidos. Nada de foto enganosa, número inventado ou montagem de pessoas reais
"para o gancho ficar mais forte". A frase promete só o que o vídeo entrega. A conta do cabeçalho é informada pelo
usuário — nunca inventada ou herdada de um exemplo.

## Processo
1. **Base pronta**: termine e aprove a edição base (ou receba o vídeo pronto, para `post`).
2. **Plano**: `python3 tools/reel_variations.py plan --out <job>/variations/plan.json --count N --strategy hook|post|mixed --base-name <nome>`.
   O plano já distribui ganchos, legendas, transições, cores e trilhas diferentes; preencha o que falta
   (para `post`: vídeo, foto, recorte, frase e destaque; cabeçalho com nome/@/foto de perfil e se é verificada).
3. **Conferência**: `python3 tools/reel_variations.py check --plan <job>/variations/plan.json` — bloqueia variações com a
   mesma combinação, mesma foto + mesma frase, campos vazios, frase de mais de 2 linhas ou cabeçalho sem conta.
4. **Produção**
   - `hook`: parametrize o build do trabalho por variação (ex.: `build.py <N>` → `comp/v<N>.html`; arquivos de cache
     com nome por variação ou por hash do conteúdo), renderize uma por vez (`hyperframes render comp -c v<N>.html`) com
     `TMPDIR` na pasta `tmp/` do trabalho; trilha própria por variação quando houver.
   - `post`: `python3 tools/reel_variations.py post --plan <plano> --var 03 --identity IDxx` — cores e fonte vêm da ID
     escolhida; áudio do vídeo pronto a −14 LUFS, pico ≤ −1,5 dB.
   - Fotos: um quadro do próprio caso, uma foto enviada pelo usuário ou mídia pesquisada com fonte registrada; sem rosto
     de comentaristas de terceiros, sem legenda gravada por cima, ponto de interesse no centro; anel/seta opcional
     sobre o detalhe que gera curiosidade. Imagens com texto (manchete, card) entram inteiras ("contain").
5. **QA de cada variação** (`method/QUALITY_BAR.md`): quadro 0 do gancho, rosto/apresentador nítido, comparações
   certas, mídia de terceiros limpa, legenda, frase sem erro e dentro da largura, anel no lugar certo, áudio.
   Um defeito do corpo comum corrige-se no build e vale para todas.
6. **Entrega**: na pasta do trabalho em `02 - Ver vídeos`, com o nome dizendo o que muda:
   `<nome>_<F>_VAR01-<gancho>_PREVIEW_Vn.mp4` … ou `<nome>_F19-print-repost_var01.mp4` …; revisões anteriores vão para
   `anteriores/`. No decision log, a tabela variação × gancho/foto × frase × legenda × trilha × cor.
7. **Resultado do teste**: quando o usuário contar qual variação performou melhor, registrar com
   `workflows/LEARN_FROM_RESULT.md` (métrica real, sem inventar retenção).

## Custos e tempo
`post` não gasta serviços externos (só render local). `hook` gasta render local e, se pedido, uma trilha por variação
(ElevenLabs Music). Troca de roupa, quando houver, é gerada uma vez na base e vale para todas as variações.
