#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros discretos.
Trilha: faixa instrumental já gerada e paga pelo usuário (Lyria; jobs/tutorial-cami/assets/music/lyria-1.mp3, ~60 BPM), reaproveitada
sem custo novo. Edição em três trechos com transição cruzada de 0,25 s nos tempos fortes:
A = 37,48–58,18 s da faixa (a subida de 42,2 s cai exatamente quando o áudio do Convidado começa a tocar);
B = 105,80–119,2 s (a subida de 107,07 s cai quando o Apresentador volta a falar); C = 169,2 s → fim da faixa no cartão final.
Sob a voz a trilha fica ~22 dB abaixo da fala (alvo −32 LUFS antes da compressão lateral pela voz → ≈ −37/−38 LUFS no resultado);
no CTA escrito ≈ −21 LUFS. O filtro volume com expressão usa ganho LINEAR. CTA=comment troca o clique do botão por teclas suaves + pop.
Saídas: renders/mix.wav (ou mix-comment.wav), tmp/bg-stem.wav, analysis/mix_report.json (ou _comment).
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
XF = 0.25


def run(a):
    subprocess.run(a, check=True)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


cut1 = T['muito']                        # A → B no "muito sinistro"
cut2 = T['speechEnd'] + 0.17             # B → C logo depois que a fala termina
pieces = [(42.215 - T['n0'], 0.0, cut1), (107.067 - (T['b0'] - cut1) - 0.0, cut1, cut2), (169.2, cut2, DUR)]
PGAIN = [-1.0, -3.0, 0.0]               # o trecho B da faixa é mais cheio: −3 dB para manter ~22 dB abaixo da fala do Apresentador
f, labs = [], []
for i, (src0, a, b) in enumerate(pieces):
    pre_ = XF if i > 0 else 0.0
    d = (b - a) + pre_ + (XF if i < len(pieces) - 1 else 0.0)
    s0 = src0 - pre_
    fo = f',afade=t=out:st={d - XF:.3f}:d={XF}' if i < len(pieces) - 1 else f',afade=t=out:st={d - 1.0:.3f}:d=1.0'
    fi = f',afade=t=in:d={XF}' if i > 0 else ',afade=t=in:d=0.02'
    ms = int(round((a - pre_) * 1000))
    f.append(f'[0:a]atrim={s0:.3f}:{s0 + d:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,volume={PGAIN[i]}dB{fi}{fo},adelay={ms}|{ms}[m{i}]')
    labs.append(f'[m{i}]')
f.append(''.join(labs) + f'amix=inputs={len(pieces)}:normalize=0:duration=longest,atrim=0:{DUR:.3f}[o]')
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -32.0 - mI
g_cta = -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(T['i0'] - 0.12, 'whoosh1', -32), (T['n0'] + 0.02, 'pop', -33), (T['craque'] - 0.08, 'whoosh2', -33), (T['prompt'] - 0.08, 'whoosh2', -34),
        (T['estilo'] - 0.12, 'swipe', -31), (T['cor'] + 0.05, 'shimmer', -34), (T['longo'] - 0.25, 'whoosh1', -31),
        (T['bom'] + 0.02, 'pop', -34), (T['sin'] - 0.02, 'whoosh3', -30), (T['sinw'] - 0.08, 'subdrop', -30), (T['b0'] - 0.05, 'swipe', -33),
        (se - 0.1, 'whoosh2', -30), (se + 0.8, 'pop', -34)]
cues += [(T['dez'] + i * 0.065, 'click', -39) for i in range(10)]
CTA_MODE = os.environ.get('CTA', 'saiba')
if CTA_MODE == 'comment':
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
rep = {'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI, 'qa_background_stem_lufs_under_speech': bgS,
       'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces': [{'track_start_s': round(p[0], 3), 'timeline': [round(p[1], 3), round(p[2], 3)], 'gain_db': PGAIN[i]} for i, p in enumerate(pieces)], 'crossfade_s': XF,
       'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2), 'cta_mode': CTA_MODE,
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / ('analysis/mix_report_comment.json' if CTA_MODE == 'comment' else 'analysis/mix_report.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'music_I_raw': mI, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI}, ensure_ascii=False))
