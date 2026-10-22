"""Local audio primitives. No credential reads, installation, or automatic cloud fallback."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

from project_layout import engine_root
from workspace_files import resolve_file, digest, portable

ROOT = Path(__file__).resolve().parents[1]


def run(command, timeout=600, env=None):
    """Bound the whole process group; never return arbitrary provider stderr."""
    with subprocess.Popen([str(x) for x in command], stdout=subprocess.PIPE, env=env,
                          stderr=subprocess.PIPE, start_new_session=os.name != 'nt') as proc:
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name != 'nt':
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=10)
            proc.communicate()
            raise ValueError('O processamento de áudio excedeu o prazo; nenhum serviço pago foi chamado.') from None
        if proc.returncode:
            raise ValueError(f'{Path(command[0]).name} falhou (código {proc.returncode}); confira o arquivo e o runtime local.')
        return stdout, stderr


def probe(path):
    raw, _ = run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_streams',
                  '-show_format', '-of', 'json', path], 30)
    data = json.loads(raw)
    if not data.get('streams'):
        raise ValueError('O arquivo não contém áudio válido.')
    duration = float(data.get('format', {}).get('duration', 0))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Duração de áudio inválida.')
    return {'duration': duration, 'sample_rate': int(data['streams'][0]['sample_rate'])}


def output_path(path, root=ROOT):
    raw = Path(path)
    if raw.is_symlink():
        raise ValueError('O destino não pode ser um atalho.')
    target = resolve_file(path, root, False)
    if target.exists():
        raise ValueError('A saída já existe; escolha uma nova versão.')
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def publish(source, target):
    # Both files are on the same workspace volume. Exclusive hardlink publication
    # avoids overwriting an original or a concurrently created output.
    os.link(source, target)


def receipt(path, data, root=ROOT):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(portable(data, root), stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def deepfilter_binary(root=ROOT):
    local = engine_root(root) / '.factory/runtimes/deepfilter' / ('deep-filter.exe' if os.name == 'nt' else 'deep-filter')
    if local.is_file() and not local.is_symlink() and os.access(local, os.X_OK):
        return str(local)
    return shutil.which('deep-filter')


def select_cleaner(provider='auto', root=ROOT):
    if provider not in ('auto', 'deepfilter', 'ffmpeg', 'elevenlabs'):
        raise ValueError('Provedor de limpeza desconhecido.')
    if provider == 'auto':
        return 'deepfilter' if deepfilter_binary(root) else 'ffmpeg'
    if provider == 'deepfilter' and not deepfilter_binary(root):
        raise ValueError('DeepFilterNet não está preparado. Prepare o runtime ou escolha a limpeza básica FFmpeg.')
    return provider


def clean(source, output, provider='auto', accept_paid=False, root=ROOT):
    """Clean FULL source at 48 kHz; keep duration, including the native model tail."""
    provider = select_cleaner(provider, root)
    if provider == 'elevenlabs' and not accept_paid:
        raise ValueError('ElevenLabs é opcional e pago; falta autorização explícita para esta chamada.')
    source = resolve_file(source, root)
    output = output_path(output, root)
    if output.suffix.lower() != '.wav':
        raise ValueError('A limpeza usa saída WAV para preservar sincronização e qualidade.')
    sidecar = output.with_suffix('.audio.json')
    if sidecar.exists():
        raise ValueError('O recibo da saída já existe; escolha outra versão.')
    info = probe(source)
    duration = info['duration']
    with tempfile.TemporaryDirectory(prefix='.audio-', dir=output.parent) as folder:
        tmp = Path(folder)
        normalized = tmp / 'source.wav'
        # Native -D removes lookahead samples without padding the tail. Pad FIRST,
        # then trim back to the exact source duration after enhancement.
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', source, '-vn', '-ac', '1',
             '-ar', '48000', '-af', 'apad=pad_dur=0.25', '-c:a', 'pcm_s16le', normalized],
            max(120, duration * 2))
        result = tmp / 'result.wav'
        if provider == 'deepfilter':
            binary = deepfilter_binary(root)
            run([binary, '-D', '-o', tmp / 'enhanced', normalized], max(120, duration * 10))
            processed = tmp / 'enhanced/source.wav'
            settings = {'runtime_sha256': digest(Path(binary)), 'delay_compensated': True}
        elif provider == 'ffmpeg':
            processed = tmp / 'filtered.wav'
            run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', normalized,
                 '-af', 'highpass=f=70,afftdn=nr=10:nf=-40:tn=1', '-c:a', 'pcm_s16le', processed], max(120, duration * 2))
            settings = {'filter': 'highpass=f=70,afftdn=nr=10:nf=-40:tn=1',
                        'limitation': 'Redução básica de ruído; não equivale a isolamento nem remoção de eco.'}
        else:
            from audio_remote import eleven_request
            processed = tmp / 'isolated.mp3'
            eleven_request('/v1/audio-isolation', processed, audio=normalized)
            settings = {'delay_compensated': False, 'sync_review_required': True}
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', processed, '-af',
             f'apad,atrim=duration={duration:.9f}', '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', result], max(120, duration * 2))
        actual = probe(result)
        if abs(actual['duration'] - duration) > 0.002:
            raise ValueError('A limpeza mudou a duração; saída bloqueada.')
        data = {'schema_version': 1, 'provider': provider, 'source': str(source), 'source_sha256': digest(source),
                'output': str(output), 'output_sha256': digest(result), 'duration': actual['duration'],
                'paid_request': provider == 'elevenlabs', 'cloud_fallback': False, 'settings': settings,
                'quality_review': 'pending_listening'}
        publish(result, output)
        receipt(sidecar, data, root)
    return data


def cache_key(source, provider, root=ROOT):
    selected = select_cleaner(provider, root)
    binary = deepfilter_binary(root) if selected == 'deepfilter' else None
    identity = [2, digest(Path(source)), selected, digest(Path(binary)) if binary else None]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input'); ap.add_argument('--out', required=True)
    ap.add_argument('--provider', choices=['auto', 'deepfilter', 'ffmpeg', 'elevenlabs'], default='auto')
    ap.add_argument('--accept-paid', action='store_true')
    args = ap.parse_args()
    try:
        data = clean(args.input, args.out, args.provider, args.accept_paid)
        print(json.dumps(portable(data, ROOT), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        ap.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
