# F09 · Personagem: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 28,5 s, com áudio.
- Receita: `patterns/f09-personagem-v1.yaml`. ID visual usada só neste exemplo: ID07 Laranja.
- Assunto (novo, diferente do vídeo que orientou a receita): a criadora e o editor discutindo quanto tempo leva editar um Reels (humor leve).
- Quadros: [`personagem-1.jpg`](personagem-1.jpg), [`personagem-2.jpg`](personagem-2.jpg), [`legenda.jpg`](legenda.jpg).

## Como foi gerado

- Retratos dos dois personagens fictícios: `bytedance-seed/seedream-5-0-pro` via OpenRouter.
- Uma fala por clipe: `bytedance/seedance-2.0-fast` (imagem → vídeo com fala nativa em português e sincronia labial, 4 s, 720×1280).
- Vozes: ElevenLabs speech-to-speech (`eleven_multilingual_sts_v2`) sobre o áudio de cada clipe, preservando o tempo da boca: “Marianne” para Lia e “Sandro San” para Valdir (vozes da biblioteca, não clonadas de pessoas).
- Composição: legenda em HTML/Canvas por `tools/studio_render.py` (camada sobreposta) e montagem/áudio com FFmpeg.

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
