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
    c.setTitle('Cortez - Instalação guiada pelo Claude')
    c.setAuthor('Cortez, por Bruno Guzela')
    width, height = A4
    style = ParagraphStyle('body', fontName='CortezManrope', fontSize=10.2, leading=16, textColor=HexColor('#D6C9E5'))
    heading = ParagraphStyle('heading', fontName='CortezBold', fontSize=11, leading=17, textColor=HexColor('#C88BF7'))
    for index, page in enumerate(data['pages']):
        c.setFillColor(HexColor('#07030D')); c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(HexColor('#C88BF7')); c.setFont('CortezBold', 23); c.drawString(48, height - 52, 'Cortez')
        c.setFillColor(HexColor('#B9A8CF')); c.setFont('CortezManrope', 8)
        c.drawRightString(width - 48, height - 48, 'ANEXE O PDF. O CLAUDE CONDUZ.')
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
        c.setStrokeColor(HexColor('#38204F')); c.line(48, 42, width - 48, 42)
        c.setFillColor(HexColor('#B9A8CF')); c.setFont('CortezManrope', 8)
        c.drawString(48, 28, 'Cortez | Guia de instalação | '+data['version'])
        c.drawRightString(width - 48, 28, f'{index+1}/{len(data["pages"])}')
        c.showPage()
    c.save()
    print(json.dumps({'ok': True, 'pages': len(data['pages']), 'output': str(out.relative_to(root))}))


if __name__ == '__main__':
    build()
