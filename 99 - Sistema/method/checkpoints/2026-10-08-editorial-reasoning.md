# Checkpoint — raciocínio editorial e revisão localizada

Data: 08/10/2026. Release: 2.2.1.
Base pública: `ff0f3ca3c9c3cb51421efa6664f4d85b4c2cba7a`, obtida diretamente da main de
`Empire-Business/edicao-por-ia` (ID 1408655066) em checkout separado. Histórico local antigo,
trabalhos, memória, credenciais e materiais privados não entram neste checkpoint.

## Mudança e motivo

- `method/EDITORIAL_REASONING.md` explicita fala → forma informacional → mecanismo permitido
  pela receita → cue semântico e evidência. Lista, processo, comparação, definição e demonstração
  deixam de depender somente de uma indicação genérica de "dinâmica".
- `method/examples/EDITORIAL_DECISIONS.md` traz exemplos didáticos sintéticos, identificados
  como tais, incluindo negação, dependência e ausência de prova real. Não aprova nenhum formato.
- `visual/EDITORIAL_REASONING_TEMPLATE.json` oferece anotações opcionais para beats e issues.
  O QA localiza tempo, fala, cena, problema, correção e resultado esperado no registro atual.
- Direção visual, planejamento, análise de referência e QA remetem a essa orientação no fluxo
  existente; os contratos documentam que as anotações não controlam render nem concedem aprovação.
- Oito testes adicionais verificam compatibilidade das anotações e preservação das rejeições
  para colisão, master/review desatualizados, falsa prova, issue aberto e gate pendente.

## Proteções de compatibilidade e precisão

Receitas, nomes, UIDs, catálogo padrão, IDs visuais, referências e locks permanecem intactos.
Nenhuma alteração em ferramentas de corte, silêncio, render, motion, fidelidade ou aprovação.
Schemas e campos obrigatórios continuam iguais; as anotações são opcionais, sem migração.
Planos antigos não precisam ser reescritos. `keep` é válido; não há cota de cobertura, efeitos,
variedade, duração de beats, zoom em todo corte ou CTA obrigatório.

Receita fixada e instruções atuais prevalecem sobre a nova orientação. Cue precisa corresponder
à informação real; proximidade de alguma palavra não prova semântica. ASR incerto, simulação,
material sem origem e ausência de playback continuam sujeitos às regras existentes.
Exemplos comentados não mudam preferência permanente nem certificam execução de um formato.

## Verificação antes da publicação

- Pacote 2.2.1: manifesto com 915 arquivos; nenhuma inclusão de dados do usuário. A lista de
  arquivos anterior foi preservada, com quatro novos arquivos de documentação/template.
- `check_release.py --tests`: PASS. Instalação limpa a partir somente do manifesto e recuperação
  de layout antigo exercitadas, incluindo preservação de bytes, catálogo e ledger sintéticos.
- Regressão Python: 485 testes considerados, 484 passaram, um skip por ausência da dependência
  opcional `jsonschema` no teste preexistente do exemplo de memória. Nenhum teste falhou.
- Regressão JavaScript: 42 testes passaram (20 motion, 22 estúdio), sem skips/falhas.
- Upgrade, mescla, rollback, fidelidade ao formato, isolamento, silêncio, memória e catálogo
  passaram dentro da regressão Python. As migrações do pacote continuam as mesmas.
- Testes focados: 51 de direção visual e 68 de estúdio passaram, incluindo os oito casos novos.
- Na instalação local, os 124 arquivos protegidos por snapshot continuam com os mesmos hashes,
  incluindo 50 arquivos em patterns e ferramentas de execução. No checkout público, receitas,
  catálogo, IDs padrão, referências, locks e ferramentas não têm diff em relação à base.
- Aplicação local limitada a documentos, template, testes, VERSION e manifesto, com backup e
  recibo dos arquivos anteriores. Nenhum job, banco de memória ou identidade pessoal foi alterado.
- Após registrar estes resultados, o manifesto é reconstruído e sua integridade é conferida
  novamente. A conclusão do pacote não é uma aprovação artística de um trabalho.

Testes sintéticos verificam contratos e compatibilidade; não comprovam qualidade artística
de uma edição em material novo. Não foi produzido vídeo de cliente nem alegada revisão de
movimento/áudio de um novo trabalho. O método exige a revisão real já existente em cada edição.
