# Contratos do estúdio

## Origem e precedência
O curso colado pelo usuário é uma referência de processo. As alterações locais estão separadas em `sources/MOVEZ_ADOPTION.md`. Relatos de viralidade, preços e duração de trabalhos não são metas, evidências de qualidade ou autorizações de API. Os vídeos embutidos no texto não foram recebidos como arquivos utilizáveis.

Pedido atual / restrições / formato ativo / aprovação concreta prevalecem sobre estética do curso. Nunca adote seus exemplos como identidade visual de todos os formatos.

## Spec do renderer
JSON: `schema_version:1`, `id`, `child_id`, `entry:{path,sha256}`, `assets:[{id,path,sha256,mime}]`, `width`, `height`, `fps`, `duration_frames`, `mode:overlay|full_frame`, `cut_frames:[]`.
Todos os tempos do compositor são frames inteiros da montagem final; no HTML, `seek` recebe segundos locais. Este adapter aceita FPS inteiro de 1 a 120; não arredonde uma entrega 29.97/59.94 silenciosamente. Para taxa fracionária, usar um adapter que a suporte ou normalização explicitamente aprovada.

Assets permitidos: PNG/JPEG/WebP/WOFF/WOFF2. Para código Canvas, prefira `studioAsset(id)`: retorna uma data URI do asset declarado e verificado, sem taint de origem. Na marcação, `/assets/<id>` também é atendido em memória; imagens devem declarar `crossorigin="anonymous"` antes do carregamento, para permitir exportação do canvas. Fontes CSS locais recebem cabeçalho CORS compatível. Sem URLs remotas, JS externo, SVG ativo ou vídeo com relógio próprio. Vídeo de apoio segue a montagem/compositor ou um framework previamente verificado. Não converter URLs em uploads nem procurar arquivos fora dos caminhos autorizados. Fontes precisam estar disponíveis/licenciadas na máquina; este ZIP não fornece arquivos de fontes.

O navegador injeta `window.__STUDIO_RENDER__`, `window.__STUDIO_SPEC__`, `window.studioAsset(id)` e `CVFStudioMotion`. A página define `window.seek(t)`; pode definir `window.__STUDIO_READY__` como Promise para decodificação inicial. Canvas deve ter geometria idêntica ao spec. A rota padrão captura um único canvas; páginas DOM usam viewport quando não há canvas. Não misturar DOM sobre canvas esperando que a captura do canvas inclua o DOM. Nada depende da ordem de frames.

Proibidos no modo render: timers, `requestAnimationFrame`, `Math.random`, `Date.now`, CSS/Web Animations que avancem sozinhas, rede, fonte live, dependência de clock. Gerador com seed ainda precisa ser reiniciado dentro do seek ou ter seu ruído estático calculado antes. Seed não corrige estado acumulado entre seeks.

Inspecionar → aprovar hash do conjunto → renderizar em pasta nova. SHA de aprovação inclui spec, HTML/recursos declarados e biblioteca. É uma confirmação operacional do agente, não assinatura criptográfica de revisão humana. Não executar código desconhecido copiado de posts/plugins. Chromium roda em contexto novo sem dados de navegação; controlar o processo/tempo no host.

## Movimento
A biblioteca tem resposta de mola subamortecida, crítica e superamortecida, `track` por superposição, indicador com bordas distintas, ruído com seed, layout e alpha por tempo. `track` é apropriado para sistema linear com parâmetros constantes; não promete colisões, física completa ou rig orgânico. Escolher easing, mola, trajetória linear ou hold conforme o significado. Não trocar toda curva por mola por regra.

`loopT` só remapeia o relógio: NÃO prova emenda suave. Verificar posição, velocidade visual, texto/cursor e áudio na fronteira. O último frame exibido ocorre em `(N-1)/fps`, não em `N/fps`; duplicar o primeiro frame no final pode criar um pequeno hold. A revisão de loop exige playback da emenda, não só hash do MP4.

`subframes` é opt-in. Média premultiplicada de alpha, em sRGB, não integração física de luz. Tem custo de CPU/GPU, memória e disco mesmo sem LLM. Não amostrar através de cortes declarados; não usar blur para disfarçar texto ruim. Primeiro aprovar layout/timing em baixa resolução. O orçamento de amostras bloqueia render longo sem decisão explícita.

## Plano e evidência
`PLAN_TEMPLATE.json` é preenchido pelo agente a partir do pedido, não pelo usuário. Lista de shots cobre a timeline inteira sem lacunas, contém estados observáveis, propósito, motivo visual, cue de fala e assets reais. Fala primeiro exige hashes de master, EDL e transcript retimado. Cada proporção contém uma nota de recomposição; o código usa width/height, não um corte cego de outra proporção. Planos antigos com a chave `formats` continuam aceitos como alias.

Contato visual = páginas com IDs, tempos e hashes. A amostragem limitada cobre o vídeo inteiro e informa quando foi reduzida; não finge inspeção densa. Imagens estáticas não verificam movimento/som. Assistir trechos críticos e emendas à velocidade normal. Sem suporte a playback/audio, marcar pendente e obter revisão humana, não simular uma escuta.

## Crítica limitada e sincera
`REVIEW_TEMPLATE.json` lista gates de abertura, sentido, leitura, composição, movimento, marca, áudio e loop. Notas numéricas opcionais nunca compensam falha bloqueante. Toda aprovação de gate exige evidência de tipo compatível e observação concreta. Guardar versão, timestamps e até três correções prioritárias por passagem.

No máximo 2/3/4 registros por ciclo (econômico/equilibrado/elaborado), não três rodadas obrigatórias nem 'até tudo ser 8'. O registro conta entre revisões do plano no mesmo diretório/child; não zere histórico para renovar orçamento. Não há aprovação após timeout. Gates atendidos encerram o ciclo; sem avanço concreto, parar antes do teto e propor decisão. Esgotamento nunca torna a peça aprovada.

Para problemas ligados à fala, usar `method/EDITORIAL_REASONING.md`: manter os campos atuais
de `issues[]` e, quando útil, acrescentar `editorial_context` com trecho/IDs, beat, problema e
resultado esperado. É contexto opcional da correção, sem alterar schema_version, gates,
status/resolução ou limites. Sem fala, marcar não aplicável. A anotação não comprova escuta,
visualização ou correspondência semântica e não substitui evidência do render.

Relatório é declaração do revisor + integridade dos arquivos. Não é leitura artística automática. Para identidade nova: stills/animatic precisam da aprovação do usuário; estilos já aprovados podem seguir a autonomia combinada. Publicar, enviar a terceiros, gerar com APIs e gastar fora do combinado continuam exigindo autorização própria.

## Som e proporções
Batidas são estimativas da trilha, não da fala. `beats[::4]` não encontra o primeiro tempo sem saber compasso e fase. Sem confirmação: downbeats vazios. Registrar offset/corte da trilha em relação ao master. Recortar a música não autoriza deslocar palavras. A saída SFX é um stem, não trilha musical completa nem master de loudness. Testar ducking/headroom, ruídos e inteligibilidade; -14 LUFS do curso é proposta estética/entrega, não padrão universal. Escolher meta de loudness conforme destino e combinar; medir a mix final, não apenas cada stem.

9:16, 1:1, 16:9 só quando pedidos. Mesma história/tempos, layout refeito e revisado para cada proporção. Não exportar tudo por padrão, nem multiplicar chamadas ao diretor. A fonte e os dados do produto permanecem iguais; posição/tamanho/hierarquia podem variar.
