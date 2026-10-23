# Biblioteca de efeitos do Cortez

50 estudos editáveis de mecanismos de edição e motion. Nenhum é um novo formato ou uma ID.

Fontes: `catalog.json` (cadastro), `references.json` (procedência), `renderer.js` (Canvas
determinístico). A interface nativa está em `web/modelos-edicao/src/effects.js` e
`effects.css`, compartilhando os componentes e estilos de Modelos. O arquivo
`catalog.template.html` é o invólucro offline; `catalogo.html` é saída gerada.
Fontes internas de pesquisa não são citadas nem incluídas nos dados exportados da interface.

Consulte `workflows/EFFECT_CATALOG.md`. A ferramenta `tools/effect_catalog.py` prepara
camadas compatíveis com o estúdio. A aparência de produção é fornecida explicitamente
pela ID escolhida; a paleta da demonstração não se torna padrão dos vídeos.

Previews e QA mecânico não equivalem à aprovação humana de estilo nem à aplicação
testada em vídeo de um cliente. Composições com mídia precisam de assets e QA no trabalho.
