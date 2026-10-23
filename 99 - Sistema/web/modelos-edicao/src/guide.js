// Painel de instruções do Cortez. Mantido pelo Cortez: ao criar, mudar ou retirar uma função
// (workflow em 99 - Sistema/workflows), atualizar esta lista e guideUpdated na mesma mudança.
export const guideUpdated = '2026-10-23';

export const installerPdf = 'instalar.pdf';

export const tutorials = [
  { id: 'como-usar', title: 'Como usar o Cortez', description: 'Veja o Cortez em uso, da gravação até a edição. Dê o play para assistir com som.', source: 'vimeo', videoId: '1238030963', hash: '1c867e709c' }
];

export const groups = [
  { id: 'comecar', label: 'Começar', lead: 'Instale, confira e deixe o Cortez pronto para editar.' },
  { id: 'editar', label: 'Editar', lead: 'Do material bruto até a prévia revisada.' },
  { id: 'testar', label: 'Testar e publicar', lead: 'Versões com ganchos diferentes e opções de capa.' },
  { id: 'som', label: 'Voz e som', lead: 'Voz limpa, silêncios, erros de fala e trilha.' },
  { id: 'cenas', label: 'Imagens e animação', lead: 'B-roll, ilustrações, motion e efeitos.' },
  { id: 'formatos', label: 'Formatos e aparência', lead: 'Escolha, crie e ensine seus modelos.' },
  { id: 'cuidar', label: 'Manutenção', lead: 'Atualize, libere espaço, recupere pastas e sugira melhorias.' }
];

// Workflows técnicos que não são pedidos diretos do usuário. Toda outra receita em
// workflows/ precisa aparecer em alguma função abaixo (o teste confere).
export const internalWorkflows = ['CLIENT_MEMORY.md', 'INGEST.md', 'PERSONALIZATION_QA.md', 'PUBLISH_FORMAT_GALLERY.md', 'CACHE_FORMAT_REFERENCES.md'];

export const functions = [
  {
    id: 'efeitos', group: 'cenas', title: 'Escolher efeitos para o vídeo',
    what: 'Na seção Efeitos do painel, explore as prévias, veja as referências e escolha um efeito pelo código FX. O Cortez ajusta texto, tempo e aparência ao seu trabalho e mostra a aplicação para revisar.',
    say: 'Mostre o catálogo de efeitos e sugira os que ajudam nesta edição.',
    prompt: 'Mostre o catálogo de efeitos e sugira quais ajudam a explicar as ideias da [E03]. Para cada sugestão, diga o código FX, o trecho da fala e o motivo. Preserve o formato F e a identidade ID escolhidos para esse trabalho. Use os materiais reais autorizados; telas e dados das demonstrações são ilustrativos. Sincronize com a montagem final, preserve o rosto e as legendas e mostre uma prévia antes de considerar a aplicação aprovada. Se faltar F ou ID no trabalho, pergunte pela escolha que falta.',
    tips: ['FX identifica um efeito, F identifica a edição e ID escolhe cores e fontes.', 'As referências públicas indicam o que foi realmente observado.', 'Logotipo exige um pedido explícito para aquele trabalho.'],
    link: {href:'#efeitos', label:'Explorar os efeitos'},
    workflows: ['EFFECT_CATALOG.md']
  },
  {
    id: 'contribuir', group: 'cuidar', title: 'Sugerir um formato ou uma melhoria',
    what: 'Você descreve a ideia e o Cortez prepara a mudança numa cópia separada, como um PR, uma proposta de mudança. A versão de todos só muda depois da aprovação.',
    say: 'Cortez, prepare um PR com esta sugestão: [descreva sua ideia].',
    prompt: 'Cortez, quero propor [um formato novo / uma melhoria] para o projeto.\n\nMinha ideia: [descreva].\nExemplo público autorizado, se for um formato: [link].\n\nPrepare a alteração em uma cópia separada da versão atual e abra um PR em rascunho para revisão. Confira comigo quais materiais podem ser publicados; envie apenas código, documentação e referências autorizadas. Não envie meus vídeos de trabalho, memória, chaves ou configurações. Não altere a versão oficial nem aprove ou publique a proposta por conta própria. Ao terminar, entregue o link do PR e explique o que foi verificado e o que falta.',
    tips: ['Não precisa saber programar: basta descrever o que você quer.', 'Formato novo precisa de um exemplo que você tenha autorização para compartilhar.', 'Sem permissão no projeto, o Cortez usa uma cópia na sua conta do GitHub e pede a revisão.'],
    workflows: ['CONTRIBUTE_PULL_REQUEST.md']
  },
  {
    id: 'instalar', group: 'comecar', title: 'Instalar o Cortez',
    what: 'Você anexa o PDF ao Claude e ele instala o Cortez completo no seu computador (macOS, Windows ou Linux), com vídeo, fala, animações e Cortez Voz, e resolve os ajustes sozinho. Se faltar acesso ao seu computador, o PDF mostra como abrir o modo certo do Claude.',
    say: 'Instale o Cortez neste computador.',
    prompt: "Instale o Cortez completo neste computador a partir de https://github.com/Empire-Business/edicao-por-ia (main, ID 1408655066). Identifique se estou no macOS, Windows ou Linux e adapte você mesmo a instalação. Eu não sei executar comandos: faça a parte técnica até concluir, pergunte somente o destino da pasta e o que realmente depender de mim, como acesso local ou uma permissão do sistema. Se eu já informei o destino, use essa escolha.\n\nAutorizo instalar as dependências gratuitas necessárias no destino escolhido, incluindo Python compatível, ferramentas de vídeo, transcrição, animações, limpeza de áudio e Cortez Voz. Autorizo inicializar os dados locais do Cortez em 99 - Sistema/context/clients e criar/inicializar o banco do Cortez Voz em 99 - Sistema/.factory/cortez-voz-data, dentro dessa nova pasta no meu computador. Isso não autoriza bancos de teste, containers, reset de dados, serviços pagos nem alterações em outros projetos. Mostre um resumo e prossiga com o que já autorizei, sem pedir confirmação de cada pacote.\n\nNão preciso criar conta no GitHub para instalar. Recomende criar uma conta gratuita em https://github.com/signup para enviar sugestões e colaborar com o Cortez. Explique que é opcional e posso deixar para depois. Se eu quiser, oriente uma etapa por vez no site oficial; eu mesmo preencho e-mail, senha e verificações, nunca na conversa. Não bloqueie a instalação por esse cadastro. Faça o download público sem login; não instale GitHub CLI como requisito. Nunca peça senha, token ou chave na conversa. Preserve qualquer pasta existente. Obtenha a main do repositório exato, fixe o commit e confira o manifesto. Leia AGENTS.md, 99 - Sistema/AGENTS.md e 99 - Sistema/workflows/INSTALL_WITH_CLAUDE.md. Use o diagnóstico e o modo de preparação que preserva as configurações do agente, conforme esse roteiro. Preserve meus modelos, esforço, velocidade, autenticação, integrações e permissões. Cortez Voz deve vir exclusivamente da revisão e do hash controlados pela Empire-Business, nunca da branch de terceiros.\n\nResolva dependências e falhas conforme o sistema encontrado, usando fontes oficiais, sem me entregar comandos técnicos. Não desative proteções nem substitua versões fixadas para fazer uma instalação passar. Reaproveite etapas concluídas. Verifique cortes, transcrição, animações e voz no meu próprio computador; não exija que eu tenha outros sistemas para testar. Downloads de modelos de áudio exigem tamanho e licença conhecidos; não aceite termos por mim. ElevenLabs e Apify continuam opcionais e nunca são alternativas pagas automáticas.\n\nComece verificando se consegue executar ferramentas no meu computador, não apenas numa nuvem ou VM. Se já consegue, prossiga. Caso contrário, explique em linguagem simples como abrir o aplicativo oficial Claude, a aba Code e o ambiente Local, escolhendo uma pasta. A disponibilidade depende do plano e do aplicativo: confira a documentação oficial atual, não invente botões e não compre assinatura. Oriente a enviar este mesmo PDF nessa sessão. Não me peça comandos nem exija conta GitHub, e não finja que instalou num chat sem ferramentas locais. Ao terminar, abra 00 - COMECE AQUI.html e o painel https://cortez.highticketai.com.br, informe a pasta e o que foi realmente testado. Se um componente tiver incompatibilidade concreta, resolva o que for possível, registre o motivo e não declare esse componente funcionando. Não publique meus arquivos, faça push ou edite vídeos durante a instalação.",
    tips: ['Veja o passo a passo ilustrado na página Instalar: anexe o PDF ao Claude Code e envie, o pedido já vem dentro dele.', 'Licença individual e intransferível: não compartilhe a pasta, o PDF nem as chaves.', 'Conta no GitHub é opcional (uma grátis ajuda a colaborar depois) e você não precisa de outro sistema para testar.'],
    workflows: ['INSTALL_WITH_CLAUDE.md']
  },
  {
    id: 'preparar', group: 'comecar', title: 'Conferir se está tudo pronto',
    what: 'O Cortez confere a transcrição de fala, o FFmpeg (o programa que processa o vídeo) e o navegador das animações. Você recebe, em linguagem simples, o que funciona e o que falta para editar.',
    say: 'Confira se o Cortez está pronto para editar.',
    prompt: 'Confira se o Cortez está pronto para editar vídeos com fala e animações.\n\nFaça o diagnóstico, me diga em linguagem simples o que está funcionando e o que falta. Antes de instalar qualquer coisa, me mostre o que será instalado e peça minha autorização.',
    tips: ['Use depois de instalar ou quando algo parar de funcionar.'],
    workflows: ['ASSISTED_START.md', 'SETUP_LOCAL.md']
  },
  {
    id: 'chaves', group: 'comecar', title: 'Ligar as integrações',
    what: 'Você cola só as chaves dos serviços que quiser usar. Limpeza de voz e trilhas locais funcionam sem ElevenLabs; ElevenLabs e Apify são opcionais.',
    say: 'Quais chaves faltam no arquivo de integrações?',
    prompt: 'Quais integrações do Cortez estão sem chave? Não leia nem mostre os valores das chaves; diga apenas quais estão faltando e para que cada uma serve.',
    tips: ['Abra “CHAVES DAS INTEGRAÇÕES.txt” na pasta, cole cada chave depois do sinal = e salve.', 'ElevenLabs e Apify podem ficar vazios, e chave preenchida não autoriza cobrança.', 'O arquivo é privado e nunca é publicado.'],
    keys: ['ElevenLabs', 'ScrapeCreators', 'OpenRouter', 'Apify'],
    workflows: []
  },
  {
    id: 'editar', group: 'editar', title: 'Editar um vídeo', featured: true,
    what: 'Você escolhe um formato (F) e uma identidade visual (ID). O Cortez corta, limpa a fala, monta as cenas e entrega uma prévia em “02 - Ver vídeos”.',
    say: 'Edite este vídeo com F02 e ID03, vertical.',
    prompt: 'Quero editar o material que coloquei em “01 - Enviar vídeos”: [nome do arquivo].\n\nFormato de edição: [F02].\nIdentidade visual: [ID03].\nTamanho: [9:16 vertical].\n\nPreserve os originais, use as regras atuais do Cortez e me entregue uma prévia para revisar. Cores e fontes vêm da identidade escolhida. Sem logotipo, a não ser que eu peça.',
    tips: ['Faltou o F ou o ID? O Cortez pergunta antes de começar e nunca escolhe por você.', 'Cada vídeo ganha um código E01, E02… e cada revisão, V1, V2…'],
    link: { href: '#modelos', label: 'Escolher o formato nos modelos' },
    workflows: ['EDIT_VIDEO.md']
  },
  {
    id: 'ajustar', group: 'editar', title: 'Ajustar uma edição',
    what: 'Você aponta o que mudar e o Cortez refaz só as partes afetadas, sem refazer o vídeo inteiro. Você recebe a próxima versão: V2, V3…',
    say: 'Na E01, aos 12 segundos, tire o texto.',
    prompt: 'Na [E01], faça estes ajustes:\n- aos [0:12], [tire o texto];\n- aos [0:40], [troque a imagem por uma do produto];\n- [a legenda está muito pequena no começo].\n\nMantenha o que já foi aprovado e me entregue a próxima versão.',
    tips: ['Diga o código E e o segundo exato.', 'Ajuste de corte e ritmo fica na memória do formato; cor e fonte vão para a identidade visual.'],
    workflows: ['EDIT_PARTIAL.md', 'REVIEW.md']
  },
  {
    id: 'continuar', group: 'editar', title: 'Continuar de onde parou',
    what: 'O Cortez retoma o trabalho do ponto salvo. Não cria pastas repetidas nem zera o que já foi gasto.',
    say: 'Continue a E04.',
    prompt: 'Continue o trabalho [E04] de onde parou. Me diga em que etapa ele está e o que falta até a prévia.',
    tips: ['Não lembra o código? Pergunte “Quais trabalhos estão em andamento?”.'],
    workflows: ['RESUME_JOB.md']
  },
  {
    id: 'roteiro', group: 'editar', title: 'Editar seguindo um roteiro',
    what: 'Você manda o roteiro e o Cortez escolhe a melhor tomada de cada ideia, descartando as repetidas. Frases ditas de outro jeito, com o mesmo sentido, continuam no vídeo.',
    say: 'Use este roteiro para escolher as melhores tomadas.',
    prompt: 'Edite [o vídeo] com [F] e [ID] usando este roteiro como referência para escolher as melhores tomadas:\n\n[cole o roteiro aqui]\n\nO roteiro é flexível: mantenha frases ditas de outro jeito com o mesmo sentido. Não invente falas que não foram gravadas e me diga se faltou alguma ideia.',
    tips: ['O roteiro também pode ir como arquivo em “01 - Enviar vídeos”.'],
    workflows: ['MATCH_REFERENCE_SCRIPT.md']
  },
  {
    id: 'dividir', group: 'editar', title: 'Separar uma gravação em vários vídeos',
    what: 'O Cortez acha onde cada vídeo começa e termina numa gravação longa. Cada um vira um trabalho separado.',
    say: 'Nesta gravação tem 4 vídeos. Separe e edite cada um.',
    prompt: 'A gravação [nome do arquivo] tem [4] vídeos diferentes. Encontre onde cada um começa e termina, me mostre a divisão proposta e edite cada vídeo separadamente com [F] e [ID].',
    tips: ['Se a divisão não estiver clara, o Cortez mostra os tempos e pergunta antes.'],
    workflows: ['SPLIT_MULTI_VIDEO.md']
  },
  {
    id: 'lote', group: 'editar', title: 'Editar vários vídeos de uma vez',
    what: 'O Cortez edita vários vídeos com um só orçamento. Cada vídeo segue como um trabalho próprio, com revisão própria.',
    say: 'Edite todos os vídeos da pasta com F14 e ID05.',
    prompt: 'Edite todos os vídeos que estão em “01 - Enviar vídeos/[pasta]” com [F14] e [ID05], vertical.\n\nCada vídeo é um trabalho separado. Me mostre a lista antes de começar e avise se algum precisar de uma escolha diferente.',
    tips: ['Bom para séries de cortes no mesmo formato.'],
    workflows: ['BATCH_FACTORY.md']
  },
  {
    id: 'longo', group: 'editar', title: 'Editar vídeo longo e tirar cortes',
    what: 'Vídeos com mais de 5 minutos têm um processo próprio: voz limpa do início ao fim e revisão de toda a fala, das legendas e da tela. Depois saem os cortes curtos.',
    say: 'Edite este vídeo longo com F18 e tire 4 cortes.',
    prompt: 'Edite o vídeo longo [nome do arquivo] com [F18] e [ID], horizontal 16:9.\n\nDepois, tire [4] cortes verticais com os melhores trechos. Cada corte é um vídeo separado.',
    tips: ['Se você disser na gravação algo como “tira isso”, o Cortez obedece e corta a instrução.'],
    workflows: ['LONG_FORM.md']
  },
  {
    id: 'revisar', group: 'editar', title: 'Revisar antes de entregar',
    what: 'O Cortez confere áudio, legendas, cortes, cenas e se as suas preferências foram seguidas. Você recebe a lista do que está bom e do que precisa de ajuste.',
    say: 'Revise a E03 antes de eu postar.',
    prompt: 'Revise a [E03] antes de eu postar: confira áudio, cortes no meio de palavras, legendas, cenas vazias e se minhas preferências do formato foram seguidas. Liste o que está bom e o que precisa de ajuste.',
    tips: ['O Cortez só diz “aprovado” depois de ver os quadros e ouvir os cortes.'],
    workflows: ['QA.md']
  },
  {
    id: 'variacoes', group: 'testar', title: 'Variações de reel para testar', isNew: true, featured: true,
    what: 'Você recebe o mesmo vídeo em quantas versões quiser, cada uma com outro gancho, para testar qual prende mais. O resto também muda (legenda, transições, B-roll, trilha), para as redes não tratarem as versões como o mesmo arquivo.',
    say: 'Me entregue 5 variações deste vídeo com 5 ganchos diferentes.',
    prompt: 'Edite [o vídeo] com [F02] e [ID05] e, no final, me entregue [5] variações para teste, com [5] ganchos visuais diferentes. Quero descobrir qual segura mais nos primeiros segundos.\n\nMantenha a mesma voz, os mesmos fatos e o mesmo CTA. Para o Instagram não reconhecer como o mesmo vídeo, mude também a legenda, as transições, o B-roll e a trilha no resto de cada variação. Me mostre o plano das variações antes de montar.',
    tips: ['Escolha ou misture: gancho re-editado ou post com foto no estilo F19 Print Repost (rápido, sem serviço pago, pede o nome e o @ da conta).', 'Serve também para vídeo que não foi bem: “O E07 flopou, faz 5 variações.”', 'Depois do teste, diga qual versão foi melhor: o resultado fica registrado no formato.'],
    workflows: ['REEL_VARIATIONS.md']
  },
  {
    id: 'capas', group: 'testar', title: 'Capas e thumbnails',
    what: 'O Cortez cria opções de capa a partir de quadros reais do vídeo e das suas referências. Cada opção é uma geração paga.',
    say: 'Crie 3 opções de capa para a E05.',
    prompt: 'Crie [3] opções de capa para a [E05], formato [16:9].\n\nUse quadros reais do vídeo e estas referências: [anexe ou indique os arquivos]. Texto da capa: [frase curta]. Me diga o custo de cada opção antes de gerar.',
    tips: ['Usa um serviço pago com a sua própria chave; o custo vem antes de gerar.'],
    keys: ['OpenRouter'], paid: true,
    workflows: []
  },
  {
    id: 'voz', group: 'som', title: 'Limpar a voz',
    what: 'O Cortez reduz o ruído da voz no seu computador, antes dos cortes, com DeepFilterNet ou uma limpeza básica. A voz é conferida antes de você ver a prévia.',
    say: 'Limpe a voz deste vídeo antes da prévia.',
    prompt: 'Limpe a voz do vídeo [nome] antes de montar a prévia: isole a voz do arquivo inteiro e só depois aplique os cortes. Me diga quanto ruído saiu nas pausas.',
    tips: ['Funciona sem chave ElevenLabs e sem enviar áudio para a internet.', 'O Cortez diz qual limpeza usou; a básica não promete tirar eco.', 'ElevenLabs só entra se você escolher e autorizar o gasto.'],
    paid: false,
    workflows: []
  },
  {
    id: 'narracao', group: 'som', title: 'Gerar narração local',
    what: 'O Cortez transforma seu roteiro em voz com o Cortez Voz, que vem na instalação a partir da cópia controlada pela Empire. No Mac, você também pode usar as vozes do sistema.',
    say: 'Gere uma narração local para este roteiro.',
    prompt: 'Gere uma narração local para [roteiro]. Mostre as vozes e os modelos locais disponíveis para eu escolher. Confira pronúncia e obtenha os tempos das palavras antes de sincronizar legendas. Se faltar algum componente, me diga o que precisa ser preparado. Não use serviço pago automaticamente.',
    tips: ['A instalação não baixa os modelos de voz nem liga a base local: o primeiro início é à parte, com sua autorização, e depois o Cortez Voz precisa estar aberto.', 'Clonar a voz de alguém exige autorização.', 'Ouça e aprove a voz antes de usar.'],
    paid: false, workflows: []
  },
  {
    id: 'silencio', group: 'som', title: 'Cortar silêncios',
    what: 'O Cortez encurta as pausas mortas, cortando som e imagem juntos. Pausas de efeito e respiros ficam.',
    say: 'Deixe o ritmo mais rápido, sem cortar palavras.',
    prompt: 'Na [E02], deixe o ritmo mais rápido cortando as pausas sem motivo. Não corte começo ou fim de palavras e mantenha as pausas de efeito.',
    tips: ['Já acontece em toda edição; peça “não corte os silêncios” para desligar.'],
    workflows: ['REMOVE_SILENCE.md']
  },
  {
    id: 'erros', group: 'som', title: 'Tirar erros de fala e tomadas repetidas',
    what: 'O Cortez tira gaguejos, frases abandonadas e tomadas repetidas quando tem certeza. Nos casos duvidosos, você decide.',
    say: 'Tire as tomadas erradas e as repetições.',
    prompt: 'No vídeo [nome], tire os erros de fala, frases abandonadas e tomadas repetidas, ficando com a melhor versão de cada ideia. Se houver dúvida sobre qual tomada usar, me pergunte mostrando os trechos.',
    tips: [],
    workflows: ['CLEAN_SPEECH.md']
  },
  {
    id: 'musica', group: 'som', title: 'Trilha e biblioteca de músicas',
    what: 'O Cortez usa faixas da sua biblioteca com licença ou autorização registrada, ajusta a duração e abaixa a música quando você fala. Gerar música com serviço pago é opcional.',
    say: 'Coloque uma trilha tensa que vira no final.',
    prompt: 'Use na [E04] uma trilha licenciada da minha biblioteca, [tensa / animada / calma], com mudança na virada aos [0:45]. Mantenha a música abaixo da voz. Se não houver uma faixa adequada, me avise antes de usar qualquer serviço pago.',
    tips: ['Envie só faixas que você tem direito de usar e diga a origem ou a licença.', 'A biblioteca é privada e não vai junto com o código do Cortez.', 'ElevenLabs Music é opcional e pede sua autorização a cada geração.'],
    paid: false,
    workflows: []
  },
  {
    id: 'meus-arquivos', group: 'cenas', title: 'Usar suas imagens e vídeos de apoio',
    what: 'Fotos, prints e B-roll que você enviar entram onde combinam com a fala. Nada entra só porque está na pasta.',
    say: 'Use as imagens da pasta apoio onde fizer sentido.',
    prompt: 'Na edição de [vídeo], use as imagens e vídeos de apoio que coloquei em “01 - Enviar vídeos/[pasta]” nos momentos em que combinam com a fala. Me diga onde cada um entrou e quais não foram usados.',
    tips: ['Envie só material que você tem direito de usar.'],
    workflows: ['USE_INSERTION_ASSETS.md']
  },
  {
    id: 'buscar-cenas', group: 'cenas', title: 'Buscar cenas do TikTok e YouTube',
    what: 'O Cortez pesquisa e baixa cenas de apoio sobre o que você fala. Cada cena vem com o link de origem registrado.',
    say: 'Busque cenas do YouTube sobre o que eu falo.',
    prompt: 'Para a [E06], busque no [TikTok / YouTube] cenas de apoio sobre [assunto] e use nos momentos em que eu falo disso. Registre o link de origem de cada cena.',
    tips: ['Usa a chave ScrapeCreators; quando o YouTube não libera o arquivo, usa a chave Apify.'],
    keys: ['ScrapeCreators', 'Apify'], paid: true,
    workflows: []
  },
  {
    id: 'direcao', group: 'cenas', title: 'Planejar as cenas a partir da fala',
    what: 'Para cada ideia do vídeo, o Cortez decide o que aparece: você, um texto, uma ilustração ou uma cena, respeitando o cenário real. Você recebe o storyboard (o plano das cenas) antes da produção.',
    say: 'Monte o storyboard da E02 antes de animar.',
    prompt: 'Leia a fala da [E02] e monte a direção visual: para cada ideia, diga se fica a pessoa, um texto, uma ilustração ou uma cena. Me mostre o storyboard antes de produzir.',
    tips: [],
    workflows: ['DIRECT_VISUALS.md']
  },
  {
    id: 'animacoes', group: 'cenas', title: 'Animações sobre a fala',
    what: 'Gráficos, números, listas e diagramas animados no momento exato da fala. Eles entram depois que os cortes estão fechados.',
    say: 'Anime os números que eu cito na E03.',
    prompt: 'Na [E03], crie animações para [os números / a lista / o passo a passo] que eu explico, sincronizadas com a fala e nas cores da identidade escolhida.',
    tips: [],
    workflows: ['CREATE_JS_ANIMATIONS.md']
  },
  {
    id: 'motion-ref', group: 'cenas', title: 'Criar motion a partir de uma referência',
    what: 'Para um estilo de animação novo, o Cortez parte da referência e mostra os estados principais, os quadros e um animatic (rascunho animado). Você revisa tudo antes do acabamento.',
    say: 'Quero um motion no estilo deste vídeo de referência.',
    prompt: 'Quero um motion no estilo desta referência: [link ou arquivo]. Assunto: [tema]. Duração: [30 s]. Me mostre os estados principais e um animatic antes de finalizar.',
    tips: [],
    workflows: ['MOTION_STUDIO.md']
  },
  {
    id: 'motion-produto', group: 'cenas', title: 'Criar motion de produto ou plataforma',
    what: 'O Cortez recria e anima as telas do seu sistema num vídeo institucional, sem você gravar nada. Você recebe em 16:9 e 9:16.',
    say: 'Faça um motion mostrando as funções da minha plataforma.',
    prompt: 'Faça um motion institucional da plataforma [nome] mostrando [as funções principais]. O código/telas estão em [repositório ou prints]. Público: [quem vai assistir]. Quero nas duas proporções, 16:9 e 9:16.',
    tips: ['Combina com o formato F07 Motion Institucional.'],
    workflows: ['PRODUCT_MOTION.md']
  },
  {
    id: 'roupa', group: 'cenas', title: 'Trocar roupa ou cenário',
    what: 'Num trecho curto, o Cortez troca a roupa de quem aparece, o fundo ou os dois, mantendo o áudio original. Você vê o antes e depois para aprovar.',
    say: 'Nos primeiros 5 segundos, me coloque de blazer.',
    prompt: 'No vídeo [nome], entre [0:00] e [0:05], troque [minha roupa por um blazer preto / o cenário por um escritório]. Me diga o custo e como o trecho será enviado antes de gerar, e me mostre o antes e depois.',
    tips: ['Geração paga: cada trecho precisa do seu “sim” na hora.', 'Só vale para a pessoa que pediu a troca.'],
    keys: ['OpenRouter'], paid: true,
    workflows: ['SWAP_OUTFIT_SCENERY.md']
  },
  {
    id: 'escolher-formato', group: 'formatos', title: 'Escolher um formato', featured: true,
    what: 'O formato define cortes, ritmo, composição e animações. Assista aos exemplos e copie o pedido pronto.',
    say: 'Qual formato combina com um vídeo sem eu aparecer?',
    prompt: 'Quero fazer um vídeo sobre [assunto], [aparecendo / sem aparecer], com [gravação / só narração / prints]. Quais formatos do Cortez combinam e por quê?',
    tips: [],
    link: { href: '#modelos', label: 'Abrir os modelos' },
    workflows: []
  },
  {
    id: 'escolher-id', group: 'formatos', title: 'Escolher cores e fontes (ID visual)',
    what: 'A identidade visual define as cores e as fontes. Qualquer ID combina com qualquer formato.',
    say: 'Use a ID05 neste vídeo.',
    prompt: 'Na [E02], troque a identidade visual para [ID05]. Mantenha cortes e animações; mude só cores e fontes.',
    tips: [],
    link: { href: '#identidades', label: 'Ver as identidades' },
    workflows: []
  },
  {
    id: 'novo-formato', group: 'formatos', title: 'Criar um formato novo',
    what: 'Você manda um nome simples e um link de exemplo. O Cortez cria o próximo código FP, analisa o vídeo real e escreve a receita da edição.',
    say: 'Crie um formato novo a partir deste exemplo.',
    prompt: 'Crie um formato novo chamado “[nome simples]” a partir deste exemplo: [link do Instagram, Drive, X ou site].\n\nAnalise o vídeo real, me explique o mecanismo da edição e só depois salve a receita. Não fixe cores ou fontes no formato.',
    tips: ['O nome descreve a edição (ex.: “Lista em Tela”), não uma pessoa ou marca.', 'Sem link de exemplo, o formato não é criado.'],
    workflows: ['DEFINE_PATTERN.md', 'ANALYZE_REFERENCE.md']
  },
  {
    id: 'opcoes-estilo', group: 'formatos', title: 'Ver opções de estilo',
    what: 'Antes de fixar um formato, o Cortez propõe de duas a quatro direções de edição bem diferentes: ritmo, legenda, zoom e animação. Você escolhe a que serve.',
    say: 'Me mostre 3 direções de edição diferentes para este vídeo.',
    prompt: 'Antes de editar [o vídeo], me proponha [3] direções de edição realmente diferentes: ritmo, legendas, zooms, animações e som. Explique para que cada uma serve.',
    tips: [],
    workflows: ['GENERATE_STYLE_OPTIONS.md']
  },
  {
    id: 'nova-id', group: 'formatos', title: 'Criar sua própria identidade',
    what: 'O Cortez cria uma IDP com as suas cores e fontes. Ou copia uma ID oficial para você personalizar sem mexer no original.',
    say: 'Crie uma identidade com as cores da minha marca.',
    prompt: 'Crie uma identidade visual minha chamada “[nome]” com estas cores: [#hex fundo, #hex destaque, #hex texto] e estas fontes: [títulos / texto]. Os arquivos das fontes estão em [pasta].',
    tips: ['Ou: “Copie a ID03 para uma IDP e troque o azul por verde”.'],
    workflows: []
  },
  {
    id: 'memoria', group: 'formatos', title: 'Ensinar suas preferências',
    what: 'Tudo que você diz sobre um formato fica na memória dele, e a próxima edição já sai do seu jeito. Não precisa dizer “salve isso”.',
    say: 'No F02, sempre comece direto na fala, sem vinheta.',
    prompt: 'A partir de agora, no [F02]: [sempre comece direto na fala / legendas com no máximo 4 palavras / sem zoom no rosto]. Isso vale para os próximos vídeos deste formato.',
    tips: ['Diga se vale “só neste vídeo” ou “sempre neste formato”.', 'Você também pode registrar resultados: “A VAR3 teve 2x mais views em 7 dias”.'],
    workflows: ['FORMAT_MEMORY.md', 'LEARN_FROM_RESULT.md']
  },
  {
    id: 'atualizar', group: 'cuidar', title: 'Atualizar o Cortez',
    what: 'O Cortez atualiza só o código, faz backup e mantém trabalhos, memória, IDs, chaves, configurações e referências já baixadas. Referências novas chegam quando você usar o formato e, se você mudou algum código, ele junta as mudanças e avisa se algo conflitar.',
    say: 'Atualize o Cortez.',
    prompt: 'Atualize o Cortez para a versão mais recente, preservando meus trabalhos, memórias, identidades, chaves e configurações. Me diga o que mudou.',
    tips: ['Não precisa baixar a pasta de novo nem fazer nada à mão.'],
    workflows: ['UPDATE_FACTORY.md']
  },
  {
    id: 'espaco', group: 'cuidar', title: 'Liberar espaço',
    what: 'O Cortez apaga só os arquivos técnicos da montagem de trabalhos já entregues. Gravações, prévias, versões finais e memória ficam.',
    say: 'Quanto espaço eu libero nos trabalhos entregues?',
    prompt: 'Mostre quanto espaço posso liberar nos trabalhos já entregues, sem apagar gravações, prévias, finais ou memória. Só remova depois que eu confirmar os trabalhos.',
    tips: ['Você vê antes o que vai sair; nada é apagado sem sua confirmação.'],
    workflows: ['CLEANUP_STORAGE.md']
  },
  {
    id: 'recuperar', group: 'cuidar', title: 'Recuperar uma pasta antiga ou misturada',
    what: 'Para instalações antigas ou misturadas, o Cortez monta uma pasta nova e organizada. A pasta original e todos os trabalhos ficam intactos.',
    say: 'Minha pasta é de uma versão antiga. Recupere sem perder nada.',
    prompt: 'Minha pasta do Cortez é de uma versão antiga (ou ficou misturada). Monte uma pasta nova organizada a partir dela, sem apagar ou alterar a original, e me mostre o recibo do que foi levado.',
    tips: ['Veja também “03 - Ajuda/ATUALIZAR SEM PERDER TRABALHOS”.'],
    workflows: []
  }
];

export const folders = [
  { name: '00 - COMECE AQUI', text: 'Página de entrada da sua pasta.' },
  { name: '01 - Enviar vídeos', text: 'Gravações, roteiros, imagens e apoios.' },
  { name: '02 - Ver vídeos', text: 'Prévias e versões finais, por data e trabalho.' },
  { name: '03 - Ajuda', text: 'Ajuda e guia de atualização.' },
  { name: '04 - Formatos', text: 'Cada F com “Como usar” e “Guia da edição”.' },
  { name: '05 - IDs Visuais', text: 'Paletas e fontes de cada ID.' },
  { name: 'CHAVES DAS INTEGRAÇÕES', text: 'Arquivo privado com as chaves dos serviços.' }
];

export const codes = [
  { code: 'F01 · FP01', text: 'Formato de edição: cortes, ritmo, cenas e animações. F é oficial; FP é seu.' },
  { code: 'ID01 · IDP01', text: 'Identidade visual: cores e fontes. ID é oficial; IDP é sua.' },
  { code: 'E01 · EP01', text: 'Uma edição específica, o seu trabalho.' },
  { code: 'V1 · VP1', text: 'Versões de uma edição. Cada ajuste gera a próxima.' },
  { code: 'VAR01, VAR02…', text: 'Variações de teste do mesmo vídeo, com ganchos diferentes.' }
];

// Biblioteca carregada pela edição/atualização; operação interna sem comando para leigos.
