"""Readable HTML editing manuals. Examples are local optional evidence, never design defaults."""
import html,json
from pathlib import Path
from urllib.parse import quote
from factory_common import inside

DETAILS={
'F01':{'inputs':'Áudio ou vídeo com uma fala clara. Roteiro e cenas de apoio são opcionais.','mechanism':'A fala é dividida em mensagens de uma conversa ilustrativa. Um balão de áudio pode virar uma cena maior e depois voltar ao chat.','steps':['Abrir com a frase mais interessante, sem esperar uma animação longa de digitação.','Separar as ideias em mensagens curtas e fáceis de ler.','Mostrar reprodução do áudio com duração e movimento coerentes com a voz real.','Transformar a mensagem principal em comparação, lista, diagrama ou cena de apoio.','Voltar à conversa e encerrar com uma mensagem que resume a ideia.'],'avoid':'Não simular depoimentos reais, inventar mensagens atribuídas a pessoas ou usar uma tela de celular tão pequena que ninguém consiga ler.'},
'F02':{'inputs':'Gravação com fala. Imagens, vídeos e dados relacionados ao assunto ajudam.','mechanism':'A edição mantém o assunto andando: corta repetições, varia o enquadramento e usa animações para explicar o que está sendo dito.','steps':['Escolher um gancho forte nos primeiros segundos.','Remover tomadas repetidas e pausas sem intenção, preservando palavras.','Variar imagem, enquadramento e tipo de explicação quando a ideia muda.','Acrescentar números, ícones ou cenas que tragam informação além da legenda.','Terminar de forma direta, sem prolongar o vídeo depois da conclusão.'],'avoid':'Evitar zooms aleatórios, efeitos em toda frase e movimentos que deixam o texto impossível de ler.'},
'F03':{'inputs':'Narração e uma foto autorizada da pessoa representada. Materiais do assunto são opcionais.','mechanism':'Uma foto ganha movimento de fala em momentos escolhidos; outras cenas explicam o conteúdo. A voz real é o relógio da animação.','steps':['Preparar a narração e confirmar qual foto pode ser usada.','Escolher momentos curtos em que a foto ajuda a conduzir a história.','Sincronizar boca/cabeça com a fala, sem inventar uma fala diferente.','Alternar a foto com imagens, dados e diagramas para evitar repetição.','Revisar a naturalidade do rosto e a clareza da explicação.'],'avoid':'Não assumir que a foto antiga do acervo representa o usuário atual, nem criar uma falsa declaração de outra pessoa.'},
'F04':{'inputs':'Vídeo curto da pessoa na abertura e gravação do restante da fala.','mechanism':'A pessoa aparece no gancho. Depois, a fala continua sobre animações e imagens que explicam o assunto.','steps':['Montar uma abertura curta com a pessoa e a promessa do vídeo.','Passar para o corpo narrado sem mudar o volume ou o timbre da voz.','Criar uma cena visual para cada ideia importante.','Usar comparações, diagramas e imagens quando forem mais claros que texto.','Fechar com a conclusão gravada ou com o pedido final informado para o trabalho.'],'avoid':'Não manter a pessoa em tela por hábito e não repetir integralmente a legenda em outra animação.'},
'F05':{'inputs':'Gancho gravado, narração e referências do assunto.','mechanism':'A apresentação parece uma matéria visual: títulos, informações e imagens se organizam para contar uma história. A fonte não é obrigatoriamente serifada; vem da ID visual.','steps':['Apresentar o assunto com um título curto e um gancho.','Construir uma sequência de problema, explicação e conclusão.','Organizar dados e relações em diagramas e composições legíveis.','Deixar cada estado tempo suficiente para ler e compreender.','Retomar a ideia principal antes de encerrar.'],'avoid':'Não confundir o estilo editorial com uma cor, marca ou fonte fixa; evitar excesso de texto no mesmo quadro.'},
'F06':{'inputs':'Fala ou roteiro de explicação, com dados e materiais verificáveis.','mechanism':'Ideias abstratas viram módulos, ícones, conexões, passos e números. Os diagramas explicam relações, em vez de decorar a tela.','steps':['Identificar a relação que a fala quer explicar.','Escolher a representação mais simples: fluxo, comparação, etapas ou quantidade.','Apresentar um elemento por vez, de acordo com a frase.','Destacar o elemento importante sem cobrir os demais.','Mostrar a conclusão do diagrama e seguir para a próxima ideia.'],'avoid':'Não criar dados falsos, animar tudo ao mesmo tempo ou depender só da cor para explicar uma relação.'},
'F07':{'inputs':'Telas, mockups ou código da interface, copiados para dentro da fábrica.','mechanism':'A interface é recriada e animada: o público acompanha menus, cliques, janelas e resultados. Não é apenas uma sequência de prints.','steps':['Conferir quais telas e ações existem de verdade.','Escolher uma tarefa simples para demonstrar.','Recriar a interface com dados fictícios quando houver informações privadas.','Mostrar clique, mudança de estado e resultado em sequência.','Adaptar a composição para cada proporção sem encolher a interface inteira.'],'avoid':'Não apresentar funções inexistentes como prontas, usar dados reais sem autorização ou inserir a logo antiga automaticamente.'},
'F08':{'inputs':'Vídeo da pessoa e cenas ou telas relacionadas à fala.','mechanism':'A pessoa fica à frente de uma cena de apoio. As camadas se integram com recorte e transição suave, sem uma divisão rígida na tela.','steps':['Limpar e montar a fala antes de escolher os apoios.','Selecionar a cena que demonstra a ideia naquele momento.','Recortar a pessoa com cuidado, sem perder mãos, cabelo ou bordas importantes.','Posicionar o apoio atrás dela e reservar espaço para legenda.','Revisar a transição e a legibilidade em uma tela pequena.'],'avoid':'Não cobrir o rosto, fingir que uma estimativa de área é um recorte preciso ou usar uma cena só porque é chamativa.'},
'F09':{'inputs':'Fala da pessoa e materiais de uma conversa ou fluxo de atendimento.','mechanism':'A fala se alterna com conversas e ações em uma tela. As mensagens mostram o fluxo explicado, com informações fictícias quando necessário.','steps':['Explicar o problema que a conversa resolve.','Mostrar as mensagens relevantes no momento certo da fala.','Destacar uma decisão ou ação da interface.','Alternar pessoa, conversa e resultado para manter o contexto.','Encerrar mostrando o efeito da ação, sem exagerar o resultado.'],'avoid':'Não inventar depoimentos, expor contatos reais ou transformar uma conversa ilustrativa em prova de venda.'},
'F10':{'inputs':'Vídeo com apresentador e telas/cenas do produto ou serviço.','mechanism':'A pessoa apresenta a ideia e a tela mostra a aplicação. Pode haver cenas reais de apoio, em tela cheia ou junto da pessoa.','steps':['Abrir com uma situação concreta ou benefício explicado pela fala.','Cortar erros claros e repetições da gravação.','Mostrar a interface quando a pessoa falar daquela ação.','Usar apoio real quando ele demonstrar melhor a situação.','Fechar com uma conclusão ou pedido final fornecido para o vídeo.'],'avoid':'Não usar cenas genéricas sem relação com o áudio ou prometer resultados que a gravação não comprova.'},
'F11':{'inputs':'Interface ou mockups de formulário e indicação do fluxo demonstrado.','mechanism':'O vídeo acompanha uma tarefa em um formulário: campo, escolha, validação, envio e resultado. O layout pode usar qualquer ID visual.','steps':['Escolher uma tarefa curta e compreensível.','Mostrar o campo e o preenchimento com dados fictícios.','Demonstrar uma escolha ou validação quando ela for importante.','Mostrar o envio e o resultado real do fluxo.','Manter rótulos e informações grandes o suficiente para leitura no celular.'],'avoid':'Não usar informações pessoais reais ou mostrar uma função de mockup como se já estivesse implementada.'},
'F12':{'inputs':'Narração, roteiro quando houver e imagens/fontes do assunto.','mechanism':'Uma história é contada com imagens, objetos recortados, números, etiquetas e comparações. Pode voltar à imagem inicial no encerramento.','steps':['Abrir com um contraste concreto que desperte curiosidade.','Apresentar a pergunta ou o problema da história.','Explicar a evolução com imagens e demonstrações por etapas.','Usar números e comparações para mostrar a mudança de escala.','Retomar o gancho e concluir a história antes do pedido final opcional.'],'avoid':'Não copiar a marca ou o pedido comercial da referência, tomar dígitos intermediários de um contador como fatos ou inventar dados históricos.'}}


def reference_section(item):
 status=item.get('reference_status')
 videos=item.get('example_videos',[])
 if not status and not videos:return ''
 body='<section><h2>Referências disponíveis</h2>'
 if status=='support_material_only_no_completed_video_found':
  body+='<p>Há fotos e materiais de apoio. Ainda não foi encontrado um vídeo completo executado para este formato. As imagens não demonstram movimento ou sincronia.</p>'
 elif status in ('external_reference_not_factory_rendered','analyzed_not_factory_rendered'):
  body+='<p>O vídeo externo orienta a receita. Ainda não foi renderizado um novo vídeo deste formato pela fábrica.</p>'
 elif status=='historical_preview_accepted_as_reference':
  body+='<p>Prévias históricas aceitas por você como referências finais. Os vídeos originais foram preservados.</p>'
 else:body+='<p>Vídeos históricos disponíveis para entender a edição.</p>'
 if item.get('example_review',{}).get('mechanism_limit'):
  body+='<p>Os exemplos misturam pessoa, mídia e gráficos. Demonstram partes do mecanismo, não diagramas em todas as cenas.</p>'
 if videos:
  body+='<ul>'
  for video in videos:
   label=video.get('filename','Vídeo de referência')
   if video.get('reference_copy_transcoded'):label+=' — cópia menor para o Drive'
   body+='<li><a href="'+html.escape(video['url'],quote=True)+'">'+html.escape(label)+'</a></li>'
  body+='</ul>'
 if item.get('example_folder_url'):
  body+='<p><a href="'+html.escape(item['example_folder_url'],quote=True)+'">Abrir a pasta de referências no Drive</a></p>'
 return body+'</section>'


def guide(root,item):
 from format_catalog import page
 key=item.get('uid','').removeprefix('factory.').upper() or item['code'];spec=DETAILS.get(key,{'inputs':'Gravação e materiais relacionados ao assunto.','mechanism':item.get('description','Receita de edição cadastrada.'),'steps':['Conferir a referência e o material enviado.','Montar a fala e preservar o sentido.','Planejar as cenas conforme a receita.','Aplicar a ID visual escolhida.','Revisar a prévia antes do final.'],'avoid':'Não aplicar cores, fontes ou logos por conta própria.'})
 custom=item.get('mechanism_details')
 if isinstance(custom,dict) and all(k in custom for k in ('inputs','mechanism','steps','avoid')) and isinstance(custom['steps'],list) and all(isinstance(v,str) for v in custom['steps']):
  spec={k:custom[k] for k in ('inputs','mechanism','steps','avoid')}
 title=item['code']+' - '+item['name'];body='<a href="COMO USAR.html">Voltar</a><h1>'+html.escape(title)+'</h1><p>'+html.escape(spec['mechanism'])+'</p>'
 body+=reference_section(item)
 body+='<section><h2>O que enviar</h2><p>'+html.escape(spec['inputs'])+'</p><p>Informe o formato e a ID visual. Exemplo: “Use '+item['code']+' com ID03”. A fábrica cria um código E para a edição.</p></section>'
 body+='<section><h2>Como a edição é feita</h2><ol>'+''.join('<li style="margin:14px 0">'+html.escape(step)+'</li>' for step in spec['steps'])+'</ol></section>'
 body+='<section><h2>O que muda com a ID visual</h2><p>As cores e fontes vêm da ID escolhida. O jeito de cortar, organizar cenas e animar continua sendo deste formato. Você pode trocar ID03 por ID05 e manter o mesmo formato.</p><p>O tamanho e a posição do texto são ajustados para a fonte continuar legível. Logotipos só entram se forem pedidos para aquele vídeo.</p></section>'
 examples_path=inside(root,'context/catalog/examples.json');examples=json.loads(examples_path.read_text()).get(item['code'],[]) if examples_path.exists() else []
 bundled=inside(root,'config/format-examples.json')
 illustrations=json.loads(bundled.read_text()).get(key,[]) if bundled.exists() else []
 library_path=inside(root,'config/reference-library.json')
 library=json.loads(library_path.read_text()).get('formats',{}).get(key) if library_path.exists() else None
 stock_images=[x for x in (library or {}).get('references',[]) if x['kind']=='actual_reference_image' or x['kind']=='visual_reference']
 stock_images=[{**x,'caption':x.get('caption','Imagem histórica da referência. Sua identidade visual e pessoa não são escolhas automáticas.')} for x in stock_images[:4]]
 examples=illustrations+stock_images+examples
 body+='<section><h2>Exemplos visuais</h2>'
 if illustrations:body+='<p class="note">As ilustrações distribuídas mostram a sequência da edição. São material próprio de demonstração, não prints de vídeos aprovados. A aparência da sua edição vem da ID escolhida.</p>'
 if examples:
  for example in examples:
   image=inside(root,example['path'])
   if not image.is_file():continue
   body+='<figure style="margin:22px 0"><img src="../../99%20-%20Sistema/'+quote(example['path'])+'" alt="'+html.escape(example['caption'],quote=True)+'" style="display:block;max-width:100%;max-height:620px;border:1px solid #ddd"><figcaption>'+html.escape(example['caption'])+'</figcaption></figure>'
  body+='<p class="note">Quando houver prints do acervo local, eles servem para entender a mecânica; não obrigam a usar as cores, fontes, pessoa ou marca mostradas.</p>'
 else:body+='<p>Ainda não há print de uma execução neste cadastro. O guia descreve a receita; a primeira aplicação será conferida em uma prévia.</p>'
 if library:
  body+='<p><a href="../../99%20-%20Sistema/examples/reference-library/'+key+'/README.md">Abrir todos os materiais de referência deste formato</a></p>'
  for ref in library['references']:
   if ref['path'].endswith('.mp4') and inside(root,ref['path']).is_file():
    body+='<figure><video controls preload="metadata" style="width:100%;max-height:650px" src="../../99%20-%20Sistema/'+quote(ref['path'])+'"></video><figcaption>Vídeo de referência'+(' — prévia histórica' if ref['kind']=='existing_motion_preview' else '')+'. A pessoa e a identidade do exemplo não são escolhas automáticas.</figcaption></figure>'
 if item.get('example_url'):body+='<p><a href="'+html.escape(item['example_url'],quote=True)+'">Abrir o link de exemplo cadastrado</a></p>'
 elif item.get('example_link_status')=='legacy_exempt':body+='<p class="note">Este cadastro já existia antes da exigência de link. Novos formatos precisam de um link de exemplo.</p>'
 body+='</section><section><h2>Cuidados</h2><p>'+html.escape(spec['avoid'])+'</p><p>A voz é montada antes de sincronizar legendas e animações. Só erros claros e pausas sem intenção são cortados. A prévia é revista para conferir fala, leitura, sincronia e materiais usados.</p></section><section><h2>Como pedir ajustes</h2><p>Use o código da edição: “Na E01, aos 12 segundos, tire o texto”. Para mudar a receita: “No '+item['code']+', quero cortes mais suaves”. Para mudar cores/fontes: “Na ID03, quero [mudança]”.</p></section>'
 return page(title+' — guia da edição',body)
