# empire-reels-v1 — componentes

Cópia congelada dos arquivos aprovados na prévia v13 (job video-26afc23b9c24, IKEA). Para um vídeo novo da Empire:
1. copie `composite.py`, `facefix.py`, `build_overlay.py`, `preview.ps1` para `jobs/<job>/visual/`;
2. use `overlay.reference.src.html` como base do overlay: mantenha os componentes (reveal/emph, captions, highlighter da manchete,
   X vermelho, cartão, degradê verde, arch/panel) e troque só o conteúdo específico (G.g_fatur, G.g_pergunta, textos dos destaques);
3. escreva o `plan.py` do vídeo novo a partir de `plan.reference.py` (shots: split / card / full / gfx, emph/emph_from/emph_to, fx por plano);
4. base do apresentador: `ffmpeg -vf lut3d=look-empire-v1.cube` (câmera 2: casamento de cor medido por gravação ANTES do LUT); `composite.py --look ref`;
5. capa: `cover.html` com um quadro do apresentador já com o look.
Não edite estes arquivos para um job: mudança que altere a saída vira `empire-reels-v2`.
