# F11 · Narração Ilustrada: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 20,4 s, com áudio.
- Receita: `patterns/f11-narracao-ilustrada-v1.yaml`. ID visual usada só neste exemplo: ID02 Lima.
- Assunto (novo, diferente do vídeo que orientou a receita): hábitos para render mais de manhã.
- Quadros: [`cena-literal.jpg`](cena-literal.jpg), [`acao-citada.jpg`](acao-citada.jpg), [`metafora.jpg`](metafora.jpg).

## Como foi gerado

- 12 cenas: `bytedance/seedance-2.0-fast` (texto → vídeo, sem áudio, 4 s, 720×1280).
- Narração: ElevenLabs `eleven_multilingual_v2`, voz “N. Ayres” da biblioteca. Trilha: ElevenLabs Music (`music_v1`, instrumental).
- Composição: legenda em HTML/Canvas por `tools/studio_render.py` (camada sobreposta) e montagem/áudio com FFmpeg.

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
