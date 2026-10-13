#!/usr/bin/env python3
"""Download a YouTube video through Apify when ScrapeCreators returns no media file.

usage: apify_youtube.py URL OUTPUT.mp4 [--quality 1080p] [--run-id ID]

Author order (2026-10-13): ScrapeCreators stays first for YouTube; when its /v1/youtube/video
response exposes no downloadable format, Apify actor streamers/youtube-video-downloader is the
approved second provider. No yt-dlp or browser scraping. Each run consumes Apify credits.
The token is loaded by service_keys and sent only in a header, never printed or put in argv.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from service_keys import api_key

ACTOR = 'streamers~youtube-video-downloader'
BASE = 'https://api.apify.com/v2'


def call(path, payload=None, timeout=900):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(BASE + path, data=data, method='POST' if data else 'GET',
                                     headers={'Content-Type': 'application/json'})
    request.add_unredirected_header('Authorization', 'Bearer ' + api_key('APIFY_API_TOKEN'))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f'Apify HTTP {exc.code}: confira o token, os créditos e o link do vídeo.') from None
    except (urllib.error.URLError, OSError):
        raise ValueError('Apify indisponível: não foi possível concluir a conexão.') from None


def media_url(item):
    """The muxed MP4 stored by the actor (downloadedFileUrl); HLS manifests are not files."""
    link = item.get('downloadedFileUrl')
    return [link] if isinstance(link, str) and link.startswith('https://api.apify.com/') else []


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration',
                             '-of', 'json', str(path)], capture_output=True, text=True)
    try:
        return json.loads(result.stdout) if result.returncode == 0 else None
    except ValueError:
        return None


def download(url, output, quality, run_id=None):
    # Long videos exceed the 300 s synchronous limit (HTTP 408): start, poll, then read the dataset.
    # --run-id resumes an earlier run so a timeout never pays for the same download twice.
    if not run_id:
        run = call(f'/acts/{ACTOR}/runs', {'videos': [{'url': url}], 'preferredQuality': quality,
                                           'preferredFormat': 'mp4', 'storeInKVStore': True})['data']
        run_id = run['id']
        print('apify run', run_id, file=sys.stderr, flush=True)
    while True:
        run = call(f'/actor-runs/{run_id}?waitForFinish=60', timeout=120)['data']
        if run['status'] not in ('READY', 'RUNNING'):
            break
    if run['status'] != 'SUCCEEDED':
        raise ValueError(f'Execução do Apify terminou como {run["status"]}.')
    items = call(f"/datasets/{run['defaultDatasetId']}/items?clean=1")
    if not isinstance(items, list) or not items:
        raise ValueError('Apify não devolveu nenhum item para este vídeo.')
    items = [i for i in items if i.get('id') and i['id'] in url]
    if not items:
        raise ValueError('O resultado do Apify não corresponde ao vídeo pedido.')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix('.part.mp4')
    record = {'provider': 'apify', 'actor': ACTOR, 'run_id': run_id, 'url': url, 'requested_quality': quality,
              'cost_usd': run.get('usageTotalUsd'),
              'item_keys': sorted(items[0].keys()), 'downloaded': False}
    try:
        for link in media_url(items[0]):
            # The KV-store link may need the same token; send it only to api.apify.com.
            request = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
            if urllib.parse.urlparse(link).hostname == 'api.apify.com':
                request.add_unredirected_header('Authorization', 'Bearer ' + api_key('APIFY_API_TOKEN'))
            try:
                with urllib.request.urlopen(request, timeout=900) as response, open(partial, 'wb') as stream:
                    while chunk := response.read(1 << 20):
                        stream.write(chunk)
            except (urllib.error.URLError, OSError):
                continue
            info = probe(partial)
            if info and any(s.get('codec_type') == 'video' and s.get('width', 0) > 0 for s in info.get('streams', [])):
                os.replace(partial, output)
                video = next(s for s in info['streams'] if s.get('codec_type') == 'video')
                record.update(downloaded=True, file=str(output.name), width=video['width'], height=video['height'],
                              has_audio=any(s.get('codec_type') == 'audio' for s in info['streams']),
                              duration=float(info.get('format', {}).get('duration') or 0))
                break
    finally:
        partial.unlink(missing_ok=True)
    if not record['downloaded']:
        record['note'] = 'Apify não forneceu um arquivo de vídeo válido.'
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('output')
    parser.add_argument('--quality', default='1080p')
    parser.add_argument('--run-id', help='Retomar uma execução já iniciada no Apify')
    args = parser.parse_args()
    try:
        print(json.dumps(download(args.url, args.output, args.quality, args.run_id), ensure_ascii=False, indent=2))
    except ValueError as exc:
        sys.exit(str(exc))
