# Exemplos comentados de raciocínio editorial

Exemplos sintéticos para explicar decisões. Não são gravações inspecionadas, planos executáveis,
edições aprovadas, referências de um F específico nem provas de qualidade artística. Não copiar
tempos, cores, fontes ou pessoas. A aplicação real usa a receita/ID escolhidos e a fala gravada.

| Fala hipotética | Forma | Decisão condicionada à receita | Precisão e revisão |
| --- | --- | --- | --- |
| "Os problemas são retrabalho, atraso e falta de informação." | Lista | Revelar itens no mecanismo de lista do formato, nas respectivas ocorrências; manter anteriores se a receita pede acúmulo. | Não apresentar problemas como etapas causais; ler negações e contexto antes de resumir. |
| "Antes de publicar, preciso da confirmação do responsável." | Dependência | Se diagramas forem permitidos, mostrar a publicação aguardando confirmação; se o formato prioriza depoimento, manter a pessoa. | Não usar foto aleatória de chefe nem inventar aprovação concluída. |
| "Tenho quatro assinaturas, mas uso apenas uma." | Comparação/quantidade | Explicitar "contratadas: 4" e "usadas: 1" no mecanismo permitido, com entrada ligada a cada informação. | Não inferir economia ou gasto: faltam preços e período. Uma razão calculada precisa explicitar a base e não se apresentar como número falado. |
| "Abra a aba Relatórios e selecione o período." | Demonstração/processo | Mostrar captura real do produto; destacar aba e seletor nas ações correspondentes. | Conferir ponto, legibilidade e estado da tela. Sem captura, registrar falta; não inventar interface nem usar tela parecida como prova. |
| "Não significa que o resultado seja garantido." | Negação/ressalva | Preservar a ressalva na fala e em qualquer resumo; manter a cena se efeito atrapalhar. | Destacar apenas "resultado garantido" inverteria o significado. Não impor CTA após a ressalva. |

## Como comentar uma referência real

Na nota existente, registrar decisões representativas:
**trecho real/utterance → forma → mecanismo observado → tempo/timebase → frame/hash → motivo →
limite de transferência**. Abrir o frame; usar playback para afirmar movimento e escuta real
para afirmar áudio. Vincular receita, UID e referência corretos. Um exemplo mostra uma
possibilidade; não muda regras nem identidade visual do formato.

## Exemplo de problema localizado

Situação hipotética: durante "selecione o período", a seta aponta para Exportar.
Registrar no issue semântico o shot e frames finais examinados, trecho retido, beat, evidência
do render e correção: apontar ao seletor de período na ocorrência certa, preservando fala e
tela real. Resultado esperado: ação falada e ponto destacado correspondem, com tempo de
leitura suficiente. Reabrir a cena corrigida e a transição.

Preencher `editorial_context` não torna o issue resolvido. A revisão ainda precisa examinar
o resultado e cumprir os gates, hashes e status do fluxo atual.
