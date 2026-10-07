#!/usr/bin/env python3
"""Requested TikTok/YouTube scenes exclusively through ScrapeCreators.

search JOB QUERY [--platform tiktok|youtube|both]
get JOB ID=name [URL=name ...]
sheet JOB name [--every 2]

Search and metadata use ScrapeCreators; only media URLs returned by that API are downloaded.
No other extractor/provider fallback. Each authorized API call can consume credits.
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
from edit_support import read_data
from scrapecreators import get as sc_get, tt_video, yt_video


def api(path, **query):
    return sc_get('/v1/' + path, **query)


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:50] or 'busca'


def job_path(job):
    path = Path(job)
    manifest = read_data(path / 'job.yaml')
    current, legacy = manifest.get('format'), manifest.get('client')
    if current and legacy and current != legacy:
        raise ValueError('O trabalho informa formatos diferentes; resolva o cadastro antes de editar.')
    if not (current or legacy):
        raise ValueError('Qual formato devo usar neste vídeo? Informe ou cadastre o formato antes de editar.')
    if not manifest.get('visual_identity'):
        raise ValueError('Escolha uma ID visual junto do formato antes de editar.')
    return path


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def search(job, query, platform):
    directory = job_path(job) / 'assets/viral/search'
    directory.mkdir(parents=True, exist_ok=True)
    results = {}
    for service, prefix, endpoint in [('tiktok', 'tt', 'tiktok/search/keyword'), ('youtube', 'yt', 'youtube/search')]:
        if platform not in (service, 'both'):
            continue
        response = api(endpoint, query=query)
        dump(directory / f'{prefix}_{slug(query)}.json', response)
        results[service] = response
        print(service, query)
        if service == 'tiktok':
            for item in (response.get('search_item_list') or [])[:14]:
                video = item.get('aweme_info', item)
                print(video.get('aweme_id'), '@' + str((video.get('author') or {}).get('unique_id', '')), (video.get('desc') or '')[:90])
        else:
            for item in (response.get('shorts') or [])[:8] + (response.get('videos') or [])[:6]:
                print(item.get('id'), (item.get('title') or '')[:90])
    return results


def media_urls(response, platform):
    """Only extract explicit video file URLs; never mistake page/thumbnail URLs for media."""
    urls = []
    if platform == 'tiktok':
        item = response.get('aweme_detail') or response.get('aweme_info') or response
        video = item.get('video') or {}
        variants = sorted([b['play_addr'] for b in video.get('bit_rate', []) if b.get('play_addr')],
                          key=lambda p: -(p.get('width', 0) * p.get('height', 0)))
        for variant in variants + [video.get('play_addr') or {}, video.get('download_addr') or {}]:
            urls.extend(variant.get('url_list') or [])
        for value in (video.get('playAddr'), video.get('downloadAddr')):
            if isinstance(value, str): urls.append(value)
    else:
        formats = (response.get('downloadOptions') or {}).get('formats') or []
        for item in sorted(formats, key=lambda x: -(x.get('height') or 0)):
            # A silent video-only file is suitable for B-roll; audio-only formats are not.
            if item.get('url') and not str(item.get('mimeType', '')).startswith('audio/') and item.get('vcodec') != 'none':
                urls.append(item['url'])
    return list(dict.fromkeys(u for u in urls if isinstance(u, str) and urllib.parse.urlparse(u).scheme == 'https'))


def download(urls, output, platform):
    """Use temporary output and actual video probing; never accept an HTTP error page as MP4."""
    partial = output.with_suffix('.part.mp4')
    try:
        for url in urls:
            command = ['curl', '--fail', '--silent', '--location', '--max-time', '300',
                       '--proto', '=https', '--proto-redir', '=https', '-A', 'Mozilla/5.0']
            if platform == 'tiktok': command += ['-H', 'Referer: https://www.tiktok.com/']
            command += ['-o', str(partial), url]
            result = subprocess.run(command, capture_output=True)
            if result.returncode or not partial.is_file(): continue
            probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                    '-show_entries', 'stream=codec_type,width,height', '-of', 'json', str(partial)],
                                   capture_output=True, text=True)
            try: streams = json.loads(probe.stdout).get('streams', [])
            except ValueError: streams = []
            if probe.returncode == 0 and any(s.get('codec_type') == 'video' and s.get('width', 0) > 0 for s in streams):
                os.replace(partial, output)
                return True
        return False
    finally:
        partial.unlink(missing_ok=True)


def selection(value):
    source, separator, name = value.rpartition('=')
    if not separator or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', name):
        raise ValueError('Informe ID=nome ou LINK=nome; use um nome simples para a cena.')
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme:
        host = parsed.hostname or ''
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise ValueError('Informe um link público HTTPS do TikTok ou YouTube.')
        if host in ('tiktok.com', 'www.tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'):
            platform = 'tiktok'
        elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'):
            platform = 'youtube'
        else:
            raise ValueError('Informe um link do TikTok ou YouTube.')
        return source, name, platform, source
    if source.isdigit() and len(source) > 11:
        return source, name, 'tiktok', None
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', source):
        return source, name, 'youtube', f'https://www.youtube.com/watch?v={source}'
    raise ValueError('ID inválido; envie o link da cena ou use um ID retornado pela pesquisa.')


def get(job, pairs):
    directory = job_path(job) / 'assets/viral'
    selections = [selection(pair) for pair in pairs]  # validate all names before calls/writes
    if len({s[1] for s in selections}) != len(selections):
        raise ValueError('Cada cena precisa de um nome diferente.')
    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = directory / 'sources.json'
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else []
    outcomes = []
    for source, name, platform, url in selections:
        cached = None
        if platform == 'tiktok' and url is None:
            for filename in sorted(glob.glob(str(directory / 'search/tt_*.json'))):
                for item in json.loads(Path(filename).read_text()).get('search_item_list') or []:
                    item = item.get('aweme_info', item)
                    if str(item.get('aweme_id')) == source:
                        cached = item
                        author = (item.get('author') or {}).get('unique_id')
                        if author: url = f'https://www.tiktok.com/@{author}/video/{source}'
                        break
                if cached: break
        record = {'file': f'assets/viral/{name}.mp4', 'platform': platform, 'provider': 'scrapecreators',
                  'url': url, 'downloaded': False, 'status': 'missing_search_result'}
        try:
            response = cached or (tt_video(url) if platform == 'tiktok' and url else yt_video(url) if platform == 'youtube' else {})
            item = response.get('aweme_detail') or response.get('aweme_info') or response
            record.update(author=(item.get('author') or {}).get('unique_id') if platform == 'tiktok' else (response.get('channel') or {}).get('handle'),
                          desc=item.get('desc') if platform == 'tiktok' else response.get('title'))
            urls = media_urls(response, platform)
            ok = download(urls, directory / (name + '.mp4'), platform) if urls else False
            # Search URLs can expire; refresh once through the same API, never another extractor.
            if not ok and cached and url:
                response = tt_video(url)
                urls = media_urls(response, platform)
                ok = download(urls, directory / (name + '.mp4'), platform) if urls else False
            record.update(downloaded=ok, status='downloaded' if ok else 'media_unavailable' if url else 'missing_search_result',
                          note=None if ok else 'ScrapeCreators não forneceu mídia utilizável. Pesquise outra cena pelo mesmo serviço.')
        except ValueError as exc:
            record.update(status='api_error', note=str(exc))
        metadata = [m for m in metadata if m.get('file') != record['file']] + [record]
        dump(metadata_path, metadata)
        outcomes.append(record)
        print(name, platform, record['status'])
    return outcomes


def sheet(job, name, every):
    directory = job_path(job) / 'assets/viral'
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', name) or every <= 0:
        raise ValueError('Nome ou intervalo inválido para examinar a cena.')
    source = directory / (name + '.mp4')
    duration = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(source)], capture_output=True, text=True, check=True).stdout)
    count = int(duration / every) + 1; columns = min(12, count); rows = -(-count // columns)
    output = directory / (name + '-sheet.jpg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-vf', f'fps=1/{every},scale=200:-1,tile={columns}x{rows}:padding=3', '-frames:v', '1', '-update', '1', '-q:v', '4', str(output)], check=True)
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('search'); p.add_argument('job'); p.add_argument('query'); p.add_argument('--platform', choices=['tiktok', 'youtube', 'both'], default='both')
    p = commands.add_parser('get'); p.add_argument('job'); p.add_argument('pairs', nargs='+')
    p = commands.add_parser('sheet'); p.add_argument('job'); p.add_argument('name'); p.add_argument('--every', type=float, default=2)
    args = parser.parse_args()
    try:
        if args.command == 'search': search(args.job, args.query, args.platform)
        elif args.command == 'get':
            if not all(r['downloaded'] for r in get(args.job, args.pairs)): raise SystemExit(2)
        else: sheet(args.job, args.name, args.every)
    except (ValueError, OSError):
        # Configuration/API errors raised here contain no response body or key.
        if isinstance(sys.exc_info()[1], ValueError): sys.exit(str(sys.exc_info()[1]))
        sys.exit('Não foi possível ler/gravar o trabalho ou examinar a mídia; confira os arquivos locais.')
