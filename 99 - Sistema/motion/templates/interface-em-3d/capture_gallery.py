#!/usr/bin/env python3
"""EXEMPLO_1 — captura da interface REAL do painel público do Cortez (https://cortez.highticketai.com.br, produto do próprio usuário) com
playwright, para virar textura 3D. Só elementos de interface: título da página de modelos, botões das IDs (sem e com seleção), a prévia
"Clareza em cada cena" em cada ID, o botão "Copiar pedido de edição", o pedido (texto) e o aviso "Copiado.". Os vídeos de referência da
galeria (exemplos externos) não são usados. Saídas: tmp/gal/*.png e tmp/gal/pedido.txt.
Run: ../../../.venv/bin/python src/capture_gallery.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

J = Path(__file__).resolve().parents[1]
O = J / 'tmp/gal'
O.mkdir(parents=True, exist_ok=True)
URL = 'https://cortez.highticketai.com.br'
IDS = ['Verde', 'Lima', 'Azul', 'Dourado', 'Roxo', 'Azul Claro', 'Azul e Papel', 'Laranja']   # Laranja por último: fica selecionada (como na live)
MARK = """()=>{document.querySelectorAll('[data-cap=preview]').forEach(e=>e.removeAttribute('data-cap'));const c=[...document.querySelectorAll('section.choice-builder *')]
  .filter(e=>/UMA IDEIA/.test(e.innerText||'')&&/O mesmo conte/.test(e.innerText||''));c.sort((a,b)=>a.getBoundingClientRect().height-b.getBoundingClientRect().height);
  c[0].setAttribute('data-cap','preview');}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(URL + '/#modelos', wait_until='load', timeout=90000); pg.wait_for_timeout(3000)
    pg.screenshot(path=str(O / 'modelos.png'))
    tags = pg.evaluate("""()=>[...document.querySelectorAll('article.model-card')].map(a=>(a.innerText||'').replace(/\\s+/g,' ').slice(0,90))""")
    (O / 'cards.txt').write_text('\n'.join(tags))
    ctx.close()
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=3)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=URL)
    pg = ctx.new_page()
    pg.goto(URL + '/#modelo=F16', wait_until='load', timeout=90000); pg.wait_for_timeout(3000)
    pg.get_by_text('Usar este modelo').first.click(); pg.wait_for_timeout(1500)
    pg.locator('section.choice-builder').first.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    for n in IDS:                                                   # botões sem seleção
        pg.locator('button.identity-choice', has_text=n).first.screenshot(path=str(O / f'idbtn_{n.replace(" ", "_")}.png'))
    for n in IDS:                                                   # prévia em cada ID (termina na Laranja, como o Apresentador escolheu na live)
        pg.locator('button.identity-choice', has_text=n).first.click(); pg.wait_for_timeout(900)
        pg.evaluate(MARK)
        pg.locator('[data-cap=preview]').screenshot(path=str(O / f'prev_{n.replace(" ", "_")}.png'))
    pg.locator('button.identity-choice', has_text='Laranja').first.screenshot(path=str(O / 'id07_sel.png'))
    ta = pg.locator('section.choice-builder textarea').first
    (O / 'pedido.txt').write_text(ta.input_value())
    ta.screenshot(path=str(O / 'pedido_box.png'))
    cp = pg.locator('section.choice-builder button', has_text='Copiar pedido de edição').first
    cp.screenshot(path=str(O / 'copy_btn.png'))
    cp.click(); pg.wait_for_timeout(600)
    pg.screenshot(path=str(O / 'after_copy2.png'))
    b.close()
print(sorted(x.name for x in O.iterdir()))
