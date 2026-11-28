#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: narração de IA (−16 LUFS) + trilha + efeitos discretos.
Trilha: faixa instrumental já gerada e paga pelo usuário para os motions (jobs/produto-gt3-motion/assets/audio/music.mp3, 87 s), sem custo
novo, desde o começo da faixa (0 s): a batida que volta em 16,8 s da faixa cai exatamente no "Ou nem isso". Durante o "Você só grava" a
trilha fica abafada (passa-baixa) e abre na batida. Sob a narração ≈ 19 dB abaixo da voz, com compressão lateral pela voz; no CTA ≈ −21 LUFS.
CTA=comment troca o clique do botão por teclas suaves + pop no envio. Saídas: renders/mix[-comment].wav, analysis/mix_report[-comment].json.
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
MODE = os.environ.get('CTA', 'saiba')
SUF = '' if MODE == 'saiba' else f'-{MODE}'


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]), float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


off = max(0.0, T['musicOff']); pad = max(0.0, -T['musicOff'])
m0, m1 = T['rec0'] - 0.3, T['ou'] - 0.03          # trecho abafado
xf = 0.3
medit = TMP / 'music-edit.wav'
graph = (f"[0:a]atrim={off:.3f}:{off + DUR:.3f},asetpts=PTS-STARTPTS,adelay={int(pad * 1000)}|{int(pad * 1000)},aformat=sample_rates={SR}:channel_layouts=stereo,asplit=2[a][b];"
         f"[a]lowpass=f=700,lowpass=f=700,volume='if(lt(t,{m0:.3f}),0,if(lt(t,{m0 + xf:.3f}),(t-{m0:.3f})/{xf},if(lt(t,{m1:.3f}),1,if(lt(t,{m1 + .06:.3f}),({m1 + .06:.3f}-t)/.06,0))))':eval=frame[lo];"
         f"[b]volume='if(lt(t,{m0:.3f}),1,if(lt(t,{m0 + xf:.3f}),({m0 + xf:.3f}-t)/{xf},if(lt(t,{m1:.3f}),0,if(lt(t,{m1 + .06:.3f}),(t-{m1:.3f})/.06,1))))':eval=frame[hi];"
         f"[lo][hi]amix=inputs=2:normalize=0,afade=t=in:d=0.25,afade=t=out:st={DUR - 1.2:.3f}:d=1.2,atrim=0:{DUR:.3f}[o]")
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', graph, '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech, g_cta = -31.5 - mI, -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)      # volume com expressão = ganho LINEAR
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.6:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.7,{lc_:.6f}))"

land = [T['d_' + k] + 0.46 for k in ('thumb', 'leg', 'cena', 'mus', 'anim')]
cues = [(T['fui'] - 0.12, 'whoosh2', -32), (T['fui'] + 0.55, 'pop', -31), (T['capaA'] - 0.18, 'whoosh1', -31), (T['capaLand'] - 0.02, 'impact', -34)]
cues += [(t - 0.02, 'pop', -33) for t in land]
cues += [(T['sweep'], 'shimmer', -34), (T['flip0'] + 0.05, 'swipe', -32), (T['flip0'] + 0.45, 'swipe', -34), (T['flip0'] + 0.8, 'swipe', -35),
         (T['rec0'] + 0.32, 'click', -30), (T['ou'], 'subdrop', -27), (se + 0.1, 'whoosh1', -32)]
if MODE == 'saiba':
    cues.append((T['tap'], 'click', -21))
else:
    ts = T['cta0'] + 1.75
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
pre = TMP / f'mix-pre{SUF}.wav'
bgp = TMP / f'bg-stem{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(bgp)])
I0, _ = lufs(pre)
OUT = J / f'renders/mix{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={-15.0 - I0:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)
bgs = TMP / f'bg-speech{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(bgp), '-af', f'atrim=0:{se:.3f},volume={-15.0 - I0:.2f}dB', str(bgs)])
vfin = TMP / 'voice-in-mix.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-af', f'volume={-15.0 - I0:.2f}dB', str(vfin)])
bgI, _ = lufs(bgs); vI, _ = lufs(vfin)
rep = {'cta': MODE, 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_track_section_s': [round(off, 2), round(off + DUR, 2)], 'music_hit_video_s': round(16.81 - off + pad, 3), 'muffled_s': [round(m0, 3), round(m1, 3)],
       'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR,
       'qa_voice_in_mix_lufs': vI, 'qa_background_under_speech_lufs': bgI, 'qa_voice_minus_bg_db': round(vI - bgI, 1)}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'voice': vI, 'bg_under_speech': bgI, 'gap_db': round(vI - bgI, 1)}, ensure_ascii=False))
