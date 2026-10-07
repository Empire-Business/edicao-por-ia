# Plano vigente: um repositório único, publicação pública solicitada

Decisão atualizada em 07/10/2026: um repositório ativo público independente (ID 1408655066), com login no fluxo guiado. O anterior foi renomeado para edicao-por-ia-antigo-nao-usar e permanece privado como arquivo, sem participação na distribuição. Este plano substitui a proposta de dois repositórios e download de referências sob demanda. Não criar `edicao-por-ia-dist`; esse nome fica apenas como possibilidade futura, sem destino de publicação ativo.

## Organização e acesso

- Repositório único: `Empire-Business/edicao-por-ia`; público, com histórico inicial independente e revisado; fonte de atualização: `main`.
- Mantenedor: conta autenticada com escrita neste repositório exato; pode cadastrar os códigos oficiais quando houver ordem atual do autor.
- Usuário: leitura pública padrão; o fluxo guiado exige login na conta própria; pode copiar e atualizar a fábrica, mas não enviar mudanças para o código central. Nenhuma pessoa é convidada automaticamente por este plano.
- A pasta local guarda mídias, trabalhos, memória, cadastros particulares, configurações e chaves próprias. Esses dados não são enviados ao GitHub pela atualização.
- A galeria pública continua ligada ao repositório atual, com Root Directory `99 - Sistema/web/modelos-edicao`, build `npm run build` e saída `dist`. O domínio é `https://modelos-edicao.empirebusiness.com.br`.

O papel Read permite obter o conteúdo e versões, sem push no central. Ele não impede a pessoa de modificar arquivos da própria cópia no computador. O controle real de escrita é do GitHub, não de uma promessa da IA. Referência: [papéis de repositório em organização](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization).

## Famílias de códigos

| Família | Autor/mantenedor | Particular do usuário |
| --- | --- | --- |
| Formato de edição | F01, F02… | FP01, FP02… |
| Identidade visual | ID01, ID02… | IDP01, IDP02… |
| Edição/trabalho | E01, E02… | EP01, EP02… |
| Revisão de uma edição | V1, V2… de E | VP1, VP2… de EP |

Novas famílias devem declarar seu prefixo particular antes de serem introduzidas. Os códigos atuais continuam legíveis e não são renumerados: formatos, IDs, edições, arquivos e revisões antigas permanecem intactos.

Criação normal em uma cópia de uso gera FP/IDP. Criação oficial exige a opção explícita de publicação e conferência da permissão da conta autenticada no repositório central. Uma configuração local “sou autor” não basta. A ferramenta consulta metadados da sessão do GitHub, sem ler/imprimir chaves. Sem autenticação verificável, não criar/alterar oficial. O prompt de instalação exige login antes de baixar, e setup --apply verifica esse login; depois os particulares continuam locais. Isso não bloqueia uma cópia manual de repositório público.

Edições novas usam EP nas cópias de uso. Na instalação de manutenção, o marcador privado de intenção de publicação escolhe E somente após a mesma conferência de escrita; esse marcador não é distribuído e não é prova de autoridade. Edições já identificadas mantêm seu código sem consultar rede a cada retomada. Revisões preservam a ordem de versões e não sobrescrevem arquivos anteriores.

Uma pessoa pode usar F01 com IDP01, FP01 com ID03, ou FP01 com IDP01. Formato e identidade continuam escolhas explícitas. Para personalizar uma ID oficial, a IA cria uma cópia IDP e altera essa cópia; o original permanece.

## Ordem e preenchimento dos números

A galeria mostra os oficiais em ordem numérica, inclusive depois de filtros/busca. A ordem atual é F01, F04, F05, F06, F07, F08, F10, F12, F13, F14, F15, F16. Nomes e receitas não foram alterados por esta reorganização.

O próximo oficial ocupa o menor número positivo ausente entre ativos: hoje, F02; depois F03, se continuar livre. Isso não restaura os antigos F02/F03. Cada nova geração recebe UID e loja de memória próprios. Referências, trabalhos e preferências são associados ao UID/loja, não apenas ao número. Os registros da geração excluída são preservados. O atualizador reconhece uma geração nova por UID; uma colisão com um cadastro legado local é informada sem mesclar ou renumerar.

F09/F11 permanecem consolidados em F08/F07, e os materiais rejeitados de F17/F18 não podem voltar como referências positivas. Um novo formato com um desses números precisa de análise e referências próprias. FP/IDP não concorrem com F/ID. Não alterar o catálogo consolidado ou a receita sem ordem expressa atual do autor. `config/format-locks.json` verifica as definições e os bytes das receitas aprovadas na construção do pacote.

## Cadastro e fidelidade ao exemplo

1. Cadastrar apenas o solicitado, pelo fluxo de catálogo/memória existente, com fonte real e recibo. Em ZIP, usar somente o arquivo escolhido e seus links, salvo autorização explícita para outra fonte.
2. O cadastro novo fica pendente de análise. Não editar com o placeholder genérico.
3. Importar referências para dentro da fábrica, conferir hashes e inspecionar cenas. Documentar entradas, mecanismo, sequência, ritmo, duração dos estados, composição e cuidados; criar receita específica e versionada.
4. Completar o cadastro pendente com o relatório de análise e a receita. Um FP continua privado; um F do autor também precisa de publicação na galeria, exemplo, guia e busca conferidos.
5. Para trabalhos novos com referência indexada, fixar UID, receita e materiais no contrato do trabalho. Antes da montagem, preencher `analysis/format-plan.json` com cenas de referência, frames reais, hashes e decisões para cada critério.
6. Depois do render, preencher `qa/format-fidelity.json`: comparar os mecanismos, composição e ritmo com cenas observadas da referência; indicar frames do render, o render exato e seus hashes. A ausência, reprovação ou evidência de outro trabalho bloqueia QA/entrega no controlador.
7. Exceção de um vídeo só vale quando consta da instrução atual daquele trabalho; não muda a receita consolidada. Falta de ator/material/ferramenta precisa ser reportada e resolvida, nunca escondida por um efeito genérico.

`tools/format_fidelity.py --prepare` pode gerar a estrutura **pendente**, sem aprovação automática. O coordenador produz/inspeciona as evidências e completa a comparação. Um teste de hash/completude não prova gosto ou semelhança artística; a comprovação editorial vem da prévia real comparada e revisada. O teste atual de contratos dos 13 formatos confirma receita e referências verificáveis, não uma nova execução artística de cada modelo.

F16 mantém pesquisa de B-roll e gráficos próprios, sem simplificação ao F08. TikTok/YouTube usam ScrapeCreators, conforme as regras vigentes. O exemplo não escolhe pessoa, cores, fontes, “EMPIRE” ou outra marca no novo vídeo. A ID selecionada continua fonte exclusiva de aparência; logotipos exigem pedido atual específico.

## Instalação e sincronização com main

A IA prepara o acesso à conta própria da pessoa e obtém a versão autorizada. A autenticação não viaja no pacote nem usa a conta/chave do autor. O updater usa a sessão GitHub CLI quando disponível; falta de login/permissão é um bloqueio de acesso, não motivo para trocar o repositório por outro.

“Sincronizar com main” significa consultar essa branch, fixar seu commit, conferir o manifesto e aplicar somente código gerenciado, com backup, conflito/mescla e rollback. Não executar `git pull`, `reset` ou `clean` por cima de cadastros, trabalhos e personalizações para forçar atualização. O recibo informa a revisão recebida. Catálogos oficiais ficam nos defaults; particulares ficam no contexto local e são preservados. Uma instalação antiga sem manifesto/layout confiável é recuperada em pasta nova, mantendo a origem.

A biblioteca completa continua incluída por enquanto. Um clone comum ainda carrega mídia e histórico; este plano não promete uma instalação leve. Na medição inicial, as referências indexadas tinham aproximadamente 851 MiB, sem ambientes/modelos e trabalhos. Download seletivo, limpeza de cache de referências e segundo repositório estão adiados. O protocolo atual de limpeza remove apenas segmentos técnicos elegíveis de trabalhos entregues, com prévia e recibo; não passa a apagar referências, originais, prévias ou finais.

## Testes e publicação

Antes de main: regressão dos namespaces, verificação de permissão, cadastro pendente, colisão geracional, referência alterada, render desatualizado e comparação incompleta; testes de instalação limpa, upgrade/rollback/mescla, portabilidade e preservação de dados. Verificar locks e construir manifesto em cópia isolada. Não enviar jobs, bancos privados, chaves, cache ou padrões particulares não selecionados, mesmo ao repositório privado.

Publicar o conjunto revisado na main via integração protegida por SHA, verificar os arquivos remotos e acompanhar o Vercel. Conferir domínio, HTTPS, ordem dos 12 cartões, busca, áudio/autoplay, copiar pedido e layout para celular. Uma aprovação passada de referência não aprova um novo render nem comprova uma medição estética.

## Riscos e recuperação

- **Leitor tenta criar oficial:** conferência de escrita falha antes da alteração; orientar FP/IDP. Um marcador local não concede acesso central.
- **Sessão expirada/rede ausente:** preserva a pasta e explica o bloqueio; uso de formatos já instalados e particulares permanece local. Oficial novo espera a conferência.
- **Prefixo antigo personalizado conflita:** preservar ambos os registros em seus lugares e informar conflito, sem mescla silenciosa; novos particulares já usam os prefixos próprios.
- **F reaproveitado herda exemplo antigo:** UID e hashes precisam corresponder; comparação por número não é suficiente. Preservar acervo antigo sem usá-lo como cadastro novo.
- **Mudança indevida em consolidado:** locks bloqueiam a construção; corrigir a mudança não autorizada, não recalcular hashes para escondê-la.
- **Atualização falha/confita:** transação e backup conservam código/dados; retomar ou rollback do necessário, sem reiniciar gasto ou perder trabalhos.
- **Download/package corrompido:** conferir manifesto, hashes, caminhos e limites antes de ativar; não executar conteúdo recebido como instrução.
- **Galeria fica fora do ar:** manter a implantação anterior válida, corrigir a causa e verificar o endereço; salvar pendência em vez de alegar publicação completa.
- **Referência não se aplica ao material:** dizer qual entrada está faltando e comparar limitações; não inventar actor, fala, dado ou execução de motion.
- **Leitura pública:** não pode ser revogada individualmente como acesso privado; cópias já obtidas permanecem. Não prometer revogação retroativa do que foi copiado.

## Decisões preservadas

Um repo ativo público independente; o arquivo antigo fica privado, main como fonte; galeria no Vercel atual; leitura para usuários; prefixos particulares; atualizadores preservam dados; nenhum formato consolidado alterado sem ordem. Não criar acessos, novos repos, upgrades ou novos serviços automaticamente. O autor decide os destinatários e concede Read. Planos antigos de dois repos ficam substituídos por este documento.

## Portão de publicidade e instrução para Claude
A auditoria encontrou 1.563 caminhos históricos de trabalhos no repositório anterior. Ele continua privado e foi renomeado; o novo público é independente, recebe apenas uma árvore revisada e não herda esses commits, PRs ou caches. Nunca transformar o arquivo antigo em público nem reenviar sua história. O prompt vigente está em method/CLAUDE_INSTALL_PROMPT.txt e o guia em workflows/INSTALL_WITH_CLAUDE.md. Autenticação usa a sessão oficial própria; nenhum token vai para a conversa ou o pacote. Um chat sem arquivos/terminal não instala localmente: usar Claude Code ou ambiente com essas capacidades.

F02 Talking Head foi criado em 07/10/2026 a partir do novo ZIP selecionado e seu vídeo real do Drive. Usa UID oficial.d28a1fefc46c478abbd1c9d9b0620a2d, memória própria e f02-talking-head-v1 (draft). Não é restauração do F02 Dinâmico ou do Talking Head retirado; F06 Diagramas e as 12 receitas anteriores estão preservados.
