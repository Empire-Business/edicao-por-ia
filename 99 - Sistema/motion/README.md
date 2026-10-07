# Animações JavaScript — uso local

Este módulo acrescenta uma camada visual à gravação já editada. O código cria a animação; o navegador exporta frames; o FFmpeg sobrepõe os frames sem trocar a voz.

## Componentes executáveis incluídos
- `keyphrase`: frase curta com entrada/saída suave.
- `steps`: dois a quatro passos com revelação sequencial.
- `lower-third`: identificação do apresentador.
- `proof-frame`: enquadramento de imagem/print local, sem alterar seus dados.

As cores e textos de `examples/` são demonstrações, não a identidade aprovada de uma marca. Os códigos podem servir de base a outras animações; novos componentes precisam de validação própria.

## Dependências
Caminho leve: Python 3.10+, FFmpeg/ffprobe, Playwright Python e Chromium. Pillow é necessário apenas para verificar imagens no proof-frame. Node.js é usado nos testes JavaScript; o render leve executa JS diretamente no navegador. Não há download automático pelo script.

Diagnóstico: `python3 tools/doctor_motion.py` na raiz da skill.
Somente após autorização, em ambiente virtual do projeto: `python3 -m pip install playwright Pillow` e `python3 -m playwright install chromium`. Grave versões no lock local. No Mac, a instalação gerenciada do Playwright também funciona; ou informe `--browser-executable` com o executável real de um Chromium compatível. Não use caminhos Linux no Mac.

## Primeiro teste
Na raiz da skill:
```
python3 tools/render_motion.py motion/examples/keyphrase.json --outdir jobs/demo-motion/frames-v1
```
Isso gera PNGs transparentes e um `frames.json`. Não edita a gravação ainda. Para colocar sobre sua gravação, siga `workflows/CREATE_JS_ANIMATIONS.md` e use o plano que prende o efeito à versão final dos cortes.

## Portabilidade
Paths de assets são resolvidos em relação ao JSON que os referencia. `AGENTS.md` é a entrada do Codex; `CLAUDE.md` continua a apontar para ele. Sem dependência de assinatura de modelo específica. As configurações `.claude/agents` só selecionam modelos no Claude Code; outros agentes devem configurar a própria delegação ou executar o trabalho no modelo disponível sem fingir chamadas a Haiku/Sonnet.

## Limites claros
Não é um gerador nativo de filmagens por IA. O render leve não anima vídeos dentro de um print, não aplica tracking automático de rosto e não gera 3D. React/Remotion é um caminho opcional para cenas complexas, com adapter fornecido e teste ainda pendente. Fonte, sistema operacional e navegador podem alterar rasterização; valide a sua máquina antes de lote de produção. Não são incluídos arquivos de fontes ou mídias de clientes.
