#!/usr/bin/env python3
"""Export only author-distributed public data. Never read jobs or user memory/catalogues."""
import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
ENGINE = SITE.parents[1]
sys.path.insert(0, str(ENGINE / 'tools'))
from format_guides import DETAILS

EDITORIAL = {
    'F01': ('stories', ['Narração', 'Conversas'], 'Transformar uma explicação em uma conversa fácil de acompanhar.'),
    'F04': ('stories', ['Apresentador', 'Animação'], 'Abrir com a pessoa e explicar o restante com imagens.'),
    'F05': ('stories', ['Notícias', 'Recortes'], 'Explicar um assunto com a organização visual de uma matéria.'),
    'F06': ('explain', ['Diagramas', 'Processos'], 'Tornar uma ideia, relação ou processo mais fácil de entender.'),
    'F07': ('products', ['Interface', 'Sem apresentador'], 'Apresentar uma plataforma e demonstrar seus recursos.'),
    'F08': ('presenter', ['Apresentador', 'Telas e conversas'], 'Explicar conteúdos com a pessoa integrada ao cenário ou junto de uma tela ou conversa.'),
    'F10': ('products', ['Produto', 'Demonstração'], 'Apresentar um produto alternando pessoa, tela e uso real.'),
    'F12': ('stories', ['Narração', 'Histórias'], 'Contar uma história com imagens, dados e comparações.'),
    'F13': ('explain', ['Dados', 'Sem apresentador'], 'Explicar quantidades e comparações com mapas, pontos e rankings.'),
}
ORDER = ['F01', 'F12', 'F08', 'F09', 'F10', 'F07', 'F13', 'F03', 'F04', 'F05', 'F06']
POSTER_TIME = {'F01': 11, 'F04': 23, 'F05': 20, 'F06': 30, 'F07': 20, 'F08': 8, 'F10': 12, 'F12': 15, 'F13': 7}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def media_asset_id(item):
    code = item['code']
    asset = item.get('asset_id', code)
    if not isinstance(asset, str) or not re.fullmatch(re.escape(code) + r'(?:-[a-z0-9][a-z0-9-]{0,63})?', asset):
        raise ValueError('Identificação de mídia inválida: ' + code)
    return asset

def authorized_file(reference):
    path = ENGINE / reference['path']
    if path.is_symlink() or not path.resolve().is_relative_to(ENGINE) or digest(path) != reference['sha256']:
        raise ValueError('Referência não verificada: ' + reference['path'])
    return path

def diagram(code, name):
    labels = {'F04': ['01. PESSOA', 'O gancho abre a história', '02. ANIMAÇÃO', 'A voz continua. A cena explica.'],
              'F06': ['01. IDEIA', 'Uma relação para explicar', '02. DIAGRAMA', 'Etapas. Conexões. Clareza.'],
              'F13': ['01. DADOS', 'A pergunta define a comparação', '02. ESCALA', 'Mapas. Quantidades. Comparações.']}[code]
    shape = '<circle cx="270" cy="350" r="38" fill="#b0b9a7"/><path d="M220 406q0-45 50-45t50 45" fill="#b0b9a7"/>' if code == 'F04' else ''.join(f'<circle cx="{150+(i%10)*25}" cy="{318+(i//10)*20}" r="6" fill="#536851"/>' for i in range(40))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="540" height="960" viewBox="0 0 540 960">
<rect width="540" height="960" fill="#e6e9df"/><g fill="#25342e" font-family="sans-serif">
<text x="38" y="62" font-size="17" letter-spacing="2">ESQUEMA DO FORMATO · {code}</text>
<text x="38" y="166" font-size="36" font-weight="700">{html.escape(name).replace(' → ', ' / ')}</text>
<rect x="38" y="230" width="464" height="202" rx="10" fill="#f5f5ef"/>
<text x="65" y="280" font-size="17" letter-spacing="2">{labels[0]}</text>
{shape}
<path d="M270 455v70m-13-13 13 13 13-13" fill="none" stroke="#536851" stroke-width="3"/>
<rect x="38" y="550" width="464" height="250" rx="10" fill="#25342e"/>
<g fill="#edf0e5"><text x="65" y="600" font-size="17" letter-spacing="2">{labels[2]}</text>
<rect x="80" y="645" width="105" height="50" rx="6" fill="#9cb890"/><rect x="355" y="645" width="105" height="50" rx="6" fill="#9cb890"/>
<path d="M196 670h143m-12-10 12 10-12 10" fill="none" stroke="#edf0e5" stroke-width="3"/>
<text x="65" y="757" font-size="19">{labels[3]}</text></g>
<text x="38" y="895" font-size="17">Guia ilustrativo. Não é uma execução em vídeo.</text></g></svg>'''

def export(media=False):
    defaults = json.loads((ENGINE / 'config/design-defaults.json').read_text())
    publication = json.loads((SITE / 'publication.json').read_text())
    descriptors = json.loads((SITE / 'descriptors.json').read_text())
    library = json.loads((ENGINE / 'config/reference-library.json').read_text())
    vimeo = json.loads((SITE / 'vimeo.json').read_text())
    output = SITE / 'public'
    for name in ['assets/posters', 'assets/videos', 'assets/fonts']:
        (output / name).mkdir(parents=True, exist_ok=True)
    formats = []
    for item in sorted(publication['formats'], key=lambda item: int(item['code'][1:])):
        code = item['code']
        asset_id = media_asset_id(item)
        if code in publication['excluded_codes']: raise ValueError('Um formato descartado não pode ser publicado: ' + code)
        stock = next((f for f in defaults['formats'] if f['code'] == code), None)
        group = library['formats'].get(code, {})
        if not stock or group.get('uid') != stock.get('uid') or (item.get('uid') and item['uid'] != stock['uid']) or stock['uid'] in publication.get('excluded_uids', []):
            raise ValueError('A geração da referência não corresponde ao formato ativo: ' + code)
        descriptor = descriptors.get(code)
        if not descriptor: raise ValueError('Complete os descritores de busca antes de publicar ' + code)
        spec = item.get('mechanism_details') or DETAILS.get(code)
        if not spec: raise ValueError('Complete o guia de edição antes de publicar ' + code)
        category, tags, use = EDITORIAL[code] if code in EDITORIAL else (descriptor['category'], descriptor['tags'], descriptor['use'])
        references = library['formats'].get(code, {}).get('references', [])
        references = publication.get('reference_media', {}).get(code, []) + references
        video_ref = next((r for r in references if r['path'].endswith('.mp4')), None)
        data = { 'code': code, 'name': item['name'], 'description': item['description'],
                 'category': category, 'tags': tags, 'use': use, 'inputs': spec['inputs'],
                 'mechanism': spec['mechanism'], 'steps': spec['steps'], 'avoid': spec['avoid'],
                 'pattern': item['pattern'], 'video': None, 'vimeo': vimeo.get(code), 'duration': None,
                 'evidence': 'image', 'evidenceLabel': 'Referência em imagem',
                 'evidenceNote': 'As imagens ajudam a entender a proposta. Ainda não há uma execução em vídeo neste acervo.' }
        data.update(descriptor)
        if video_ref:
            source = authorized_file(video_ref)
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-show_streams', '-show_format', '-of', 'json', str(source)]))
            data.update(video=f'assets/videos/{asset_id}.mp4', poster=f'assets/posters/{asset_id}.jpg',
                        duration=round(float(probe['format']['duration'])), evidence='video', evidenceLabel='Exemplo em vídeo')
            data['evidenceNote'] = 'Vídeo histórico de referência. A pessoa, marca, cores e fontes deste exemplo não são escolhas para a sua edição.'
            if video_ref.get('evidence_label'): data['evidenceLabel'] = video_ref['evidence_label']
            if video_ref.get('evidence_note'): data['evidenceNote'] = video_ref['evidence_note']
            if code == 'F07':
                data['evidenceLabel'] = 'Prévia histórica'
                data['evidenceNote'] = 'Prévia histórica de uma interface. Demonstra cenas do formato, sem representar a conclusão de uma nova edição.'
            if code in ['F12', 'F13']:
                data['evidenceLabel'] = 'Referência externa'
                data['evidenceNote'] = 'Referência externa que orienta a receita. Não é um novo vídeo produzido pela fábrica.'
            video_out = output / data['video']
            poster_out = output / data['poster']
            if media and not video_out.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(source), '-map', '0:v:0', '-map', '0:a?', '-vf', 'scale=480:854:force_original_aspect_ratio=decrease,pad=480:854:(ow-iw)/2:(oh-ih)/2', '-r', '24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '29', '-maxrate', '850k', '-bufsize', '1700k', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', '-y', str(video_out)], check=True)
            if media and not poster_out.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', str(POSTER_TIME.get(code, min(3, float(probe['format']['duration']) * .15))), '-i', str(source), '-frames:v', '1', '-vf', 'scale=540:-2', '-q:v', '3', '-y', str(poster_out)], check=True)
        elif code in ['F04', 'F06', 'F13']:
            data.update(poster=f'assets/posters/{code}.svg', evidence='guide', evidenceLabel='Guia ilustrativo')
            (output / data['poster']).write_text(diagram(code, item['name']))
        else:
            reference = next(r for r in references if r['path'].endswith(('.jpg', '.jpeg', '.png')))
            source = authorized_file(reference)
            data['poster'] = f'assets/posters/{code}{source.suffix}'
            shutil.copyfile(source, output / data['poster'])
        data['referenceFrames'] = []
        for index, frame in enumerate(publication.get('reference_frames', {}).get(code, [])):
            source = authorized_file(frame['reference'])
            if source.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                raise ValueError('Quadro de referência precisa ser uma imagem real.')
            target = f'assets/posters/{asset_id}-frame-{index}{source.suffix.lower()}'
            shutil.copyfile(source, output / target)
            data['referenceFrames'].append({'poster': target, 'caption': frame['caption']})
        data['examples'] = []
        for variant in publication.get('extra_examples', {}).get(code, []):
            if not variant['id'].replace('-', '').isalnum(): raise ValueError('Código de exemplo inválido.')
            source = authorized_file(variant['reference'])
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-show_format', '-of', 'json', str(source)]))
            suffix = asset_id + '-' + variant['id']
            example = {'id': variant['id'], 'label': variant['label'], 'video': f'assets/videos/{suffix}.mp4', 'poster': f'assets/posters/{suffix}.jpg',
                       'duration': round(float(probe['format']['duration'])), 'evidenceLabel': 'Exemplo histórico',
                       'evidenceNote': 'Outra variação do mesmo formato: pessoa explicando telas e conversas. A identidade do exemplo não é uma escolha automática.'}
            video_out = output / example['video']; poster_out = output / example['poster']
            if media and not video_out.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(source), '-map', '0:v:0', '-map', '0:a?', '-vf', 'scale=480:854:force_original_aspect_ratio=decrease,pad=480:854:(ow-iw)/2:(oh-ih)/2', '-r', '24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '29', '-maxrate', '850k', '-bufsize', '1700k', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', '-y', str(video_out)], check=True)
            if media and not poster_out.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', '15', '-i', str(source), '-frames:v', '1', '-vf', 'scale=540:-2', '-q:v', '3', '-y', str(poster_out)], check=True)
            data['examples'].append(example)
        formats.append(data)
    formats.sort(key=lambda f: int(f['code'][1:]))
    identities = []
    for item in defaults['visual_identities']:
        # Published presets only. Never resolve the mutable context/visual-identities path.
        preset = json.loads((ENGINE / f"config/visual-presets/{item['code']}/identity-v1.json").read_text())
        identities.append({key: preset[key] for key in ['code', 'name', 'palette', 'typography']})
    for name in ['manrope-variable.ttf', 'libre-baskerville-variable.ttf', 'jetbrains-mono-variable.ttf',
                 'ibm-plex-mono-400-latin.woff2', 'inter-400-latin.woff2', 'inter-600-latin.woff2', 'inter-800-latin.woff2']:
        shutil.copyfile(ENGINE / 'assets/fonts/portable' / name, output / 'assets/fonts' / name)
    catalog = { 'schema': 1, 'scope': 'author_distributed_stock_only', 'formats': formats, 'identities': identities,
                'categories': [{'id': 'all', 'label': 'Todos os modelos'}, {'id': 'presenter', 'label': 'Com apresentador'},
                               {'id': 'stories', 'label': 'Histórias e narração'}, {'id': 'products', 'label': 'Produtos e telas'},
                               {'id': 'explain', 'label': 'Ideias e processos'}] }
    (output / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    (SITE / 'provenance.json').write_text(json.dumps({'scope': catalog['scope'], 'catalog_sha256': digest(output / 'catalog.json'),
        'publication_sha256': digest(SITE / 'publication.json'),
        'excluded_codes': publication['excluded_codes'],
        'sources': {p: digest(ENGINE / p) for p in ['config/design-defaults.json', 'config/reference-library.json', 'tools/format_guides.py']},
        'media_policy': 'Verified author-indexed originals preserved. Web derivatives only; no jobs, user catalogues or memory included.'}, indent=2) + '\n')
    print(json.dumps({'formats': len(formats), 'videos': sum(bool(f['video']) for f in formats), 'identities': len(identities)}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--media', action='store_true')
    export(parser.parse_args().media)
