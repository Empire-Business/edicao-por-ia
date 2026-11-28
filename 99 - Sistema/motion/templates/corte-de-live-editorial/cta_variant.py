# MODELO F23 Corte de Live Editorial: arquivo derivado do criativo de exemplo; textos, tempos, falas, provas e caminhos são do exemplo e devem ser trocados.
"""Variante de CTA do fechamento (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md).
CTA=saiba (padrão) devolve os trechos originais do "Saiba mais →" (saída idêntica à aprovada);
CTA=comment troca o botão por "Comente CORTEZ" com campo de comentário em que CORTEZ é digitado e enviado."""
import json, os
from pathlib import Path

WORD = 'CORTEZ'


def snippets(src_dir, top, acc, dark, light_rgb, muted, font, typed_weight):
    mode = os.environ.get('CTA', 'saiba')
    if mode == 'saiba':
        return mode, json.loads((Path(src_dir) / 'cta_saiba.json').read_text())
    assert mode == 'comment', mode
    ft, sx, sy = top + 152, 840, top + 198            # campo; ponta do cursor no centro do botão de enviar (856, top+204)
    css = f'''
#cmain {{ position:absolute; left:0; right:0; top:{top}px; height:116px; z-index:10; opacity:0; display:flex; justify-content:center; }}
#cmain .pl {{ display:flex; align-items:center; gap:20px; height:116px; padding:0 56px 0 44px; border-radius:999px; background:{acc}; color:{dark};
  font-family:{font}; font-weight:600; font-size:46px; letter-spacing:-.01em; white-space:nowrap; box-shadow:0 24px 60px rgba(0,0,0,.55); }}
#cmain .pl b {{ font-weight:800; letter-spacing:.03em; }}
#cmain svg {{ width:54px; height:54px; flex:none; }}
#cfield {{ position:absolute; left:170px; width:740px; top:{ft}px; height:104px; z-index:10; opacity:0; box-sizing:border-box; border-radius:999px;
  background:rgba(255,255,255,.05); border:2px solid rgba({light_rgb},.22); display:flex; align-items:center; padding:0 16px 0 44px; }}
#cfield .tx {{ flex:1; display:flex; align-items:center; font-family:{font}; font-size:40px; white-space:nowrap; overflow:hidden; height:60px; }}
#ctyped {{ display:inline-block; color:rgb({light_rgb}); font-weight:{typed_weight}; letter-spacing:.04em; }}
#ctyped .tl {{ display:none; }}
#ccaret {{ display:inline-block; width:3px; height:46px; margin:0 6px 0 3px; background:{acc}; flex:none; }}
#cph {{ color:{muted}; font-weight:400; }}
#csend {{ flex:none; width:72px; height:72px; border-radius:50%; background:{acc}; display:flex; align-items:center; justify-content:center; }}
#csend svg {{ width:36px; height:36px; }}'''
    letters = ''.join(f'<span class="tl" id="tc{k}">{c}</span>' for k, c in enumerate(WORD))
    html_ = (f'<div id="cmain"><div class="pl"><svg viewBox="0 0 54 54"><path d="M27 8C15.4 8 6 15.9 6 25.6c0 5.2 2.7 9.9 7 13.1L11.5 47l9.2-4.9c2 .5 4.1.7 6.3.7 '
             f'11.6 0 21-7.9 21-17.6S38.6 8 27 8Z" fill="none" stroke="{dark}" stroke-width="4" stroke-linejoin="round"/></svg>Comente <b>{WORD}</b></div></div>\n'
             f'  <div id="cfield"><div class="tx"><span id="ctyped">{letters}</span><span id="ccaret"></span><span id="cph">Adicione um comentário…</span></div>'
             f'<div id="csend"><svg viewBox="0 0 36 36"><path d="M18 30V7M8 16l10-10 10 10" fill="none" stroke="{dark}" stroke-width="4.5" stroke-linecap="round" '
             f'stroke-linejoin="round"/></svg></div></div>')
    tl = f'''  tl.fromTo('#cmain',{{opacity:0,y:40}},{{opacity:1,y:0,duration:.6,ease:'power3.out',immediateRender:false}},T.cta0+1.05);
  tl.fromTo('#cfield',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,ease:'power3.out',immediateRender:false}},T.cta0+1.3);
  {{ const ts=T.cta0+1.6, te=ts+{len(WORD) - 1}*.1;
    for(let t=T.cta0+1.3,k=0;t<T.end;t+=.27,k++){{ tl.set('#ccaret',{{opacity:(t>ts-.05&&t<T.tap+.3)?1:(k%2?0:1)}},t); }}
    tl.set('#cph',{{display:'none'}},ts);
    '{WORD}'.split('').forEach((c,k)=>tl.set('#tc'+k,{{display:'inline'}},ts+k*.1));
    tl.fromTo('#cursor',{{opacity:0,x:930,y:{top + 420}}},{{opacity:1,x:{sx},y:{sy},duration:.8,ease:'power2.inOut',immediateRender:false}},T.tap-.85);
    tl.to('#csend',{{scale:.86,duration:.09,yoyo:true,repeat:1,ease:'power2.out'}},T.tap-.02);
    tl.to('#cursor',{{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'}},T.tap-.02);
    tl.to('#ctyped',{{y:-36,opacity:0,duration:.3,ease:'power2.in'}},T.tap+.06);
    tl.set('#ctyped',{{display:'none'}},T.tap+.38); tl.set('#cph',{{display:'inline'}},T.tap+.4);
    tl.to('#cmain .pl',{{scale:1.04,duration:.14,yoyo:true,repeat:1,ease:'power2.out'}},T.tap+.12);
    tl.to('#cursor',{{x:{sx + 60},y:{sy + 110},opacity:0,duration:.6,ease:'power2.in'}},T.tap+.5); }}'''
    return mode, {'CTA_CSS': css, 'CTA_HTML': html_, 'CTA_TL': tl}
