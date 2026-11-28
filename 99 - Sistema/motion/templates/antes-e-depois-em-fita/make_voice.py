#!/usr/bin/env python3
"""EXEMPLO_1 — trilha de fala (voz + trechos sonoros da prova), no relógio do EDL.
  • Apresentador (live do YouTube): voz isolada no ElevenLabs (material-compartilhado/audio/yt-1279-1350-el.wav, janela já paga e autorizada;
    defasagem conferida 0 ms) → ganho por fala (−17 LUFS) → HPF 85 Hz → EQ de clareza (−2,5 dB em 280 Hz, +2,5 dB em 3,2 kHz,
    +1,5 dB acima de 7 kHz) → compressor 2,5:1 (a mesma cadeia dos cortes 1 e 2).
  • ANTES: som original da gravação bruta (sem limpeza — é o "antes"), só HPF 80 Hz e nível igual ao da fala.
  • DEPOIS: som da própria entrega EXEMPLO_2 V2 (voz tratada + trilha + efeitos dela), só nível.
Cada pedaço com fades de 20 ms (40 ms nas bordas da entrega, que tem trilha por baixo) → concatenação → ganho fixo para −16 LUFS
→ limitador (≤ −1,5 dBTP). Saídas: renders/voice.wav, renders/voice-apresentador-only.wav (para a transcrição de QA),
analysis/voice_levels.json e analysis/splice_check.json.
"""
import json, subprocess
from pathlib import Path

J = Path(__file__).resolve().parents[1]
SH = J.parent / 'material-compartilhado'
SR = 48000
edl = json.loads((J / 'edit/edl.json').read_text())
FPS = edl['fps']
AUD = {'raw': (J / 'tmp/audio/raw-bf.wav', 0.0), 'e117': (J / 'tmp/audio/e117-mix.wav', 0.0)}
YTWIN = [(1279.0, 1350.0, SH / 'audio/yt-1279-1350-el.wav'), (1558.0, 1584.0, SH / 'audio/yt-1558-1584-el.wav'), (1660.0, 1681.0, SH / 'audio/yt-1660-1681-el.wav')]


def aud(s):
    """arquivo de áudio e deslocamento do segmento; na live, a janela isolada no ElevenLabs que contém o trecho (sem chamada nova)"""
    if s['src'] != 'yt':
        return AUD[s['src']]
    w = [x for x in YTWIN if x[0] <= s['in'] - 0.05 and x[1] >= s['out'] + 0.05]
    if not w:
        raise SystemExit(f"trecho {s['take']} fora das janelas isoladas no ElevenLabs")
    return w[0][2], w[0][0]
TMP = J / 'tmp/voice'
TMP.mkdir(parents=True, exist_ok=True)
OUT = J / 'renders/voice.wav'
OUT.parent.mkdir(exist_ok=True)
CHAIN = ('highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,highshelf=f=7000:g=1.5,'
         'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=140:makeup=2')


def lufs(path, ss=None, t=None):
    a = ['ffmpeg', '-nostats'] + (['-ss', f'{ss:.3f}', '-t', f'{t:.3f}'] if ss is not None else []) + ['-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-']
    o = subprocess.run(a, capture_output=True, text=True).stderr.splitlines()
    return (float([l for l in o if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in o if l.strip().startswith('Peak:')][-1].split()[1]))


segs = edl['segments']
for s in segs:
    aud(s)
# ganho por take, medido só no que fica (os pedaços do take emendados), para todos os takes falarem no mesmo nível
gain = {}
for tid in dict.fromkeys(s['take'] for s in segs):
    ss = [s for s in segs if s['take'] == tid]
    f, off = aud(ss[0])
    tk = TMP / f'take-{tid}.wav'
    fl = ';'.join(f"[0:a]atrim={s['in'] - off:.4f}:{s['out'] - off:.4f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono[p{k}]" for k, s in enumerate(ss))
    ch = CHAIN if ss[0]['src'] == 'yt' else ('highpass=f=80' if ss[0]['src'] == 'raw' else 'anull')     # medido depois da mesma cadeia
    fl += ';' + ''.join(f'[p{k}]' for k in range(len(ss))) + f'concat=n={len(ss)}:v=0:a=1,{ch}[o]'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(f), '-filter_complex', fl, '-map', '[o]', '-c:a', 'pcm_s16le', str(tk)], check=True)
    I, _ = lufs(tk)
    target = {'yt': -17.0, 'raw': -17.5, 'e117': -18.0}[ss[0]['src']]      # a entrega já vem masterizada (com trilha): um pouco abaixo
    gain[tid] = round(target - I, 2)

parts = []
for i, s in enumerate(segs):
    f, off = aud(s)
    d = s['frames'] / FPS
    a = s['in'] - off
    fi, fo = (0.04, 0.04) if s['src'] == 'e117' else (0.020, 0.020)      # V2: 20 ms nas emendas
    chain = CHAIN if s['src'] == 'yt' else ('highpass=f=80' if s['src'] == 'raw' else 'anull')
    p = TMP / f'p{i:02d}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, a - 0.5):.4f}', '-i', str(f), '-t', f'{d + 1.0:.4f}', '-af',
                    f"aformat=sample_rates=48000:channel_layouts=mono,{chain},atrim={min(a, 0.5):.4f}:{min(a, 0.5) + d:.4f},asetpts=PTS-STARTPTS,"
                    f"volume={gain[s['take']]}dB,afade=t=in:d={fi},afade=t=out:st={max(0, d - fo):.4f}:d={fo},apad=whole_dur={d:.4f},atrim=0:{d:.4f}",
                    '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', str(p)], check=True)
    parts.append(p)
lst = TMP / 'list.txt'
lst.write_text(''.join(f"file '{p}'\n" for p in parts))
raw = TMP / 'voice-raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c:a', 'pcm_s16le', str(raw)], check=True)
I0, P0 = lufs(raw)
g = -16.0 - I0


def master(gain_db, src=raw, out=OUT):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', f'volume={gain_db:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled',
                    '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', str(out)], check=True)
    return lufs(out)


I2, P2 = master(g)
for _ in range(3):
    if abs(I2 + 16.0) <= 0.3 and P2 <= -1.5:
        break
    g += -16.0 - I2
    I2, P2 = master(g)
# versão só com o Apresentador (os outros pedaços em silêncio), para a transcrição de QA e o teste de inteligibilidade
mask = TMP / 'list-apresentador.txt'
bp = []
for i, (s, p) in enumerate(zip(segs, parts)):
    if s['src'] == 'yt':
        bp.append(p)
    else:
        z = TMP / f'z{i:02d}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=mono', '-t', f"{s['frames'] / FPS:.4f}", '-c:a', 'pcm_s16le', str(z)], check=True)
        bp.append(z)
mask.write_text(''.join(f"file '{p}'\n" for p in bp))
braw = TMP / 'apresentador-raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(mask), '-c:a', 'pcm_s16le', str(braw)], check=True)
master(g, braw, J / 'renders/voice-apresentador-only.wav')

per = []
for i, s in enumerate(segs):
    d = s['frames'] / FPS
    per.append({'i': i, 'take': s['take'], 'src': s['src'], 'start': s['start'], 'lufs': lufs(OUT, s['start'], d)[0] if d > 0.45 else None})
(J / 'analysis/splice_check.json').write_text(json.dumps({'per_segment_lufs_in_final_voice': per}, ensure_ascii=False, indent=1))
rep = {'sources': {'yt': 'material-compartilhado/audio/yt-1279-1350-el.wav, yt-1558-1584-el.wav e yt-1660-1681-el.wav (ElevenLabs Audio Isolation, janelas já pagas/autorizadas no lote)',
                   'raw': '<PREENCHER: fonte ou prova própria>',
                   'e117': 'áudio da entrega EXEMPLO_2 V2 (DEPOIS)'},
       'per_take_gain_db': gain, 'before': {'lufs': I0, 'peak_dbtp': P0}, 'fixed_gain_db': round(g, 2), 'final_lufs': I2, 'final_true_peak_dbtp': P2,
       'duration': edl['duration'], 'chain_apresentador': CHAIN}
(J / 'analysis/voice_levels.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I2, 'tp': P2, 'gains': gain}, ensure_ascii=False))
for p in per:
    print(p)
