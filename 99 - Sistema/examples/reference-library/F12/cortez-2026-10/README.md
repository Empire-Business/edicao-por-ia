# F12 · Documentário: exemplo original do Cortez

Exemplo original produzido pelo sistema (Cortez) em 19–20/10/2026, com roteiro próprio e mídia gerada por IA. Não contém vídeo, imagem, voz ou música de terceiros, rosto de pessoa real, logotipo ou marca. Pessoas, assunto, cores e fontes pertencem a este exemplo e não são padrões: a aparência de uma nova edição vem da ID escolhida.

- Vídeo: [`exemplo.mp4`](exemplo.mp4), 1080×1920, 61,6 s, com áudio.
- Receita: `patterns/f12-v3.yaml`. ID visual usada só neste exemplo: ID08 Azul e Papel.
- Assunto (novo, diferente do vídeo que orientou a receita): a história da fita cassete.
- Quadros: [`objeto.jpg`](objeto.jpg), [`lista.jpg`](lista.jpg), [`sequencia-clara.jpg`](sequencia-clara.jpg).

## Como foi gerado

- 8 imagens (7 usadas): `bytedance-seed/seedream-5-0-pro` via OpenRouter, com instrução de não exibir textos, marcas ou logotipos.
- Narração: ElevenLabs `eleven_multilingual_v2`, voz “KATIUSCIA” da biblioteca. Trilha: ElevenLabs Music (`music_v1`, instrumental). Efeitos: sintetizados localmente.
- Composição: cena HTML/Canvas por `tools/studio_render.py` (quadro inteiro) e áudio com FFmpeg.

Custos e chamadas ficaram registrados fora do repositório, no recibo da sessão de geração.
