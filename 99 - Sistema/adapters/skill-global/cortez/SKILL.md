---
name: cortez
description: Cortez edita vídeos com IA numa pasta de trabalho no computador da pessoa (gravações em "01 - Enviar vídeos", entregas em "02 - Ver vídeos"), com formatos de edição (F01 a F21, como Talking Head, Notícia Comentada, Pessoa + Tela) e identidades visuais (IDs). Use quando pedirem "Cortez", editar, cortar ou legendar um vídeo, tirar silêncio, aplicar um formato ou uma identidade visual, fazer cortes de um vídeo longo, instalar o Cortez, achar a pasta do Cortez, atualizar o Cortez pela main ou sugerir um formato novo. Não use para escrever roteiro de VSL, planejar conteúdo de redes sociais ou criar site.
---

# Cortez: porta de entrada

Esta skill é só a porta. Quem faz o trabalho é o Cortez instalado na **pasta de trabalho** da
pessoa: é lá que ficam os vídeos, as entregas, a memória e as regras completas. Esta skill encontra a
pasta (ou ajuda a criar) e passa a trabalhar dentro dela.

Quem usa normalmente não programa. Fale simples, uma pergunta por vez, sem pedir para a pessoa
digitar comandos: você executa, ela decide.

## 1. Achar a pasta de trabalho

Rode o ajudante desta skill (Python 3, sem dependências):

```
python3 ~/.claude/skills/cortez/cortez_pasta.py onde
```

No Windows, use `py -3` ou `python` no lugar de `python3`, e `%USERPROFILE%\.claude\skills\cortez\`
no lugar de `~/.claude/skills/cortez/`.

O que fazer com a resposta:

| Resposta | O que fazer |
|---|---|
| Um caminho | Vá para o passo 3. |
| `"varias"` com uma lista | Pergunte em qual pasta trabalhar, mostrando os caminhos. |
| `"sumiu"` | A pasta registrada não foi encontrada (HD externo desplugado, pasta movida ou renomeada). Diga isso em uma frase e pergunte se a pessoa quer plugar o disco, informar o novo lugar ou instalar de novo. **Nunca instale em outro lugar por conta própria.** |
| `"nenhuma"` | Pergunte: "Você já tem o Cortez instalado em alguma pasta?". Se sim, peça o caminho (ou para arrastar a pasta para a conversa) e registre com `cortez_pasta.py registrar "<pasta>"`. Se não, vá para o passo 2. |

## 2. Instalar (só se a pessoa ainda não tem)

1. Explique em até 3 linhas: o Cortez cria uma pasta no computador onde a pessoa põe as gravações e
   recebe os vídeos editados; a instalação leva um tempo e você faz a parte técnica.
2. **Pergunte onde criar a pasta.** Sugira um lugar fácil de achar, como a pasta Documentos ou um HD
   externo com espaço (vídeo ocupa muito). Evite pastas sincronizadas (iCloud, Google Drive,
   OneDrive): ficam lentas e enchem a cota. A escolha é da pessoa, porque é ela que vai abrir essa pasta
   todo dia.
3. Siga o roteiro oficial de instalação, o mesmo do PDF do Cortez, com a pasta escolhida como destino:
   `https://raw.githubusercontent.com/Empire-Business/edicao-por-ia/main/99%20-%20Sistema/method/CLAUDE_INSTALL_PROMPT.txt`
   Leia esse texto como o pedido da pessoa e cumpra do jeito que ele manda (repositório
   Empire-Business/edicao-por-ia, branch main, manifesto conferido). Se a pessoa já tem o PDF, pode
   usá-lo no lugar.
4. No fim, registre a pasta: `cortez_pasta.py registrar "<pasta>"` (o próprio Cortez também faz isso
   ao concluir a preparação).

## 3. Trabalhar dentro da pasta

1. Leia `AGENTS.md` da pasta e `99 - Sistema/AGENTS.md`. As regras de lá valem acima desta skill.
2. Rode as ferramentas do Cortez com a pasta como diretório de trabalho, do jeito que esses arquivos
   mandam.
3. Para quem é leigo, o dia a dia é este:
   - gravações e materiais vão em `01 - Enviar vídeos`;
   - os vídeos prontos aparecem em `02 - Ver vídeos`;
   - formatos em `04 - Formatos`, identidades visuais em `05 - IDs Visuais`;
   - `00 - COMECE AQUI.html` abre o painel de ajuda.
4. Termine cada resposta dizendo onde o resultado está e qual é o próximo passo.

## 3.1 Ensinar a configurar (quem usa não sabe)

A pessoa quase nunca sabe criar conta, chave ou crédito num serviço. Sempre que um pedido depender de
um serviço extra, ensine antes, em linguagem simples e **um passo por vez**, esperando ela dizer que
terminou:

1. O que é o serviço e para que o Cortez vai usar, em uma frase.
2. Quanto custa e se dá para começar grátis. Antes de qualquer gasto, mostre o custo e peça o sim.
3. Onde clicar, com o nome do botão como está no site. Se a tela estiver diferente, peça para ela
   descrever ou mandar um print.
4. Onde colar: no arquivo `CHAVES DAS INTEGRAÇÕES.txt`, na pasta do Cortez, depois do sinal `=`.
5. Como conferir que funcionou.

| Serviço | Para que serve | Guia na pasta |
|---|---|---|
| OpenRouter (recomendado) | música com IA, narração e capas | `03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html` |
| ScrapeCreators | buscar cenas do TikTok e do YouTube | `03 - Ajuda/COMO CONFIGURAR O SCRAPECREATORS.html` |
| ElevenLabs (opcional) | só tratar ruído pesado da voz; a limpeza local é o padrão | `03 - Ajuda/COMO CONFIGURAR O ELEVENLABS.html` |
| Apify (opcional) | baixar vídeo do YouTube quando o ScrapeCreators não entrega | `03 - Ajuda/COMO CONFIGURAR O APIFY.html` |

Nunca peça a chave na conversa. Se a pessoa colar uma chave no chat, diga com calma para apagar essa
chave no site do serviço, criar outra e colar a nova só no arquivo.

## 4. Atualizar

Quando pedirem para atualizar ("atualize o Cortez pela main"), siga
`99 - Sistema/workflows/UPDATE_FACTORY.md` dentro da pasta. Nunca use `git pull`, `reset`, `clean` ou
ZIP por cima: isso pode apagar trabalhos. A atualização também renova esta skill.

## 5. Nunca

- Gravar vídeo, trabalho ou memória dentro desta skill (`~/.claude/skills/cortez`). Tudo vai na pasta
  de trabalho.
- Pedir senha, token ou chave na conversa.
- Usar serviço pago sem a pessoa concordar com o gasto.
- Publicar, fazer push ou mexer na versão oficial por conta própria.

## Outro sistema operacional

O Cortez roda em macOS, Windows e Linux. Se algo aqui não bater com o computador da pessoa, adapte
você mesmo e conte o que realmente testou:

- **Python:** `python3` (macOS/Linux) ou `py -3` / `python` (Windows). O Cortez pede Python 3.11 ou
  mais novo; este ajudante funciona com qualquer Python 3.
- **Pasta pessoal:** `~` é `%USERPROFILE%` no Windows. A skill fica em `~/.claude/skills/cortez` e o
  registro das pastas em `~/.config/cortez/config.json` nos três sistemas.
- **Caminhos com espaço** (como `01 - Enviar vídeos`) vão sempre entre aspas; no PowerShell, use aspas
  também.
- **Programas** (ffmpeg, Node etc.): instale pelo gerenciador oficial do sistema (Homebrew no macOS,
  winget no Windows, apt/dnf no Linux), como manda o roteiro de instalação do Cortez.
- Falta de Windows/Linux no computador do autor não é pendência da pessoa: teste no computador dela.
