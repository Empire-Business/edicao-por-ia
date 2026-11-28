# MODELO F44 Cordilheira de Cortes: arquivo derivado do criativo de exemplo; textos, tempos, falas, provas e caminhos são do exemplo e devem ser trocados.
"""Fechamento do EXEMPLO_1 em duas versões (jobs/material-compartilhado/CTA_COMENTE_CORTEZ.md).
CTA=saiba (padrão): botão azul de ação da ID03 "Saiba mais →" com toque do cursor.
CTA=comment: "Comente CORTEZ" (CORTEZ no azul da ID03) com balão de comentário, campo onde CORTEZ é digitado e enviado e a linha
"aqui nos comentários" com seta desenhada. Sem promessa de link ou brinde."""
import os

WORD = 'CORTEZ'
GOLD, INK, NAVY, CARD, MUTED, ACT, ACT_L, ACT_T = '#4A92E6', '#F2F6FC', '#0C1118', '#172333', '#9AA8B8', '#4A92E6', '#7FB4F2', '#FFFFFF'


def mode():
    m = os.environ.get('CTA', 'saiba')
    assert m in ('saiba', 'comment'), m
    return m


def layout(m):
    # cartão do vídeo final no CTA (escala, deslocamento vertical, raio antes da escala) e topo do bloco de ação
    return ({}, 1250) if m == 'saiba' else ({}, 1170)


def snippets(m, top):
    if m == 'saiba':
        tl = (f"  tl.fromTo('#btn',{{opacity:0,y:40}},{{opacity:1,y:0,duration:.6,ease:'power3.out',immediateRender:false}},T.cta0+1.15);\n"
              f"  tl.fromTo('#cursor',{{opacity:0,x:820,y:{top + 330}}},{{opacity:1,x:600,y:{top + 62},duration:.8,ease:'power2.inOut',immediateRender:false}},T.tap-.85);\n"
              f"  tl.to('#btn',{{scale:.95,duration:.09,yoyo:true,repeat:1,ease:'power2.out'}},T.tap-.02);\n"
              f"  tl.to('#cursor',{{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'}},T.tap-.02);\n"
              f"  tl.to('#cursor',{{x:660,y:{top + 170},opacity:0,duration:.6,ease:'power2.in'}},T.tap+.5);")
        return {'CTA_CSS': '', 'CTA_HTML': '<div id="btn">Saiba mais <span>→</span></div>', 'CTA_TL': tl}
    ft, sx, sy = top + 150, 832, top + 196
    css = f'''
#cmain {{ position:absolute; left:0; right:0; top:{top}px; height:116px; z-index:10; opacity:0; display:flex; justify-content:center; }}
#cmain .pl {{ display:flex; align-items:center; gap:20px; height:116px; padding:0 56px 0 44px; border-radius:999px; background:{CARD}; border:3px solid {GOLD}; color:{INK};
  font-weight:700; font-size:48px; letter-spacing:-.01em; white-space:nowrap; box-shadow:0 24px 60px rgba(2,4,4,.6); }}
#cmain .pl b {{ font-weight:800; letter-spacing:.03em; color:{GOLD}; }}
#cmain svg {{ width:56px; height:56px; flex:none; }}
#cfield {{ position:absolute; left:170px; width:740px; top:{ft}px; height:104px; z-index:10; opacity:0; border-radius:999px;
  background:rgba(23,35,51,.94); border:2px solid rgba(154,168,184,.35); display:flex; align-items:center; padding:0 16px 0 44px; }}
#cfield .tx {{ flex:1; display:flex; align-items:center; font-size:40px; white-space:nowrap; overflow:hidden; height:60px; }}
#ctyped {{ display:inline-block; color:{INK}; font-weight:700; letter-spacing:.04em; }}
#ctyped .tl {{ display:none; }}
#ccaret {{ display:inline-block; width:3px; height:46px; margin:0 6px 0 3px; background:{GOLD}; flex:none; }}
#cph {{ color:{MUTED}; font-weight:400; }}
#csend {{ flex:none; width:72px; height:72px; border-radius:50%; background:linear-gradient(180deg,{ACT_L},{ACT}); display:flex; align-items:center; justify-content:center; }}
#csend svg {{ width:36px; height:36px; }}
#chint {{ position:absolute; left:0; right:0; top:{ft + 124}px; z-index:10; opacity:0; display:flex; justify-content:center; align-items:center; gap:12px;
  font-weight:700; font-size:26px; letter-spacing:.16em; text-transform:uppercase; color:{MUTED}; }}
#chint svg {{ width:26px; height:30px; }}'''
    letters = ''.join(f'<span class="tl" id="tc{k}">{c}</span>' for k, c in enumerate(WORD))
    html_ = (f'<div id="cmain"><div class="pl"><svg viewBox="0 0 56 56"><path d="M28 8C16 8 6 16.2 6 26.4c0 5.4 2.8 10.3 7.3 13.6L11.7 48.6l9.6-5.1c2.1.5 4.3.8 6.7.8 '
             f'12 0 22-8.2 22-18.4S40 8 28 8Z" fill="none" stroke="{GOLD}" stroke-width="4" stroke-linejoin="round"/><circle cx="19" cy="26.5" r="2.8" fill="{GOLD}"/>'
             f'<circle cx="28" cy="26.5" r="2.8" fill="{GOLD}"/><circle cx="37" cy="26.5" r="2.8" fill="{GOLD}"/></svg>Comente <b>{WORD}</b></div></div>\n'
             f'  <div id="cfield"><div class="tx"><span id="ctyped">{letters}</span><span id="ccaret"></span><span id="cph">Adicione um comentário…</span></div>'
             f'<div id="csend"><svg viewBox="0 0 36 36"><path d="M18 30V7M8 16l10-10 10 10" fill="none" stroke="{ACT_T}" stroke-width="4.5" stroke-linecap="round" '
             f'stroke-linejoin="round"/></svg></div></div>\n'
             f'  <div id="chint">aqui nos comentários<svg viewBox="0 0 26 30"><path d="M13 3v22M4 16l9 9 9-9" fill="none" stroke="{GOLD}" stroke-width="3.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
    tl = f'''  tl.fromTo('#cmain',{{opacity:0,y:40}},{{opacity:1,y:0,duration:.6,ease:'power3.out',immediateRender:false}},T.cta0+1.1);
  tl.fromTo('#cfield',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,ease:'power3.out',immediateRender:false}},T.cta0+1.35);
  tl.fromTo('#chint',{{opacity:0}},{{opacity:1,duration:.4,immediateRender:false}},T.cta0+1.6);
  {{ const ts=T.cta0+1.75;
    for(let t=T.cta0+1.35,k=0;t<T.end;t+=.27,k++){{ tl.set('#ccaret',{{opacity:(t>ts-.05&&t<T.tap+.3)?1:(k%2?0:1)}},t); }}
    tl.set('#cph',{{display:'none'}},ts);
    '{WORD}'.split('').forEach((c,k)=>tl.set('#tc'+k,{{display:'inline'}},ts+k*.1));
    tl.fromTo('#cursor',{{opacity:0,x:930,y:{top + 420}}},{{opacity:1,x:{sx},y:{sy},duration:.8,ease:'power2.inOut',immediateRender:false}},T.tap-.85);
    tl.to('#csend',{{scale:.86,duration:.09,yoyo:true,repeat:1,ease:'power2.out'}},T.tap-.02);
    tl.to('#cursor',{{scale:.86,duration:.09,yoyo:true,repeat:1,transformOrigin:'20% 10%'}},T.tap-.02);
    tl.to('#ctyped',{{y:-36,opacity:0,duration:.3,ease:'power2.in'}},T.tap+.06);
    tl.set('#ctyped',{{display:'none'}},T.tap+.38); tl.set('#cph',{{display:'inline'}},T.tap+.4);
    tl.to('#cmain .pl',{{scale:1.04,duration:.14,yoyo:true,repeat:1,ease:'power2.out'}},T.tap+.12);
    tl.to('#cursor',{{x:{sx + 60},y:{sy + 110},opacity:0,duration:.6,ease:'power2.in'}},T.tap+.5); }}'''
    return {'CTA_CSS': css, 'CTA_HTML': html_, 'CTA_TL': tl}
