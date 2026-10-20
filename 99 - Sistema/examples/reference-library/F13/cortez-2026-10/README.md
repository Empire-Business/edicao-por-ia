# F13 · Dados Dark: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 30,0 s, com áudio.
- Receita: `patterns/f13-v2.yaml`. ID visual usada só neste exemplo: ID03 Azul.
- Assunto (novo, diferente do vídeo que orientou a receita): se o Brasil fosse 100 pessoas: população por região (Censo 2022).
- Quadros: [`mapa.jpg`](mapa.jpg), [`grade-ranking.jpg`](grade-ranking.jpg), [`destaque.jpg`](destaque.jpg).

## Como foi gerado

- Sem imagens geradas: todo o visual é desenhado em código (HTML/Canvas) e renderizado por `tools/studio_render.py`.
- Narração: ElevenLabs `eleven_multilingual_v2`, voz “Carla - For Conversational” da biblioteca. Trilha: ElevenLabs Music (`music_v1`, instrumental).

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
