# F05 · Notícia Comentada: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 44,6 s, com áudio.
- Receita: `patterns/f05-v1.yaml`. ID visual usada só neste exemplo: ID04 Dourado.
- Assunto (novo, diferente do vídeo que orientou a receita): Islândia e a jornada de trabalho reduzida (testes de 2015 a 2019).
- Quadros: [`apresentadora.jpg`](apresentadora.jpg), [`comparacao.jpg`](comparacao.jpg), [`documento.jpg`](documento.jpg).

## Como foi gerado

- Retrato da apresentadora fictícia e 3 imagens ilustrativas (rua nórdica genérica, escritório, relógio): `bytedance-seed/seedream-5-0-pro` via OpenRouter.
- Abertura falada: `bytedance/seedance-2.0-fast` (imagem → vídeo, fala nativa em português, 5 s, 720×1280); voz convertida com ElevenLabs speech-to-speech para a voz “Thais N” da biblioteca.
- Narração: ElevenLabs `eleven_multilingual_v2`, voz “Thais N”.
- Composição: cena HTML/Canvas renderizada por `tools/studio_render.py` (camada sobreposta) e montagem/áudio com FFmpeg.

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
