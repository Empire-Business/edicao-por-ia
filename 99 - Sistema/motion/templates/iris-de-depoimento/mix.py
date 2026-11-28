#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz (IA + Convidado, −16 LUFS) + trilha + poucos efeitos.
Trilha: faixa instrumental já gerada e paga pelo usuário para os motions (jobs/produto-gt3-motion/assets/audio/music.mp3, 87 s), sem custo novo.
Trecho DIFERENTE do EXEMPLO_2 (que usou 10,4–34 s da faixa): aqui 43–77 s — a pausa da faixa (48–50 s) cai em "…dizendo que sou bom. Mas é melhor…"
e a virada (50,5 s) cai na abertura da íris (o Convidado aparece). Sob a IA ≈ 19 dB abaixo da voz; sob o Convidado ≈ 22 dB abaixo; no CTA ≈ −21 LUFS;
compressão lateral pela voz. Volume com expressão = ganho LINEAR. CTA=comment troca o clique do botão por teclas suaves + pop no envio.
Saídas: renders/mix[-comment].wav, analysis/mix_report[-comment].json.
"""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
T = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
B = json.loads((J / 'edit/edl.json').read_text())
BLK = {}
for s in B['segments']:
    b = BLK.setdefault(s['take'], {'start': s['start'], 'end': 0}); b['end'] = s['start'] + (s['out'] - s['in'])
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
MODE = os.environ.get('CTA', 'saiba')
SUF = '' if MODE == 'saiba' else f'-{MODE}'


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


DROP_TRACK = 50.5
drop = T['open0'] + 0.6
off = DROP_TRACK - drop
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-af', f'atrim={off:.3f}:{off + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates={SR}:channel_layouts=stereo,'
     f'afade=t=in:d=0.35,afade=t=out:st={DUR - 1.3:.3f}:d=1.3', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_ai, g_jo, g_cta = -29.0 - mI, -33.0 - mI, -21.0 - mI
la, lj, lc = (10 ** (g / 20) for g in (g_ai, g_jo, g_cta))
j0, j1e, se = BLK['j1']['start'], BLK['j2']['end'], T['speechEnd']


def ramp(t0, d, a, b):
    return f"({a:.6f}+({b - a:.6f})*(t-{t0:.3f})/{d:.3f})"


# IA → Convidado (rampa 0,3 s) → IA → CTA (rampa 0,7 s)
vol = (f"if(lt(t,{j0 - 0.3:.3f}),{la:.6f},if(lt(t,{j0:.3f}),{ramp(j0 - 0.3, 0.3, la, lj)},"
       f"if(lt(t,{j1e:.3f}),{lj:.6f},if(lt(t,{j1e + 0.3:.3f}),{ramp(j1e, 0.3, lj, la)},"
       f"if(lt(t,{se - 0.1:.3f}),{la:.6f},if(lt(t,{se + 0.6:.3f}),{ramp(se - 0.1, 0.7, la, lc)},{lc:.6f}))))))")
cues = [(0.25, 'whoosh2', -32), (T['cards0'] + 0.05, 'swipe', -32), (T['open0'] + 0.1, 'shimmer', -31), (T['open1'] - 0.1, 'subdrop', -30),
        (T['arc0'] + 0.1, 'shimmer', -34), (T['close0'] + 0.05, 'whoosh1', -34), (T['dois'] - 0.02, 'click', -33), (T['reopen0'] + 0.05, 'shimmer', -33),
        (se + 0.15, 'subdrop', -28)] + [(T[k] - 0.03, 'click', -34) for k in ('rA0', 'rA1', 'rB0', 'rB1')]   # V2: obturador nas trocas para o Reel
if MODE == 'saiba':
    cues.append((T['tap'], 'click', -21))
else:
    ts = T['cta0'] + 1.6
    cues += [(ts + k * 0.1, 'click', -37) for k in range(6)] + [(T['tap'], 'pop', -27)]
inputs, fl = [], []
for k, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k + 2}:a]aformat=sample_rates={SR}:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{k}]')
n = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates={SR}:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k}]' for k in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]',
    '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
    f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
    f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
pre = TMP / f'mix-pre{SUF}.wav'; bgp = TMP / f'bg-stem{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(bgp)])
I0, _ = lufs(pre)
OUT = J / f'renders/mix{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={-15.0 - I0:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)


def part(src, a, b, name):
    p = TMP / f'{name}{SUF}.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', f'atrim={a:.3f}:{b:.3f},volume={-15.0 - I0:.2f}dB', str(p)])
    return lufs(p)[0]


rep_parts = {}
for nm, (a, b) in {'ia1': (0.0, j0 - 0.3), 'convidado': (j0, j1e), 'ia2': (j1e + 0.3, se)}.items():
    v = part(J / 'renders/voice.wav', a, b, f'v-{nm}'); m = part(bgp, a, b, f'bg-{nm}')
    rep_parts[nm] = {'voice_lufs': v, 'bg_lufs': m, 'gap_db': round(v - m, 1)}
bgI = part(bgp, 0.0, se, 'bg-speech'); vI = part(J / 'renders/voice.wav', 0.0, se, 'v-all')
rep = {'cta': MODE, 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_track_offset_s': round(off, 3), 'music_track_section_s': [round(off, 2), round(off + DUR, 2)], 'music_drop_video_s': round(drop, 3),
       'music_gain_ai_db': round(g_ai, 2), 'music_gain_convidado_db': round(g_jo, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR,
       'qa_voice_in_mix_lufs': vI, 'qa_background_under_speech_lufs': bgI, 'qa_voice_minus_bg_db': round(vI - bgI, 1), 'qa_parts': rep_parts}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_under_speech': bgI, 'gap_db': round(vI - bgI, 1), 'parts': rep_parts}, ensure_ascii=False))
