#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros.
Trilha: faixa instrumental do criativo Namoral 01 (gerada e paga antes pelo usuário; reuso sem custo). O EXEMPLO_2 usou 3,0–40,2 s e o
acorde final (71,4 s →); aqui entra só o trecho do meio (41,6 → ~69 s), que o EXEMPLO_2 não usou, sem o final. Pulso medido na faixa:
0,5705 s (onsets 47,04 + k·0,5705). O deslocamento põe um tempo forte exatamente na volta da cena escura (T.t04, "E é bem editado").
Na máquina de tipos (fundo claro) a trilha passa por um passa-baixas (versão filtrada misturada por envelope) e "abre" de volta no
corte para o escuro. Sob a voz ≈ −31 LUFS antes da normalização (~22 dB abaixo da fala, compressão lateral pela voz); CTA ≈ −21 LUFS.
Saídas: renders/mix.wav e analysis/mix_report.json.
"""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
CTA_MODE = os.environ.get('CTA', 'more')          # 'comment' = variante "Comente CORTEZ" (CTA_COMENTE_CORTEZ.md)
SUF = '-comment' if CTA_MODE == 'comment' else ''
T = json.loads((J / f'analysis/motion_plan{SUF}.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
BEAT0, BEAT = 47.04, 0.5705


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


# 1) trilha: tempo forte da faixa em T.t04
k = round((41.4 + T['t04'] - BEAT0) / BEAT)
OFFSET = BEAT0 + k * BEAT - T['t04']
a0, a1 = T['t03'] - 0.35, T['t03'] - 0.05          # entra o filtro
b0, b1 = T['t04'] - 0.03, T['t04'] + 0.03          # abre no corte para o escuro
mwet = f"if(lt(t,{a0:.3f}),0,if(lt(t,{a1:.3f}),(t-{a0:.3f})/{a1 - a0:.3f},if(lt(t,{b0:.3f}),1,if(lt(t,{b1:.3f}),1-(t-{b0:.3f})/{b1 - b0:.3f},0))))"
f = [f'[0:a]atrim={OFFSET:.3f}:{OFFSET + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.06,'
     f'afade=t=out:st={DUR - 1.4:.3f}:d=1.4,asplit=2[d][w0]',
     f"[w0]lowpass=f=520:p=2,lowpass=f=900,volume=1.25[w1]",
     f"[d]volume='1-({mwet})':eval=frame[dd]", f"[w1]volume='{mwet}':eval=frame[ww]", '[dd][ww]amix=inputs=2:normalize=0[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -31.0 - mI
g_cta = -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)      # o filtro volume com expressão usa ganho LINEAR (não dB)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

# 2) efeitos sonoros (tempo, arquivo, ganho dB) — discretos, só onde há movimento real na imagem
cues = [(0.0, 'whoosh1', -33), (T['sem'] + 0.12, 'swipe', -33),
        (T['apa'] - 0.12, 'whoosh1', -32), (T['cen'] - 0.12, 'whoosh1', -32), (T['des'] - 0.12, 'whoosh1', -32), (T['des'] + 0.3, 'shimmer', -35),
        (T['apresentador'] + 0.05, 'whoosh2', -31), (T['esc'] - 0.1, 'pop', -31), (T['t03'] - 0.4, 'whoosh2', -29),
        (T['letra'], 'click', -31), (T['letra'] + 0.28, 'click', -32), (T['letra'] + 0.56, 'click', -32), (T['tam'], 'pop', -29), (T['cor'], 'shimmer', -33),
        (T['t04'] - 0.22, 'swipe', -30), (T['t04'], 'subdrop', -27),
        (T['efe'] - 0.08, 'pop', -32), (T['mus'] - 0.08, 'pop', -32), (T['vis'] - 0.08, 'pop', -32),
        (T['t05'] + 0.05, 'whoosh2', -31), (T['poss'] + 0.1, 'shimmer', -34),
        (se - 0.15, 'whoosh2', -30), (se + 0.2, 'subdrop', -27)]
if CTA_MODE == 'comment':   # CORTEZ digitado (teclas suaves) e enviado (pop discreto) no lugar do clique no botão
    cues += [(round(se + 1.62 + i * 0.1, 3), 'click', -37) for i in range(6)] + [(T['tap'], 'pop', -27)]
else:
    cues += [(T['tap'], 'click', -20)]
inputs, fl = [], []
for i, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{i + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{i}]')
n = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{i}]' for i in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]',
    '[mud]asplit=2[mud1][mud2]', '[fx]asplit=2[fx1][fx2]',
    f'[vm][mud1][fx1]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR:.3f}[pre]',
    f'[mud2][fx2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{DUR:.3f}[bg]'])
pre = TMP / f'mix-pre{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-i', str(medit), *inputs, '-filter_complex', graph, '-map', '[pre]',
     '-ar', str(SR), '-c:a', 'pcm_s16le', str(pre), '-map', '[bg]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(TMP / f'bg-stem{SUF}.wav')])
I0, P0 = lufs(pre)
g = -15.0 - I0
OUT = J / f'renders/mix{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)
# fundo (trilha + efeitos) na mesma escala da mistura final, só no trecho com fala
bg_scaled = TMP / f'bg-stem-final{SUF}.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / f'bg-stem{SUF}.wav'), '-af', f'volume={g:.2f}dB,atrim=0:{se:.3f}', str(bg_scaled)])
bgI, _ = lufs(bg_scaled)
voice_scaled = TMP / 'voice-final-scale.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-af', f'volume={g:.2f}dB', str(voice_scaled)])
vI = lufs(voice_scaled)[0]
rep = {'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_offset_s': round(OFFSET, 3), 'music_track_span_s': [round(OFFSET, 3), round(OFFSET + DUR, 3)], 'e118_used_track_spans_s': [[3.0, 40.2], [71.4, 77.7]],
       'music_beat_on_t04': True, 'lowpass_window_s': [round(a0, 3), round(b1, 3)], 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1,
       'qa_voice_lufs_in_final_scale': vI, 'qa_background_stem_lufs_speech_part_final_scale': bgI, 'voice_minus_background_db': round(vI - bgI, 1), 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'voice': vI, 'bg': bgI, 'offset': round(OFFSET, 3)}, ensure_ascii=False))
