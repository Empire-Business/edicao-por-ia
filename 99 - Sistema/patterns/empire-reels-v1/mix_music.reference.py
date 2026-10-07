"""v6 music: "VIOLIN - TONELOOM" (user file Downloads/Violin.mp3 -> music-violin-toneloom.mp3) under voice-master-v5.
Music is offset so its natural ending lands on the video end; normalised to -31 LUFS (user reference), carved
-3 dB @ 1.5-4 kHz for voice room, side-chain ducked ~4 dB under speech; final mix normalised to -14 LUFS (linear,
voice/music relationship preserved). Prints stem loudness so the balance is measured, not guessed."""
import json, os, subprocess, sys
A = os.path.dirname(os.path.abspath(__file__)); p = lambda n: os.path.join(A, n)
VOICE, MUSIC, OUT = 'voice-master.wav', 'music-violin-toneloom.mp3', 'mix-master.wav'
DUR = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p(VOICE)], capture_output=True, text=True).stdout)
END_IN_MUSIC = 179.6            # music's own decrescendo ends here (S -9 -> -21 LUFS around 177-180 s)
OFF = END_IN_MUSIC - DUR
MUSIC_LUFS = float(sys.argv[1]) if len(sys.argv) > 1 else -31.0
def run(*a): return subprocess.run(['ffmpeg', '-hide_banner', *a], capture_output=True, text=True)
def lufs(f, af=''):
    r = run('-i', p(f), '-af', (af + ',' if af else '') + 'ebur128', '-f', 'null', '-').stderr
    return float(r[r.rindex('I:'):].split()[1])
# 1) music segment, EQ carve, fades
run('-y', '-ss', f'{OFF:.3f}', '-t', f'{DUR:.3f}', '-i', p(MUSIC), '-af',
    # v7: flat bed — carve voice band, heavy compression + brickwall limiter so the level never moves
    f'highpass=f=60,equalizer=f=2600:t=q:w=0.9:g=-4,equalizer=f=1200:t=q:w=1:g=-1.5,'
    f'acompressor=threshold=-30dB:ratio=12:attack=4:release=120:knee=3:makeup=8,'
    f'alimiter=limit=0.35:attack=1:release=40:level=disabled,'
    f'afade=t=in:d=0.12,afade=t=out:st={DUR - 0.6:.3f}:d=0.6,aresample=48000', '-ac', '2', '-c:a', 'pcm_s24le', p('music-seg.wav'))
g = MUSIC_LUFS - lufs('music-seg.wav')
run('-y', '-i', p('music-seg.wav'), '-af', f'volume={g:.2f}dB', '-c:a', 'pcm_s24le', p('music-seg-norm.wav'))
# 2) duck under the voice (key = voice), then mix
run('-y', '-i', p(VOICE), '-i', p('music-seg-norm.wav'), '-filter_complex',
    '[0:a]aformat=channel_layouts=stereo,asplit=2[v][k];'
    '[1:a]anull[md];[k]anullsink;'   # v7: no ducking (user wants a constant music level)
    '[md]asplit=2[mdo][mdm];[v][mdm]amix=inputs=2:duration=first:normalize=0[mx]',
    '-map', '[mx]', '-c:a', 'pcm_s24le', p('mix-pre.wav'), '-map', '[mdo]', '-c:a', 'pcm_s24le', p('music-bed-flat.wav'))
# 3) final loudness -14 LUFS / -1.5 dBTP, two-pass linear
r = run('-i', p('mix-pre.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json', '-f', 'null', '-').stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
f2 = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
run('-y', '-i', p('mix-pre.wav'), '-af', f2, '-c:a', 'pcm_s24le', p(OUT))
post = -14.0 - float(m['input_i'])     # gain applied to both stems by the final normalisation
v, md = lufs(VOICE), lufs('music-bed-flat.wav')
print(f'music offset {OFF:.2f}s..{END_IN_MUSIC}s | music bed (before duck) {MUSIC_LUFS} LUFS | voice {v:.1f} LUFS | music after duck {md:.1f} LUFS')
print(f'in the final -14 LUFS mix: voice ≈ {v + post:.1f} LUFS, music ≈ {md + post:.1f} LUFS, gap {v - md:.1f} dB')
r = run('-i', p(OUT), '-af', 'ebur128=peak=true', '-f', 'null', '-').stderr; print(r[r.rindex('Summary'):].replace('\n', ' ')[:400])
