# Adoção crítica do curso — original versus v1.7

O curso recebido é a base desta melhoria. Esta matriz explicita ajustes; não atribui nossas correções ao autor.

| Parte | Situação encontrada na v1.6 | Decisão na v1.7 |
|---|---|---|
| 01 Pixels | Frames determinísticos nos quatro componentes SVG | Ampliado com renderer HTML/Canvas `seek(t)` de código revisado; navegador/FFmpeg continuam responsáveis pelos pixels/MP4 |
| 02 Setup | Preparação assistida já existe | Reutilizar; corrigir dependências de motion (Pillow); áudio opcional separado. Não instalar plugins/frameworks em lote |
| 03 One-liner | Sem rota específica de showreel | Usar só como teste técnico; não como briefing de cliente ou garantia de qualidade |
| 04 Brand | Contexto e assets por cliente já existem | Plano exige origem, hash, associação ao child e UI real; simulações têm rótulo. Sem métrica inventada |
| 05 Reference | Análise conceitual de referência | Guia com observado/inferido/proposto, frames reais e transferir/não copiar; texto com 'Imagem' não substitui referência visual |
| 06 Spec | Briefs de fala/visual, sem state list obrigatório | Plano de shots/estados validável, coverage, cue e motivos; agente preenche, leigo não faz ficha de 12 itens |
| 07 Engine | Renderer limitado a templates SVG | Novo Canvas/HTML com autorização por hash, assets allowlist, render parcial, subframes opt-in, manifest compatível |
| 08 Springs | Componentes com easing | Biblioteca analítica com três regimes de amortecimento e superposição; não converter todas as curvas em molas |
| 09 Sound | Instruções gerais sobre áudio | Detector de beats/onsets e SFX local; compassos/downbeats não inferidos por 'cada quarto'; fala com prioridade |
| 10 Overnight | Checkpoints, orçamento e subagentes existentes | Guia comum antes de paralelizar, piloto antes de polish; sem consentimento por timeout. Geração/traçado avançado fica opcional, não implementado |
| 11 Critique | QA e alguns frames | Evidência paginada cobrindo toda duração, strip, hashes de pixels repetidos/reversos/nova sessão; registro de revisão com gates/limites |
| 12 Ship | Padrões e entregas | Layout por formato e reuso; sem exportar tudo ou anunciar preço de agência por padrão |

## Correções técnicas próprias, não transcrição do curso
- Exemplo de mola: no código recebido, `z >= 1` usa a forma crítica. Isso não é a resposta exata no regime superamortecido. Nossa biblioteca implementa o regime separado e tem testes de equação diferencial.
- Seed: um RNG com seed avançando entre frames continua dependente da ordem de seek. Reinicializar por cena/tempo ou precomputar dados fixos.
- Determinismo: hash do MP4 mede também container/encoder. Comparar RGBA decodificado em tempos iguais, incluindo seeks fora de ordem e navegador novo. Esse teste é amostrado, não prova universal.
- Loop: módulo do relógio não garante continuidade de posição/velocidade/áudio. Uma sequência pode repetir e ainda saltar na emenda.
- Beat grid: `beat_track` estima batidas/tempo, não compasso e fase do primeiro tempo. Cada quarta batida só pode ser chamada de downbeat com hipótese musical confirmada.
- Contact sheet `tile=6x5` com uma saída mostra no máximo 30 imagens. Uma renderização longa precisa de paginação/cobertura ou amostragem distribuída declarada; nossa ferramenta não chama primeiros 15s de revisão completa.
- Motion blur 60fps×4 multiplica amostras de render; não é 'sem custo' por não usar LLM. Só após preview aprovado, com orçamento de frames.
- O curso sugere continuar sem resposta após dez minutos. Nesta fábrica isso NÃO autoriza orçamento, envio de arquivos, mudança de estilo, publicação ou render final aprovado.
- Notas 8+ e três revisões mínimas não são prova de qualidade. Usamos defeitos concretos, gates verificáveis e teto de 2/3/4 registros conforme perfil; não aceitamos falha bloqueante porque o orçamento acabou.

## Adaptação ao usuário
A edição de vídeos com fala continua sendo o centro. Novidade visual a cada 2–4 segundos é uma preferência de showreel do artigo, não obrigação para uma explicação, um gesto importante ou uma pausa intencional. O som não manda cortar palavras. Frame de referência orienta linguagem, não autoriza copiar UI/mascote/dados ou criar uma prova comercial inexistente.
