# Documentário Visual Animado — análise da referência

Formato novo e independente, solicitado em 06/10/2026. Referência autorizada: `greco_dev-2107253470420226331.mp4`.
O cadastro não muda formatos anteriores e não cria um formato padrão da fábrica.

## Evidência e limites

Vídeo vertical de 79,62 s, 1080 × 1920, 60 fps; 35 frames direcionados inspecionados, mais uma folha geral.
Fonte original preservada; uma cópia com o mesmo SHA-256 foi guardada aqui porque a origem está em uma pasta temporária.
`media.json` identifica o arquivo, `analysis.json` resume a evidência e `scene-map.json` relaciona faixas e mecanismos.
A transcrição foi feita localmente com Whisper, sem serviço pago ou envio de mídia.
ASR bruto preservado em `transcript.json`: há erro em Bell Labs e no CTA e repetição numérica na cauda.
Não usar essa cauda como fala/legenda, nem tratar essa hipótese como decisão de corte do original.
Cenas e mecanismos foram observados; a fonte tipográfica, as curvas exatas, os stems e o método original de produção não são conhecidos.
A primeira aplicação da receita ainda precisa ser validada; o padrão tem status `draft`.

## Linguagem visual

É um mini-documentário narrado sem apresentador em câmera: a imagem demonstra cada ideia.
Mistura fotografia histórica, macrofotografia, objetos recortados em perspectiva, diagramas e tipografia.
As telas usam uma camada de contexto pequena no topo (objeto/local/ano), título grande, objeto ou imagem dominante,
labels técnicos pequenos e legenda curta separada. Há profundidade pela escala e sobreposição, sem uma grade de cartões genéricos.

A maior parte do vídeo usa fundo azul-marinho quase preto, texto branco e destaque azul-claro.
Uma sequência central (por volta de 43–55 s) muda para papel claro e texto escuro para criar contraste editorial.
Há textura/grão e pequenos pontos luminosos. Usar isso discretamente, sem competir com a informação.
Valores hexadecimais definidos na receita são aproximações de trabalho, não cores oficiais de uma marca.

## Tipografia e legendas

Headline sans-serif pesada, grande, alinhada à esquerda, com poucas linhas e palavras-chave azuis.
A frase é montada progressivamente (frames 0,70/1,50/2,60 s); não aparece uma parede de texto de uma só vez.
Números dominam a tela nos momentos de escala; unidade ou explicação vem menor, junto do número.
Os contadores mostram dígitos intermediários em movimento: esses frames não representam valores factuais finais.
Labels compactos em caixa alta, com aparência monoespaçada, ligados a pontos relevantes por traços finos.
Legendas inferiores curtas, centralizadas, brancas sobre fundo escuro; algumas palavras ficam azuis.
No trecho claro, o texto passa para escuro e os destaques podem ganhar um fundo azul.
A legenda não disputa espaço com o título; sua região se move de acordo com a composição.
A fonte exata não foi identificada. A implementação pode usar uma sans pesada e uma mono legível equivalentes.

## Ritmo e narrativa

Abertura com contraste concreto: sala inteira versus objeto minúsculo. Pergunta cria a ponte para a explicação.
Depois: problema → primeiras soluções → evolução em marcos → aceleração numérica → comparação final → retorno ao gancho → CTA.
Narração em frases curtas; mudanças visuais acompanham a nova ideia, não uma regra arbitrária de cortar a cada segundo.
A escalada em marcos é mais rápida do que a demonstração de um mecanismo. Manter estados longos o suficiente para ler e comparar.
Faixas narrativas em `scene-map.json` são aproximadas; não são uma contagem automática de planos.
A sequência de fundo claro quebra a monotonia num ponto de virada e a imagem inicial reaparece no final.

## Movimento reutilizável

1. Entrada e substituição de fragmentos do título, sincronizadas à frase.
2. Aproximação/recuo suave de foto ou objeto com movimento discreto de profundidade.
3. Contador numérico que termina no valor correto e fica estável para leitura.
4. Linhas de chamada, pontos e etiquetas que revelam partes específicas do objeto.
5. Comparação lado a lado ou acima/abaixo quando tamanho/quantidade forem o argumento.
6. Vista explodida em camadas quando existem imagens/peças adequadas e uma explicação de componentes.
7. Grade de pontos ou pequenos elementos para demonstrar quantidade, e duplicação visual para demonstrar crescimento.
8. Transições curtas de brilho/flash e mudanças de luminância usadas para separar marcos, em quantidade limitada.

Esses mecanismos não exigem copiar o aparelho, a marca, os fatos, a fala, o nome do criador ou o CTA da referência.
Objetos 3D reais não foram comprovados; perspectiva e camadas 2D podem cumprir o mesmo papel quando suficientes.
Toda animação deve poder ser reconstruída a partir de um tempo fixo; a fala editada comanda a sincronização.

## Áudio

Mix completo medido em −14,6 LUFS integrados, LRA 2,7 LU, pico verdadeiro −4,1 dBFS.
O detector não encontrou regiões abaixo de −35 dB por 0,35 s no mix. Isso não comprova ausência de pausas de voz.
Não houve escuta crítica nem separação dos stems. Música, SFX, timbre e origem da voz permanecem não confirmados.
Para uma nova aplicação, usar áudio autorizado, voz inteligível e trilha/SFX apenas quando servirem à narrativa;
não copiar a voz/trilha do criador. Normalização e limpeza seguem as regras atuais da fábrica.

## O que vira receita e o que não vira regra

A solicitação autoriza cadastrar este estilo como referência do novo formato e usar uma receita derivada v1.
A receita define a estrutura visual; suas faixas de duração, escalas e tamanhos de texto são parâmetros iniciais propostos.
Não são medidas exatas recuperadas do arquivo nem uma aprovação de um novo render.
Datas, modelos de chip e números do vídeo são exemplos de conteúdo; validar os dados de cada vídeo futuro.
O botão “Comente PROMPT” e a assinatura final pertencem ao exemplo; usar somente o CTA e a marca do trabalho novo.
As cores deste cadastro permanecem apenas nele e podem ser substituídas por instrução explícita para esse formato/trabalho.
