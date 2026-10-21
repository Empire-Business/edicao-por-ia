// Painel de instruções da fábrica. Mantido pela IA: ao criar, mudar ou retirar uma função
// (workflow em 99 - Sistema/workflows), atualizar esta lista e guideUpdated na mesma mudança.
export const guideUpdated = '2026-10-21';

export const groups = [
  { id: 'comecar', label: 'Começar', lead: 'Instalar, conferir e deixar a fábrica pronta.' },
  { id: 'editar', label: 'Editar', lead: 'Do material bruto até a prévia revisada.' },
  { id: 'testar', label: 'Testar e publicar', lead: 'Versões para testar ganchos, capas e entregas.' },
  { id: 'som', label: 'Voz e som', lead: 'Voz limpa, silêncios, erros de fala e trilha.' },
  { id: 'cenas', label: 'Imagens e animação', lead: 'B-roll, ilustrações, motion e efeitos.' },
  { id: 'formatos', label: 'Formatos e aparência', lead: 'Escolher, criar e ensinar seus modelos.' },
  { id: 'cuidar', label: 'Manutenção', lead: 'Atualizar, liberar espaço e recuperar.' }
];

// Workflows técnicos que não são pedidos diretos do usuário. Toda outra receita em
// workflows/ precisa aparecer em alguma função abaixo (o teste confere).
export const internalWorkflows = ['CLIENT_MEMORY.md', 'INGEST.md', 'PERSONALIZATION_QA.md', 'PUBLISH_FORMAT_GALLERY.md', 'CACHE_FORMAT_REFERENCES.md'];

export const functions = [
  {
    id: 'instalar', group: 'comecar', title: 'Instalar a fábrica',
    what: 'A IA cria a pasta no seu computador, confere sua conta do GitHub e prepara o que falta, sempre mostrando antes o que vai instalar.',
    say: 'Instale a fábrica de vídeos neste computador.',
    prompt: 'Instale a fábrica de vídeos neste computador seguindo o guia de instalação que anexei.\n\nPergunte primeiro onde devo criar a pasta. Confira minha conta do GitHub, não sobrescreva nenhuma pasta existente e me mostre o que vai instalar antes de instalar. No fim, diga o que foi testado de verdade e o que ficou pendente.',
    tips: ['Anexe o PDF de instalação na conversa com o Claude.', 'Nada é instalado sem a sua autorização.'],
    workflows: ['INSTALL_WITH_CLAUDE.md']
  },
  {
    id: 'preparar', group: 'comecar', title: 'Conferir se está tudo pronto',
    what: 'Diagnóstico da pasta: transcrição de fala, FFmpeg, navegador para animações e o que ainda falta para editar.',
    say: 'Confira se a fábrica está pronta para editar.',
    prompt: 'Confira se esta fábrica está pronta para editar vídeos com fala e animações.\n\nFaça o diagnóstico, me diga em linguagem simples o que está funcionando e o que falta. Antes de instalar qualquer coisa, me mostre o que será instalado e peça minha autorização.',
    tips: ['Use depois de instalar ou quando algo parar de funcionar.'],
    workflows: ['ASSISTED_START.md', 'SETUP_LOCAL.md']
  },
  {
    id: 'chaves', group: 'comecar', title: 'Ligar as integrações',
    what: 'Voz limpa, música, busca de cenas e capas usam serviços externos. Cada um precisa da sua chave no arquivo de chaves.',
    say: 'Quais chaves faltam no arquivo de integrações?',
    prompt: 'Quais integrações da fábrica estão sem chave? Não leia nem mostre os valores das chaves; diga apenas quais estão faltando e para que cada uma serve.',
    tips: ['Abra “CHAVES DAS INTEGRAÇÕES.txt” na pasta, cole cada chave depois do sinal = e salve.', 'O arquivo é privado e nunca é publicado.'],
    keys: ['ElevenLabs', 'ScrapeCreators', 'OpenRouter', 'Apify'],
    workflows: []
  },
  {
    id: 'editar', group: 'editar', title: 'Editar um vídeo', featured: true,
    what: 'Você escolhe um formato (F) e uma identidade visual (ID). A IA corta, limpa a fala, monta cenas e entrega uma prévia em “02 - Ver vídeos”.',
    say: 'Edite este vídeo com F02 e ID03, vertical.',
    prompt: 'Quero editar o material que coloquei em “01 - Enviar vídeos”: [nome do arquivo].\n\nFormato de edição: [F02].\nIdentidade visual: [ID03].\nTamanho: [9:16 vertical].\n\nPreserve os originais, use as regras atuais da fábrica e me entregue uma prévia para revisar. Cores e fontes vêm da identidade escolhida. Sem logotipo, a não ser que eu peça.',
    tips: ['Sem F ou sem ID a IA pergunta antes de começar: nenhuma dupla é escolhida sozinha.', 'Cada vídeo recebe um código E01, E02… e cada revisão V1, V2…'],
    link: { href: '#modelos', label: 'Escolher o formato nos modelos' },
    workflows: ['EDIT_VIDEO.md']
  },
  {
    id: 'ajustar', group: 'editar', title: 'Ajustar uma edição',
    what: 'Correções pontuais sem refazer o vídeo inteiro. Só as etapas afetadas são refeitas e uma nova versão V2, V3… aparece.',
    say: 'Na E01, aos 12 segundos, tire o texto.',
    prompt: 'Na [E01], faça estes ajustes:\n- aos [0:12], [tire o texto];\n- aos [0:40], [troque a imagem por uma do produto];\n- [a legenda está muito pequena no começo].\n\nMantenha o que já foi aprovado e me entregue a próxima versão.',
    tips: ['Diga o código E e o momento em segundos.', 'Ajuste de corte e ritmo vira memória do formato; cor e fonte vão para a identidade visual.'],
    workflows: ['EDIT_PARTIAL.md', 'REVIEW.md']
  },
  {
    id: 'continuar', group: 'editar', title: 'Continuar de onde parou',
    what: 'Retoma um trabalho pelo andamento salvo, sem criar pastas duplicadas e sem zerar o que já foi gasto.',
    say: 'Continue a E04.',
    prompt: 'Continue o trabalho [E04] de onde parou. Me diga em que etapa ele está e o que falta até a prévia.',
    tips: ['Não lembra o código? Peça “Quais trabalhos estão em andamento?”.'],
    workflows: ['RESUME_JOB.md']
  },
  {
    id: 'roteiro', group: 'editar', title: 'Editar seguindo um roteiro',
    what: 'Com o roteiro, a IA reconhece as ideias, escolhe as melhores tomadas e descarta as repetidas. Paráfrases equivalentes são mantidas.',
    say: 'Use este roteiro para escolher as melhores tomadas.',
    prompt: 'Edite [o vídeo] com [F] e [ID] usando este roteiro como referência para escolher as melhores tomadas:\n\n[cole o roteiro aqui]\n\nO roteiro é flexível: mantenha frases ditas de outro jeito com o mesmo sentido. Não invente falas que não foram gravadas e me diga se faltou alguma ideia.',
    tips: ['O roteiro também pode ir como arquivo em “01 - Enviar vídeos”.'],
    workflows: ['MATCH_REFERENCE_SCRIPT.md']
  },
  {
    id: 'dividir', group: 'editar', title: 'Uma gravação com vários vídeos',
    what: 'A IA encontra onde cada vídeo começa e termina numa gravação longa e cria um trabalho separado para cada um.',
    say: 'Nesta gravação tem 4 vídeos. Separe e edite cada um.',
    prompt: 'A gravação [nome do arquivo] tem [4] vídeos diferentes. Encontre onde cada um começa e termina, me mostre a divisão proposta e edite cada vídeo separadamente com [F] e [ID].',
    tips: ['Se a divisão não estiver clara, a IA mostra os tempos e pergunta antes.'],
    workflows: ['SPLIT_MULTI_VIDEO.md']
  },
  {
    id: 'lote', group: 'editar', title: 'Editar vários vídeos de uma vez',
    what: 'Lote com um orçamento compartilhado. Cada vídeo continua sendo um trabalho independente, com sua própria revisão.',
    say: 'Edite todos os vídeos da pasta com F14 e ID05.',
    prompt: 'Edite todos os vídeos que estão em “01 - Enviar vídeos/[pasta]” com [F14] e [ID05], vertical.\n\nCada vídeo é um trabalho separado. Me mostre a lista antes de começar e avise se algum precisar de uma escolha diferente.',
    tips: ['Bom para séries de cortes com o mesmo formato.'],
    workflows: ['BATCH_FACTORY.md']
  },
  {
    id: 'longo', group: 'editar', title: 'Vídeo longo e cortes',
    what: 'Vídeos acima de 5 minutos seguem um procedimento próprio: voz limpa inteira, revisão de toda a fala, legendas e tela. Depois saem os cortes curtos.',
    say: 'Edite este vídeo longo com F18 e tire 4 cortes.',
    prompt: 'Edite o vídeo longo [nome do arquivo] com [F18] e [ID], horizontal 16:9.\n\nDepois, tire [4] cortes verticais com os melhores trechos. Cada corte é um vídeo separado.',
    tips: ['Instruções faladas durante a gravação, como “tira isso”, são obedecidas e cortadas.'],
    workflows: ['LONG_FORM.md']
  },
  {
    id: 'revisar', group: 'editar', title: 'Revisar antes de entregar',
    what: 'Conferência técnica e visual: áudio, legendas, cortes, cenas e se as suas preferências foram aplicadas.',
    say: 'Revise a E03 antes de eu postar.',
    prompt: 'Revise a [E03] antes de eu postar: confira áudio, cortes no meio de palavras, legendas, cenas vazias e se minhas preferências do formato foram seguidas. Liste o que está bom e o que precisa de ajuste.',
    tips: ['A IA não declara “aprovado” sem abrir os quadros e ouvir os cortes.'],
    workflows: ['QA.md']
  },
  {
    id: 'variacoes', group: 'testar', title: 'Variações de reel para testar', isNew: true, featured: true,
    what: 'O mesmo vídeo em quantas versões você quiser, para descobrir qual gancho prende mais. Cada versão muda o começo e também detalhes no resto (legenda, transições, B-roll, trilha), para as redes não tratarem como o mesmo arquivo.',
    say: 'Me entregue 5 variações deste vídeo com 5 ganchos diferentes.',
    prompt: 'Edite [o vídeo] com [F02] e [ID05] e, no final, me entregue [5] variações para teste, com [5] ganchos visuais diferentes. Quero descobrir qual segura mais nos primeiros segundos.\n\nMantenha a mesma voz, os mesmos fatos e o mesmo CTA. Para o Instagram não reconhecer como o mesmo vídeo, mude também a legenda, as transições, o B-roll e a trilha no resto de cada variação. Me mostre o plano das variações antes de montar.',
    tips: ['Dois jeitos, que podem ser misturados: gancho re-editado (a edição muda) ou post com foto chamativa no estilo F19 Print Repost (rápido, sem serviço pago).', 'Exemplo misto: “5 edições × 2 posts com foto = 10 reels”.', 'Vídeo que não foi bem? “O E07 flopou, faz 5 variações.”', 'Para o post com foto, informe o nome e o @ da conta que vai postar.', 'Depois do teste, conte qual foi melhor: o resultado fica registrado no formato.'],
    workflows: ['REEL_VARIATIONS.md']
  },
  {
    id: 'capas', group: 'testar', title: 'Capas e thumbnails',
    what: 'Opções de capa geradas a partir de quadros reais do vídeo e das suas referências de capa. Cada opção é uma geração paga.',
    say: 'Crie 3 opções de capa para a E05.',
    prompt: 'Crie [3] opções de capa para a [E05], formato [16:9].\n\nUse quadros reais do vídeo e estas referências: [anexe ou indique os arquivos]. Texto da capa: [frase curta]. Me diga o custo de cada opção antes de gerar.',
    tips: ['Usa serviço pago com chave própria.'],
    keys: ['OpenRouter'], paid: true,
    workflows: []
  },
  {
    id: 'voz', group: 'som', title: 'Limpar a voz',
    what: 'Remove ruído e eco da gravação inteira antes dos cortes. É o que deixa a fala limpa entre as palavras.',
    say: 'Limpe a voz deste vídeo antes da prévia.',
    prompt: 'Limpe a voz do vídeo [nome] antes de montar a prévia: isole a voz do arquivo inteiro e só depois aplique os cortes. Me diga quanto ruído saiu nas pausas.',
    tips: ['Usa a chave ElevenLabs. Só o áudio é enviado ao serviço.'],
    keys: ['ElevenLabs'], paid: true,
    workflows: []
  },
  {
    id: 'silencio', group: 'som', title: 'Cortar silêncios',
    what: 'Pausas mortas são encurtadas automaticamente, cortando som e imagem juntos. Pausas intencionais e respiros ficam protegidos.',
    say: 'Deixe o ritmo mais rápido, sem cortar palavras.',
    prompt: 'Na [E02], deixe o ritmo mais rápido cortando as pausas sem motivo. Não corte começo ou fim de palavras e mantenha as pausas de efeito.',
    tips: ['Já acontece em toda edição. Peça “não corte os silêncios” para desligar.'],
    workflows: ['REMOVE_SILENCE.md']
  },
  {
    id: 'erros', group: 'som', title: 'Tirar erros de fala e tomadas repetidas',
    what: 'Gaguejos, frases abandonadas e tomadas repetidas saem quando a certeza é alta. Os casos duvidosos vêm para você decidir.',
    say: 'Tire as tomadas erradas e as repetições.',
    prompt: 'No vídeo [nome], tire os erros de fala, frases abandonadas e tomadas repetidas, ficando com a melhor versão de cada ideia. Se houver dúvida sobre qual tomada usar, me pergunte mostrando os trechos.',
    tips: [],
    workflows: ['CLEAN_SPEECH.md']
  },
  {
    id: 'musica', group: 'som', title: 'Trilha original',
    what: 'Música gerada sob medida, sem direitos autorais, com a virada no momento certo e abaixando sozinha quando você fala.',
    say: 'Coloque uma trilha tensa que vira no final.',
    prompt: 'Coloque na [E04] uma trilha original [tensa / animada / calma], que mude no momento [da virada, aos 0:45]. A música precisa ficar bem abaixo da voz o tempo todo.',
    tips: ['Usa a chave ElevenLabs.'],
    keys: ['ElevenLabs'], paid: true,
    workflows: []
  },
  {
    id: 'meus-arquivos', group: 'cenas', title: 'Usar suas imagens e vídeos de apoio',
    what: 'Fotos, prints e B-roll que você enviar entram nos momentos em que fazem sentido. Nada é forçado só porque existe.',
    say: 'Use as imagens da pasta apoio onde fizer sentido.',
    prompt: 'Na edição de [vídeo], use as imagens e vídeos de apoio que coloquei em “01 - Enviar vídeos/[pasta]” nos momentos em que combinam com a fala. Me diga onde cada um entrou e quais não foram usados.',
    tips: ['Só envie material que você pode usar.'],
    workflows: ['USE_INSERTION_ASSETS.md']
  },
  {
    id: 'buscar-cenas', group: 'cenas', title: 'Buscar cenas do TikTok e YouTube',
    what: 'Pesquisa e baixa cenas de apoio citadas no vídeo, registrando de onde veio cada uma.',
    say: 'Busque cenas do YouTube sobre o que eu falo.',
    prompt: 'Para a [E06], busque no [TikTok / YouTube] cenas de apoio sobre [assunto] e use nos momentos em que eu falo disso. Registre o link de origem de cada cena.',
    tips: ['Usa a chave ScrapeCreators; vídeos do YouTube sem arquivo disponível usam a chave Apify.'],
    keys: ['ScrapeCreators', 'Apify'], paid: true,
    workflows: []
  },
  {
    id: 'direcao', group: 'cenas', title: 'Direção visual a partir da fala',
    what: 'Cada ideia do vídeo recebe uma decisão visual: manter a pessoa, mostrar um texto, uma ilustração ou uma cena, respeitando o cenário real.',
    say: 'Monte o storyboard da E02 antes de animar.',
    prompt: 'Leia a fala da [E02] e monte a direção visual: para cada ideia, diga se fica a pessoa, um texto, uma ilustração ou uma cena. Me mostre o storyboard antes de produzir.',
    tips: [],
    workflows: ['DIRECT_VISUALS.md']
  },
  {
    id: 'animacoes', group: 'cenas', title: 'Animações sobre a fala',
    what: 'Gráficos, números, listas e diagramas animados no tempo exato da fala, depois que os cortes estão fechados.',
    say: 'Anime os números que eu cito na E03.',
    prompt: 'Na [E03], crie animações para [os números / a lista / o passo a passo] que eu explico, sincronizadas com a fala e nas cores da identidade escolhida.',
    tips: [],
    workflows: ['CREATE_JS_ANIMATIONS.md']
  },
  {
    id: 'motion-ref', group: 'cenas', title: 'Motion a partir de uma referência',
    what: 'Para uma linguagem de animação nova: referência, lista de estados, quadros, animatic e revisão com você antes do acabamento.',
    say: 'Quero um motion no estilo deste vídeo de referência.',
    prompt: 'Quero um motion no estilo desta referência: [link ou arquivo]. Assunto: [tema]. Duração: [30 s]. Me mostre os estados principais e um animatic antes de finalizar.',
    tips: [],
    workflows: ['MOTION_STUDIO.md']
  },
  {
    id: 'motion-produto', group: 'cenas', title: 'Motion de produto ou plataforma',
    what: 'Vídeo institucional com as telas do seu sistema recriadas e animadas, em 16:9 e 9:16, sem precisar gravar.',
    say: 'Faça um motion mostrando as funções da minha plataforma.',
    prompt: 'Faça um motion institucional da plataforma [nome] mostrando [as funções principais]. O código/telas estão em [repositório ou prints]. Público: [quem vai assistir]. Quero nas duas proporções, 16:9 e 9:16.',
    tips: ['Combina com o formato F07 Motion Institucional.'],
    workflows: ['PRODUCT_MOTION.md']
  },
  {
    id: 'roupa', group: 'cenas', title: 'Trocar roupa ou cenário',
    what: 'Num trecho curto, troca a roupa de quem aparece e/ou o fundo, mantendo o áudio original. Você vê o antes e depois para aprovar.',
    say: 'Nos primeiros 5 segundos, me coloque de blazer.',
    prompt: 'No vídeo [nome], entre [0:00] e [0:05], troque [minha roupa por um blazer preto / o cenário por um escritório]. Me diga o custo e como o trecho será enviado antes de gerar, e me mostre o antes e depois.',
    tips: ['Geração paga: cada trecho pede o seu “sim” na hora.', 'Só para quem pediu a troca.'],
    keys: ['OpenRouter'], paid: true,
    workflows: ['SWAP_OUTFIT_SCENERY.md']
  },
  {
    id: 'escolher-formato', group: 'formatos', title: 'Escolher um formato', featured: true,
    what: 'O formato define cortes, ritmo, composição e animações. Assista aos exemplos e copie o pedido pronto.',
    say: 'Qual formato combina com um vídeo sem eu aparecer?',
    prompt: 'Quero fazer um vídeo sobre [assunto], [aparecendo / sem aparecer], com [gravação / só narração / prints]. Quais formatos da fábrica combinam e por quê?',
    tips: [],
    link: { href: '#modelos', label: 'Abrir os modelos' },
    workflows: []
  },
  {
    id: 'escolher-id', group: 'formatos', title: 'Escolher cores e fontes (ID visual)',
    what: 'A identidade visual define a paleta e as fontes. Qualquer ID combina com qualquer formato.',
    say: 'Use a ID05 neste vídeo.',
    prompt: 'Na [E02], troque a identidade visual para [ID05]. Mantenha cortes e animações; mude só cores e fontes.',
    tips: [],
    link: { href: '#identidades', label: 'Ver as identidades' },
    workflows: []
  },
  {
    id: 'novo-formato', group: 'formatos', title: 'Criar um formato novo',
    what: 'Envie um nome simples e um link de exemplo. A fábrica cria o próximo código FP, analisa o exemplo real e escreve a receita.',
    say: 'Crie um formato novo a partir deste exemplo.',
    prompt: 'Crie um formato novo chamado “[nome simples]” a partir deste exemplo: [link do Instagram, Drive, X ou site].\n\nAnalise o vídeo real, me explique o mecanismo da edição e só depois salve a receita. Não fixe cores ou fontes no formato.',
    tips: ['O nome descreve a edição (ex.: “Lista em Tela”), não uma pessoa ou marca.', 'Sem link de exemplo o formato não é criado.'],
    workflows: ['DEFINE_PATTERN.md', 'ANALYZE_REFERENCE.md']
  },
  {
    id: 'opcoes-estilo', group: 'formatos', title: 'Ver opções de estilo',
    what: 'Duas a quatro direções de edição realmente diferentes (ritmo, legenda, zoom, animação) antes de fixar um formato.',
    say: 'Me mostre 3 direções de edição diferentes para este vídeo.',
    prompt: 'Antes de editar [o vídeo], me proponha [3] direções de edição realmente diferentes: ritmo, legendas, zooms, animações e som. Explique para que cada uma serve.',
    tips: [],
    workflows: ['GENERATE_STYLE_OPTIONS.md']
  },
  {
    id: 'nova-id', group: 'formatos', title: 'Criar sua própria identidade',
    what: 'Cria uma IDP com as suas cores e fontes, ou copia uma ID oficial para personalizar sem mexer no original.',
    say: 'Crie uma identidade com as cores da minha marca.',
    prompt: 'Crie uma identidade visual minha chamada “[nome]” com estas cores: [#hex fundo, #hex destaque, #hex texto] e estas fontes: [títulos / texto]. Os arquivos das fontes estão em [pasta].',
    tips: ['Ou: “Copie a ID03 para uma IDP e troque o azul por verde”.'],
    workflows: []
  },
  {
    id: 'memoria', group: 'formatos', title: 'Ensinar suas preferências',
    what: 'Tudo que você diz sobre um formato vira memória dele: a próxima edição já sai do seu jeito. Não precisa dizer “salve isso”.',
    say: 'No F02, sempre comece direto na fala, sem vinheta.',
    prompt: 'A partir de agora, no [F02]: [sempre comece direto na fala / legendas com no máximo 4 palavras / sem zoom no rosto]. Isso vale para os próximos vídeos deste formato.',
    tips: ['Diga se é “só neste vídeo” ou “sempre neste formato”.', 'Resultados de audiência também podem ser registrados: “A VAR3 teve 2x mais views em 7 dias”.'],
    workflows: ['FORMAT_MEMORY.md', 'LEARN_FROM_RESULT.md']
  },
  {
    id: 'atualizar', group: 'cuidar', title: 'Atualizar a fábrica',
    what: 'Atualiza só o código, com backup, mantendo trabalhos, memória, referências já baixadas, IDs, chaves e configurações. Novas referências são baixadas quando o formato for usado. Se você personalizou código, nada é sobrescrito.',
    say: 'Atualize esta fábrica.',
    prompt: 'Atualize esta fábrica para a versão mais recente, preservando meus trabalhos, memórias, identidades, chaves e configurações. Me diga o que mudou.',
    tips: ['Não precisa baixar a pasta de novo nem rodar nada manualmente.'],
    workflows: ['UPDATE_FACTORY.md']
  },
  {
    id: 'espaco', group: 'cuidar', title: 'Liberar espaço',
    what: 'Remove apenas arquivos técnicos de renderização de trabalhos já entregues. Gravações, prévias, finais e memória ficam.',
    say: 'Quanto espaço eu libero nos trabalhos entregues?',
    prompt: 'Mostre quanto espaço posso liberar nos trabalhos já entregues, sem apagar gravações, prévias, finais ou memória. Só remova depois que eu confirmar os trabalhos.',
    tips: ['Primeiro vem a prévia do que sai; nada é apagado sem confirmação.'],
    workflows: ['CLEANUP_STORAGE.md']
  },
  {
    id: 'recuperar', group: 'cuidar', title: 'Recuperar uma pasta antiga ou misturada',
    what: 'Para instalações antigas: cria uma pasta nova e organizada, preservando a original e todos os trabalhos.',
    say: 'Minha pasta é de uma versão antiga. Recupere sem perder nada.',
    prompt: 'Minha pasta da fábrica é de uma versão antiga (ou ficou misturada). Monte uma pasta nova organizada a partir dela, sem apagar ou alterar a original, e me mostre o recibo do que foi levado.',
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
