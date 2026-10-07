# bruno-wpp — Conversa que vira cena

Direção inicial de 01/10/2026. Padrão `bruno-wpp-chat-v1`, versão 1, **draft**.
Preferências do usuário estão na memória canônica. Os detalhes visuais abaixo são proposta
editorial para o primeiro vídeo; não representam aprovação de uma execução ou resultado medido.

## A assinatura

Bruno manda um áudio. O balão começa a tocar, revela uma frase e se transforma naquilo que
ele está explicando: vídeo, comparação, lista, gráfico ou palavra de impacto. A conclusão
recolhe a cena ao chat. A conversa avança, em vez de servir apenas de moldura para legendas.
Repetir a gramática de transformação, variando seu conteúdo conforme a fala.

O chat ocupa a tela vertical diretamente, sem um celular pequeno dentro do vídeo. Aparência
familiar do WhatsApp com acabamento próprio: fundo escuro, verde pontual, letras grandes,
hierarquia limpa e animações com peso. Sem rosto, avatar com foto ou voz sintética necessários.
“Dark” significa produção sem aparecer; o tema escuro é uma escolha inicial ajustável.

## Como uma história funciona

1. **Entrada:** o gancho falado começa imediatamente. Um balão curto dá contexto; o estado
   “gravando áudio” pode aparecer por um instante sem atrasar a fala. Não simular 40 segundos
   de gravação antes de reproduzir uma mensagem de 40 segundos.
2. **Áudio:** waveform extraída da voz real, duração correta e cursor acompanhando a
   reprodução. Trechos da transcrição aparecem em blocos legíveis no balão ativo.
3. **Desenvolvimento:** separar ideias em mensagens. Usar resposta citada para retomar um
   argumento; usar uma lista ou comparação quando ela explicar mais que um vídeo genérico.
4. **Vídeo recebido/enviado:** B-roll aparece dentro de uma mensagem de vídeo. O play inicia
   o trecho pertinente; o cartão pode expandir e voltar ao chat. A voz continua guiando.
5. **Virada:** o balão-chave vira uma cena explicativa maior. Um único foco de atenção;
   movimento rápido de entrada, pausa para compreender e saída curta.
6. **Fechamento:** uma mensagem sintetiza o que foi efetivamente dito. CTA somente se
   existir no áudio ou for fornecido pelo usuário. Final limpo, sem uma fila de notificações.

Os tempos seguem a gravação editada, não uma estrutura rígida de duração. Uma conversa
encenada não deve inventar depoimentos, respostas reais ou fala atribuída a outra pessoa.
Mensagens editoriais resumidas devem ser distinguíveis de legendas literais. Identificar
a encenação de forma discreta e legível como “Conversa ilustrativa”.

## Biblioteca a construir e reaproveitar

- `VoiceNote`: waveform real, play, duração e cursor sincronizados.
- `ChatMessage`: texto, entrada, envio e confirmação com pausa de leitura.
- `ReplyQuote`: citação de uma ideia efetivamente presente no áudio.
- `VideoMessage`: thumbnail pertinente, player, crédito e expansão controlada.
- `BubbleToScene`: balão que vira comparação, passos ou gráfico e retorna ao chat.
- `PinnedTakeaway`: frase final ou ideia central fixada por alguns segundos.

Esta é uma especificação de componentes, não uma alegação de que já foram implementados.
Construir com JavaScript determinístico e `seek(t)` após fechar cortes e silêncios. Usar
workflow de motion e referência → estados → stills → animatic → QA na primeira produção.
Reaproveitar componentes validados com novos textos e tempos nos vídeos seguintes.

## Áudio e pesquisa

Analisar o original e conservar a fonte. A preferência é isolamento ElevenLabs do áudio
completo antes dos cortes; depois limpeza de erros de alta confiança, silêncio com proteção
de palavras e pausas intencionais, retiming, normalização e mixagem. Comparar voz tratada e
original para rejeitar metalização, sílabas perdidas ou mudança de timbre.

O usuário solicitou ElevenLabs e pesquisa TikTok para esse cliente. Não houve chamada,
upload, leitura de chave ou cobrança nesta configuração. Cada produção deve conferir
custo/condições e registrar o uso; saldo desconhecido não autoriza tentativas ilimitadas.
Não adicionar geração de música, voz, imagem ou vídeo paga por inferência.

Pesquisar a partir das ideias retidas: ação, objeto e contexto concreto. Escolher trechos
pela relação com a fala e composição utilizável, não só por visualizações. Guardar URL,
autor, trecho, finalidade e situação de uso em `assets/viral/sources.json`. Disponibilidade
no TikTok não equivale a licença; com direitos pendentes, usar diagrama ou mídia autorizada.
Não acessar memória pessoal de outros clientes: reaproveitar os mecanismos documentados
da fábrica, mantendo este cliente independente.

Música é opção editorial ainda não definida pelo usuário. Se adotada, precisa seguir os
momentos da fala e ficar abaixo das palavras mais suaves. Sons de envio/play são pontuais;
o áudio original do B-roll fica mudo por padrão.

## Primeiro vídeo e critérios de validação

Entrada necessária: um áudio de Bruno. Criar job separado com cliente `bruno-wpp`; o
padrão já será selecionado pela preferência `defaults.pattern`. Não criar job vazio ou
marcar a linguagem como aprovada antes de existir uma produção representativa.

Verificar voz natural, cortes completos, sincronização do player/legendas, leitura em
tela pequena, transformações com propósito, mídia pertinente, ausência de falsas provas
e final coerente. Renderizar draft e cumprir QA/personalização antes do final. Medidas de
retenção só entram como resultados quando houver dados reais; nenhuma promessa de viralizar.
