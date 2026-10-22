#!/usr/bin/env python3
"""Rebuild the reviewed installer PDF. Requires reportlab and fonttools; no setup or network."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from fontTools.ttLib import TTFont as VariableFont
    from fontTools.varLib.instancer import instantiateVariableFont
    root = Path(root)
    fonts = root / 'assets/branding/cortez'
    cache = root / '.factory/pdf-fonts'
    cache.mkdir(parents=True, exist_ok=True)
    for name, weight in [('CortezManrope', 500), ('CortezBold', 800)]:
        font = VariableFont(fonts / 'manrope-variable.ttf')
        static = instantiateVariableFont(font, {'wght': weight}, inplace=False)
        for name_id in (1, 3, 4, 6, 16):
            for platform, encoding, language in ((3, 1, 0x409), (1, 0, 0)):
                static['name'].setName(name, name_id, platform, encoding, language)
        path = cache / (name + '.ttf'); static.save(path)
        pdfmetrics.registerFont(TTFont(name, str(path)))
    data = json.loads((root / 'method/CLAUDE_INSTALL_GUIDE_SOURCE.json').read_text())
    out = root / 'method/CLAUDE_INSTALL_GUIDE.pdf'
    c = canvas.Canvas(str(out), pagesize=A4, invariant=1)
    c.setTitle('Cortez - Instalação conduzida pela IA')
    c.setAuthor('Cortez, por Bruno Guzela')
    width, height = A4
    style = ParagraphStyle('body', fontName='CortezManrope', fontSize=10.2, leading=16, textColor=HexColor('#D6C9E5'))
    heading = ParagraphStyle('heading', fontName='CortezBold', fontSize=11, leading=17, textColor=HexColor('#C88BF7'))
    logo = ImageReader(str(fonts / 'logo-lockup.png'))
    portrait = ImageReader(str(fonts / 'apresentacao.webp'))
    total_pages = len(data['pages']) + 1

    def background():
        c.setFillColor(HexColor('#07030D')); c.rect(0, 0, width, height, fill=1, stroke=0)

    def footer(number):
        c.setStrokeColor(HexColor('#38204F')); c.line(48, 42, width - 48, 42)
        c.setFillColor(HexColor('#B9A8CF')); c.setFont('CortezManrope', 8)
        c.drawString(48, 28, 'Cortez | Guia de instalação | '+data['version'])
        c.drawRightString(width - 48, 28, f'{number}/{total_pages}')

    def paragraph(text, x, y, w, appearance):
        para = Paragraph(escape(text), appearance)
        _, h = para.wrap(w, height)
        para.drawOn(c, x, y-h)
        return y-h

    # Product cover: original logo and portrait, with the same official palette.
    background()
    c.drawImage(logo, 48, height-91, width=170, height=45.22, mask='auto')
    c.setFillColor(HexColor('#C88BF7')); c.setFont('CortezBold', 8)
    c.drawRightString(width-48, height-68, 'GUIA DE INSTALAÇÃO')
    c.setStrokeColor(HexColor('#38204F')); c.line(48,height-111,width-48,height-111)
    c.drawImage(portrait, width-48-222, height-475, width=222, height=333)
    hero = ParagraphStyle('hero', fontName='CortezBold', fontSize=33, leading=38, textColor=HexColor('#F4EEFB'))
    y=paragraph('Você grava. O Cortez edita.',48,height-151,245,hero)
    tagline = ParagraphStyle('tagline', parent=style, fontSize=15, leading=22, textColor=HexColor('#C88BF7'))
    y=paragraph('Você aprova.',48,y-12,230,tagline)
    paragraph('O agente que edita seus vídeos. Um pedido para preparar tudo no seu computador.',48,y-25,224,style)
    c.setFillColor(HexColor('#1B0F2E')); c.roundRect(48,220,width-96,118,12,fill=1,stroke=0)
    paragraph('ANEXE ESTE PDF AO CLAUDE E ENVIE',66,318,width-132,heading)
    prompt = ParagraphStyle('prompt',parent=heading,fontSize=19,leading=26,textColor=HexColor('#F4EEFB'))
    paragraph('O pedido já está neste PDF.',66,288,width-132,prompt)
    paragraph('Sem conta no GitHub. Sem comandos para copiar.',66,248,width-132,style)
    paragraph('macOS  •  Windows  •  Linux',48,192,width-96,heading)
    paragraph('O guia confere o acesso local do Claude e adapta a instalação ao computador. Inclui vídeo, transcrição, animações, limpeza de áudio e Cortez Voz. Se faltar acesso, a IA orienta o próximo passo.',48,166,width-96,style)
    c.linkURL('https://cortez.highticketai.com.br/',(48,58,width-48,81),relative=0)
    paragraph('cortez.highticketai.com.br',48,79,width-96,heading)
    footer(1);c.showPage()
    for index, page in enumerate(data['pages']):
        background()
        c.drawImage(logo,48,height-57,width=124,height=33,mask='auto')
        c.setFillColor(HexColor('#B9A8CF')); c.setFont('CortezManrope', 8)
        c.drawRightString(width - 48, height - 48, 'ANEXE O PDF. A IA CONDUZ.')
        c.setStrokeColor(HexColor('#38204F')); c.line(48, height - 68, width - 48, height - 68)
        c.setFillColor(HexColor('#F4EEFB')); c.setFont('CortezBold', 21)
        c.drawString(48, height - 110, page['title'])
        y = height - 143
        for block in page['blocks']:
            for key, appearance in [('heading', heading), ('text', style)]:
                if not block.get(key): continue
                para = Paragraph(escape(block[key]), appearance)
                _, h = para.wrap(width - 96, height)
                if y - h < 55: raise ValueError('PDF text exceeds page '+str(index+1))
                para.drawOn(c, 48, y - h); y -= h + 5
            y -= 12
        footer(index+2)
        c.showPage()
    c.save()
    print(json.dumps({'ok': True, 'pages': total_pages, 'output': str(out.relative_to(root))}))


if __name__ == '__main__':
    build()
