"""Shot plan (output seconds, 30 fps) shared by overlay and compositor. Adapted from video-4cb9c29dec82.
mode: split = media/graphic top (0-960), presenter below, captions on the seam
      full  = presenter full frame (zoom = punch-in), captions lower third
      cover = real video full screen (presenter hidden): blurred fill + sharp 16:9 band, captions lower third
      gfx   = full-screen motion graphic (presenter hidden)
video.crop = [x, y, w, h] in source pixels (removes watermarks / burned subtitles) before scaling."""
import json, os
V = os.path.dirname(os.path.abspath(__file__)); J = os.path.dirname(V)
M = json.load(open(os.path.join(J, 'edit', 'edit_map.json'), encoding='utf-8'))
SEG = {s['label']: s for s in M['segments']}
FPS = M['fps']; END = M['duration']
def st(l): return SEG[l]['start']
def en(l): return SEG[l]['end']
def w(l, word, k=0):
    hits = [x for x in SEG[l]['words'] if x['w'].lower().strip('.,:?!').startswith(word.lower())]
    return hits[k]['s']
def f(t): return round(t * FPS) / FPS
P_ = {(p['label'], p['part']): p['out_start'] for p in M['pieces']}

# v9 (2026-10-02): all inserted media re-sourced in HD (assets/hd/, via ScrapeCreators search + yt-dlp), see edit/decision_log.md.
# split top = video only (or the PT headline with highlighter); horizontal media -> 'card' (black frame, rounded video card, ref. image 2).
HD = 'assets/hd/'
WALK = dict(file=HD + 'yt-ikea-walk4k.mp4', crop=[0, 0, 1920, 1080])        # IKEA facade (clean window 3.8-5.0 s, overlay after)
LON = dict(file=HD + 'yt-ikea-london4k.mp4', crop=[0, 100, 1920, 980])   # top info icon cropped       # walking into the store
CCB = dict(file=HD + 'yt-callcenter-b.mp4', crop=[0, 0, 1920, 1012])        # row of agents with headsets (stock)
CCA = dict(file=HD + 'yt-callcenter-a.mp4', crop=[0, 0, 1920, 1012])        # call-centre team (stock)
UPA = dict(file=HD + 'yt-upintheair-trailer.mp4', crop=[0, 22, 1920, 1036])  # 1080p trailer
UAE = dict(file=HD + 'yt-ikea-uae-makeover.mp4', crop=[0, 0, 1920, 1080])   # IKEA UAE official: interior design service
ROB = dict(file=HD + 'yt-irobot-rogue.mp4', crop=[0, 130, 1920, 800])       # letterbox + Movieclips mark removed
KRE = dict(file=HD + 'yt-ikea-kreativ-in.mp4', crop=[0, 0, 1920, 1080])   # v10: IKEA India official, Kreativ AI (scan 3.84-7.37, planner UI 12.61-17.75)
STR = dict(file=HD + 'yt-strike-nbc.mp4', crop=[0, 0, 1920, 912])          # v10: NBC News SAG-AFTRA/WGA strike (AI protections); lower-third chyron cropped
CLK = dict(file=HD + 'yt-click-remote.mp4', crop=[0, 0, 1920, 1080])       # v10: Click (2006) universal remote menu (continuous 66.94-81.54)
AMZ = dict(file=HD + 'yt-amazon-robots.mp4', crop=[0, 0, 1920, 1080])     # v11: Amazon Kiva robots (clean windows 148.7-154.8, 214.7-219.8)
CHA = dict(file=HD + 'yt-chaplin-factory.mp4', crop=[316, 0, 1286, 900])    # pillarbox + bottom copyright line removed
shots = [
 dict(t0=0, t1=P_[('hook', 1)], mode='split', top='video', video=dict(WALK, src=3.9)),
 dict(t0=P_[('hook', 1)], t1=P_[('hook', 2)], mode='split', top='video', video=dict(KRE, src=4.6)),
 dict(t0=P_[('hook', 2)], t1=en('hook'), mode='split', top='video', video=dict(KRE, src=18.6)),
 dict(t0=st('fatur'), t1=en('fatur'), mode='split', top='g_fatur'),
 # trailer shots (scene cuts measured with scdet): Clooney firing 26.15-26.82 / Galifianakis 28.61-29.95 / Simmons 29.95-30.99
 dict(t0=st('demitiu'), t1=8.45, mode='card', video=dict(UPA, src=26.17)),
 dict(t0=8.45, t1=9.78, mode='card', video=dict(UPA, src=28.63), emph='zero', emph_from=w('demitiu', 'não') - .06),
 dict(t0=9.78, t1=en('demitiu'), mode='card', video=dict(UPA, src=29.97), emph='zero', emph_from=w('demitiu', 'não') - .06),
 # IKEA UAE: co-worker walks clients in (50.96-52.21), co-worker presents a wardrobe (52.21-55.92), design consultation at the table (31.12-32.58)
 dict(t0=st('realocou'), t1=w('realocou', 'realocaram'), mode='card', video=dict(UAE, src=50.98)),
 dict(t0=w('realocou', 'realocaram'), t1=w('realocou', 'consultoria') - .2, mode='card', video=dict(UAE, src=52.24)),
 dict(t0=w('realocou', 'consultoria') - .2, t1=en('realocou'), mode='card', video=dict(UAE, src=31.14)),
 dict(t0=st('ponto'), t1=en('ponto'), mode='full', zoom=1.62, emph='ponto', emph_from=w('ponto', 'um') - .06),
 # v12: same I, Robot excerpt split on its own cuts (scdet 46.71/48.30/49.72/50.93/51.97), each framed on the faces (fx = horizontal focus)
 dict(t0=st('manda'), t1=17.6, mode='split', top='video', video=dict(ROB, src=48.33, fx=0.60)),            # Will Smith close-up
 dict(t0=17.6, t1=w('manda', 'medo') - .1, mode='split', top='video', video=dict(ROB, src=49.75, fx=0.36)),  # Will among the NS-5s
 dict(t0=w('manda', 'medo') - .1, t1=19.75, mode='split', top='video', video=dict(ROB, src=46.74, fx=0.60)), # robots staring (on "medo")
 dict(t0=19.75, t1=en('manda'), mode='split', top='video', video=dict(ROB, src=52.0, fx=0.42)),            # overhead, Will in the crowd
 dict(t0=st('vantagem'), t1=22.1, mode='split', top='video', video=dict(AMZ, src=150.0)),
 dict(t0=22.1, t1=w('vantagem', 'para'), mode='split', top='video', video=dict(AMZ, src=155.6, fx=0.8)),   # v12: operator at the laptop among the robots (user: show people)
 dict(t0=w('vantagem', 'para'), t1=en('vantagem'), mode='full', zoom=1.3, emph='valor', emph_from=w('vantagem', 'que', 2) - .06),
 dict(t0=st('pergunta'), t1=w('pergunta', 'quantas') - .05, mode='full', zoom=1.3),
 dict(t0=w('pergunta', 'quantas') - .05, t1=en('pergunta'), mode='gfx', top='g_pergunta'),
 dict(t0=st('cta1'), t1=en('cta1'), mode='full', zoom=1.3),
 dict(t0=st('cta2'), t1=P_[('cta2', 3)], mode='full', zoom=1.3, emph='comente', emph_from=st('cta2') - .04, emph_to=P_[('cta2', 1)] + 1.5),
 dict(t0=P_[('cta2', 3)], t1=END, mode='full', zoom=1.3, emph='ganhos', emph_from=w('cta2', 'mais') - .3),
]
for s in shots:
    s['t0'] = f(s['t0']); s['t1'] = f(s['t1'])
    for k in ('emph_from', 'emph_to'):
        if k in s: s[k] = round(s[k], 3)
for a, b in zip(shots, shots[1:]):
    assert abs(a['t1'] - b['t0']) < 1e-6, (a, b)
anchors = {
 'ikea': w('hook', 'ikea'), 'agente': w('hook', 'agente'), 'ia': w('hook', 'ia'), 'trabalho': w('hook', 'trabalho'), 'n8500': w('hook', '8.500'), 'pessoas': w('hook', 'pessoas'),
 'faturamento': w('fatur', 'faturamento'), 'v14': w('fatur', '1,4'), 'dolares': w('fatur', 'dólares'),
 'nao': w('demitiu', 'não'), 'ninguem': w('demitiu', 'ninguém'),
 'realocaram': w('realocou', 'realocaram'), 'vendas': w('realocou', 'vendas'), 'consultoria': w('realocou', 'consultoria'),
 'ponto': w('ponto', 'ponto'), 'medo': w('manda', 'medo'),
 'liberar': w('vantagem', 'liberar'), 'tempo': w('vantagem', 'tempo'), 'atividades': w('vantagem', 'atividades'), 'valor': w('vantagem', 'valor'),
 'quantas': w('pergunta', 'quantas'), 'substituir': w('pergunta', 'substituir'), 'mas': w('pergunta', 'mas'), 'quanto': w('pergunta', 'quanto'),
 'valor2': w('pergunta', 'valor'), 'gerar': w('pergunta', 'gerar'),
 'comente': w('cta2', 'comente'), 'aqui': w('cta2', 'aqui'), 'ia': w('cta2', '"ia'), 'relatorio': w('cta2', 'relatório'), 'receita': w('cta2', 'receita'), 'mais2': w('cta2', 'mais'), 'menos': w('cta2', 'menos'), 'melhorar': w('cta2', 'melhorar'), 'custos': w('cta2', 'custos'), 'entrega': w('cta2', 'entrega'),
}
# v7 multicam: camera 2 (C0052, side angle, synced +6.228 s, muted, same grade) at existing cut points / section changes.
# Opening stays on the frontal camera; B = side angle. Each entry = camera from t onward.
P = {(p['label'], p['part']): p['out_start'] for p in M['pieces']}
cams = [[0.0, 'A'], [P[('hook', 2)], 'B'], [st('fatur'), 'A'], [st('ponto'), 'B'], [st('manda'), 'A'],
        [st('vantagem'), 'B'], [w('vantagem', 'para'), 'A'], [P[('vantagem', 1)], 'B'], [st('pergunta'), 'A'],
        [P[('cta1', 2)], 'B'], [st('cta2'), 'A'], [P[('cta2', 2)], 'B'], [P[('cta2', 4)], 'A']]
cams = [[f(t), c] for t, c in cams]
json.dump({'fps': FPS, 'duration': END, 'shots': shots, 'anchors': anchors, 'cams': cams,
           'captions': [{'label': s['label'], 'words': s['words'], 'end': s['end']} for s in M['segments']]},
          open(os.path.join(V, 'layout.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(shots), 'shots', END)

