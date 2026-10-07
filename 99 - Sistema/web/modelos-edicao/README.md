# Modelos de edição

Biblioteca pública para escolher um formato, assistir às referências, escolher uma ID visual e copiar um pedido para a fábrica local. O site não acessa o disco do visitante nem recebe gravações de clientes.

Destino: **modelos-edicao.empirebusiness.com.br**.

## Importação no Vercel

Importar o repositório `Empire-Business/edicao-por-ia`. Usar o diretório raiz **`99 - Sistema/web/modelos-edicao`**. O framework é **Other**, o build é `npm run build`, e a saída é `dist`. Não há variáveis de ambiente, banco de dados ou dependências npm. Em Domains, adicionar `modelos-edicao.empirebusiness.com.br` e aplicar no provedor DNS o registro indicado pelo próprio Vercel.

A implantação deste site é independente do pacote de atualização da fábrica. Não publicar a raiz da fábrica como diretório estático. O build copia somente o código da interface, o catálogo público, as fontes e a mídia referenciada. Trabalhos, memória, credenciais e catálogos privados não entram no resultado.

## Conteúdo publicado

`publication.json` congela a seleção autorizada a partir dos códigos ativos do catálogo local. F02 e F03 estão descartados; F09 foi incorporado ao F08 e F11 ao F07. A seleção contém 12 modelos, com F14 Lista em Tela, F15 Dois Lados e F16 Comentário com B-roll. O F16 preserva a pesquisa e a montagem rica de mídia como workflow independente. Nenhum cadastro privado é descoberto ou publicado automaticamente. O build rejeita códigos descartados e entradas que não constam da seleção.

`public/catalog.json` guarda somente os campos públicos necessários à interface. As fontes das IDs vêm dos presets distribuídos, sem herdar pessoa, marca ou logotipo. Os guias do painel são uma versão sanitizada das receitas, com materiais e sequência de edição.

Os vídeos publicados são cópias otimizadas das referências autorizadas, com áudio e sem alterar os originais. Referência externa, prévia histórica, referência em imagem e esquema ilustrativo têm rótulos próprios. A aparência do exemplo não é a identidade da nova edição.

## Vimeo

`vimeo.json` aceita um código de formato como chave e um objeto com `id` e, se necessário, `hash` de um vídeo não listado. A galeria prioriza o Vimeo quando a entrada existe e mantém uma cópia local como alternativa se o player não carregar. O player começa sem som, com loop e `autopause=0`; o controle de áudio silencia as outras prévias. Somente vídeos visíveis reproduzem, e o visitante pode pausar todos.

Nesta versão o envio ao Vimeo ficou bloqueado pela permissão de acesso a URLs de arquivo da extensão do Chrome. Não há IDs inventados. Os vídeos locais mantêm a galeria funcional enquanto essa integração está pendente.

Documentação do player: https://help.vimeo.com/hc/en-us/articles/12426260232977-About-Player-Parameters e https://github.com/vimeo/player.js.

## Manutenção técnica pela IA

Não regenerar a publicação a partir dos defaults: o catálogo local pode ter códigos descartados ou consolidar formatos. Revisar os códigos ativos, selecionar explicitamente os que o autor autorizou distribuir e atualizar `publication.json` com somente campos públicos. Usar o fluxo normal de cadastro/memória da fábrica para criar, renomear ou descartar formatos; este site não altera registros.

O exportador `scripts/export_catalog.py` deve ser executado a partir do motor `99 - Sistema`, numa instalação que tenha as referências. Ele confere SHA-256, lê apenas os presets de IDs e a seleção de publicação, e usa os guias de edição. O parâmetro `--media` prepara cópias de distribuição. Fontes ficam locais, com licenças OFL. O Vercel usa os arquivos já exportados e não roda Python/FFmpeg.

Verificar `npm test`, `npm run build` e as rotas, busca, favoritos, controles de mídia, seleção sem ID automática, compartilhamento e layout móvel. O servidor de desenvolvimento está em `scripts/serve.mjs`. Os comandos são documentação para manutenção pela IA, não etapas de uso do visitante.

## Busca e seleção rápida

`descriptors.json` mantém palavras de busca, materiais de partida, presença em câmera e mecanismos. A busca aceita acentos, aliases como zap/WhatsApp e frases como sem aparecer; os filtros refinam material e presença da pessoa. O botão Copiar pedido na biblioteca copia o F destacado e deixa ID, tamanho e material explicitamente por completar. Nenhuma edição começa com ID automática.

## Integridade de marca e referências

Nenhum formato adiciona logotipo, nome fixo de empresa ou assinatura de marca por padrão. F05 proíbe explicitamente EMPIRE como cabeçalho/assinatura de edição. As marcas vistas nos vídeos são do material histórico, preservado como referência. As receitas novas usam a ID atual e o material da pessoa.

O ZIP recebido foi conferido pelos vídeos reais, não pelos títulos. Tela dividida e recorte/comparação são aplicações do F08; o workflow rico de comentário com pesquisa foi mantido no F16. F17 e F18 foram retirados por correção explícita do autor: suas referências e receitas não vieram do ZIP autorizado. Seus códigos permanecem reservados, e os exemplos foram removidos da galeria e do pacote. Nesta importação, só usar arquivos do ZIP enviado e os links de referência nele contidos; não completar ausências com vídeos locais, outro ZIP ou pesquisas externas sem autorização explícita.

A proposta de dois repositórios foi substituída: a distribuição continua no mesmo repositório Empire-Business/edicao-por-ia, main. Visibilidade pública foi solicitada, com login no fluxo guiado; a ativação aguarda tratamento autorizado do histórico de trabalhos. Formatos particulares usam FP e não entram automaticamente na galeria. Downloads sob demanda ficam adiados. A biblioteca pública de escolha permanece ordenada numericamente por F, preservando nomes e receitas consolidados.
