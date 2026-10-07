"""ScrapeCreators API client; credentials are loaded locally by service_keys.

usage: scrapecreators.py tt-search QUERY | yt-search QUERY | tt-video URL | yt-video URL
No yt-dlp, browser scraping or alternate provider. API errors never print credentials/body.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from service_keys import api_key

BASE = 'https://api.scrapecreators.com'


def key():
    return api_key('SCRAPECREATORS_API_KEY')


def get(path, **params):
    if not path.startswith(('/v1/', '/v2/')) or '..' in path or '?' in path:
        raise ValueError('Endpoint ScrapeCreators inválido.')
    request = urllib.request.Request(BASE + path + '?' + urllib.parse.urlencode(params),
                                     headers={'Accept': 'application/json'})
    # A provider redirect must never forward a credential to a CDN/other host.
    request.add_unredirected_header('x-api-key', key())
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f'ScrapeCreators HTTP {exc.code}: verifique a chave, os créditos e a disponibilidade da cena.') from None
    except (urllib.error.URLError, OSError):
        raise ValueError('ScrapeCreators indisponível: não foi possível concluir a conexão.') from None
    except (ValueError, UnicodeError):
        raise ValueError('ScrapeCreators retornou uma resposta inválida.') from None
    if not isinstance(result, dict) or result.get('success') is False:
        raise ValueError('ScrapeCreators não concluiu o pedido; confira chave, créditos ou disponibilidade da cena.')
    return result


def tt_search(q, **kw): return get('/v1/tiktok/search/keyword', query=q, trim='true', **kw)
def yt_search(q, **kw): return get('/v1/youtube/search', query=q, **kw)
def tt_video(url, **kw): return get('/v2/tiktok/video', url=url, **kw)
def yt_video(url, **kw): return get('/v1/youtube/video', url=url, **kw)

if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        fn = {'tt-search': tt_search, 'yt-search': yt_search, 'tt-video': tt_video, 'yt-video': yt_video}[sys.argv[1]]
        print(json.dumps(fn(sys.argv[2]), ensure_ascii=False)[:200000])
    except (ValueError, IndexError, KeyError) as exc:
        sys.exit(str(exc) if isinstance(exc, ValueError) else 'Informe a operação e a busca/link.')
