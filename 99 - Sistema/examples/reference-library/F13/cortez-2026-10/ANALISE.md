# F13 · Dados Dark: análise do exemplo original

Exemplo original produzido pelo sistema. 30,0 s, 9:16, ID ID03 Azul, receita `f13-v2`.

## Mecanismo demonstrado

- Abertura com pergunta: partículas convergem para um mapa do Brasil em pontos (malha estadual, 857 pontos).
- Contador 203 MILHÕES (embaralha e bate só no valor real) sobre o mapa recuado.
- Cada um dos 100 pontos sai de um ponto do mapa da própria região e forma uma grade 10×10 com escala explícita (1 ponto = 1% ≈ 2 milhões de pessoas); os grupos acendem e o ranking cresce no tempo da fala: Sudeste 42, Nordeste 27, Sul 15, Norte 8, Centro-Oeste 8.
- Volta ao mapa, foco no Centro-Oeste com alfinete e cartão +1,2% AO ANO (2010 → 2022).
- Títulos pesados em caixa alta com palavra-chave em bloco azul (ID03), cabeçalho e nota de fonte em mono; legendas curtas de apoio sem destaque por palavra; trilha original baixa com ducking, -16 LUFS.

## Roteiro

Se o Brasil tivesse só cem pessoas, onde cada uma estaria? O Censo de 2022 contou 203 milhões de habitantes. Aqui, cada ponto vale um por cento. Quarenta e dois pontos ficam no Sudeste. Vinte e sete, no Nordeste. Quinze, no Sul. Norte e Centro-Oeste dividem o resto, com oito pontos cada. Mas quem mais cresce é justamente o Centro-Oeste: um vírgula dois por cento ao ano, desde 2010.

## Fontes e verificação

- IBGE, Censo Demográfico 2022 (divulgação de 28/06/2023): população de 203,1 milhões; Sudeste 41,8%, Nordeste 26,9%, Sul 14,7%, Norte 8,5%, Centro-Oeste 8,0%; crescimento anual 2010–2022 de 1,23% no Centro-Oeste, o maior entre as regiões.
- Percentuais arredondados para somar 100 pontos (Norte 8,5% → 8; Centro-Oeste 8,0% → 8), como diz a nota no quadro.
- Contorno dos estados: arquivo público `brazil-states.geojson` (projeto click_that_hood, derivado da malha do IBGE), usado só para posicionar os pontos.

## Transferível e não transferível

Transferível: a mecânica descrita acima. Não transferível: personagens, vozes, assunto, textos, cores e fontes deste exemplo; a aparência de uma nova edição vem da ID escolhida.
