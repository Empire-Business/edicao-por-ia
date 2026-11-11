# Kit ad-motion (F22 · Anúncio com motion)

Kit de cenas e pipeline local para anúncios verticais de produto. Um `job.json` descreve o anúncio; o kit gera o plano, renderiza o motion com transparência (GSAP + Playwright, quadro a quadro por `seek(t)`), monta a base de rosto/fundo, mixa o áudio e faz o QA mecânico.

## Uso (operado pelo Cortez)

```
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> plan      # EDL + palavras da legenda + plano
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> stills    # prévia + miniaturas da galeria
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> track     # posição do rosto (enquadramento fixo na mediana)
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> frames 0 4.6 12   # quadros-chave para revisão
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> base
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> overlay 5 # 5 navegadores em paralelo
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> audio
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> final
python studio/ad-motion/kit/ad_motion.py --job jobs/<id> qa
```

Comece copiando `example/job.example.json` (o anúncio real que originou o formato). Fontes são cópias dentro da fábrica; transcrições com tempo por palavra ficam em `analysis/`. Cores vêm da ID escolhida (`identity_tokens`: `p`, `p-hi`, `ink`, `deep`); fontes locais do motor; GSAP local, sem CDN; nenhuma logo automática.

## Biblioteca de cenas (`segments[].scene`)

| Cena | Quando usar | Props principais |
|---|---|---|
| `hook_gallery` | Gancho de dor sem apresentador | `label`, `line1`, `line2`, `counter`, `counter_label`, `pain_chip`, âncoras |
| `reveal_timeline` | Revelação do produto (idealmente no drop da música) | `product`, `head_label`, `line1`, `line2` |
| `app_agent` | Produto rodando dentro de um app (réplica realista) | `app_title`, `agent`, `user_message`, `reply`, `stamp` |
| `upload_raw` | Envio do material bruto | — |
| `models_dial` | Escolha entre opções/modelos com mostrador | `prompt` |
| `editor_checklist` | O produto trabalhando (checklist + linha do tempo) | `window_title` |
| `result_phone` | Resultado com identidade aplicada (paleta, fonte, legenda) | `palette`, `font_name` |
| `typed_request` / `version_update` | Pedido de ajuste e nova versão | `request` |
| `face_title` | Rosto com título cinético | `label`, `lines[{text,alt,anchor}]` |
| `face_steps` | Rosto com resumo em passos | `label`, `steps[{text,anchor}]` |
| `face_cta` | Rosto com chamada para ação | `label`, `lines`, `cta`, `cta_anchor` |
| `type_hook` | Gancho ou trecho só com tipografia gigante palavra por palavra (sem rosto; a cena substitui a legenda) | `keys` (palavras em bloco), `per_line` |
| `before_after` | Antes × depois: bruto acinzentado com pausas marcadas × editado | `before_label`, `after_label`, `title_a`, `title_b` |
| `numbers_bars` | Explicação com números: total, descontos e resultado em barras | `title`, `total`, `total_label`, `items[{label,value,anchor}]`, `result_label`, `unit` |
| `three_points` | Lista de 3 pontos em cartões com ícone | `label`, `title`, `points[{text,anchor,icon}]` |
| `voice_card` | Cobre um trecho de rosto quando o anúncio não mostra a pessoa (forma de onda + título) | `label`, `lines` |

`props.anchors` troca a palavra-âncora padrão de uma cena pela palavra do novo roteiro. Sem âncora encontrada, a cena usa um tempo relativo seguro. `panel` liga o painel "NESTE VÍDEO" nos trechos com rosto.

## Variação entre anúncios

Os anúncios de uma mesma campanha não devem sair iguais:

- **Abertura:** alternar entre gancho só em motion (`hook_gallery`, `reveal_timeline`), abertura com rosto e título cinético (`face_title`) e abertura direto na demonstração (`app_agent`, `editor_checklist`).
- **Presença:** alguns anúncios sem rosto (só voz + cenas), outros com rosto nas viradas.
- **Ordem e escolha de cenas:** cada passo falado escolhe a cena que melhor mostra a ideia; não repetir a mesma sequência.
- **Ritmo:** cena de motion nova a cada 4–8 s; trechos de rosto curtos (2–6 s) para respirar.

## QA e lições (das 5 rodadas do exemplo)

- Quadro 0 sempre cheio; bloco do título só aparece com a palavra (sem filete vazio).
- Enquadramento do rosto fixo e centralizado (câmera que segue o rosto parece tela mexendo).
- Nenhuma cena parada por mais de 0,4 s (parece travamento) — `qa` mede com `freezedetect`.
- Legenda no terço inferior sem cobrir cartões, mãos ou rosto.
- Poucos efeitos sonoros (só em momentos-chave); voz limpa localmente (DeepFilterNet quando instalado, com −6 dB de folga); fades de 25 ms nos cortes.
- Captura de quadro pesada pode falhar no compositor por software: o kit tenta de novo antes de desistir.
