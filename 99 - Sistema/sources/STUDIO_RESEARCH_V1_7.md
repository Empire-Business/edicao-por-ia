# Verificação externa focal — 2026-09-27

Separada do material recebido e da adaptação local. Não foram auditados os nove posts, métricas de engajamento, preços de agência ou demos sociais. Não clonamos os repositórios citados.

## Fontes primárias consultadas
- Anthropic, modelo Opus 5.5: https://platform.claude.com/docs/en/models/opus-5-5/overview
  Confirma entrada texto/imagem e saída texto; esforço padrão medium. Isso não significa emitir MP4 nativamente nem validar qualidade dos exemplos do post.
- Claude Code, configuração de modelo: https://code.claude.com/docs/en/model-config
  Modelos/esforço dependem de configuração e provedor. A documentação descreve custo maior para xhigh e retornos decrescentes possíveis para max. A versão de modelo não é escolhida por copiar um tweet.
- Remotion, propriedades animadas: https://www.remotion.dev/docs/animating-properties
  Movimento deve seguir frame; transições CSS independentes podem causar problemas. Interpolação e springs são opções, não uma obrigação de usar uma única curva.
- librosa 0.11, beat tracker: https://librosa.org/doc/0.11.0/generated/librosa.beat.beat_track.html
  Saídas são tempo estimado e eventos de batida; silêncio pode retornar BPM zero/lista vazia. Não fornece fase de compasso.
- librosa, tempo variável: https://librosa.org/doc/0.11.0/auto_examples/plot_dynamic_beat.html
  Tempo global não representa bem todas as faixas com variação radical. A ferramenta local marca a saída como estimativa.
- Playwright, screenshots: https://playwright.dev/docs/api/class-pageassertions
  Desabilitar animações pode avançar animações finitas; por isso não usamos captura como substituto de um relógio seek correto.
- FFmpeg, filtros: https://ffmpeg.org/ffmpeg-filters.html
  Base de consulta para captura, tile, integração de áudio/mix e codificação; o código do post foi revisado, não executado literalmente.
- Codex, skills: https://developers.openai.com/codex/skills
  Caminho de skill é compartilhado com instruções da fábrica; o módulo não troca modelos do Codex por nomes de modelos Anthropic.

- HyperFrames, repositório oficial HeyGen: https://github.com/heygen-com/hyperframes
  Consultado somente para enquadrar a rota HTML/animações seekable. Não clonado, instalado ou renderizado nesta revisão.
- Remotion, skills oficiais: https://www.remotion.dev/docs/ai/skills
  Referência de integração opcional. Não executamos os comandos de instalação do curso.

## Implementação e validação locais
O novo renderer, biblioteca de movimento, validação de planos, relatório de evidências, detector musical e SFX foram escritos para o pacote. O relatório de testes da v1.7 distingue execução local de inferência/avaliação artística. Os adaptadores de modelos existentes foram preservados; não foi feita autenticação ou chamada cobrada a provedores.
