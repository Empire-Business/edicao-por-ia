#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: narração de IA do Cortez (−16 LUFS) + trilha + efeitos sonoros.
Trilha: jobs/tutorial-cami/assets/music/lyria-4.mp3 (Lyria, já gerada e paga pelo usuário; reuso sem custo; 80 BPM, compasso 3,0 s).
Trecho diferente do EXEMPLO_2 (que usou 47–71 s): a pausa curta da faixa (119 s) e a volta forte em 120,0 s caem no mergulho para dentro da pasta
(troca para o túnel). Depois da fala, emenda num tempo da grade para o fim da faixa (decaimento natural ≈169–173 s) sob o CTA.
Sob a narração ≈ 19 dB abaixo (fundo ≈ −35 LUFS) com compressão lateral pela voz; no CTA ≈ −20 LUFS. Ganho do filtro volume = LINEAR.
CTA=comment usa a mesma trilha e troca o clique do botão por teclas suaves + "pop" de enviar.
Saídas: renders/mix{-comment}.wav, tmp/bg-stem*.wav e analysis/mix_report*.json.
"""
import json, os, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
MUSIC = J.parent / '<PREENCHER: fonte ou prova própria>'
SFX = SH / 'audio/sfx'
CTA = os.environ.get('CTA', 'saiba')
SUF = '' if CTA == 'saiba' else '-comment'
T = json.loads((J / f'analysis/motion_plan{SUF}.json').read_text())['T']
DUR = T['end']
TMP = J / 'tmp'
SR = 48000
BEAT = 0.75
DROP, END_HIT = 120.0, 173.0


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


OFF = DROP - T['tun']
se = T['speechEnd']
n = 1
while T['tun'] + n * BEAT < se + 0.15:
    n += 1
cut = T['tun'] + n * BEAT                        # emenda num tempo da grade logo depois da fala
m = round((END_HIT - (DUR - cut) - DROP) / BEAT)
E0 = DROP + m * BEAT                                 # ponto da grade: o fim do vídeo cai no decaimento final da faixa
pieces = [(OFF, OFF + cut), (E0, E0 + (DUR - cut) + 0.05)]
f = []
for i, (a, b) in enumerate(pieces):
    d = b - a
    f.append(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={0.35 if i == 0 else 0.02},afade=t=out:st={d - 0.03:.3f}:d=0.03[m{i}]')
f.append('[m0][m1]concat=n=2:v=0:a=1,aformat=sample_rates=48000:channel_layouts=stereo,' + f'afade=t=out:st={DUR - 0.9:.3f}:d=0.9,atrim=0:{DUR:.3f}[o]')
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -30.5 - mI
g_cta = -19.5 - mI
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(T['pasta1'] - 0.08, 'swipe', -33), (T['video1'] - 0.15, 'whoosh1', -32), (T['pasta2'] + 0.4, 'subdrop', -33),
        (T['aparece'] - 0.3, 'whoosh1', -32), (T['aparece'] + 0.3, 'shimmer', -35), (T['tube0'], 'riser1', -35),
        (T['no'] - 0.05, 'whoosh2', -30), (T['tun'] - 0.02, 'impact', -31), (T['tun'], 'subdrop', -31),
        (T['limpo'] - 0.05, 'swipe', -34), (T['silencios'] + 0.05, 'subdrop', -33), (T['erros'] - 0.02, 'whoosh3', -33),
        (T['cenas'] + 0.25, 'pop', -33), (T['cenas'] + 0.35, 'pop', -34), (T['legenda'] - 0.05, 'shimmer', -34), (T['animacao'], 'whoosh1', -33),
        (T['sem1'] - 0.22, 'pop', -32), (T['edicao'] - 0.05, 'whoosh2', -32), (T['linha'] - 0.05, 'swipe', -34),
        (T['tempo'] - 0.3, 'riser2', -34), (T['exit'] - 0.02, 'impact', -31), (se + 0.15, 'subdrop', -31)]
if CTA == 'saiba':
    cues += [(T['tap'], 'click', -20)]
else:
    cues += [(T['type2'] + i * 0.11, 'click', -36) for i in range(6)] + [(T['tap'], 'pop', -25)]
inputs, fl = [], []
for k_, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k_ + 2}:a]volume={gdb}dB,adelay={ms}|{ms}[s{k_}]')
nc = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k_}]' for k_ in range(nc)) + f'amix=inputs={nc}:normalize=0:duration=longest[fx]',
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
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / f'bg-stem{SUF}.wav'), '-t', f'{se:.3f}', str(TMP / f'bg-speech{SUF}.wav')])
bgS, _ = lufs(TMP / f'bg-speech{SUF}.wav')
vI = lufs(J / 'renders/voice.wav')[0]
rep = {'qa_voice_lufs': vI, 'qa_background_stem_lufs_full': bgI, 'qa_background_stem_lufs_under_speech': bgS,
       'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_pieces_track_seconds': [[round(a, 3), round(b, 3)] for a, b in pieces], 'music_drop_track_s': DROP, 'music_drop_video_s': T['tun'],
       'music_join_video_s': round(cut, 3), 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_full': bgI, 'bg_speech': bgS, 'voice': vI, 'pieces': rep['music_pieces_track_seconds'], 'join': round(cut, 3)}, ensure_ascii=False))
