#!/usr/bin/env python3
"""Generate YouTube cover (thumbnail) options with the newest OpenAI image model on OpenRouter.

usage:
  python3 tools/gen_thumbnails.py models
  python3 tools/gen_thumbnails.py run JOB --brief JOB/thumbs/brief.json [--model auto]

brief.json: {"options": [{"name": "opcao-1", "prompt": "...", "refs": ["thumbs/refs/rosto.jpg", ...]}, ...]}
`refs` are job-relative images (real frames of the presenter, author-approved style references).
Each option is one paid image call; record authorization in the job decision log. The model is
resolved from the live OpenRouter list at run time ("sempre o mais recente"): the newest non-mini
openai/gpt-image* entry; the chosen id, the candidates and the reported cost go to thumbs/receipt.json.
Loads OPENROUTER_API_KEY through service_keys; the key is sent only to openrouter.ai.
"""
import argparse, base64, json, mimetypes, re, sys, time
from pathlib import Path
from gen_video_edit import API, http, api
from service_keys import api_key


def image_models():
    status, raw = http(API + '/models?output_modalities=image')
    if status != 200:
        raise ValueError('Não foi possível consultar a lista de modelos da OpenRouter.')
    models = [m for m in json.loads(raw)['data']
              if re.match(r'openai/gpt-image', m['id']) and 'mini' not in m['id']
              and 'image' in (m.get('architecture', {}).get('input_modalities') or [])]
    return sorted(models, key=lambda m: (-m.get('created', 0), m['id']))


def newest():
    models = image_models()
    if not models:
        raise ValueError('Nenhum modelo GPT Image disponível na OpenRouter agora.')
    top = models[0].get('created', 0)
    return models[0]['id'], [m['id'] for m in models if m.get('created', 0) == top]


def data_url(path):
    kind = mimetypes.guess_type(path.name)[0] or 'image/jpeg'
    return f'data:{kind};base64,' + base64.b64encode(path.read_bytes()).decode()


def generate(key, model, prompt, refs):
    content = [{'type': 'text', 'text': prompt}] + [{'type': 'image_url', 'image_url': {'url': data_url(r)}} for r in refs]
    body = {'model': model, 'modalities': ['image'], 'messages': [{'role': 'user', 'content': content}],
            'image_config': {'aspect_ratio': '16:9'}}
    response = api('/chat/completions', key, body)
    images = (response.get('choices') or [{}])[0].get('message', {}).get('images') or []
    if not images:
        raise ValueError('O modelo não devolveu imagem para esta opção.')
    url = images[0]['image_url']['url']
    if not url.startswith('data:image/'):
        raise ValueError('Formato de imagem inesperado devolvido pelo serviço.')
    return base64.b64decode(url.split(',', 1)[1]), (response.get('usage') or {}).get('cost')


def run(job, brief_path, model):
    job = Path(job)
    brief = json.loads(Path(brief_path).read_text(encoding='utf-8'))
    options = brief.get('options') or []
    if not options:
        raise ValueError('O brief não tem opções de capa.')
    tied = []
    if model == 'auto':
        model, tied = newest()
    out = job / 'thumbs'
    out.mkdir(parents=True, exist_ok=True)
    key = api_key('OPENROUTER_API_KEY')
    if not key:
        raise ValueError('Falta OPENROUTER_API_KEY no arquivo CHAVES DAS INTEGRAÇÕES.txt.')
    receipt = {'model': model, 'same_date_candidates': tied, 'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'options': []}
    for option in options:
        name = option['name']
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,40}', name):
            raise ValueError('Nome de opção inválido.')
        refs = [job / r for r in option.get('refs', [])]
        for ref in refs:
            if not ref.resolve().is_relative_to(job.resolve()) or not ref.is_file():
                raise ValueError(f'Referência ausente ou fora do trabalho: {ref.name}')
        raw, cost = generate(key, model, option['prompt'], refs)
        target = out / f'{name}.png'
        target.write_bytes(raw)
        receipt['options'].append({'name': name, 'file': f'thumbs/{target.name}', 'refs': option.get('refs', []), 'cost_usd': cost})
        print(name, target, cost)
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('models')
    p = commands.add_parser('run'); p.add_argument('job'); p.add_argument('--brief', required=True); p.add_argument('--model', default='auto')
    args = parser.parse_args()
    try:
        if args.command == 'models':
            chosen, tied = newest()
            print(json.dumps({'newest': chosen, 'same_date_candidates': tied, 'all': [m['id'] for m in image_models()]}, indent=2))
        else:
            run(args.job, args.brief, args.model)
    except ValueError as exc:
        sys.exit(str(exc))
