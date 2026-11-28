#!/usr/bin/env python3
"""EXEMPLO_1 V2 — mixagem: trilha de fala (renders/voice.wav, −16 LUFS) + trilha musical + efeitos sonoros discretos.
Trilha: faixa instrumental já gerada e paga pelo usuário para o criativo Namoral 03 (jobs/criativo-namoral-03/renders/music-lyria-v1.mp3),
reaproveitada sem custo novo, só em trechos DEPOIS do que o corte 2 usou (19,3–51,7 s): 52,0 s → sob o Apresentador e o fim natural da faixa
(80–83,5 s) no CTA. Muda no ANTES (som cru da gravação) e no DEPOIS (som da entrega EXEMPLO_2, que já tem trilha).
Sob a fala ≈ −32,5 LUFS antes da compressão lateral (fundo ≈ −37/−38 LUFS, ~22 dB abaixo da voz); no CTA ≈ −21 LUFS.
O filtro volume com expressão usa ganho LINEAR. Saídas: renders/mix.wav, tmp/bg-stem.wav e analysis/mix_report.json.
"""
import json, subprocess, sys
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
T = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
CTA_MODE = 'comment' if '--cta' in sys.argv and sys.argv[sys.argv.index('--cta') + 1] == 'comment' else 'more'
SUF = '-comment' if CTA_MODE == 'comment' else ''
DUR = T['end']
TMP = J / 'tmp'
SR = 48000


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


# 1) trilha (V2): dois trechos da faixa, ambos depois do que o corte 2 usou (19,3–51,7 s):
#    A = 52,0 s → … sob o Apresentador (do primeiro comentário até o DEPOIS); B = o fim natural da faixa (decaimento 80–83,5 s) no CTA.
#    No ANTES (som cru) e no DEPOIS (som da própria entrega, que tem trilha) a nossa trilha fica muda.
b0, dB, se = T['errou0'], T['dep0'], T['speechEnd']
END_TRACK = 83.5
A0, a_at, a_len = 52.0, b0 - 0.3, (dB + 0.3) - (b0 - 0.3)
b_at = se - 0.6; b_len = DUR - b_at; B0 = END_TRACK - b_len
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex',
     f'[0:a]asplit=2[x][y];'
     f'[x]atrim={A0:.3f}:{A0 + a_len:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.3,afade=t=out:st={a_len - 0.3:.3f}:d=0.3,adelay={int(a_at * 1000)}|{int(a_at * 1000)}[ma];'
     f'[y]atrim={B0:.3f}:{END_TRACK:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.4,afade=t=out:st={b_len - 0.6:.3f}:d=0.6,adelay={int(b_at * 1000)}|{int(b_at * 1000)}[mb];'
     f'[ma][mb]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur={DUR:.3f},atrim=0:{DUR:.3f}[o]',
     '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
o = subprocess.run(['ffmpeg', '-nostats', '-ss', f'{b0:.3f}', '-t', f'{dB - b0:.3f}', '-i', str(medit), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
mI = float([l for l in o.splitlines() if l.strip().startswith('I:')][-1].split()[1])
ls_, lc_ = 10 ** ((-34.0 - mI) / 20), 10 ** ((-21.0 - mI) / 20)    # V2: trecho 52 s+ da faixa é mais denso; −34 deixa o fundo ≈ −37,5


def ramp(t0, t1, a, b):
    return f"({a:.6f}+({b - a:.6f})*(t-{t0:.3f})/{t1 - t0:.3f})"


# envelope (ganho LINEAR): 0 no ANTES → fala → 0 no DEPOIS → CTA
vol = (f"if(lt(t,{b0 - 0.15:.3f}),0,"
       f"if(lt(t,{b0 + 0.25:.3f}),{ramp(b0 - 0.15, b0 + 0.25, 0, ls_)},"
       f"if(lt(t,{dB - 0.12:.3f}),{ls_:.6f},"
       f"if(lt(t,{dB + 0.08:.3f}),{ramp(dB - 0.12, dB + 0.08, ls_, 0)},"
       f"if(lt(t,{se - 0.1:.3f}),0,"
       f"if(lt(t,{se + 0.5:.3f}),{ramp(se - 0.1, se + 0.5, 0, lc_)},{lc_:.6f}))))))")

# 2) efeitos (tempo, arquivo, ganho dB) — discretos, só onde há movimento real na tela
cues = [(b0 + 0.02, 'subdrop', -30), (T['bruto0'] - 0.05, 'whoosh2', -29), (T['cortez0'] - 0.05, 'shimmer', -32)]
cues += [(f, 'click', -31) for f in T['flags']]
cues += [(T['limpar'] + 0.05, 'swipe', -27), (T['limpar'] + 0.35, 'whoosh1', -30), (T['remontar'] - 0.05, 'whoosh3', -29), (T['remontar'] + 1.05, 'impact', -31),
         (T['fecho0'] + 0.05, 'whoosh1', -31), (dB - 0.5, 'whoosh2', -29),
         (se - 0.2, 'whoosh2', -30), (se + 0.2, 'subdrop', -27)]
if CTA_MODE == 'comment':                       # teclas suaves na digitação de CORTEZ e um pop no envio
    cues += [(T['type0'] + i * 0.16, 'click', -36) for i in range(6)] + [(T['tap'], 'pop', -24)]
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
OUT = J / f'renders/mix{SUF}.wav'
for _ in range(3):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
    I1, P1 = lufs(OUT)
    if abs(I1 + 15) <= 0.3:
        break
    g += -15.0 - I1
# o fundo medido com o MESMO ganho final da mixagem (para comparar com a voz no master)
bgf = TMP / 'bg-stem-final.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / 'bg-stem.wav'), '-af', f'volume={g:.2f}dB', '-c:a', 'pcm_s16le', str(bgf)])
bgI, _ = lufs(bgf)
o = subprocess.run(['ffmpeg', '-nostats', '-ss', f'{b0:.3f}', '-t', f'{dB - b0:.3f}', '-i', str(bgf), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
bg_speech = float([l for l in o.splitlines() if l.strip().startswith('I:')][-1].split()[1])
rep = {'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_track_seconds': {'A_under_apresentador': [A0, round(A0 + a_len, 3)], 'B_cta': [round(B0, 3), END_TRACK]}, 'c2_used_track_seconds': [19.26, 51.66], 'music_raw_lufs_playing_part': mI,
       'music_gain_speech_db': round(-34.0 - mI, 2), 'music_gain_cta_db': round(-21.0 - mI, 2),
       'music_muted': ['ANTES (som cru da gravação)', 'DEPOIS (som da entrega EXEMPLO_2, que já tem trilha)'],
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1,
       'qa_background_stem_lufs_full_in_master': bgI, 'qa_background_stem_lufs_under_apresentador_in_master': bg_speech, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_full': bgI, 'bg_under_speech': bg_speech, 'music_I': mI}, ensure_ascii=False))
