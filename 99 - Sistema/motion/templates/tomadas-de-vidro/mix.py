#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz (tomada bruta real + narração de IA + frase limpa da entrega EXEMPLO_2) + trilha + efeitos sonoros.
Trilha: jobs/criativo-namoral-01/renders/music-lyria-v1.mp3 (Lyria, já gerada e paga pelo usuário; reuso sem custo; 77,7 s).
Arranjo próprio, num trecho pouco usado: a faixa entra do começo (0 s, abertura em fade: o gancho fica só com o som real da sala),
segue a parte A sob a narração; na frase da entrega EXEMPLO_2 ela abaixa mais (a entrega já tem a trilha dela); depois emenda na pausa da
faixa (22,74 s → silêncio quase total em "Ninguém vai saber… Só eu.") e a virada da faixa (25,5 s) cai exatamente no CTA.
(Usos anteriores desta faixa: EXEMPLO_3 3,0–40,2 e 71,4–77,7; EXEMPLO_4 41,6–69,3; EXEMPLO_5 39,4–74,2; EXEMPLO_6 16,7–51,7 e 71,4–76,0 — a faixa
inteira já foi usada; este arranjo é diferente: 0–19,9 + 22,7–30,3.)
Sob a narração ≈ 19,5 dB abaixo (fundo ≈ −35,5 LUFS) com compressão lateral pela voz; no CTA ≈ −20 LUFS. Ganho do filtro volume = LINEAR.
CTA=comment troca o clique do botão por teclas suaves + "pop" de enviar.
Saídas: renders/mix{-comment}.wav, tmp/bg-stem*.wav e analysis/mix_report*.json.
"""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
CTA = os.environ.get('CTA', 'saiba')
SUF = '' if CTA == 'saiba' else '-comment'
T = json.loads((J / f'analysis/motion_plan{SUF}.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
DROP = 25.5


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


J1 = round(T['eb1'] + 0.15, 3)                       # emenda logo depois da frase da entrega
Y = DROP - (T['cta0'] - J1)                          # a virada cai no CTA
XF = 0.3
pieces = [(0.0, J1 + XF), (Y, Y + DUR - J1 + 0.05)]
f = [f'[0:a]atrim=0:{J1 + XF:.3f},asetpts=PTS-STARTPTS[m0]',
     f'[0:a]atrim={Y:.3f}:{Y + DUR - J1 + 0.05:.3f},asetpts=PTS-STARTPTS[m1]',
     f'[m0][m1]acrossfade=d={XF}:c1=tri:c2=tri,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={DUR - 0.9:.3f}:d=0.9,atrim=0:{DUR:.3f}[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
# nível de referência: a parte A da faixa (3–19 s)
ref = TMP / 'music-ref.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(medit), '-ss', '3.5', '-t', '12', str(ref)])
mI, _ = lufs(ref)
g_speech = -31.0 - mI                 # antes da compressão lateral (que tira ~4–5 dB sob a fala)
g_cta = -20.5 - mI
lin = lambda db: 10 ** (db / 20)
ls_, lc_ = lin(g_speech), lin(g_cta)
le_ = lin(g_speech - 9.0)                            # sob a frase da entrega (que já tem trilha própria)
lb_ = lin(g_speech + 9.0)                            # pausa da faixa (muito baixa por natureza) em "Ninguém… Só eu."
e0, e1 = T['eb0'] - 0.15, T['eb1'] + 0.05
c0 = T['cta0'] - 0.25
vol = (f"if(lt(t,{e0:.3f}),{ls_:.6f},if(lt(t,{e0 + 0.3:.3f}),{ls_:.6f}+({le_ - ls_:.6f})*(t-{e0:.3f})/0.3,"
       f"if(lt(t,{e1:.3f}),{le_:.6f},if(lt(t,{c0:.3f}),{lb_:.6f},if(lt(t,{c0 + 0.5:.3f}),{lb_:.6f}+({lc_ - lb_:.6f})*(t-{c0:.3f})/0.5,{lc_:.6f})))))")

cues = [(T['travou'] - 0.02, 'click', -30), (T['gague'] - 0.1, 'whoosh1', -31), (T['repetiu'] + 0.05, 'whoosh3', -32),
        (T['relaxa'] - 0.05, 'subdrop', -33), (T['eu1'] + 0.3, 'shimmer', -34),
        (T['encontro'] - 0.02, 'pop', -33), (T['encontro'] + 0.36, 'pop', -33), (T['erros'] - 0.02, 'pop', -33),
        (T['tiro'] + 0.0, 'swipe', -30), (T['tiro'] + 0.08, 'swipe', -32), (T['tiro'] + 0.16, 'swipe', -33),
        (T['deixo'] + 0.1, 'whoosh2', -32), (T['melhor'] - 0.04, 'click', -30), (T['eb0'] - 0.2, 'whoosh1', -32),
        (T['ninguem'] - 0.1, 'subdrop', -31), (T['so'] - 0.03, 'shimmer', -35), (T['cta0'] - 0.1, 'whoosh2', -31)]
if CTA == 'saiba':
    cues += [(T['tap'], 'click', -21)]
else:
    k0 = T['cta0'] + 1.9
    cues += [(k0 + i * 0.13, 'click', -37) for i in range(6)] + [(T['tap'], 'pop', -26)]
inputs, fl = [], []
for k_, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k_ + 2}:a]volume={gdb}dB,adelay={ms}|{ms}[s{k_}]')
nc = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k_}]' for k_ in range(nc)) + f'amix=inputs={nc}:normalize=0:duration=longest[fx]',
    '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
    f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
    f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
pre = TMP / f'mix-pre{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(TMP / f'bg-stem{SUF}.wav')])
I0, P0 = lufs(pre)
g = -15.0 - I0
OUT = J / f'renders/mix{SUF}.wav'
for _ in range(3):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.79:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
    I1, P1 = lufs(OUT)
    if abs(I1 + 15.0) <= 0.3:
        break
    g += -15.0 - I1
se = T['speech_end']
bgI, _ = lufs(TMP / f'bg-stem{SUF}.wav')
# fundo sob a narração (exclui a frase da entrega, que traz a trilha dela)
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / f'bg-stem{SUF}.wav'), '-ss', f"{T['travou']:.3f}", '-t', f"{T['eb0'] - T['travou']:.3f}", str(TMP / f'bg-speech{SUF}.wav')])
bgS, _ = lufs(TMP / f'bg-speech{SUF}.wav')
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'cta': CTA, 'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI, 'qa_background_stem_lufs_under_narration': bgS,
       'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces_track_seconds': [[round(a, 3), round(b, 3)] for a, b in pieces], 'music_join_video_s': J1, 'music_drop_track_s': DROP,
       'music_drop_video_s': T['cta0'], 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_full': bgI, 'bg_narr': bgS, 'voice': vI, 'pieces': rep['music_pieces_track_seconds']}, ensure_ascii=False))
