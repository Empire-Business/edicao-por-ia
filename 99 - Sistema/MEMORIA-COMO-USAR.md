# Memória de formatos e feedbacks — guia prático

## Como funciona

Um **formato** é um perfil nomeável de edição, com contexto e preferências próprios. Ele é separado
da **proporção de saída** do vídeo: 9:16, 16:9, 1:1 etc. A memória registra informações úteis e
feedbacks durante o trabalho, sem você precisar pedir “salve isso” a cada mensagem. Antes de editar
novamente, o sistema recupera somente o formato do job. O registro é local, tem histórico, origem e
escopo; não é treinamento do modelo.

Exemplos ilustrativos:
- “Este formato usa azul e branco e fala com empresários.” → fatos do formato.
- “Nos próximos vídeos deste formato, quero animações mais discretas.” → preferência duradoura.
- “Só neste vídeo, não ponha legendas.” → exceção deste job, sem alterar os próximos.
- “Gostei dessa animação; mantenha.” → referência aprovada daquela versão.
- “Esse corte ficou seco demais.” → correção localizada; ajustar o corte real e anotar o motivo.
- “Não gostei.” → reação registrada, sem inventar a causa. Pergunta curta se necessária.

A memória não exige uma métrica de alcance para aceitar seu gosto. Métricas são necessárias para
falar de desempenho, não para respeitar uma preferência explícita.

## Atualizar uma instalação sem apagar seu trabalho

Extraia a nova versão em uma pasta separada. Abra seu agente na instalação usada para editar e
indique as duas pastas. Você pode pedir:

> Atualize minha instalação. Preserve meus jobs, padrões personalizados, formatos e arquivos
> locais. Integre os hooks sem substituir minhas outras configurações. Cadastre ou recupere o
> formato com as informações que eu realmente já forneci e salve meus próximos feedbacks
> automaticamente. Não invente informações ausentes. Confirme qual formato está ativo e faça um
> teste de salvar e recuperar uma preferência.

O agente compara os arquivos antes de atualizar. Não sobrescreva `context/clients`, jobs, memórias
ou padrões com dados de outra instalação. O nome `context/clients` é mantido por compatibilidade;
os diretórios dentro dele representam formatos. Dados antigos só podem ser lidos para o formato
identificado, com a origem preservada; dados ambíguos ficam como candidatos. O pacote não acessa
automaticamente o histórico que está no seu computador.

### Hooks no Claude Code

O ZIP contém `.claude/settings.json` pronto para uma pasta nova com Python 3 disponível. Em
instalação existente, o utilitário abaixo faz a mesclagem com backup; não altera permissões:

```bash
python3 tools/install_memory_hooks.py
python3 tools/install_memory_hooks.py --apply
```

O primeiro comando só mostra o plano; o segundo aplica quando você autorizou a configuração. Em
Windows, use o Python disponível, por exemplo `py -3 tools/install_memory_hooks.py --apply`. Abra
uma nova sessão e confira os hooks do projeto. Políticas da organização podem desativá-los. Sem
hooks, o `AGENTS.md` manda o agente executar o mesmo ciclo pelas ferramentas. Os hooks não chamam
modelos nem copiam a conversa: lembram o agente e cobram um recibo.

### Identificar um formato

O agente usa um ID local para o nome que você informou e vincula o job a esse formato.
Antes de editar, informe um formato cadastrado ou peça o cadastro de um novo. A fábrica não
escolhe Bruno, o único cadastro, um formato padrão antigo ou uma sessão anterior automaticamente.
Um trabalho existente especificamente indicado conserva seu formato cadastrado. Marcas, cores e
preferências ficam isoladas. Se o formato não estiver claro, o agente pergunta qual usar e espera
antes de editar, ler ou salvar preferências.

## Como saber se salvou

Após um feedback útil, espere uma confirmação curta dizendo o que foi salvo e qual é o escopo. A
confirmação só vem depois do retorno da ferramenta. Você também pode pedir: “Mostre minhas
preferências de edição”, “Isso vale só para este vídeo”, “Volte à preferência anterior” ou “Esqueça
essa preferência”. O agente usa as ferramentas locais, não só promete.

`tools/format_memory.py context --format ID` mostra o resumo atual. `show --format ID --key CHAVE`
mostra o histórico dessa informação. Os registros completos ficam em SQLite, sem depender de um
serviço externo. O resolvedor gera um resumo e recibo para a revisão do job.

## O que entra na edição

`tools/make_job.py --format ID ...` cria também `job.effective.json`, com preferências mecânicas
suportadas já aplicadas e respeitando seus overrides. `job.effective.silence-settings.json` entra
no planejador de silêncios. Preferências subjetivas precisam ser traduzidas pelo editor em decisões
concretas de cortes e enquadramentos, e conferidas no vídeo real. Se o formato mudou depois do
plano, a verificação avisa para resolver uma nova revisão.

## Aprender com exemplos sem generalizar seu gosto errado

Além das preferências explícitas, existe uma consulta curta às versões que você aprovou ou rejeitou
em trabalhos anteriores do mesmo formato. Ao criar algo semelhante, o agente consulta esse
repertório e o motivo do feedback. Uma animação aprovada pode orientar a próxima; um problema
localizado não vira proibição universal. Reações ambíguas ficam numa fila separada e podem ser
esclarecidas sem reabrir a conversa inteira.

## Compatibilidade e cuidados

Use `--format` nos comandos novos. Jobs antigos com `client`, o argumento `--client`, a chave de
escopo `client` e o caminho `context/clients/<id>/memory.sqlite3` continuam aceitos para preservar
dados existentes. Não é necessário mover nem renomear os bancos. `tools/client_memory.py` e
`tools/resolve_client_context.py` também continuam disponíveis como aliases; as entradas novas são
`tools/format_memory.py` e `tools/resolve_format_context.py`.

A skill não dá ao agente uma memória infalível. Um comentário vago pode exigir esclarecimento. O
hook verifica a revisão, não a qualidade da interpretação. Sem permissão de escrita ou fora da
pasta atualizada, o salvamento pode não acontecer. Guardar localmente não quer dizer criptografar;
não publique os diretórios de formatos no Git. Ao migrar, copie o diretório do formato que deseja
levar; o pacote genérico não contém memórias pessoais. “Esquecer” remove o dado da base atual, não
de backups, exports ou chats do host.
