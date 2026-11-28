#!/usr/bin/env python3
"""EXEMPLO_1 — mixagem: voz final (−16 LUFS) + trilha + efeitos sonoros.
Trilha: faixa instrumental já gerada e paga pelo usuário para o criativo Namoral 02 (Lyria 3 Pro, 100,2 BPM; 2º ato a partir de
37,8 s; último acorde em ~67,0 s; jobs/criativo-namoral-02/renders/music-lyria-v1.mp3), reaproveitada sem custo novo e sem emendas:
o vídeo inteiro fica no 2º ato e o último acorde cai 1 s depois do início do CTA escrito (quando o botão aparece).
Sob a voz ≈ −31 LUFS na trilha crua + compressão lateral pela voz (fundo medido ≈ −37/−38 LUFS, ~22 dB abaixo da fala); no CTA ≈ −21 LUFS.
Efeitos discretos: palhetas (cliques) no placar, "pop" das mensagens, whoosh no mergulho e na volta do portal, subgrave nas viradas.
Saídas: renders/mix.wav, tmp/bg-stem.wav e analysis/mix_report.json.
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
CTA_MODE = os.environ.get('CTA', 'saiba')          # 'comment' = variante "Comente CORTEZ" (teclas suaves + pop no envio)
SUF = '' if CTA_MODE == 'saiba' else '-comente-cortez'


def run(a):
    subprocess.run(a, check=True)


def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ls = o.splitlines()
    return (float([l for l in ls if l.strip().startswith('I:')][-1].split()[1]),
            float([l for l in ls if l.strip().startswith('Peak:')][-1].split()[1]))


HIT = 67.0
OFFSET = HIT - (T['cta0'] + 1.0)
f = [f'[0:a]atrim={OFFSET:.3f}:{OFFSET + DUR:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.04,afade=t=out:st={DUR - 0.8:.3f}:d=0.8[o]']
medit = TMP / 'music-edit.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC), '-filter_complex', ';'.join(f), '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', str(medit)])
mI, _ = lufs(medit)
g_speech = -32.0 - mI
g_cta = -21.0 - mI
se = T['speechEnd']
ls_, lc_ = 10 ** (g_speech / 20), 10 ** (g_cta / 20)      # volume com expressão = ganho LINEAR
# V2b (nota do diretor): nos trechos do áudio de WhatsApp do Convidado (lo-fi) a trilha desce mais 4 dB (rampas de 0,15 s);
# os trechos da live ficam como estavam. Ganho LINEAR na expressão.
EDL = json.loads((J / 'edit/edl.json').read_text())
VN = []
for sg in EDL['segments']:
    if sg['src'] == 'yt':
        a_, b_ = sg['start'], sg['start'] + sg['frames'] / EDL['fps']
        if VN and a_ - VN[-1][1] < 0.05: VN[-1][1] = b_
        else: VN.append([a_, b_])
VN_DIP_DB = float(os.environ.get('VN_DIP_DB', '6'))   # testado 4/6/8 dB: 6 dB foi o menor que deixou "prompt" reconhecido
DIP = 10 ** (-VN_DIP_DB / 20)
w = '+'.join(f'clip((t-{a_ - 0.15:.3f})/0.15,0,1)*clip(({b_ + 0.15:.3f}-t)/0.15,0,1)' for a_, b_ in VN)
dip = f'(1-{1 - DIP:.6f}*clip({w},0,1))'
WX = f'clip({w},0,1)'
VN_CARVE_DB = float(os.environ.get('VN_CARVE_DB', '8'))   # nos áudios do Convidado a trilha também abre espaço na faixa da voz (1,2 e 2,5 kHz)
vol = f"if(lt(t,{se - 0.1:.3f}),{ls_:.6f}*{dip},if(lt(t,{se + 0.5:.3f}),{ls_:.6f}+({lc_ - ls_:.6f})*(t-{se - 0.1:.3f})/0.6,{lc_:.6f}))"

roll = [T['pct'] - 1.05 + k * 0.17 for k in range(6)]
cues = [(T['q'] - 0.15, 'swipe', -31), (T['flap'] - 0.62, 'click', -27), (T['flap'] - 0.3, 'click', -24),
        (T['mandei'] + 0.1, 'pop', -33), (T['caramba'] - 0.04, 'pop', -27), (T['sinistro'] - 0.12, 'whoosh3', -31), (T['sinistro'], 'subdrop', -28),
        (T['v2'] - 0.18, 'pop', -30), (T['styles'] - 0.05, 'swipe', -31), (T['v3'] - 0.1, 'whoosh2', -27), (T['v3'] + 0.5, 'subdrop', -27),
        (T['ten'] - 0.02, 'swipe', -29), (T['ten'] + 0.25, 'shimmer', -33), (T['k1'] - 0.05, 'whoosh1', -35), (T['k2'] - 0.05, 'whoosh1', -35),
        (T['k3'] - 0.05, 'whoosh1', -35), (T['k4'] - 0.05, 'whoosh1', -35), (T['p0'] - 0.45, 'whoosh2', -29),
        *[(r, 'click', -35) for r in roll], (T['pct'] - 0.12, 'click', -24), (T['pct'], 'subdrop', -29),
        (T['f0'] - 0.18, 'pop', -30), (se + 0.15, 'whoosh2', -31), (se + 0.25, 'subdrop', -27)]
if CTA_MODE == 'saiba':
    cues += [(T['tap'], 'click', -20)]
else:
    k0 = round(T['cta0'] + 1.6, 3)
    cues += [(k0 + i * 0.11, 'click', -38) for i in range(6)] + [(T['tap'], 'pop', -25)]
inputs, fl = [], []
for k, (t, name, gdb) in enumerate(cues):
    inputs += ['-i', str(SFX / f'{name}.wav')]
    ms = max(0, int(round(t * 1000)))
    fl.append(f'[{k + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gdb}dB,adelay={ms}|{ms}[s{k}]')
n = len(cues)
graph = ';'.join([
    f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={DUR:.3f}[v]',
    '[v]asplit=2[vm][vsc]',
    f"[1:a]asplit=2[mA][mB];[mB]equalizer=f=2500:t=q:w=1.2:g=-{VN_CARVE_DB},equalizer=f=1200:t=q:w=1.2:g=-{VN_CARVE_DB / 2}[mBq]",
    f"[mA]volume='1-{WX}':eval=frame[mA2]", f"[mBq]volume='{WX}':eval=frame[mB2]",
    f"[mA2][mB2]amix=inputs=2:normalize=0,volume='{vol}':eval=frame[mu]",
    '[mu][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=350:makeup=1[mud]',
    *fl,
    ''.join(f'[s{k}]' for k in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest[fx]',
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
# fundo sob a fala (até o fim da voz), no mesmo ganho final
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(TMP / f'bg-stem{SUF}.wav'), '-t', f'{se:.3f}', '-af', f'volume={g:.2f}dB', str(TMP / f'bg-speech{SUF}.wav')], check=True)
bgI, _ = lufs(TMP / f'bg-speech{SUF}.wav')
vI = lufs(J / 'renders/voice.wav')[0]
# margem trilha × voz nos trechos do áudio do Convidado (mesmo ganho final)
def seg_lufs(path, a_, b_):
    o = subprocess.run(['ffmpeg', '-nostats', '-ss', f'{a_:.3f}', '-t', f'{b_ - a_:.3f}', '-i', str(path), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
    return float([l for l in o if l.strip().startswith('I:')][-1].split()[1])
vn_margin = []
for a_, b_ in VN:
    vI_ = seg_lufs(J / 'renders/voice.wav', a_, b_); mI_ = seg_lufs(TMP / f'bg-stem{SUF}.wav', a_, b_)
    vn_margin.append({'span': [round(a_, 3), round(b_, 3)], 'voice_lufs': vI_, 'bg_lufs': mI_, 'margin_db': round(vI_ - mI_, 1)})
rep = {'voice_note_spans_margin': vn_margin, 'voice_note_extra_dip_db': -VN_DIP_DB, 'voice_note_music_carve_db': {'2500Hz': -VN_CARVE_DB, '1200Hz': -VN_CARVE_DB / 2}, 'music_offset_s': round(OFFSET, 3), 'music_source': '<PREENCHER: fonte ou prova própria>',
       'music_final_hit_video_s': round(T['cta0'] + 1.0, 3), 'music_gain_speech_db': round(g_speech, 2), 'music_gain_cta_db': round(g_cta, 2),
       'qa_voice_lufs': vI, 'qa_background_under_speech_lufs_final_gain': bgI, 'final_gain_db': round(g, 2),
       'sfx': [{'t': round(t, 3), 'file': n_, 'gain_db': gd} for t, n_, gd in cues], 'final_lufs': I1, 'final_true_peak_dbtp': P1, 'duration': DUR}
(J / f'analysis/mix_report{SUF}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({'final_lufs': I1, 'tp': P1, 'bg_under_speech': bgI, 'music_I_raw': mI, 'vn_margin_db': [m['margin_db'] for m in vn_margin]}, ensure_ascii=False))
