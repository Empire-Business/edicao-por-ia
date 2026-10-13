#!/usr/bin/env python3
"""Swap the outfit and/or the scenery of a short recorded range with a generative video-edit model.

Works for any editing format: `run` edits one short range of a recording and returns a clip with the
same size, frame rate, duration and ORIGINAL audio; `patch` builds a derived copy of the recording
with that range replaced, so cuts, captions and motion keep their timing. Originals are never changed.

usage:
  python3 tools/gen_video_edit.py models
  python3 tools/gen_video_edit.py run --input SRC --start 24 --duration 5 --change roupa \
      --describe "a tailored black blazer over a white dress shirt, open collar, no tie" \
      --out OUT.mp4 --temp-public-link
  python3 tools/gen_video_edit.py patch --input SRC --clip OUT.mp4 --start 24 --out DERIVED.mov

Loads OPENROUTER_API_KEY through service_keys. The provider only accepts the input clip as a public
HTTPS link: pass one the user hosts (--source-url) or, with the user's consent for this clip,
--temp-public-link (Litterbox, removed after 1 hour). Read method/EXTERNAL_SERVICES.md first.
"""
import argparse, hashlib, json, math, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

API = 'https://openrouter.ai/api/v1'
API_HOST = 'openrouter.ai'
DEFAULT_MODEL = 'black-forest-labs/flux-video-edit'
TEMP_HOST = 'https://litterbox.catbox.moe/resources/internals/api.php'
TEMP_LINK_HOST = 'litter.catbox.moe'
MAX_SECONDS = 10
DONE = ('completed', 'failed', 'cancelled', 'expired')
KEEP_PERSON = ('face, hair, expression, lip movements, hands, jewelry, any object being held, '
               'and all motion and timing')
PROMPTS = {
    'roupa': ("Replace the person's clothing with {d}. Keep everything else exactly unchanged: "
              + KEEP_PERSON + ', the lighting and the background. Keep the camera framing identical.'),
    'cenario': ('Replace only the background behind the person with {d}. Keep the person exactly '
                'unchanged: clothing, ' + KEEP_PERSON + '. Keep the camera framing identical.'),
    'ambos': ("Replace the person's clothing and the background behind the person as follows: {d}. "
              'Keep the person exactly unchanged otherwise: ' + KEEP_PERSON
              + '. Keep the camera framing identical.'),
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def http(url, data=None, headers=None, timeout=120, follow=False):
    """Return (status, bytes). Redirects are refused unless `follow`, so a key never leaves its host."""
    request = urllib.request.Request(url, data=data, headers=headers or {}, method='POST' if data is not None else 'GET')
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError('Sem resposta do serviço; confira a conexão e tente de novo.') from None


def provider_message(raw):
    try:
        error = json.loads(raw).get('error')
    except (ValueError, AttributeError):
        return ''
    message = error.get('message') if isinstance(error, dict) else error
    return str(message)[:300] if message else ''


def api(path, key, body=None):
    url = path if path.startswith('https://') else API + path
    if urllib.parse.urlsplit(url).hostname != API_HOST:
        raise ValueError('Endereço inesperado devolvido pelo serviço; operação interrompida.')
    status, raw = http(url, None if body is None else json.dumps(body).encode(),
                       {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    if status == 401:
        raise ValueError('A chave OPENROUTER_API_KEY foi recusada; confira o arquivo de chaves.')
    if status == 402:
        raise ValueError('Créditos insuficientes na OpenRouter; nada foi gerado.')
    if status >= 300:
        raise ValueError(f'A OpenRouter recusou o pedido ({status}). {provider_message(raw)}'.strip())
    return json.loads(raw)


def list_models():
    status, raw = http(API + '/videos/models')
    if status >= 300:
        raise ValueError(f'Não foi possível consultar os modelos ({status}).')
    return json.loads(raw).get('data', [])


def video_edit_models(models):
    """Models that take a video as input. The public list has pricing; input types come from /models."""
    status, raw = http(API + '/models?output_modalities=video')
    takes_video = set()
    if status < 300:
        takes_video = {m['id'] for m in json.loads(raw).get('data', [])
                       if 'video' in (m.get('architecture', {}).get('input_modalities') or [])}
    return [m for m in models if m.get('id') in takes_video]


def estimate_usd(model, seconds):
    """Cost for per-second models; None when the model bills another way (unknown before running)."""
    skus = model.get('pricing_skus') or {}
    cents = skus.get('cents_per_second_output')
    if cents is None:
        return None
    usd = float(cents) * math.ceil(seconds) / 100
    return max(usd, float(skus.get('minimum_cents_per_generation', 0)) / 100)


def build_prompt(change, describe):
    describe = ' '.join(describe.split()).rstrip('.')
    if change not in PROMPTS:
        raise ValueError('Escolha o que trocar: roupa, cenario ou ambos.')
    if len(describe) < 8:
        raise ValueError('Descreva a roupa ou o cenário desejado com mais detalhe.')
    return PROMPTS[change].format(d=describe)


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise ValueError('Falha ao preparar o vídeo: ' + result.stderr.strip()[-300:])
    return result.stdout


def probe(path):
    """Display size (rotation already applied by ffmpeg), frame rate and duration of a video file."""
    data = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height,r_frame_rate:stream_side_data=rotation:format=duration',
                           '-of', 'json', str(path)]))
    stream = data['streams'][0]
    num, _, den = stream['r_frame_rate'].partition('/')
    width, height = int(stream['width']), int(stream['height'])
    rotation = next((x['rotation'] for x in stream.get('side_data_list', []) if 'rotation' in x), 0)
    if abs(int(rotation)) % 180 == 90:
        width, height = height, width
    return {'width': width, 'height': height,
            'fps': float(num) / float(den or 1), 'duration': float(data['format']['duration'])}


def even(value):
    return max(2, int(round(value / 2)) * 2)


def cut_reference(source, start, duration, out):
    """The untouched range at display size: the audio and the size/fps the result must match."""
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.3f}', '-t', f'{duration:.3f}', '-i', str(source),
         '-map', '0:v:0', '-map', '0:a:0?', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(out)])


def make_upload_clip(reference, out, long_side):
    info = probe(reference)
    scale = min(1.0, long_side / max(info['width'], info['height']))
    width, height = even(info['width'] * scale), even(info['height'] * scale)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(reference), '-vf', f'scale={width}:{height},fps=30',
         '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
         '-movflags', '+faststart', str(out)])


def conform(generated, reference, out):
    """Generated picture at the reference size/fps/duration, with the reference (original) audio."""
    info = probe(reference)
    width, height = even(info['width']), even(info['height'])
    picture = (f'[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},'
               f'fps={info["fps"]:.5f},setsar=1[v]')
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(generated), '-i', str(reference), '-filter_complex', picture,
         '-map', '[v]', '-map', '1:a:0?', '-t', f'{info["duration"]:.3f}', '-c:v', 'libx264', '-crf', '16',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(out)])


def side_by_side(reference, edited, out):
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(reference), '-i', str(edited), '-filter_complex',
         '[0:v][1:v]hstack[v]', '-map', '[v]', '-map', '0:a:0?', '-c:v', 'libx264', '-crf', '18',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', str(out)])


def temp_public_link(path):
    """Upload to Litterbox with a 1-hour expiry and return the public link. Requires user consent."""
    boundary = uuid.uuid4().hex
    parts = b''
    for name, value in (('reqtype', 'fileupload'), ('time', '1h')):
        parts += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
    parts += (f'--{boundary}\r\nContent-Disposition: form-data; name="fileToUpload"; filename="clip.mp4"\r\n'
              'Content-Type: video/mp4\r\n\r\n').encode() + Path(path).read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    status, raw = http(TEMP_HOST, parts, {'Content-Type': f'multipart/form-data; boundary={boundary}'}, timeout=300)
    link = raw.decode(errors='replace').strip()
    if status >= 300 or urllib.parse.urlsplit(link).hostname != TEMP_LINK_HOST or not link.startswith('https://'):
        raise ValueError('O link temporário não pôde ser criado; hospede o trecho e informe --source-url.')
    return link


def check_source_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname:
        raise ValueError('O link do trecho precisa ser HTTPS e público.')
    return url


def generate(key, model, prompt, link, poll_seconds=8, max_polls=150):
    job = api('/videos', key, {'model': model, 'prompt': prompt,
                               'input_references': [{'type': 'video_url', 'video_url': {'url': link}}]})
    for _ in range(max_polls):
        if job.get('status') in DONE:
            break
        time.sleep(poll_seconds)
        job = api(job['polling_url'], key)
    if job.get('status') != 'completed':
        raise ValueError(f"A geração não terminou ({job.get('status')}). {str(job.get('error') or '')[:200]}".strip())
    return job


def download(key, job, out):
    urls = job.get('unsigned_urls') or []
    url = urls[0] if urls else f"{API}/videos/{job['id']}/content?index=0"
    own = urllib.parse.urlsplit(url).hostname == API_HOST
    if not url.startswith('https://'):
        raise ValueError('O serviço devolveu um endereço de resultado inválido.')
    status, data = http(url, None, {'Authorization': 'Bearer ' + key} if own else {}, timeout=600, follow=not own)
    if status >= 300 or not data:
        raise ValueError(f'O resultado não pôde ser baixado ({status}).')
    Path(out).write_bytes(data)
    probe(out)  # an error page is never accepted as a video


def cmd_models(_):
    for model in video_edit_models(list_models()):
        skus = model.get('pricing_skus') or {}
        cents = skus.get('cents_per_second_output')
        price = 'preço por volume (só medido ao rodar)' if cents is None else f'US$ {float(cents) / 100:.2f}/s'
        if skus.get('minimum_cents_per_generation'):
            price += f" (mínimo US$ {float(skus['minimum_cents_per_generation']) / 100:.2f} por geração)"
        print(f"{model['id']}\t{price}\t{model.get('name', '')}")


def cmd_run(a):
    source, out = Path(a.input), Path(a.out)
    if not source.is_file():
        raise ValueError('Vídeo de origem não encontrado.')
    if not 1 <= a.duration <= MAX_SECONDS:
        raise ValueError(f'Use um trecho de 1 a {MAX_SECONDS} segundos por geração.')
    if bool(a.source_url) == bool(a.temp_public_link):
        raise ValueError('Informe --source-url (link que o usuário hospedou) OU --temp-public-link (com consentimento).')
    prompt = a.prompt or build_prompt(a.change, a.describe or '')
    model = next((m for m in list_models() if m.get('id') == a.model), None)
    if model is None:
        raise ValueError('Modelo de vídeo não encontrado na OpenRouter.')
    usd = estimate_usd(model, a.duration)
    if usd is None and not a.accept_unknown_cost:
        raise ValueError('Este modelo não tem preço por segundo; confirme com o usuário e use --accept-unknown-cost.')
    if usd is not None and usd > a.max_usd:
        raise ValueError(f'Custo estimado US$ {usd:.2f} acima do limite US$ {a.max_usd:.2f}; confirme e ajuste --max-usd.')
    from service_keys import api_key
    key = api_key('OPENROUTER_API_KEY')
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_suffix('.work')
    work.mkdir(exist_ok=True)
    reference, upload, raw = work / 'original.mp4', work / 'enviado.mp4', work / 'gerado.mp4'
    cut_reference(source, a.start, a.duration, reference)
    make_upload_clip(reference, upload, a.long_side)
    link = check_source_url(a.source_url) if a.source_url else temp_public_link(upload)
    job = generate(key, a.model, prompt, link)
    download(key, job, raw)
    conform(raw, reference, out)
    compare = out.with_name(out.stem + '-antes-e-depois.mp4')
    side_by_side(reference, out, compare)
    receipt = {
        'tool': 'gen_video_edit', 'provider': 'openrouter', 'model': a.model, 'change': a.change, 'prompt': prompt,
        'source': str(source), 'start': a.start, 'duration': a.duration,
        'sent_clip_sha256': hashlib.sha256(upload.read_bytes()).hexdigest(), 'sent_clip': probe(upload),
        'hosting': 'user_url' if a.source_url else 'temp_public_link:litterbox:1h',
        'generation_id': job.get('id'), 'estimated_usd': usd, 'cost_usd': (job.get('usage') or {}).get('cost'),
        'returned': probe(raw), 'output': str(out), 'output_info': probe(out), 'comparison': str(compare),
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    out.with_suffix('.receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('output', 'comparison', 'cost_usd', 'returned', 'output_info')},
                     ensure_ascii=False))


def cmd_patch(a):
    """Derived copy of the recording with [start, start+clip) replaced; audio stream untouched."""
    source, clip, out = Path(a.input), Path(a.clip), Path(a.out)
    if out.resolve() == source.resolve():
        raise ValueError('O original nunca é sobrescrito; escolha outro arquivo de saída.')
    if out.suffix.lower() != '.mov':
        raise ValueError('Use saída .mov para preservar o áudio original sem recodificar.')
    info, part = probe(source), probe(clip)
    if (even(info['width']), even(info['height'])) != (part['width'], part['height']):
        raise ValueError('O trecho gerado não tem o tamanho da gravação; gere-o com run a partir dela.')
    if a.start < 0 or a.start + part['duration'] > info['duration'] + 0.05:
        raise ValueError('O trecho não cabe na gravação nesse ponto.')
    end = a.start + part['duration']
    out.parent.mkdir(parents=True, exist_ok=True)
    graph = (f"[1:v]setpts=PTS-STARTPTS+{a.start:.3f}/TB[p];"
             f"[0:v][p]overlay=enable='between(t,{a.start:.3f},{end:.3f})':eof_action=pass[v]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-i', str(clip), '-filter_complex', graph,
         '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p',
         '-r', f'{info["fps"]:.5f}', '-c:a', 'copy', str(out)])
    result = probe(out)
    if abs(result['duration'] - info['duration']) > 0.1:
        raise ValueError('A cópia derivada ficou com duração diferente da gravação; não use.')
    print(json.dumps({'derived': str(out), 'replaced': [a.start, round(end, 3)], 'info': result}, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('models', help='modelos que editam vídeo e o preço atual')
    r = sub.add_parser('run', help='gera o trecho com a roupa e/ou o cenário trocados')
    r.add_argument('--input', required=True)
    r.add_argument('--start', type=float, required=True, help='segundo inicial na gravação')
    r.add_argument('--duration', type=float, required=True)
    r.add_argument('--change', choices=sorted(PROMPTS), required=True)
    r.add_argument('--describe', help='descrição em inglês da roupa/cenário novo')
    r.add_argument('--prompt', help='substitui o pedido montado (uso avançado)')
    r.add_argument('--out', required=True)
    r.add_argument('--model', default=DEFAULT_MODEL)
    r.add_argument('--source-url', help='link HTTPS público do trecho, hospedado pelo usuário')
    r.add_argument('--temp-public-link', action='store_true', help='link público temporário (1 h); exige consentimento')
    r.add_argument('--max-usd', type=float, default=0.50)
    r.add_argument('--accept-unknown-cost', action='store_true')
    r.add_argument('--long-side', type=int, default=1280, help='lado maior do trecho enviado')
    p = sub.add_parser('patch', help='cria uma cópia derivada da gravação com o trecho trocado')
    p.add_argument('--input', required=True)
    p.add_argument('--clip', required=True)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    try:
        {'models': cmd_models, 'run': cmd_run, 'patch': cmd_patch}[a.cmd](a)
    except ValueError as error:
        sys.exit(str(error))


if __name__ == '__main__':
    main()
