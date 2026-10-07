#!/usr/bin/env python3
"""Build original, static illustrative storyboards. Not frames of completed edits.

Pillow is used only by the maintainer; PNGs/SVGs are bundled for every installation.
No real faces, contacts, product screens, brands or customer media.
"""
from pathlib import Path
import html, json
ROOT = Path(__file__).resolve().parents[1]

STORIES = {
'F01': [('Conversa', ['Uma ideia vira mensagem', 'Áudio: 0:06', 'Reproduzindo a fala']), ('Explicação', ['A mensagem abre uma cena', 'Ideia → comparação', 'O áudio continua']), ('Conclusão', ['A cena volta ao chat', 'Resumo em uma mensagem', 'Fim da conversa'])],
'F02': [('Gancho', ['Pessoa: por que isso importa?', 'Legenda curta', 'Enquadramento próximo']), ('Variação', ['Corte na mudança de ideia', 'Número + apoio visual', 'A fala mantém o ritmo']), ('Fechamento', ['Retoma o ponto principal', 'Conclusão gravada', 'Sem prolongar a saída'])],
'F03': [('Foto', ['Foto autorizada da pessoa', 'Movimento sincronizado', 'Narração conduz a cena']), ('Apoio', ['Imagem relacionada ao tema', 'Dado ou comparação', 'A voz segue contínua']), ('Retorno', ['Foto em um trecho curto', 'Expressão coerente', 'Conclusão da narração'])],
'F04': [('Abertura', ['Pessoa apresenta o gancho', 'Frase forte e curta', 'Começa a história']), ('Animação', ['A voz continua', 'Elementos explicam a ideia', 'Uma relação por cena']), ('Conclusão', ['Última ideia da narração', 'Resumo visual', 'Pedido final se informado'])],
'F05': [('Título', ['Pergunta central da história', 'Pessoa no gancho', 'Informação em destaque']), ('Matéria visual', ['Imagem + título curto', 'Diagrama explica a relação', 'Tempo suficiente para ler']), ('Síntese', ['Problema → explicação', 'Retoma a ideia principal', 'Conclusão visual'])],
'F06': [('Elementos', ['Entrada', 'Processo', 'Resultado']), ('Conexões', ['Entrada → processo', 'Processo → resultado', 'Uma etapa por frase']), ('Conclusão', ['Destaca o resultado', 'Compara antes e depois', 'Segue para a próxima ideia'])],
'F07': [('Tela inicial', ['Menu da interface', 'Escolha de uma tarefa', 'Dados de demonstração']), ('Ação', ['Clique em um controle', 'Mudança de estado', 'Mostra o que mudou']), ('Resultado', ['Interface após a ação', 'Benefício demonstrado', 'Leitura no celular'])],
'F08': [('Pessoa + fundo', ['Pessoa no primeiro plano', 'Cena de apoio atrás', 'Legenda em área livre']), ('Troca do apoio', ['A fala muda de ideia', 'O fundo muda junto', 'Recorte continua estável']), ('Conclusão', ['Pessoa termina a fala', 'Apoio mostra o resultado', 'Rosto e mãos visíveis'])],
'F09': [('Contexto', ['Pessoa explica a situação', 'Conversa ilustrativa', 'Contatos fictícios']), ('Conversa', ['Mensagem relevante', 'Uma ação na interface', 'Resposta do fluxo']), ('Resultado', ['Pessoa retoma a explicação', 'Tela mostra o efeito', 'Sem falso depoimento'])],
'F10': [('Pessoa', ['Situação concreta', 'Apresentador explica', 'Gancho ligado à tarefa']), ('Tela', ['Demonstra a ação citada', 'Tela cheia ou com pessoa', 'Apoio real quando útil']), ('Conclusão', ['Resultado da ação', 'Retorno à pessoa', 'Conclusão gravada'])],
'F11': [('Campos', ['Nome: exemplo fictício', 'Escolha de uma opção', 'Rótulos legíveis']), ('Validação', ['Campo obrigatório', 'Correção demonstrada', 'Pronto para enviar']), ('Envio', ['Botão: enviar', 'Confirmação da tarefa', 'Estado final da interface'])],
'F12': [('Contraste', ['Objeto pequeno × grande', 'Pergunta da história', 'Gancho visual']), ('Evolução', ['Imagem + informação', 'Comparação de escala', 'Números verificáveis']), ('Retomada', ['Volta à imagem inicial', 'Responde à pergunta', 'Conclusão da história'])],
}


def build():
    from PIL import Image, ImageDraw, ImageFont
    directory = ROOT / 'examples/formats'; directory.mkdir(parents=True, exist_ok=True)
    defaults = json.loads((ROOT / 'config/design-defaults.json').read_text())
    names = {x['code']:x['name'] for x in defaults['formats']}
    font = ROOT / 'assets/fonts/portable/manrope-variable.ttf'
    def ft(n):
        face=ImageFont.truetype(str(font), n);face.set_variation_by_axes([500]);return face
    catalog = {}
    for code, states in STORIES.items():
        title = code + ' · ' + names[code]
        image = Image.new('RGB', (1440, 950), '#f5f4ef'); d = ImageDraw.Draw(image)
        d.text((65,45), title, font=ft(48), fill='#222222')
        subtitle = 'EXEMPLO ILUSTRATIVO · sequência de edição · cores e fontes vêm da ID escolhida'
        d.text((65,116), subtitle, font=ft(21), fill='#555555')
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="950" viewBox="0 0 1440 950" role="img">', '<title>' + html.escape(title) + '</title>', '<rect width="1440" height="950" fill="#f5f4ef"/>']
        def text(x,y,value,size=26):
            svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="#222">{html.escape(value)}</text>')
        text(65,95,title,48); text(65,141,subtitle,21)
        for i,(label,lines) in enumerate(states):
            x=65+i*450
            d.rounded_rectangle((x,190,x+410,795), radius=20, fill='#ffffff', outline='#aaaaaa', width=2)
            d.text((x+25,220), f'{i+1:02d}  {label}', font=ft(29), fill='#222222')
            svg.append(f'<rect x="{x}" y="190" width="410" height="605" rx="20" fill="white" stroke="#aaa"/>')
            text(x+25,257,f'{i+1:02d}  {label}',29)
            # Neutral shapes describe the mechanism, never a ready-to-render design preset.
            if code in ('F07','F11'):
                for n in range(3):
                    d.rounded_rectangle((x+35,305+n*65,x+375,352+n*65),radius=8,outline='#888888',width=2)
                    svg.append(f'<rect x="{x+35}" y="{305+n*65}" width="340" height="47" rx="8" fill="none" stroke="#888"/>')
                d.rectangle((x+240,503,x+375,540),fill='#333333')
                svg.append(f'<rect x="{x+240}" y="503" width="135" height="37" fill="#333"/>')
            elif code == 'F01' or code == 'F09':
                for n in range(3):
                    xx=x+35+(n%2)*55
                    d.rounded_rectangle((xx,310+n*75,xx+285,365+n*75),radius=14,fill='#eeeeee',outline='#999999',width=1)
                    svg.append(f'<rect x="{xx}" y="{310+n*75}" width="285" height="55" rx="14" fill="#eee" stroke="#999"/>')
            elif code == 'F06' or code == 'F12':
                for n in range(3):
                    yy=310+n*80
                    d.rectangle((x+95,yy,x+315,yy+48),outline='#555555',width=2)
                    svg.append(f'<rect x="{x+95}" y="{yy}" width="220" height="48" fill="none" stroke="#555"/>')
                    if n<2:
                        d.line((x+205,yy+50,x+205,yy+78),fill='#555555',width=3)
                        svg.append(f'<path d="M{x+205} {yy+50}v28" stroke="#555"/>')
            else:
                d.rounded_rectangle((x+35,310,x+375,525),radius=10,fill='#eeeeee')
                d.ellipse((x+170,330,x+240,400),outline='#666666',width=3)
                d.rounded_rectangle((x+130,410,x+280,515),radius=25,outline='#666666',width=3)
                svg += [f'<rect x="{x+35}" y="310" width="340" height="215" rx="10" fill="#eee"/>', f'<circle cx="{x+205}" cy="365" r="35" fill="none" stroke="#666" stroke-width="3"/>', f'<rect x="{x+130}" y="410" width="150" height="105" rx="25" fill="none" stroke="#666" stroke-width="3"/>']
            for n,line in enumerate(lines):
                d.text((x+25,600+n*53),line,font=ft(22),fill='#333333'); text(x+25,622+n*53,line,22)
        note='Material próprio de demonstração. Não é print de uma execução aprovada nem reprodução da referência original.'
        d.text((65,847),note,font=ft(21),fill='#555555');text(65,869,note,21)
        svg.append('</svg>');(directory / (code+'.svg')).write_text('\n'.join(svg)+'\n')
        image.save(directory / (code+'.png'),optimize=True)
        catalog[code]=[{'path':'examples/formats/'+code+'.png','caption':title+' — três estados ilustrativos da edição.','status':'illustrative_storyboard'}]
    (ROOT / 'config/format-examples.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    return catalog

if __name__ == '__main__': build()
