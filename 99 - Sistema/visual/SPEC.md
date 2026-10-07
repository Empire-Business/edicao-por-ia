# Contratos da direção visual

`tools/visual_direction.py` é o validador executável. Os JSONs de exemplo são estruturas de
trabalho, não registros de inspeção de um vídeo do cliente.

## context.json (produzido mecanicamente)
`client_id`, `child_id`, `timebase=clean_master_frames`, `width`, `height`, `fps`, `duration_frames`;
`base`, `edl`, `transcript`: caminhos relativos ao arquivo e SHA-256;
`shots`: limites start inclusivo/end exclusivo e sample_frames;
`utterances`: id, texto retido, tempos finais, índices das palavras e plano inicial;
`frames`: frame, dimensões efetivas da miniatura, caminho e hash.
A divisão inicial usa pausas/pontuação/cortes, não entendimento semântico. O agente agrupa as
unidades pelo sentido. A amostragem não é tracking nem detecção completa de cenas.

## scene-map-reviewed-vN.json (agente após inspeção)
Manter IDs e intervalos do contexto, `context_sha256`, cliente/filho e
`coordinate_space=normalized_clean_master`. Cada plano registra `reviewed`, `inspected_frames`,
`observations`, `forbidden` e `candidates`. Exemplo de região:
`{"role":"rosto e mãos em movimento", "box":[0.10,0.08,0.40,0.72]}`.
Box significa [x,y,largura,altura] de 0 a 1 no quadro final, não o tamanho em metros do ambiente.
`global_forbidden` recebe área de legenda/interface validada para o formato atual; não existe
uma região universal certificada pelo pacote. Não marcar plano revisado sem abrir os frames.

## plan-vN.json (agente após decidir)
- version, client_id, child_id, context_sha256, timebase;
- style: direction, colors {foreground,background,accent} como #RRGGBB, font_family,
  referências autorizadas opcionais. Não copiar paleta de outro cliente;
- caption_pipeline: after_visuals ou preserve_reserved_area;
- beats: id, utterance_ids, start_frame, end_frame, meaning, purpose, mode, engine;
- cada unidade de fala aparece exatamente uma vez (pode agrupar); `keep` usa engine none;
- visual: shot_id, box (envelope máximo incluindo movimento), evidence
  (concept/simulation/provided_media), componente/props ou generation_brief;
- asset: path/sha256 relativos AO PLANO, não ao contexto; só arquivos autorizados;
- `on_screen_label` quando simulação ou caso realista inventado; `represents_real_case` explicita
  essa condição; não ocultar aviso apenas em metadados;
- generation_brief: subject, relationship, composition, motion e avoid; acrescentar estética,
  luz, perspectiva, negativos e local de transparência/área vazia conforme a direção.

Modos: keep / overlay / cutaway / behind_subject / tracked_surface.
Engines: none / js_svg / existing_asset / remotion / image_generator / video_generator / vfx.
Os nomes designam ROTA, não adaptadores já instalados. O exportador só produz specs prontos
para os quatro componentes JS existentes: keyphrase, steps, lower-third e proof-frame.
Demais rotas produzem brief, com dependência pendente. Para uma ilustração original em SVG,
o agente ainda precisa escrever e testar o componente; não basta declarar js_svg.

## Saídas e limites
`check` verifica hashes, isolamento, cobertura, tempos, áreas declaradas, colisões e rótulos.
`export` grava briefs e specs candidatos a rascunho. Nenhum desses comandos gera aprovação
artística ou de publicação. `render_approval` continua false; a revisão usa VISUAL_QA.md.
A folga de colisão .015 é uma heurística do utilitário; não prova segurança para uma mão que
não foi registrada nem para uma animação que ultrapassa seu envelope declarado.
Cenas avançadas não são aprovadas pelo validador leve: precisam de máscara/track e compositor.
