#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros.
Trilha: faixa instrumental do criativo Namoral 03 (Lyria, já gerada e paga pelo usuário; reuso sem custo; 104 BPM, compasso 2,307 s).
O EXEMPLO_2 usou a 1ª virada (31,8 s). Aqui: trecho 42–50 s (energia da 1ª parte) com a pausa curta da faixa (48,5–50,3 s) caindo no
"e fica de qualquer jeito" e a 2ª virada (≈50,4 s) cravada no "Aqui não"; no fim da fala, emenda num tempo forte para o final
da faixa (78,1 s → acorde final), já no CTA escrito. Sob a voz ≈ 22 dB abaixo da fala (fundo ≈ −38 LUFS) com compressão lateral
pela voz; no CTA ≈ −20 LUFS. Ganho do filtro volume com expressão = LINEAR.
Saídas: renders/mix.wav, tmp/bg-stem.wav e analysis/mix_report.json.
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
import os
CTA = os.environ.get('CTA', 'saiba')
SUF = '' if CTA == 'saiba' else '-comment'
T = json.loads((J / f'analysis/motion_plan{SUF}.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
BAR = 60 / 104.05 * 4


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


DROP = 50.40
OFF = DROP - T['nao']                    # a virada cai no "não"
se = T['speechEnd']
k = 1
while T['nao'] + k * BAR < se + 0.15:     # emenda no 1º tempo forte depois do fim da fala
    k += 1
cut = T['nao'] + k * BAR
END0 = 80.39 - BAR                       # 1 compasso antes do final da faixa
pieces = [(OFF, OFF + cut), (END0, END0 + (DUR - cut) + 0.05)]
f = []
for i, (a, b) in enumerate(pieces):
    d = b - a
    f.append(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={0.25 if i == 0 else 0.02},afade=t=out:st={d - 0.03:.3f}:d=0.03[m{i}]')
f.append('[m0][m1]concat=n=2:v=0:a=1,aformat=sample_rates=48000:channel_layouts=stereo,' + f'afade=t=out:st={DUR - 1.2:.3f}:d=1.2,atrim=0:{DUR:.3f}[o]')
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -32.0 - mI
g_cta = -20.0 - mI
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(T['rolar'] - 0.05, 'swipe', -31), (T['inund'] - 0.1, 'whoosh1', -31),
        (T['aqui'] - 0.25, 'whoosh2', -29), (T['nao'], 'impact', -27), (T['nao'] + 0.05, 'subdrop', -27), (T['nao'] + 0.45, 'shimmer', -33),
        (T['type0'] - 0.45, 'whoosh1', -31), (T['type0'] + 0.1, 'click', -31), (T['cenas'], 'pop', -31), (T['pick'], 'click', -27),
        (T['fly0'] + 0.1, 'whoosh3', -30), (T['land'], 'pop', -29), (T['full'] - 0.35, 'whoosh2', -30),
        (se - 0.2, 'whoosh1', -31), (se + 0.15, 'subdrop', -28)] + \
       ([(T['tap'], 'click', -20)] if CTA == 'saiba' else [(T['tap'], 'pop', -25)])   # variante comentário: "enviar" = pop suave
inputs, fl = [], []
for k_, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k_ + 2}:a]volume={gdb}dB,adelay={ms}|{ms}[s{k_}]')
n = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k_}]' for k_ in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]',
    '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
    f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
    f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
pre = TMP / 'mix-pre.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(TMP / f'bg-stem{SUF}.wav')])
I0, P0 = lufs(pre)
g = -15.0 - I0
OUT = J / f'renders/mix{SUF}.wav'
for _ in range(3):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
    I1, P1 = lufs(OUT)
    if abs(I1 + 15.0) <= 0.3:
        break
    g += -15.0 - I1
bgI, _ = lufs(TMP / f'bg-stem{SUF}.wav')
# fundo só no trecho com fala (o que importa para a inteligibilidade)
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / f'bg-stem{SUF}.wav'), '-t', f'{se:.3f}', str(TMP / f'bg-speech{SUF}.wav')])
bgS, _ = lufs(TMP / f'bg-speech{SUF}.wav')
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI, 'qa_background_stem_lufs_under_speech': bgS,
       'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces_track_seconds': [[round(a, 3), round(b, 3)] for a, b in pieces], 'music_drop_track_s': DROP, 'music_drop_video_s': T['nao'],
       'music_join_video_s': round(cut, 3), 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI, 'pieces': rep['music_pieces_track_seconds']}, ensure_ascii=False))
