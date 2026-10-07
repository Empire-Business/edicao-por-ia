# Bruno Guzela — direção editorial e identidade visual

Status: **proposta v1 solicitada pelo usuário**, criada a partir da referência anexada. Validar no primeiro piloto antes de tratar o novo motion como linguagem aprovada.

## Referências

- references/visual-id-reference.png: referência fornecida pelo usuário para a nova identidade. Inspira o contraste carvão + azul e a geometria do monograma; não inserir a imagem literalmente nos vídeos.
- assets/ia-mark.svg: proposta vetorial original do monograma IA.
- assets/brand-board.svg: prancha de identidade proposta.

## Identidade visual proposta

- **Assinatura:** BRUNO GUZELA; monograma IA geométrico independente, desenhado para este perfil.
- **Paleta:** carvão #0C1118, azul #4A92E6, azul claro #76C8FF, branco frio #F2F6FC e cinza azulado #9AA8B8.
- **Tipografia:** sans-serif geométrica e limpa, com títulos em peso alto e letras compactas; Avenir Next, Inter ou Helvetica Neue quando disponíveis. Não usar as serifas editoriais da Empire.
- **Grafismos:** blocos e recortes geométricos, linhas técnicas finas, nós e diagramas simples; azul como acento de hierarquia, com bastante espaço escuro para leitura.
- **Evitar:** dourado, marfim/pedra, wordmark EMPIRE, reproduções literais dos materiais da Empire e elementos de interface decorativos que prejudiquem a locução.

As cores e formas detalhadas acima são uma interpretação de design para o perfil novo; a referência original e a solicitação de uma identidade distinta são a base. A direção é proposta até a revisão do piloto.

## Lógica de edição herdada de Empire1

### Gancho, locução e visuais

- O apresentador aparece em câmera no gancho/headline. Caprichar nos primeiros segundos; editar também o gancho com legenda e motion, priorizando o primeiro segundo.
- Após o gancho, manter a locução enviada e ilustrar todo o áudio com motion graphics relacionados ao significado da fala. Alternar entre tipografia cinética, diagramas, relações de dados, arquitetura e composições abstratas quando ajudarem a explicar a ideia.
- Movimento rico, controlado e legível; deixar a fala liderar o tempo e não animar por obrigação.
- Quando a locução citar pessoas pelo nome, fotos relevantes podem entrar quando houver licença aberta, domínio público ou autorização do usuário. Registrar créditos quando exigidos e não forçar imagens sem função editorial.

### Voz, cortes e trilha

- Tratamento herdado para silêncio: minimum_silence_seconds = 0.15 e keep_pause_seconds = 0.0. Preservar fala, pausas protegidas e intenção editorial conforme method/SILENCE_POLICY.md; evidência de fala prevalece sobre o aperto automático.
- Falas repetidas que sejam claramente tomadas duplicadas: manter a melhor e remover as demais. Intenção ambígua vai para revisão.
- Incluir trilha de fundo elegante sob a locução, com ducking para manter a voz clara. Vídeo sem trilha é incompleto para este perfil.
- A referência sonora chamada “Echo Sax End” não foi fornecida. Confirmar seus atributos quando estiver disponível antes de tentar reproduzi-la.
- Antes de entregar, revisar loudness entre gancho e locução, timbre, picos/clipping, cliques nas emendas e música sob a voz; registrar as medições.

### Gravações enviadas em partes

Quando a locução chegar antes do vídeo do gancho, editar a locução como corpo principal; depois colocar o gancho no início, manter a mesma direção visual e igualar o áudio entre as partes.

### Entrega e organização

- Trabalhar com acabamento alto, renderizar uma prévia e revisar antes do final.
- Manter entrada/ para originais e saida/ para entregas. Originais são imutáveis. Cada vídeo final independente tem sua própria pasta/saída, com nome legível.
- Para cada vídeo, entregar também uma capa 1080×1920 em saida/<pasta-do-video>/capa-9x16.png.
- Capa: quadro do apresentador durante o gancho, confiante e centralizado; título curto em sans-serif, palavra-chave em azul; retratos circulares somente quando pessoas forem citadas e as imagens forem autorizadas; assinatura BRUNO GUZELA.
- Manter informação importante entre y=240 e y=1680 px e reservar aproximadamente 250 px inferiores para a interface da plataforma.
- Usar templates/cover-9x16.html; para cada vídeo, copiar o SVG assets/ia-mark.svg junto do HTML e substituir o quadro, o título, a etiqueta e retratos opcionais.
- Qualquer serviço ou geração paga exige autorização explícita do usuário, conforme a política global.

## Primeira validação

A identidade visual e o motion novo permanecem em proposta até serem vistos em uma prévia de vídeo. A aprovação futura deve apontar para o artefato e a versão exatos; ela não aprova automaticamente todos os efeitos para sempre.
