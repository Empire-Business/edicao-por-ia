#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: narração de IA (−16 LUFS) + trilha + efeitos discretos. CTA=saiba (padrão) ou CTA=comment (teclas + pop no envio).
Trilha: Namoral 03 (jobs/criativo-namoral-03/renders/music-lyria-v1.mp3, gerada e paga antes; reuso sem custo). A troca de música é de
verdade: "Trilha 1" = abertura esparsa da faixa (0 s…) até o "Me fala." da música (T.mf3); ali entra a "Trilha 2" = retomada cheia da
faixa depois da pausa em ≈49–50 s (início ≈50,85 s cai no "fala."), com cruzamento de 0,12 s. As duas partes são niveladas entre si
(a 2 fica +1,5 dB) e o fundo sob a fala é calibrado em duas passadas para ≈ −35,5 LUFS (≈19,5 dB abaixo da voz); no CTA ≈ −21 LUFS.
Ganho do filtro volume = LINEAR. Saídas: renders/mix[-comment].wav, tmp/bg-stem[-comment].wav e analysis/mix_report[-comment].json."""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SFX = J.parent / 'material-compartilhado/audio/sfx'
MP = json.loads((J / 'analysis/motion_plan.json').read_text())
T = MP['T']; DUR = T['end']; SE = T['speechEnd']
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
BOFF = MP['music']['b_offset']
M = os.environ.get('CTA', 'saiba'); suf = '' if M == 'saiba' else '-' + M
TMP = J / 'tmp'; SR = 48000
X = 0.12


def run(a):
    subprocess.run([str(x) for x in a], check=True)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]), float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


# 1) edição da trilha: A (0 → mf3) + B (onset ≈ mf3 → fim), niveladas entre si
la, lb = T['mf3'] + X / 2, DUR - T['mf3'] + X / 2
pa, pb = TMP / 'mA.wav', TMP / 'mB.wav'
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-t', f'{la:.3f}', '-i', MUSIC, '-af', 'aformat=sample_rates=48000:channel_layouts=stereo', '-ar', SR, pa])
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{T["mf3"] + BOFF - X / 2:.3f}', '-t', f'{lb:.3f}', '-i', MUSIC, '-af', 'aformat=sample_rates=48000:channel_layouts=stereo', '-ar', SR, pb])
IA, _ = lufs(pa); IB, _ = lufs(pb)
gB = (IA - IB) + 1.5
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', pa, '-i', pb, '-filter_complex',
     f'[0:a]afade=t=in:d=0.2[a];[1:a]volume={gB:.2f}dB[b];[a][b]acrossfade=d={X}:c1=tri:c2=tri,afade=t=out:st={DUR - 1.4:.3f}:d=1.4,atrim=0:{DUR:.3f}[o]',
     '-map', '[o]', '-ar', SR, '-c:a', 'pcm_s16le', medit])
mI, _ = lufs(medit)

# 2) efeitos (tempo, arquivo, ganho dB)
cues = [(0.04, 'click', -33), (T['mf1'] - 0.03, 'swipe', -28), (T['mf1'] + 0.02, 'impact', -28), (T['mf1'] + 0.1, 'click', -28),
        (T['leg'] - 0.06, 'whoosh1', -35), (T['mf2'] + 0.02, 'pop', -26), (T['mf2'] + 0.04, 'impact', -30), (T['mf2'] + 0.1, 'click', -28),
        (T['mus'] - 0.06, 'whoosh1', -35), (T['mf3'] - 0.01, 'swipe', -29), (T['mf3'] + 0.03, 'impact', -29), (T['mf3'] + 0.1, 'click', -28),
        (T['cortez'] - 0.12, 'whoosh2', -31), (T['cortez'] + 0.2, 'shimmer', -35),
        (T['quantas'] + 0.12, 'click', -29), (T['quantas'] + 0.40, 'click', -30), (T['quantas'] + 0.68, 'click', -31),
        (T['esperar'] - 0.06, 'whoosh1', -32), (T['esperar'] + 0.36, 'impact', -32),
        (T['diasEnd'] - 0.2, 'swipe', -30), (T['diasEnd'] + 0.1, 'subdrop', -31), (SE + 0.05, 'whoosh1', -31)]
if M == 'saiba':
    cues.append((T['tap'], 'click', -20))
else:
    ts = SE + 1.75
    cues += [(ts + k * 0.1, 'click', -37) for k in range(6)] + [(T['tap'], 'pop', -27)]


def render(g_speech, g_cta):
    ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
    vol = f"if(lt(t,{SE - 0.1:.3f}),{ls_:.6f},if(lt(t,{SE + 0.6:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{SE - 0.1:.3f})/0.7,{lc_:.6f}))"
    inputs, fl = [], []
    for k, (t, name, gdb) in enumerate(cues):
        inputs += ['-i', SFX / f'{name}.wav']
        ms = max(0, int(round(t * 1000)))
        fl.append(f'[{k + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{k}]')
    n = len(cues)
    graph = ';'.join([f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]', '[v]asplit=2[vm][vsc]',
                      f"[1:a]volume='{vol}':eval=frame[mu]", '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]', *fl,
                      ''.join(f'[s{k}]' for k in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]', '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
                      f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
                      f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', J / 'renders/voice.wav', '-i', medit, *inputs, '-filter_complex', graph, '-map', '[pre]', '-ar', SR, '-c:a', 'pcm_s16le',
         TMP / f'mix-pre{suf}.wav', '-map', '[bg]', '-ar', SR, '-c:a', 'pcm_s16le', TMP / f'bg-stem{suf}.wav'])
    return lufs(TMP / f'bg-stem{suf}.wav', 0, SE)[0]


TARGET = -35.5
g_s, g_c = -28.0 - mI, -21.0 - mI
bg = render(g_s, g_c)
g_s += TARGET - bg
bg = render(g_s, g_c)
I0, _ = lufs(TMP / f'mix-pre{suf}.wav')
OUT = J / f'renders/mix{suf}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', TMP / f'mix-pre{suf}.wav', '-af', f'volume={-15.0 - I0:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', SR,
     '-c:a', 'pcm_s16le', OUT])
I1, P1 = lufs(OUT)
vI = lufs(J / 'renders/voice.wav')[0]
ctaI = lufs(TMP / f'bg-stem{suf}.wav', SE + 0.7, DUR - SE - 1.5)[0]
aI = lufs(TMP / f'bg-stem{suf}.wav', 0.3, T['mf3'] - 0.4)[0]; bI = lufs(TMP / f'bg-stem{suf}.wav', T['mf3'] + 0.2, SE - T['mf3'] - 0.3)[0]
rep = {'cta_mode': M, 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_edit': {'A_track_s': [0.0, round(la, 3)], 'B_track_s': [round(T['mf3'] + BOFF - X / 2, 3), round(T['mf3'] + BOFF - X / 2 + lb, 3)], 'switch_video_s': T['mf3'],
                      'B_level_vs_A_db': round(gB, 2)},
       'voice_lufs': vI, 'bg_stem_lufs_under_speech': bg, 'bg_stem_lufs_trilha1': aI, 'bg_stem_lufs_trilha2': bI, 'bg_stem_lufs_cta': ctaI,
       'music_gain_speech_db': round(g_s, 2), 'music_gain_cta_db': round(g_c, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{suf}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_speech': bg, 'bgA': aI, 'bgB': bI, 'bg_cta': ctaI, 'voice': vI}, ensure_ascii=False))
