# Tutorial OMNX Sell — piloto "Análise de Conversas"

- Vídeo: `out/omnx-sell-analise-conversas-piloto.mp4` (1920x1080, 16:9, 30 fps, 72 s)
- Editar: `npm start` (Remotion Studio). Roteiro em `src/videos/omnx.tsx`, prints em `public/analise/`.
- Renderizar: `npx remotion render OmnxAnalise out/video.mp4 --crf=17`

## O que é captura real e o que foi alterado
Ambas as telas são capturas reais de sell.omnx.pro (conta logada), com texto trocado no navegador antes do print (nada foi alterado na plataforma):
- `01-lista.jpg`: e-mail, nome do workspace, iniciais dos participantes e títulos das 9 reuniões trocados por exemplos ("Cliente A" etc.). Datas, durações e contadores são reais.
- `02-detalhe.jpg`: nome do vendedor, título e todo o texto do "Resumo da IA" substituídos por texto fictício. Contadores (dores 4, objeções 0...) e a mensagem "Sem nota" são reais.
- Nenhum botão de ação (importar, criar, apagar) foi clicado.

## Limitações do piloto
- Prints saem de uma captura de ~1360 px, então o zoom fica um pouco macio.
- Só as abas "Análise" da lista e do detalhe foram capturadas; Transcrição, Oráculo e Plano de ação não.
