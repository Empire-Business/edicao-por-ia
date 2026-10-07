> Revisão atual: `REVISAO_V1_6.md`. O relatório abaixo é histórico e mantém seu escopo original.

# RELATÓRIO DE CONSTRUÇÃO

- arquivos recebidos: 1 meta-prompt/instrução de arquitetura de skill portátil;
- arquivos preservados: `sources/META_PROMPT_ORIGINAL.txt`;
- arquivos vazios: nenhum arquivo funcional; `.gitkeep` intencionais;
- duplicatas: nenhuma detectada no material recebido;
- fontes convertidas: material original preservado em texto; pesquisa registrada em `sources/RESEARCH.md`;
- regras extraídas: roteamento curto, progressive disclosure, separação regra/exemplo, factualidade, QA, memória e testes;
- workflows criados: setup, ingest, definição de padrão, edição, limpeza de fala, split multi-vídeo, batch, review, QA, aprendizado;
- padrões criados: 3 starters + template;
- exemplos anotados: os patterns starter são explicitamente rotulados como starter, não como aprovados;
- contradições: nenhuma no material-base; o pacote separa Claude como raciocínio de ferramentas locais como execução de mídia;
- lacunas: não foram fornecidos vídeos-referência reais nem padrões de marca do usuário, então não foi inventada uma house style definitiva;
- testes estruturais executados: `tools/verify_package.py` PASS; `compileall` PASS; `doctor.py` executado; smoke test de probe + EDL + render + retime + SRT + QA PASS; teste adicional de source sem áudio + split + frames PASS; fonte sintética permaneceu com o mesmo SHA-256;
- testes comportamentais executados: não executados com LLM durante a construção; os casos em `tests/TEST_CASES.json` permanecem como especificação;
- testes ainda pendentes: transcrição real (nenhum backend Whisper opcional estava instalado no ambiente de build), edição real com mídia do usuário, avaliação auditiva/visual humana e testes com padrões efetivamente aprovados pelo usuário;
- riscos conhecidos: ASR pode errar; cortes semanticamente ambíguos exigem revisão; backends opcionais dependem de hardware/modelos locais; padrões `hybrid` podem exigir implementação Remotion específica por marca.


# Revisão 1.1.0

Veja `REVISION_REPORT.md`: auditoria dos dois pontos pedidos, mudanças implementadas, 37 testes unitários, integração FFmpeg com 16 verificações e smoke original com 6 verificações. A comparação semântica por modelo e a qualidade de edição de gravações reais do usuário permanecem pendentes de execução. Os resultados anteriores acima são históricos, não substituem as evidências desta revisão.

## v1.2.0 revision
- Added explicit support for user-provided insertion assets (images/videos/B-roll/cutaways/proof assets).
- Added `method/INSERTION_ASSETS_POLICY.md` and `workflows/USE_INSERTION_ASSETS.md`.
- Extended job schema/template with `supporting_assets`.
- Added `tools/prepare_supporting_assets.py` for conservative local preparation of still-image clips.
- Updated router, input contract, patterns, and acceptance criteria.

## v1.3.0 — JavaScript motion

Ver `MOTION_REVISION_REPORT.md` para as mudanças, testes realmente executados, correção de fps e limitações. O caminho React/Remotion permanece não testado; a rota JS/browser/FFmpeg foi renderizada e composta de fato.

## Atualização 1.4.0
Para o diagnóstico atual e os testes executados, consulte `MEMORY_REVISION_REPORT.md`.
As seções anteriores deste documento são registros históricos e não novos testes de memória.
O pacote passou a ter cadastro/feedback persistente por cliente e aplicação em jobs efetivos.
