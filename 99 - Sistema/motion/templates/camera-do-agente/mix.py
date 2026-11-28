#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros discretos.
Trilha: faixa instrumental do criativo Namoral 01 (Lyria; gerada e paga antes pelo usuário — reuso sem custo; 100 BPM, pulso medido
0,5705 s com tempos em 47,04 + k·0,5705). Os cortes 1, 4 e 7 já usaram toda a faixa em outras montagens; aqui a virada da faixa
(25,8 s) cai exatamente no "Cortez" (feitos com o Cortez) e, no fim da fala, a faixa pula num tempo forte para o acorde final
(71,4 s →), que soa no cartão escrito. Sob a voz ≈ −32 LUFS antes da compressão lateral (≈ −37/−38 LUFS no resultado, ~22 dB abaixo
da fala); no CTA ≈ −21 LUFS. O filtro volume com expressão usa ganho LINEAR.
CTA=comment → variante "Comente CORTEZ": teclas suaves enquanto CORTEZ é digitado + pop no envio (no lugar do clique do botão).
Saídas: renders/mix.wav (ou mix-comment.wav), tmp/bg-stem*.wav, analysis/mix_report*.json."""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
CTA_MODE = os.environ.get('CTA', 'saiba')
SUF = '-comment' if CTA_MODE == 'comment' else ''
T = json.loads((J / f'analysis/motion_plan{SUF}.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
BEAT0, BEAT, DROP, FINAL = 47.04, 0.5705, 25.8, 71.4


def run(a):
    subprocess.run(a, check=True)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


OFFSET = DROP - T['reveal']
se = T['speechEnd']
k = round((OFFSET + se + 0.05 - BEAT0) / BEAT)
A_OUT = BEAT0 + k * BEAT
if A_OUT - OFFSET < se:
    A_OUT += BEAT
cut = A_OUT - OFFSET                       # tempo do vídeo em que a faixa pula para o acorde final
XF = 0.12
pieces = [(round(OFFSET, 3), round(A_OUT + XF, 3)), (FINAL, round(FINAL + DUR - cut + 0.05, 3))]
f = [f'[0:a]atrim={OFFSET:.3f}:{A_OUT + XF:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.3[m0]',
     f'[0:a]atrim={FINAL:.3f}:{FINAL + DUR - cut + 0.05:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[m1]',
     f'[m0][m1]acrossfade=d={XF}:c1=tri:c2=tri,afade=t=out:st={DUR - 0.9:.3f}:d=0.9,atrim=0:{DUR:.3f}[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -32.0 - mI
g_cta = -21.0 - mI
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(0.02, 'whoosh2', -32), (T['reveal'] - 0.12, 'shimmer', -31), (T['ele'] - 0.05, 'swipe', -30), (T['plat_tick'] - 0.05, 'click', -31),
        (T['print_tick'] - 0.01, 'click', -24), (T['grav1'], 'pop', -33), (T['fez'] + 0.2, 'whoosh1', -31), (T['prop'] - 0.05, 'shimmer', -33),
        (T['usando'] - 0.35, 'swipe', -31), (T['t03'] - 0.05, 'whoosh3', -31), (T['t03'] + 0.15, 'subdrop', -30),
        (T['negocio'] - 0.2, 'pop', -34), (T['site'] - 0.15, 'pop', -34), (T['ferr'] - 0.15, 'pop', -34), (T['soft'] - 0.15, 'pop', -34),
        (T['quem'] + 0.1, 'riser1', -36), (T['maravilha'] - 0.05, 'shimmer', -32), (se - 0.1, 'whoosh2', -30), (se + 0.25, 'subdrop', -29)]
if CTA_MODE == 'comment':
    cues += [(T['type0'] + i * 0.11, 'click', -36) for i in range(6)] + [(T['tap'], 'pop', -24)]
else:
    cues += [(T['tap'], 'click', -20)]
inputs, fl = [], []
for k_, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k_ + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{k_}]')
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
pre = TMP / f'mix-pre{SUF}.wav'
bg = TMP / f'bg-stem{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(bg)])
I0, P0 = lufs(pre)
g = -15.0 - I0
OUT = J / f'renders/mix{SUF}.wav'
for _ in range(3):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
    I1, P1 = lufs(OUT)
    if abs(I1 + 15.0) <= 0.2:
        break
    g += -15.0 - I1
bgI, _ = lufs(bg)
bgS, _ = lufs(bg, 0, se)
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'cta': CTA_MODE, 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces_track_seconds': pieces, 'music_jump_video_s': round(cut, 3), 'music_drop_video_s': T['reveal'],
       'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2), 'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI,
       'qa_background_stem_lufs_under_speech': bgS, 'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues],
       'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'music_I_raw': mI, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI, 'jump': round(cut, 3)}, ensure_ascii=False))
