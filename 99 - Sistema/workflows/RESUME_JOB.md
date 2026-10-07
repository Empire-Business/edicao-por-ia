# Workflow — continuar sem recomeçar

`python factory.py resume` lista trabalhos quando houver ambiguidade; `--job ID --format FORMATO` verifica o isolamento do formato. Não escolher só pelo último arquivo de outro formato.

## Fonte de andamento
`.factory/state.sqlite3` guarda lote, entradas, jobs, estágios, reservas e auditoria. `jobs/ID/progress.json` é uma visualização regenerável. Nunca editar o banco para contornar limite ou completar etapa.

Etapas: probe → transcript → scope → script → assembly → silence → visual/captions → preview → approval → final → qa → delivery.

- `probe`: metadados verificados.
- `transcript`: transcrição da gravação real; dispensável só se não houver fala ou houver dispensa justificada.
- `scope`: delimitar o vídeo-filho com JSON `{job_id, segments:[{source,in,out}]}`; fontes absolutas e tempos originais. O controlador confere duração real via FFprobe e bloqueia sobreposição entre filhos, salvo `shared_ranges_authorized:true` com autorização registrada. Esse JSON é evidência da delimitação, não a montagem final.
- `script`: comparar roteiro correto; `assign-script --job ID --path ... --note ...` resolve associação pendente. `--without-script` exige dispensa explícita, não conveniência do agente.
- `assembly/silence`: executar ferramentas sobre o escopo escolhido. Antes de renderizar, validar com `factory.py validate-edl --job ID --edl ARQUIVO`: nenhum trecho de fala pode sair do recorte aprovado.
- `visual/captions`: considerar tempo final; manter cada asset no vídeo correto. Roteiro não substitui transcrição das legendas.
- `preview`: arquivo renderizado; `approval`: decisão explícita do usuário sobre esta versão.
- `final/qa/delivery`: render, revisão real e entrega, separados. Um arquivo existente não prova sua qualidade.

`checkpoint --job ID --stage ETAPA --artifact CAMINHO --note EVIDÊNCIA` só aceita artefatos deste trabalho. `--skip` existe apenas para etapas opcionais. Aprovação usa `--user-approved` somente após o usuário aprovar, jamais para contornar o gate. Um registro técnico não equivale a assistir/ouvir nem autoriza afirmar qualidade artística.

## Alterações parciais
`change --job ID --kind asset|captions|assembly|silence|source|script|visual|pattern --note ...` invalida as etapas dependentes; preserva arquivos e histórico. Print → visual e derivados, sem refazer transcrição. Corte → timings e nova aprovação. Rodar de novo não é obrigação quando tudo permanece válido.

Se um arquivo original/roteiro mudou fora do controlador, `resume` bloqueia por `inputs_changed`. Confirmada a nova versão, `refresh-inputs --batch ID --note ...` atualiza hashes sem mexer no arquivo, invalida o necessário e conserva orçamento. Arquivo ausente não é aceito como substituição.

O formato recebeu feedback novo? `resume` detecta contexto efetivo desatualizado. `refresh-context --job ID --note ...` cria `job.effective-vN.json` e `effective-current.json`, preserva versões e reabre a montagem/revisão. Use esse novo arquivo e os novos ajustes de silêncio. A invalidação de contexto é conservadora; explique o que realmente precisará mudar e preserve trechos aprovados compatíveis.

## Sessão retomada ou troca de agente
Conferir entradas/evidências, contexto e saldo. Chamada iniciada sem resultado não pode ser repetida como se não tivesse gasto. Processos desconhecidos não são cancelados automaticamente. Resolver/conferir antes de conciliar. Arquivos existentes de um job legado sem registro no novo controlador devem ser inspecionados/importados pelo agente; não afirmar que histórico antigo foi reconstruído automaticamente.

## Portabilidade
A pasta contém a memória local; não há sincronização entre máquinas. As mídias continuam nos caminhos autorizados. Se mover o projeto ou as mídias, atualizar os caminhos de maneira explícita, conferir hashes e refazer setup para os hooks; não procurar automaticamente discos privados. Não copiar bancos SQLite abertos: fechar processos e fazer backup consistente.

## Comparação obrigatória com a referência do formato
Para trabalhos novos com format_contract, inspecionar referência real e preencher analysis/format-plan.json antes da montagem. Após renderizar, preencher qa/format-fidelity.json com critérios do contrato, decisões, cenas de referência e frames do render com hashes. O controlador bloqueia montagem/QA/entrega sem comparação válida. Usar tools/format_fidelity.py --prepare para estrutura pendente; isso não aprova nada. Referência, UID/geração, receita e render devem corresponder ao trabalho. Não afirmar semelhança artística só por validação mecânica. Exceção atual deve constar em format_deviations do trabalho e coincidir com user_instruction no relatório; não altera o modelo consolidado.
