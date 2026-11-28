#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros discretos.
Trilha: jobs/tutorial-cami/assets/music/lyria-3.mp3 (Lyria; gerada e paga antes pelo usuário — reuso sem custo; ≈95 BPM, compasso 2,527 s,
grade em 20,30 + k·0,6318). O EXEMPLO_2 usou 12,0–36,1 s e o final (168,8 s →); aqui entra o miolo da faixa: a parte cheia (≈78,6 s) sob o
gancho e as gavetas, a respiração (90–100 s) sob "repara… cenas na internet" e a volta da faixa (100,53 s, na grade) cai no "Já mostrei
vários resultados", quando as gavetas abrem em onda. No fim da fala a faixa pula num tempo da grade para o acento final (170,95 s),
que soa no cartão escrito. Sob a voz ≈ −32 LUFS antes da compressão lateral (≈ −37/−38 LUFS no resultado, ~22 dB abaixo da fala);
no CTA ≈ −21 LUFS. O filtro volume com expressão usa ganho LINEAR.
CTA=comment → variante "Comente CORTEZ": teclas suaves enquanto CORTEZ é digitado + pop no envio (no lugar do clique do botão).
Saídas: renders/mix.wav (ou mix-comment.wav), tmp/bg-stem*.wav, analysis/mix_report*.json."""
import json, math, os, subprocess
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
BEAT0, BEAT, DROP, END_HIT = 20.30, 2.527 / 4, 100.532, 170.95


def run(a):
    subprocess.run(a, check=True)


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    ls = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


OFFSET = DROP - (T['ja'] + 0.15)                 # a volta da faixa cai quando as gavetas começam a abrir em onda
se = T['speechEnd']
k = math.ceil((OFFSET + se + 0.08 - BEAT0) / BEAT)
A_OUT = BEAT0 + k * BEAT                            # emenda num tempo da grade logo depois da fala
cut = A_OUT - OFFSET                                # tempo do vídeo em que a faixa pula
want = T['cta0'] + 1.2                              # o acento final soa quando o botão/campo aparece
m = round((END_HIT - (want - cut) - BEAT0) / BEAT)
E0 = BEAT0 + m * BEAT
XF = 0.12
pieces = [(round(OFFSET, 3), round(A_OUT + XF, 3)), (round(E0, 3), round(E0 + DUR - cut + 0.05, 3))]
f = [f'[0:a]atrim={OFFSET:.3f}:{A_OUT + XF:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.25[m0]',
     f'[0:a]atrim={E0:.3f}:{E0 + DUR - cut + 0.05:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[m1]',
     f'[m0][m1]acrossfade=d={XF}:c1=tri:c2=tri,afade=t=out:st={DUR - 0.9:.3f}:d=0.9,atrim=0:{DUR:.3f}[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -32.0 - mI
g_cta = -21.0 - mI
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(0.02, 'whoosh2', -32), (T['ele1'] + 0.05, 'swipe', -31), (T['ele1'] + 0.15, 'click', -33), (T['noticias'] - 0.4, 'whoosh1', -33),
        (T['ele2'] + 0.2, 'swipe', -32), (T['prints'] - 0.2, 'whoosh1', -33), (T['t02'] + 0.3, 'swipe', -32),
        (T['genericas'] - 0.02, 'impact', -28), (T['imagens2'] - 0.02, 'impact', -26), (T['imagens2'] + 0.12, 'click', -31),
        (T['t03'], 'whoosh3', -31), (T['t03'] + 0.2, 'subdrop', -31),
        *[(T['animac'] + k_ * 0.17, 'pop', -35) for k_ in range(3)], *[(T['aleat'] + k_ * 0.13, 'swipe', -34) for k_ in range(3)],
        (T['aqui1'], 'whoosh2', -31), (T['pesquisas'] - 0.15, 'whoosh1', -33), (T['cenas'] + 0.05, 'swipe', -31), (T['internet'], 'shimmer', -33),
        (T['ja'] + 0.15, 'riser1', -35), (T['ja'] + 0.3, 'whoosh3', -31), (T['cortez'] - 0.1, 'shimmer', -30), (T['saiu'] - 0.1, 'whoosh2', -32),
        (se - 0.1, 'whoosh2', -30), (se + 0.25, 'subdrop', -29)]
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
       'music_pieces_track_seconds': pieces, 'music_jump_video_s': round(cut, 3), 'music_reentry_video_s': round(T['ja'] + 0.15, 3), 'music_end_hit_video_s': round(cut + END_HIT - E0, 3),
       'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2), 'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI,
       'qa_background_stem_lufs_under_speech': bgS, 'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues],
       'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'music_I_raw': mI, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI, 'jump': round(cut, 3)}, ensure_ascii=False))
