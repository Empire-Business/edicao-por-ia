#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: narração de IA (−16 LUFS) + trilha + poucos efeitos.
Trilha: faixa instrumental já gerada e paga pelo usuário para os motions (jobs/produto-gt3-motion/assets/audio/music.mp3, 87 s), sem custo novo.
A batida que volta em 16,5 s da faixa cai no início da varredura de render (o vídeo "acende"). Antes disso a trilha entra abafada (passa-baixa),
como uma confissão; depois abre. Sob a narração ≈ 19 dB abaixo da voz, com compressão lateral pela voz; no CTA ≈ −21 LUFS.
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


HIT_TRACK = 16.5
hit = T['sweep0'] + 0.05
off = HIT_TRACK - hit
medit = TMP / 'music-edit.wav'
xf = 0.35
graph = (f"[0:a]atrim={off:.3f}:{off + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates={SR}:channel_layouts=stereo,asplit=2[a][b];"
         f"[a]lowpass=f=650,lowpass=f=650,volume='if(lt(t,{hit - xf:.3f}),1,if(lt(t,{hit:.3f}),({hit:.3f}-t)/{xf},0))':eval=frame[lo];"
         f"[b]volume='if(lt(t,{hit - xf:.3f}),0,if(lt(t,{hit:.3f}),(t-{hit - xf:.3f})/{xf},1))':eval=frame[hi];"
         f"[lo][hi]amix=inputs=2:normalize=0,afade=t=in:d=0.4,afade=t=out:st={DUR - 1.2:.3f}:d=1.2[o]")
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', graph, '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech, g_cta = -30.0 - mI, -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)      # volume com expressão = ganho LINEAR
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.6:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.7,{lc_:.6f}))"

cues = [(T['c0'] - 0.15, 'whoosh2', -31), (T['sweep0'], 'shimmer', -33), (T['lock'], 'click', -30), (T['cut'] - 0.04, 'swipe', -27),
        (T['anim'], 'pop', -33), (T['s6'] + 0.1, 'whoosh1', -31), (se + 0.15, 'subdrop', -28)]
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
pre = TMP / f'mix-pre{SUF}.wav'
bgp = TMP / f'bg-stem{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(bgp)])
I0, _ = lufs(pre)
OUT = J / f'renders/mix{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={-15.0 - I0:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)
# fundo sob a fala (mesmo ganho final aplicado)
bgs = TMP / f'bg-speech{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(bgp), '-af', f'atrim=0:{se:.3f},volume={-15.0 - I0:.2f}dB', str(bgs)])
vfin = TMP / 'voice-in-mix.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-af', f'volume={-15.0 - I0:.2f}dB', str(vfin)])
bgI, _ = lufs(bgs); vI, _ = lufs(vfin)
rep = {'cta': MODE, 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_track_offset_s': round(off, 3), 'music_hit_video_s': round(hit, 3), 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR,
       'qa_voice_in_mix_lufs': vI, 'qa_background_under_speech_lufs': bgI, 'qa_voice_minus_bg_db': round(vI - bgI, 1)}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'voice': vI, 'bg_under_speech': bgI, 'gap_db': round(vI - bgI, 1)}, ensure_ascii=False))
