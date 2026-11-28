#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros discretos.
Trilha: faixa instrumental já gerada e paga pelo usuário para o criativo Namoral 02 (Lyria 3 Pro, 100 BPM; jobs/criativo-namoral-02/renders/
music-lyria-v1.mp3), reaproveitada sem custo novo. Trecho POSTERIOR da faixa (32,2 s → fim): a parada de um tempo da faixa (≈36,8–37,3 s)
cai no "Um vídeo profissional" e a resolução entra no "que antes era impossível"; o acorde final (≈67 s) cai no toque do botão do CTA.
Níveis (regra do usuário): sob a voz ≈ 22 dB abaixo da fala (fundo ≈ −37/−38 LUFS) com compressão lateral pela voz; no CTA ≈ −21 LUFS.
O filtro volume com expressão usa ganho LINEAR. Saídas: renders/mix.wav, tmp/bg-stem.wav e analysis/mix_report.json.
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
OFFSET = 32.2


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


f = [f'[0:a]atrim={OFFSET:.3f}:{OFFSET + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.12,'
     f'afade=t=out:st={DUR - 0.9:.3f}:d=0.9[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
G_SPEECH, G_CTA = -32.0, -21.0
g_speech = G_SPEECH - mI
g_cta = G_CTA - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

cues = [(T['minutos'] + 0.2, 'whoosh3', -33), (T['editar'] - 0.1, 'swipe', -31), (T['prof'] - 0.05, 'whoosh1', -33),
        (T['ed0'] + 0.25, 'whoosh2', -31), (T['dois'] - 0.05, 'swipe', -37), (T['dois'] + 0.42, 'swipe', -37),
        (T['correcao'] + 0.55, 'swipe', -37),      # sem efeito em cima de "pedir correção" (QA de inteligibilidade)
        (T['pr0'] + 0.2, 'whoosh1', -31), (T['v20'] - 0.05, 'click', -34), (T['v30'] - 0.05, 'click', -34), (T['termina2'] - 0.05, 'whoosh3', -32),
        (T['se'], 'swipe', -34), (T['manda2'] + 0.28, 'pop', -31),
        (T['jo0'] + 0.05, 'whoosh2', -31), (T['bp0'] + 0.15, 'whoosh1', -31), (T['tres'] - 0.1, 'shimmer', -34),
        (T['cta0'] + 0.05, 'whoosh2', -31), (T['cta0'] + 0.62, 'subdrop', -27)]
CTA_MODE = os.environ.get('CTA', 'saiba')
if CTA_MODE == 'comment':      # "Comente CORTEZ": teclas suaves enquanto CORTEZ é digitado + pop no envio (nível discreto)
    k0, k1 = T['cta0'] + 1.15, T['tap'] - 0.55
    cues += [(k0 + i * (k1 - k0) / 6, 'click', -37) for i in range(6)] + [(T['tap'], 'pop', -25)]
else:
    cues += [(T['tap'], 'click', -21)]
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
OUT = J / ('renders/mix.wav' if CTA_MODE == 'saiba' else 'renders/mix-comment.wav')
run(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af', f'volume={g:.2f}dB,alimiter=limit=0.84:attack=2:release=50:level=disabled', '-ar', str(SR), '-c:a', 'pcm_s16le', str(OUT)])
I1, P1 = lufs(OUT)
# fundo só no trecho com fala (o que importa para a inteligibilidade)
run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / 'bg-stem.wav'), '-t', f'{se:.3f}', '-af', f'volume={g:.2f}dB', str(TMP / 'bg-speech.wav')])
run(['ffmpeg', '-v', 'error', '-y', '-i', str(J / 'renders/voice.wav'), '-af', f'volume={g:.2f}dB', str(TMP / 'voice-in-mix.wav')])
bgI, _ = lufs(TMP / 'bg-speech.wav')
vI, _ = lufs(TMP / 'voice-in-mix.wav')
rep = {'music_source': '<PREENCHER: fonte ou prova própria>', 'music_offset_s': OFFSET,
       'music_raw_lufs': mI, 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'qa_voice_in_mix_lufs': vI, 'qa_background_under_speech_lufs': bgI, 'qa_voice_minus_background_db': round(vI - bgI, 1),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / ('analysis/mix_report.json' if CTA_MODE == 'saiba' else 'analysis/mix_report_comment.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: rep[k] for k in ('final_lufs', 'final_true_peak_dbtp', 'qa_voice_in_mix_lufs', 'qa_background_under_speech_lufs', 'qa_voice_minus_background_db')}))
