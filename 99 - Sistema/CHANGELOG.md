# Histórico de versões

## 2.5.0 — 20 de outubro de 2026

- Variações de reel para teste, em qualquer formato e na quantidade que a pessoa quiser (pedido do autor: "qualquer
  pessoa pode querer fazer algo semelhante na quantidade que quiser"). Novo fluxo `workflows/REEL_VARIATIONS.md`
  (substitui `HOOK_VARIATIONS.md`), com dois jeitos que podem ser misturados: gancho re-editado (começo diferente e
  legenda, transições, cor e trilha variando no resto) e post com foto chamativa (mecânica do F19, nova foto e frase
  por versão).
- Nova ferramenta `tools/reel_variations.py`: `plan` cria o plano de N variações já diferentes entre si, `check`
  bloqueia repetições (mesma foto e frase, mesma combinação de gancho) e campos vazios, e `post` gera o post com as
  cores e a fonte da ID escolhida.
- Painel de formatos e cada "Como usar" explicam como pedir variações; a ajuda ganhou a seção "Variações para testar
  reels" e passou a explicar que a troca de roupa devolve o rosto original.

## 2.4.0 — 20 de outubro de 2026

Correções pedidas pelo autor durante a edição de reels (br05, br06 e br08), para não se repetirem:
- Silêncio: todos os formatos passam a cortar pausas acima de 0,15 s, mantendo cerca de 0,05 s de cada lado e aparando
  o começo e o fim de cada tomada. Um ritmo mais solto continua possível quando o trabalho pede explicitamente.
- Erros de gravação escondidos: nova ferramenta `tools/find_hidden_retakes.py` encontra falsos começos e repetições que
  a transcrição engole (palavra "longa", fala não transcrita, frase repetida) e retranscreve cada trecho sozinho.
  Passa a ser obrigatória na voz original e na voz final.
- Troca de roupa sem perda de qualidade: enviar só o recorte que aparece na tela e devolver o rosto original em
  resolução cheia com `tools/composite_original_head.py` (rastreado quadro a quadro, sem emenda).
- Novas checagens de qualidade: gancho visível no 1º quadro, rosto de comentaristas e legendas estrangeiras fora,
  trechos de B-roll sem transição cinza/preta, comparações conferidas quadro a quadro, temporário de render no disco
  de trabalho.
- Motion próprio no lugar de B-roll genérico quando a fala apresenta um produto do autor.
- Novo fluxo `workflows/HOOK_VARIATIONS.md` para entregar 5 variações de gancho para teste.

## 2.3.0 — 12 de outubro de 2026

- Troca de roupa e de cenário em um trecho curto de uma única gravação, disponível em qualquer formato. Usa um modelo de edição de vídeo pela OpenRouter, com chave própria em OPENROUTER_API_KEY.
- Ferramenta `tools/gen_video_edit.py`: lista modelos e preços atuais, gera o trecho no tamanho e na cadência da gravação com o áudio original, cria o antes e depois e monta uma cópia derivada da gravação sem alterar a original.
- Cada trecho exige consentimento para o gasto e para o envio, com limite de custo por geração. Não há autorização permanente.
- Validado em trechos verticais de 5 segundos com o modelo padrão. Outros modelos e trechos mais longos ainda não foram testados.

## 2.1.0 — 6 de outubro de 2026

- Todos os formatos padrão acompanham uma biblioteca de referências reais disponíveis: vídeos completos, fotos, pranchas, áudios de referência e análises, organizados por F.
- Biblioteca incluída no manifesto e nas atualizações, com checksum de cada arquivo. Ausência de uma referência indexada bloqueia o release.
- Guias exibem prints e vídeos locais; a IA recebe o caminho da biblioteca ao consultar o formato. Referências não impõem a pessoa, cor, fonte ou logo de outro vídeo.
- Links padrão apontam às coleções reais. Links próprios de usuários permanecem preservados.
- Bancos privados, chaves, ledgers e outros arquivos dos trabalhos continuam locais; somente cópias de materiais selecionados como referência são distribuídas.

## 2.0.2 — 6 de outubro de 2026

- Atualização somente por pedido à IA, com os mesmos backups e controles de preservação.
- Retirados os três atalhos de atualização da raiz e da distribuição. Cópias antigas sem personalizações são retiradas pelo atualizador com backup.
- Guias técnicos de atualização e versões ficam em 99 - Sistema; a ajuda legível continua em 03 - Ajuda.
- Regra permanente para manter a raiz simples e não recriar atalhos ou instaladores visíveis.

## 2.0.1 — 6 de outubro de 2026

- Guia de atualização e recuperação para estruturas antigas, conflitos e pastas misturadas.
- Recuperação assistida em pasta nova com pacote verificado, prévia, verificação das cópias e recibo; origem permanece intacta. Duplicatas são preservadas separadamente.
- Doze exemplos ilustrativos próprios incluídos nos guias e nos cadastros iniciais. Links apontam às ilustrações; não representam execução aprovada ou a referência histórica.
- Atualizador técnico com mensagens legíveis e verificação de alterações reais nos arquivos locais.
- README com primeira instalação, F/ID/E, integrações, atualização e preservação de dados.
- Testes no GitHub para integridade do pacote, instalação limpa, atualização, recuperação e regressão. Recursos opcionais dependem do ambiente disponível.

## 2.0.0 — 6 de outubro de 2026

- Separação de doze formatos de edição e oito IDs visuais; escolha de ambos exigida antes de editar.
- Códigos estáveis F, ID e E e nomes simples.
- Guias HTML detalhados por formato, sem logos automáticas.
- Link de exemplo obrigatório para novos cadastros; registros anteriores dispensados.
- Arquivo visível de chaves e ScrapeCreators como única integração para cenas pedidas de TikTok/YouTube.
- Materiais locais portáteis e atualização transacional de código com backup, revisão de conflitos e migrações aditivas.

## Estruturas anteriores

Versões anteriores podem ter `tools`, `jobs` e `context` diretamente na raiz. Os relatórios técnicos históricos ficam em `99 - Sistema`. Para migrar dessas estruturas ou de uma pasta misturada, siga **ATUALIZACAO.md**; sincronização de Git não executa as migrações de dados.
