# F30 Linha de Acabamento — modelo de composição

Código-base do formato **F30 Linha de Acabamento** (receita `patterns/f30-linha-de-acabamento-v1.yaml`), derivado do criativo de exemplo E128 V1 (vídeo em `examples/reference-library/F30/linha-de-acabamento/reference.mp4`). O material bruto real desfila numa esteira 3D e passa por estações; a cada etapa narrada ele muda de estado até sair como vídeo pronto, aprovado com um toque.

Os textos, tempos, falas, provas, nomes de pessoas, caminhos, paleta e fontes que aparecem nos arquivos são **do exemplo** (pessoas e marcas foram trocadas por marcadores como `Convidado`, `Apresentador`, `PRODUTO` e `<PREENCHER…>`): cada trabalho troca por seus próprios. Cores e fontes vêm da ID escolhida.

## Arquivos

| Arquivo | Papel |
|---|---|
| `build.py` | Gera a composição, o plano de cenas e as legendas a partir das palavras ditas |
| `finalize.sh` | Roda tudo na ordem e junta imagem e som |
| `index.tpl.html` | Composição HyperFrames (GSAP pausado + cena three.js guiada por hf-seek) |
| `make_assets.py` | Texturas por quadro das provas, fontes da ID, three.js r186 local e GSAP |
| `make_audio.py` | Áudio: narração e trechos reais curtos |
| `mix.py` | Trilha subordinada à voz, efeitos discretos, final −15 LUFS |
| `qa.py` | Conferências (transcrição, níveis, quadros) |
| `write_qa.py` | Grava o relatório de QA |

## Como usar num trabalho

Copiar para `jobs/<trabalho>/src/`, preencher fontes, provas, trilha e as âncoras de cena (palavras ditas) e rodar `finalize.sh` (ou os scripts na ordem dele): EDL/voz → materiais → composição → render HyperFrames → mixagem → junção e nome com `tools/output_naming.py`. A variante de chamada final é um parâmetro do build (`CTA=more` para "Saiba mais", `CTA=comment` para "Comente <PALAVRA>").

## Regras que o exemplo já segue

- Fala com sentido do começo ao fim; nenhuma palavra cortada (limiar de silêncio relativo à própria voz, folga depois da última palavra, só pausas ≥ 0,30 s).
- Nada de trecho com outro áudio tocando por baixo (o isolamento de voz não separa duas vozes).
- Câmera three.js em escala de pixels (fov 30, distância = 960 / tan 15°); profundidade de campo minúscula nessa escala para a prova não borrar.
- Tudo em função do tempo do quadro (evento `hf-seek`), `Math.random` com semente fixa, vídeos no 3D como sequências JPG por quadro.
- O filtro `volume` do ffmpeg com expressão usa ganho linear; conferir o nível da trilha sozinha.
- Provas só do próprio usuário, rotuladas com honestidade; sem logotipos de terceiros; nada de números ou preços inventados.
- A fala termina e o cartão final escrito encerra o vídeo.
