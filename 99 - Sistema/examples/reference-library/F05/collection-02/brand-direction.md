# Empire1 — direção visual e sonora

Status: direção solicitada pelo usuário; validar em um piloto com a primeira gravação antes de tratá-la como linguagem de motion aprovada.

## Referências preservadas

- `references/editorial-headline-reference.png`: títulos editoriais de alto contraste, serifas expressivas, fundo escuro e acentos dourados.
- `references/empire-identity-board.png`: identidade Empire em composições editoriais e diagramas técnicos, com retratos, arquitetura, linhas finas e tons de pedra.

## Regras para os vídeos

- O apresentador aparece em câmera somente no gancho, gravado por ele.
- Depois do gancho, manter a locução enviada e ilustrar todo o conteúdo com motion graphics ligados ao sentido da fala. A direção pode alternar entre tipografia cinética, diagramas, relações de dados, arquitetura e composições abstratas conforme a ideia.
- Paleta: carvão/preto, marfim/pedra e dourado quente. Usar serifas editoriais de alto contraste nos títulos e tipografia auxiliar discreta para dados e rótulos.
- Composição editorial, hierarquia clara, linhas e detalhes técnicos finos; movimento controlado e elegante, com leitura confortável. Não reutilizar literalmente textos ou imagens das referências como fatos do vídeo.
- Criar ou selecionar uma trilha elegante inspirada na referência chamada “Echo Sax End”, preservando a clareza da voz. O áudio dessa referência ainda não foi fornecido; confirmar suas características quando estiver disponível.

## Herança de `brunoguzela`

Herdar o tratamento de pausas, prioridade do gancho, nível alto de acabamento, prévia antes do final, organização entrada/saída e exigência de autorização para serviços pagos. A referência antiga de motion não foi transferida porque a Empire tem direção visual própria.

## Capa 9:16 (processo fixo por vídeo — pedido do cliente)
- Para cada vídeo, além do MP4 final, gerar uma capa 1080x1920 e salvar em `saida/<pasta-do-video>/capa-9x16.png`.
- Base: um quadro do apresentador na headline (escolher expressão confiante, olhando para a câmera, bem centralizado) + título curto do vídeo em serifa (palavra-chave em dourado itálico) + retratos circulares quando pessoas são citadas + wordmark EMPIRE.
- Tudo importante entre y 240 e 1680 px (corte do grid 3:4 do perfil); manter ~250 px inferiores livres da interface.
- Modelo: `templates/cover-9x16.html` (trocar BASE_FRAME.png, título e retratos). Exemplo aprovado por uso: Conselho bilionário (jobs/conselho-empire1/cover).
