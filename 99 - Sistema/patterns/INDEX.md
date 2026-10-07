# Pattern Index

Starter patterns below are examples, not automatically user-approved house style.

| Pattern | Status | Use |
|---|---|---|
| `talking-head-clean-v1` | starter | Natural talking-head cleanup, minimal effects |
| `reels-dynamic-v1` | starter | Vertical short-form, tighter pace and selective punch-ins |
| `longform-clean-v1` | starter | Long-form speech with conservative cleanup |

Create client-specific patterns as new files rather than mutating these silently.

## Client-specific drafts
- `bruno-wpp-chat-v1` — draft: áudio sem rosto em conversa WhatsApp encenada; balões viram cenas, B-roll aparece como mensagem de vídeo. Direção em `context/clients/bruno-wpp/DIRECTION-v1.md`. Validar no primeiro job antes de aprovar.

## Version 2 starters — explicit automatic silence cleanup
- `talking-head-clean-v2` — natural pacing, optional flexible reference script.
- `reels-dynamic-v2` — tighter silence settings.
- `longform-clean-v2` — more relaxed pause preservation.

All remain starter proposals, not approved house styles. V1 files are preserved byte-for-byte; their previous silence thresholds remain respected by the planner.

## Client patterns
- `empire-reels-v1` — **approved** (empire1, 2026-10-02, a partir da prévia v13 do job IKEA). Bruno alternando com mídia real; tela dividida com
  profundidade (rembg), cartão de borda preta, gráfico verde; identidade verde/laranja/creme; filtro `look-empire-v1.cube`; destaques na altura da
  legenda surgindo de blur. Componentes congelados em `patterns/empire-reels-v1/` (SHA256SUMS).

## Formatos de edição v2 — independentes da ID visual

- F01 — WhatsApp Narrado: `f01-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F02 — removido do cadastro ativo (código reservado; receita histórica): `f02-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F03 — retirado do catálogo ativo; código e receita histórica preservados.
- F04 — Pessoa → Animação: `f04-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F05 — Notícia Comentada: `f05-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F06 — Diagramas: `f06-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F07 — Motion Institucional: `f07-v2.yaml` (draft). Tour, recursos e formulários de plataforma; versões anteriores preservadas.
- F08 — Pessoa + Tela: `f08-v2.yaml` (draft). Pessoa integrada ou explicando telas/conversas; incorpora o F09.
- F09 — incorporado ao F08; código e receita histórica preservados.
- F10 — Produto Explicado: `f10-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.
- F11 — incorporado ao F07 — Motion Institucional. `f11-v1.yaml` preservado para o histórico; código reservado.
- F12 — Documentário: `f12-v1.yaml` (draft). Paleta e fonte vêm da ID escolhida.

- F13 — Dados Dark: `f13-v2.yaml` (draft). Narração com mapas, pontos, contadores e comparações; sem apresentador. ID visual separada.

- F14 — Lista em Tela: `f14-v1.yaml` (draft). Lista cumulativa sincronizada com a fala.
- F15 — Dois Lados: `f15-v1.yaml` (draft). Classificação de itens em duas áreas.
- F16 — Comentário com B-roll: `f16-v1.yaml` (draft). Pesquisa, mídia real, múltiplas composições, gráficos, destaques e trilha. Mecanismos da referência histórica preservados sem marca/paleta/fontes fixas.

Novos formatos do catálogo do autor também precisam ser publicados na galeria pelo fluxo `workflows/PUBLISH_FORMAT_GALLERY.md`.



- F17 e F18 — retirados pelo autor; códigos reservados. Receitas e exemplos rejeitados ficam fora da distribuição.

- `f02-talking-head-v1`: F02 Talking Head, nova geração a partir do vídeo do ZIP de 07/10/2026. Draft; preserva as receitas anteriores.
