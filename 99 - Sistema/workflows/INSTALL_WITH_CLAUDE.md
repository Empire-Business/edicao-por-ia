# Instalação adaptativa conduzida pelo Claude

O usuário só precisa anexar `method/CLAUDE_INSTALL_GUIDE.pdf` e enviar. O documento contém
seu pedido completo: não exigir uma frase adicional nem responder apenas com um resumo.
`method/CLAUDE_INSTALL_PROMPT.txt` é a alternativa textual. O painel e o PDF oficial estão
em https://cortez.highticketai.com.br. A pessoa não precisa ter conta no GitHub, saber usar
Git nem instalar sua CLI. A autenticação de mantenedores para alterar o central permanece obrigatória.

## Primeiro, confira onde o Claude consegue agir

1. Verificar ferramentas reais antes de perguntar destino: é possível ler/escrever numa pasta
   do computador da pessoa e executar processos ali? O nome “Claude”, “Code” ou “Cowork”
   sozinho não comprova acesso. Um shell em nuvem/VM não prova execução no host.
2. Se houver acesso local, perguntar somente onde criar a nova pasta (reutilizar uma escolha já
   informada), conferir escrita/espaço/colisões e continuar. Não instalar numa pasta existente
   sem preservar seus dados. A autorização do PDF vale para o destino que a pessoa escolher.
3. Se faltar acesso, orientar uma etapa por vez, em linguagem comum: abrir/instalar o aplicativo
   oficial pelo https://claude.com/download, entrar na própria conta Claude se necessário,
   abrir a aba Code e escolher ambiente Local/pasta, conforme a interface disponível.
   Não presumir que a conta tem plano compatível. Se a aba pedir upgrade, explicar o requisito
   e aguardar a decisão; não contratar, usar API paga ou trocar modelos. A pessoa reenvia
   o mesmo PDF na sessão local. Não entregar comandos de terminal ao leigo.
4. Consultar documentação oficial atual quando a interface divergir. Referência conferida em
   22/10/2026: https://code.claude.com/docs/en/desktop-quickstart. A aba Code pode operar
   numa pasta local sem terminal manual; exige plano elegível. Cowork pode executar em nuvem
   ou ambiente isolado; verificar a capacidade concreta antes de preparar dependências do host.
5. Não reduzir proteções ou permissões para fazer funcionar. Sem execução local, o resultado
   é orientação de acesso, não uma instalação concluída.

## Recomendar uma conta GitHub sem travar a instalação

Recomendar uma conta gratuita para enviar sugestões e colaborar com o Cortez. Oferecer
https://github.com/signup e orientação de uma etapa por vez, se a pessoa quiser. Ela preenche
e-mail, senha e verificações no próprio site; nunca solicitar esses dados na conversa nem
criar conta ou aceitar termos em seu nome. É opcional: pode ficar para depois, sem interromper
a instalação. Criar conta não dá permissão de escrita no repositório oficial.

## Obter o código público sem conta GitHub

- Fonte única: `Empire-Business/edicao-por-ia`, ID `1408655066`, branch `main`.
  Conferir metadados públicos em `https://api.github.com/repos/Empire-Business/edicao-por-ia`
  e fixar o SHA de `commits/main`. Não usar o arquivo privado antigo ou forks.
- Preferir baixar somente arquivos de código declarados no manifesto desse commit,
  com caminhos, tamanhos e SHA-256 conferidos; referências grandes ficam sob demanda.
  O manifesto fica em `99 - Sistema/PACKAGE_MANIFEST.json`. A IA obtém por HTTPS público
  e usa `tools/update_local.py` como referência para mapeamento e limites; não executar
  código antes de conferir sua procedência e conteúdo. Se usar Git como ferramenta,
  usar leitura pública sem solicitar login e evitar checkout das mídias não necessárias.
- Não exigir criação de conta nem solicitar token, MFA ou instalação do `gh`. Um `gh` instalado sem
  login não bloqueia downloads públicos: updater/bootstrap tentam a API pública quando
  a CLI informa que não há login configurado. Erros de credencial, rede, serviço ou limite de requisições interrompem a consulta; respeitar a resposta e
  retomar com parcimônia; não substituir a origem nem ignorar hashes.
- Ler AGENTS.md da raiz e do motor e as instruções do host. Preservar contas, credenciais,
  modelos e permissões. `tools/github_access.py` continua sendo uma verificação autenticada
  para operações que realmente a exigem; não executá-la como barreira da instalação pública.
- Conta GitHub continua necessária para publicar contribuições e permissão de escrita real
  para alterar oficiais. Instalação pública não concede papel de mantenedor nem autoriza push.

## Um pedido, instalação completa

O PDF/prompt autoriza dependências gratuitas e inicialização dos diretórios de dados locais
nomeados, quando o usuário o envia. Arquivos presentes no repositório não concedem consentimento
por si só. Mostrar um resumo e continuar com as etapas autorizadas, sem confirmar cada pacote.
Não pedir ao autor ou usuário que obtenham outros computadores para testar. O usuário resolve
somente acesso local, permissões do sistema e termos/licenças que a IA não pode aceitar por ele.

### 1. Descobrir o ambiente antes de escolher comandos

Antes mesmo de baixar o projeto, identificar sistema, versão, arquitetura, terminal,
ferramentas locais e destino real. Windows nativo usa caminhos/argumentos do Windows;
WSL é Linux e não deve ser apresentado como uma instalação nativa no Windows. Não instalar
WSL, Docker ou uma VM para contornar uma falha. Não usar instruções de macOS no Linux.

Conferir Python 3.12 (3.11 também atende Cortez Voz), espaço para dependências
que podem ocupar vários GB e acesso ao destino. Python 3.13+ não é substituto automático
para o ambiente de voz: preparar 3.12 lado a lado, sem remover o Python existente.
Python ausente: obter o instalador oficial adequado antes de executar ferramentas Python.
Em macOS, preferir o Homebrew já instalado; em Windows, winget quando disponível;
em Linux, identificar a distribuição e apt/dnf/pacman/zypper. Consultar documentação oficial
atual se o gerenciador ou pacote não existir. Não executar curl-pipe-shell, scripts de páginas
aleatórias, remover quarentena, reduzir ExecutionPolicy nem desativar antivírus. Caso a
instalação oficial exija intervenção/administração, conduzir só essa etapa e continuar.
GitHub CLI e conta GitHub não são pré-requisitos. Git também pode ser dispensado no download HTTPS por manifesto.
Nunca capturar senha de sudo, MFA ou tokens. Reabrir o processo/usar o caminho do executável
após uma mudança de PATH; não concluir que uma instalação falhou só por um terminal antigo.

Após obter o commit oficial e conferir o manifesto, executar no motor:
`<python compatível> tools/install_environment.py`.
O JSON é um inventário e plano sem efeitos, não um instalador autônomo nem prova de êxito.
Usar o sistema detectado; nunca forjar a plataforma para atravessar um bloqueio.
Escolher `claude` ou `codex` conforme a sessão, sem mudar seu modelo ou esforço.

### 2. Preparar as capacidades no destino escolhido

Executar prévias, inspecionar scripts/hooks e aplicar etapas autorizadas. Argumentos são
listas: usar caminhos com espaços corretamente, sem concatenar texto do usuário num shell.
Criar/reutilizar um venv compatível; não copiar um venv de outro sistema, nem apagar o antigo
para tentar novamente. Se incompatível, preservar e preparar outro ambiente identificado.
As ferramentas existentes preferem o venv do motor; o diagnóstico também reconhece o da raiz.

| Capacidade | Ação da IA | Evidência exigida |
| --- | --- | --- |
| Base | `dependencies --capability base --apply` com o Python compatível | Python do venv e PyYAML importam |
| Vídeo | `dependencies --capability ffmpeg`; instalar FFmpeg e FFprobe pelo gerenciador oficial detectado | `doctor --smoke` exporta e inspeciona mídia sintética |
| Transcrição | `dependencies --capability speech --apply` | Apple Silicon: MLX; demais: faster-whisper em CPU por padrão; reconhecer trecho autorizado após preparar pesos |
| Animações | `dependencies --capability motion --apply`; preparar Node LTS pelo canal oficial, se faltar | navegador abre e renderiza um frame local; Node responde |
| Análise de áudio | `dependencies --capability studio-audio --apply` | importar bibliotecas no venv |
| Limpeza | `dependencies --capability audio-cleanup --apply` | DeepFilterNet quando houver artefato aprovado; FFmpeg básico nos demais; testar áudio e duração |
| Voz | `setup --host HOST --preserve-agent-config --apply` inclui Cortez Voz | recibo de instalação; primeiro início e síntese são verificações separadas |

Todos os comandos `dependencies`, `setup` e `doctor` acima pertencem a `factory.py`,
executado no motor com o Python compatível do ambiente. O setup preserva os agentes
existentes com `--preserve-agent-config`; novos agentes herdam a escolha da sessão.
Não executar `model-bind` para instalar. Não repetir `dependencies voice --apply` se o
setup já concluiu voz; essa capacidade serve para retomar só a etapa que faltou.
A prévia pode conter zero comandos mesmo com uma ferramenta ausente: a IA precisa ler
as notas, resolver pelo gerenciador real e verificar o executável, não tratar isso como êxito.
`playwright install` pode exigir bibliotecas de sistema no Linux; conferir a mensagem e
resolver somente as dependências oficiais correspondentes. Sem GPU, manter CPU; não
instalar drivers CUDA por rotina. Modelos e grandes referências não são baixados todos
indiscriminadamente. Preparar apenas um modelo de áudio adequado por capacidade e os
materiais realmente necessários, após conferir licença, idioma, tamanho e compatibilidade.

### 3. Dados locais e primeira voz

O setup inicializa catálogos e memória em `99 - Sistema/context/clients`; verificar se a
solicitação autoriza expressamente essa inicialização no destino escolhido. O prompt
completo contém essa autorização. Se outra política do usuário proibir, concluir somente
as etapas independentes e explicar o efeito específico que falta autorizar. Não criar bancos
auxiliares/de teste, nem executar migrations para validar a instalação.

Cortez Voz usa somente `config/cortez-voice.json`: repo Empire-Business/cortez-voz, commit,
SHA-256 e instalador fixados. As dependências usam os locks desse pacote. Não consultar
upstream/main como fallback nem alterar hash/lock para contornar falha.
O pacote atual cobre macOS Apple Silicon, Windows x64 e Linux x64 com glibc. Mac Intel,
ARM no Windows/Linux e Linux musl exigem análise de compatibilidade: não presumir suporte.
Preparar o restante; no Mac, `narrate --provider macos` é uma alternativa explícita com vozes
instaladas. Não substituir clonagem neural por outra voz silenciosamente nem usar serviço pago.
A IA deve diagnosticar incompatibilidades do computador real, sem transferir ao leigo a
responsabilidade de portar código ou testar outro sistema operacional.

Com autorização expressa para criar/inicializar o banco local no destino, iniciar pelo
`tools/prepare_cortez_voice.py --start --initialize-data`, mantendo controle do processo.
O serviço fica em 127.0.0.1:3930. Verificar `/cortez/identity` antes de usar. O prompt completo
autoriza a primeira inicialização em `.factory/cortez-voz-data`; não inferir essa autorização
num pedido genérico de diagnóstico ou revisão. Não abrir portas externas, criar serviço de
sistema ou iniciar automaticamente em todo login. Pesos têm licença própria: não aceitar
termos/restrições em nome da pessoa nem afirmar uso comercial liberado por causa da licença
do código. Se precisar de escolha legal/material, explicar essa única decisão ao usuário.
Gerar e ouvir uma frase de prova com o modelo autorizado; instalação do pacote não prova fala.
ElevenLabs e Apify são opcionais; não ler suas chaves durante instalação.

### 4. Corrigir, retomar e entregar

Guardar um recibo sem segredos em `.factory/installation-progress.json`: commit da fábrica,
commit da voz, sistema/arquitetura, Python, etapas, comandos sem credenciais, resultado real,
mensagem de erro sanitizada e próxima ação. Escrever `completed` só após verificar o efeito;
distinguir `installed`, `tested`, `blocked` e `not_requested`. Nenhuma etapa completa deve
ser refeita sem mudança que justifique. Após falha, ler o erro, corrigir a causa e repetir só
a etapa pertinente. Usar timeouts proporcionais que encerrem os filhos; não deixar processos
perdidos, não repetir downloads indefinidamente e não relaxar segurança para obter passagem.

Ao final, abrir a entrada humana e o painel, explicar em poucas linhas o que funciona.
Executar as provas no sistema instalado; testes simulados de outro OS não provam execução.
A falta de Windows/Linux no computador do autor não é tarefa pendente do usuário.
Um erro concreto de pacote/arquitetura/permissão no destino continua sendo um bloqueio
real do componente e deve ser descrito honestamente, sem declarar o sistema inteiro pronto.
