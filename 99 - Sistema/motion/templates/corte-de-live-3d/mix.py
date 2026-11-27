#!/usr/bin/env python3
# Modelo F22 Corte de Live 3D — derivado da edição de exemplo E119 (prévia aprovada pelo autor em 27/11/2026).
# Copie para jobs/<trabalho>/src e preencha: fonte, falas (TAKES), cenas/legendas, provas próprias e trilha. Ver README.md desta pasta.
"""Mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros.
Trilha: faixa instrumental já gerada e paga pelo usuário para os criativos anteriores do usuário (Lyria 3 Pro, 100 BPM, tensão → virada →
resolução; audio/<trilha>.mp3), reaproveitada sem custo novo. Edição em compassos (2,4 s):
A = trilha 3,0–16,2 s; B = 13,8–40,2 s (repete 1 compasso para a virada da trilha cair no "de Hollywood");
C = 71,4 s → acorde final, no CTA escrito. V2 (usuário: "música muito alta, dá pra entender nada"): sob a voz ≈ −34 LUFS
(~18 dB abaixo da fala) com compressão lateral forte pela voz; no CTA ≈ −21 LUFS. Efeitos: só whooshes discretos nas trocas e um clique.
Saídas: renders/mix.wav e analysis/mix_report.json.
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J
MUSIC = J / 'audio/<trilha>.mp3'   # trilha própria/licenciada; nunca gerar paga sem o sim do usuário
SFX = SH / 'audio/sfx'
T = json.loads((J / 'analysis/motion_plan.json').read_text())['T']
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


# 1) edição da trilha
# Exemplo E119: trilha reaproveitada. Virada da faixa (31,8 s) cai no "nossa" (vídeo 12,54 s).
OFFSET = 31.8 - T['reveal']
pieces = [(OFFSET, OFFSET + DUR)]
f = [f'[0:a]atrim={OFFSET:.3f}:{OFFSET + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.25,afade=t=out:st={DUR - 1.3:.3f}:d=1.3[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -31.0 - mI
g_cta = -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)      # o filtro volume com expressão usa ganho LINEAR (não dB)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

# 2) efeitos sonoros (tempo, arquivo, ganho dB)
cues = [(T['flip1'] - 0.3, 'whoosh1', -30), (T['flip2'] - 0.3, 'whoosh1', -30),
        (T['reveal'] - 0.15, 'swipe', -27), (T['reveal'], 'subdrop', -26), (T['long0'] - 0.2, 'whoosh2', -29), (T['shorts0'] - 0.1, 'whoosh1', -28),
        (T['back'] - 0.2, 'swipe', -30), (T['word'], 'whoosh3', -30), (T['word'] + 0.3, 'shimmer', -31),
        (se - 0.2, 'whoosh2', -30), (se + 0.2, 'subdrop', -26), (T['tap'], 'click', -20)]
inputs, fl = [], []
for k, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k + 2}:a]volume={gdb}dB,adelay={ms}|{ms}[s{k}]')
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
OUT = J / 'renders/mix.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)
bgI, _ = lufs(TMP / 'bg-stem.wav')
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'music_offset_s': round(OFFSET, 3), 'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI,'music_source': 'audio/<trilha>.mp3 (trilha própria/licenciada)',
       'music_pieces_track_seconds': pieces, 'music_drop_video_s': T['reveal'], 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / 'analysis/mix_report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'music_I_raw': mI}, ensure_ascii=False))
