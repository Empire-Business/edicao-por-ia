# Workflow — preparar e usar sem exigir conhecimento técnico

## Missão
O usuário conversa com um editor; o coordenador organiza ferramentas e decisões. Uma pergunta essencial por vez. Não abrir outro briefing para dados já fornecidos.

## Preparação
Na instalação guiada pelo usuário, confirmar sua conta do GitHub antes de obter o projeto e seguir INSTALL_WITH_CLAUDE.md. O setup aplicado verifica essa autenticação, sem ler/imprimir credenciais. Público não implica permissão de escrita nem bloqueia downloads manuais anônimos.
1. Detectar pasta e host atual. Ler `COMECE-AQUI.md`, executar `python factory.py doctor` usando Python 3.11+. Se Python faltar, apresentar instalação oficial adequada e obter autorização; não fingir que o instalador Python se executa sem Python.
2. Não declarar “pronto” com base só em FFmpeg. Para fala, precisa de transcritor; para JS, navegador e Node; máscara/rastreamento continuam opcionais com implantação própria.
3. Gerar `python factory.py setup --host both` como prévia (ou apenas host escolhido). Mostrar resumo/conflitos; com autorização usar `--apply`. Não substituir configurações globais nem ampliar permissões.
4. Preparar apenas dependências faltantes: `dependencies --capability ffmpeg`, depois `speech`; `motion` somente se o pedido usar animações. Cada comando mostra prévia; obter autorização antes de `--apply`. Criar `.venv`, não alterar Python global. Após criar venv, repetir setup para os hooks usarem o novo interpretador.
5. Executar `doctor --smoke` e, após instalação de ASR/pesos autorizada, transcrever trecho de prova. Biblioteca encontrada não é prova de voz reconhecida. Registrar o que foi realmente testado e o que está pendente.
6. Verificar modelos no seletor do próprio host e modo assinatura/API, sem ler `.env`, chaves ou arquivos de auth. Confirmar créditos extras com usuário quando “nada por fora” for uma restrição. Usar `model-bind` somente com evidência da disponibilidade. Não presumir preços ou equivalência de modelos entre hosts.
7. Configurações locais alteradas exigem reabrir a sessão. Se o ambiente bloquear uma integração, explicar o bloqueio, não desabilitar a segurança para contornar.

## Atualização de uma instalação anterior
Leia `workflows/UPDATE_FACTORY.md`. O usuário pode pedir “Atualize esta fábrica”. Use o atualizador de código com backup, revisão main fixada por SHA e migrações declaradas. Não substituir jobs, catálogo, IDs, memória, chaves, configurações ou gastos. Conflitos deixam a versão ativa intacta para revisão. Nunca usar git reset/clean como atualização.

## Pasta portátil
Todos os materiais precisam estar dentro da pasta copiada da fábrica. Quando o usuário enviar
um arquivo externo, importe uma cópia verificada com `tools/workspace_files.py import` antes de
criar o trabalho. Não guarde caminhos absolutos de outro computador ou atalhos para fora.
Use referências internas relativas/`workspace://`; vídeos, roteiros, imagens, fontes e bibliotecas
específicas do projeto acompanham a pasta. Os programas são preparados pelo setup na máquina nova.

## Pedido de edição
1. Exigir um formato F e uma ID visual ID escolhidos explicitamente pelo usuário. Usar `workflows/FORMAT_MEMORY.md`. Perguntar somente pela escolha que falta: formato F e/ou ID visual ID; cadastrar somente o formato solicitado, com recibo, e atualizar as pastas com `tools/format_catalog.py refresh`. Não editar sem formato, nem herdar owner, sessão antiga, único cadastro, Bruno, suas cores ou exemplos de outros formatos.
2. Extrair gravações, número de vídeos, roteiros, assets e padrão. Receita: a do F escolhido; nenhuma ID padrão; perfil ausente: equilibrado. Padrão desconhecido: mostrar existentes.
3. Criar um JSON no formato de `jobs/INTAKE_TEMPLATE.json` para `factory.py intake`. Caminhos devem existir. Se já cadastrado, usar `resume`, não criar mais pastas. Duas saídas criam dois jobs, **um lote e um orçamento**.
4. Trabalho antigo: confirmar F e ID e usar `factory.py assign-design --job E01 --format F01 --visual-id ID03 --note "Escolha atual"`. Isso mantém o lote e o gasto, invalidando as etapas editoriais dependentes. Nunca recriar o lote para contornar o bloqueio.
5. Não tratar a análise ainda inexistente como concluída. Rodar `workflows/EDIT_VIDEO.md` e registrar checkpoints conforme `workflows/RESUME_JOB.md`.
6. Antes de workers remotos: configurar orçamento, verificar modelo e registrar autorização. Preferir ferramentas locais. Não delegar as sete funções por rotina.
7. Linguagem visual nova: primeiro trecho-piloto. Estilo já aprovado: reutilizar. Depois da prévia, salvar feedback com escopo correto, revisar o necessário e registrar aprovação de verdade.

## Encerrar cada turno
Salvar novas informações/feedbacks relevantes com recibo. Registrar etapa, pendência e próxima ação. Entregar resumo curto do que aconteceu, onde está a prévia e a única decisão necessária. Nunca falar “anotado”, “testado” ou “finalizado” sem a correspondente gravação/verificação.

### Pasta antiga/misturada ou atualização sem base confiável
Siga a seção de recuperação em `workflows/UPDATE_FACTORY.md` e `ATUALIZACAO.md` da versão nova. Prepare uma pasta separada com `recover_installation.py`, mantendo a origem intacta. Não exigir que um iniciante execute comandos ou resolva conflitos Git. Não declarar uma recuperação pronta apenas por ter copiado arquivos: conferir um trabalho antigo, gastos, mídia, catálogo/IDs e pendências; preparar o ambiente executável à parte.
