#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros discretos.
Trilha: faixa instrumental já gerada e paga pelo usuário para os criativos da Namoral (Lyria, ~100 BPM, compasso ≈ 2,415 s;
jobs/criativo-namoral-02/renders/music-lyria-v1.mp3), reaproveitada sem custo novo. Os cortes 3 (EXEMPLO_2) e 6 (EXEMPLO_3) usaram a parte
de 32 s em diante; aqui entra a ABERTURA da faixa, que eles não usaram: a subida inicial embaixo do gancho e a entrada cheia (4,5 s da faixa)
exatamente na pergunta do Apresentador; em 26,24 s a faixa volta 8 compassos (19,32 s, mesma fase) para cobrir a fala; o acorde final
(64,875 s da faixa) cai ~1,2 s depois do início do cartão final e decai até o fim.
Sob a voz a trilha fica ~22 dB abaixo da fala (compressão lateral pela voz; conferido no stem de fundo ≈ −37/−38 LUFS);
no CTA escrito ≈ −20 LUFS. O filtro volume com expressão usa ganho LINEAR. Saídas: renders/mix.wav (ou mix-comment.wav), tmp/bg-stem.wav, analysis/mix_report.json.
"""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
T = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000


def run(a):
    subprocess.run(a, check=True)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


BAR = 2.415
DROP = 4.5                                  # entrada cheia da faixa
OFF = DROP - T['q0']                        # a entrada cai na pergunta do Apresentador
J1 = DROP + 9 * BAR                         # 26,235 s: fim da frase de 9 compassos
J1v = J1 - OFF
B0 = J1 - 8 * BAR                           # volta 8 compassos (mesma fase)
B1 = B0 + 5 * BAR
C0 = 64.875                                 # acorde final da faixa
cv = J1v + (B1 - B0)                        # instante (vídeo) do acorde final
C1 = C0 + (DUR - cv) + 0.05
pieces = [(round(OFF, 3), round(J1, 3)), (round(B0, 3), round(B1, 3)), (C0, round(C1, 3))]
f = []
for i, (a, b) in enumerate(pieces):
    d = b - a
    f.append(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={0.02 if i else 0.3},afade=t=out:st={d - 0.03:.3f}:d=0.03[m{i}]')
f.append('[m0][m1][m2]concat=n=3:v=0:a=1,aformat=sample_rates=48000:channel_layouts=stereo,' + f'afade=t=out:st={DUR - 0.9:.3f}:d=0.9,atrim=0:{DUR:.3f}[o]')
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -31.5 - mI
g_cta = -20.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(T['nossa'] + 0.15, 'shimmer', -34), (T['q0'] - 0.3, 'whoosh1', -31), (T['t1'] - 0.1, 'swipe', -31), (T['postar'] + 0.02, 'pop', -29),
        (T['t2'] - 0.2, 'whoosh3', -32), (T['br'] - 0.05, 'whoosh2', -32), (T['pd'], 'swipe', -32)]
cues += [(T['varias'] + k * 0.12 + 1.2, 'pop', -36) for k in range(5)]
cues += [(T['pedi'] + 0.1, 'whoosh1', -32), (T['fez'] - 0.05, 'subdrop', -31), (T['fez'] + 0.05, 'swipe', -32), (T['muito'] + 0.1, 'shimmer', -31),
         (se - 0.1, 'whoosh2', -32)]
CTA_MODE = os.environ.get('CTA', 'saiba')
if CTA_MODE == 'comment':      # teclas suaves ao digitar CORTEZ + pop no envio (no lugar do clique do botão)
    cues += [(T['cta0'] + 1.6 + i * 0.1, 'click', -37) for i in range(6)] + [(T['tap'], 'pop', -25)]
else:
    cues += [(T['tap'], 'click', -20)]
inputs, fl = [], []
for k, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{k}]')
n = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k}]' for k in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]',
    '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
    f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
    f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
pre = TMP / 'mix-pre.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(TMP / 'bg-stem.wav')])
I0, P0 = lufs(pre)
g = -15.0 - I0
OUT = J / ('renders/mix-comment.wav' if CTA_MODE == 'comment' else 'renders/mix.wav')
for _ in range(3):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
    I1, P1 = lufs(OUT)
    if abs(I1 + 15.0) <= 0.2:
        break
    g += -15.0 - I1
bgI, _ = lufs(TMP / 'bg-stem.wav')
bgS, _ = lufs(TMP / 'bg-stem.wav', 0, se)
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'music_offset_s': round(OFF, 3), 'music_final_chord_video_s': round(cv, 3), 'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI, 'qa_background_stem_lufs_under_speech': bgS,
       'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces_track_seconds': pieces, 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / ('analysis/mix_report_comment.json' if CTA_MODE == 'comment' else 'analysis/mix_report.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'music_I_raw': mI, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI}, ensure_ascii=False))
