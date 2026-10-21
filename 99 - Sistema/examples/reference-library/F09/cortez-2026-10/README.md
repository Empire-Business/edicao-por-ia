# F09 · Personagem: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 11,9 s, com áudio (demo curta, 4 falas).
- Receita: `patterns/f09-personagem-v1.yaml`. ID visual usada só neste exemplo: ID07 Laranja.
- Assunto (novo, diferente do vídeo que orientou a receita): a criadora e o editor discutindo quanto tempo leva editar um Reels (humor leve).
- Quadros: [`personagem-1.jpg`](personagem-1.jpg), [`personagem-2.jpg`](personagem-2.jpg), [`legenda.jpg`](legenda.jpg).

## Como foi gerado

- Quadro de abertura de cada personagem: `bytedance-seed/seedream-5-0-pro` via OpenRouter, os dois na mesma sala, câmera de lado (três quartos), cada um olhando para o outro fora do quadro; no plano do Valdir, o ombro da Lia desfocado em primeiro plano.
- Uma fala por clipe: `google/veo-3.1` (imagem → vídeo, 1080×1920, com fala nativa em português). Voz e boca saem do mesmo clipe, sem troca de voz, para o lip sync ficar como o modelo gerou.
- Composição: legenda em HTML/Canvas por `tools/studio_render.py` (camada sobreposta) e montagem/áudio com FFmpeg.

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
