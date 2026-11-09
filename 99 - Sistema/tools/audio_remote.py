"""Explicit paid audio calls. No import-time keys, retries, redirects, or body logging.

OpenRouter (music with Google Lyria 3 and narration/TTS) and the optional ElevenLabs Voice
Isolator live here, in one place. Every call needs the user's current yes for that spend; the
caller checks --accept-paid before anything here runs. Keys are read only at call time.
"""
from pathlib import Path
import base64
import json
import time
try:
    import requests
except ImportError:  # instalado pela capacidade base
    requests = None
from service_keys import api_key
MAX_RESPONSE_BYTES = 128 * 1024 * 1024
MAX_SECONDS = 600
OPENROUTER = 'https://openrouter.ai/api/v1'
OPENROUTER_ENDPOINTS = ('/chat/completions', '/audio/speech', '/key')
MISSING_REQUESTS = 'Falta o pacote requests no Python do Cortez. A IA deve rodar factory.py dependencies --capability base --apply e tentar de novo.'


def eleven_request(endpoint, output=None, payload=None, audio=None, method='POST'):
    # Decisão do dono 09/11/2026: ElevenLabs só trata ruído. Música e narração são pelo OpenRouter.
    if endpoint != '/v1/audio-isolation':
        raise ValueError('Endpoint ElevenLabs não permitido: o ElevenLabs agora só isola ruído. Música e narração são pelo OpenRouter.')
    if requests is None: raise ValueError(MISSING_REQUESTS)
    with requests.Session() as session:
        session.trust_env = False
        headers = {'xi-api-key': api_key('ELEVENLABS_API_KEY')}
        kwargs = {'headers': headers, 'timeout': (20, 60), 'allow_redirects': False, 'stream': True}
        if payload is not None: kwargs['json'] = payload
        try:
            if audio:
                with Path(audio).open('rb') as stream:
                    response = session.request(method, 'https://api.elevenlabs.io' + endpoint,
                                               files={'audio': ('audio.wav', stream, 'audio/wav')}, **kwargs)
            else:
                response = session.request(method, 'https://api.elevenlabs.io' + endpoint, **kwargs)
            with response:
                if response.status_code != 200:
                    raise ValueError(f'ElevenLabs HTTP {response.status_code}; confira a chave opcional e os créditos.')
                started = time.monotonic()
                limit = MAX_RESPONSE_BYTES
                size = 0
                stream = Path(output).open('xb') if output else None
                data = bytearray()
                try:
                    for chunk in response.iter_content(1024 * 1024):
                        size += len(chunk)
                        if size > limit or time.monotonic() - started > MAX_SECONDS:
                            raise ValueError('Resposta ElevenLabs excedeu o limite de tamanho ou tempo.')
                        if stream: stream.write(chunk)
                        else: data.extend(chunk)
                except Exception:
                    if stream:
                        stream.close(); Path(output).unlink(missing_ok=True)
                    raise
                finally:
                    if stream: stream.close()
                if not output:
                    try: return json.loads(data)
                    except (ValueError, UnicodeError): raise ValueError('Resposta ElevenLabs inválida.') from None
        except requests.RequestException:
            raise ValueError('Falha de conexão com ElevenLabs; não houve tentativa automática adicional.') from None


# ---------------------------------------------------------------- OpenRouter

def _provider_message(response):
    """Short provider error text (never the request, never headers). Bounded to avoid log dumps."""
    try:
        raw = response.raw.read(16 * 1024, decode_content=True) if getattr(response, 'raw', None) else b''
        error = json.loads(raw or b'{}').get('error')
    except Exception:
        return ''
    message = error.get('message') if isinstance(error, dict) else error
    return ' '.join(str(message).split())[:200] if message else ''


def openrouter_error(status, detail=''):
    """Plain-language message for a failed OpenRouter call. Never retried automatically."""
    if status == 401:
        return ('A OpenRouter recusou a chave (HTTP 401). Confira OPENROUTER_API_KEY no arquivo '
                '“CHAVES DAS INTEGRAÇÕES.txt” (guia: 03 - Ajuda/COMO CONFIGURAR O OPENROUTER.html). Nada foi gerado.')
    if status == 402:
        return ('A conta da OpenRouter está sem créditos (HTTP 402). Nada foi gerado. Adicione créditos em '
                'https://openrouter.ai/settings/credits ou use a biblioteca local de trilhas.')
    if status == 429 or status >= 500:
        return (f'O serviço da OpenRouter está instável agora (HTTP {status}). Não houve nova tentativa automática, '
                'para não cobrar duas vezes. Tente mais tarde ou use a biblioteca local de trilhas.')
    return f'A OpenRouter recusou o pedido (HTTP {status}). {detail}'.strip()


def _openrouter_post(endpoint, payload, read_timeout):
    if endpoint not in OPENROUTER_ENDPOINTS:
        raise ValueError('Endpoint OpenRouter não permitido.')
    if requests is None: raise ValueError(MISSING_REQUESTS)
    key = api_key('OPENROUTER_API_KEY')
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.request('GET' if payload is None else 'POST', OPENROUTER + endpoint,
                                   headers={'Authorization': 'Bearer ' + key}, json=payload,
                                   timeout=(20, read_timeout), allow_redirects=False, stream=True)
    except requests.RequestException:
        session.close()
        raise ValueError('Falha de conexão com a OpenRouter; não houve tentativa automática adicional.') from None
    if response.status_code != 200:
        detail = _provider_message(response)
        response.close(); session.close()
        raise ValueError(openrouter_error(response.status_code, detail))
    return session, response


def _bounded(response):
    started, size = time.monotonic(), 0
    for chunk in response.iter_content(256 * 1024):
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES or time.monotonic() - started > MAX_SECONDS:
            raise ValueError('Resposta da OpenRouter excedeu o limite de tamanho ou tempo.')
        yield chunk


def _lines(response):
    pending = b''
    for chunk in _bounded(response):
        pending += chunk
        *complete, pending = pending.split(b'\n')
        for line in complete:
            yield line.rstrip(b'\r')
    if pending:
        yield pending.rstrip(b'\r')


def parse_music_stream(lines):
    """Join the base64 audio pieces of an OpenRouter SSE stream. Returns audio bytes, text, cost, id."""
    pieces, text, cost, generation = [], [], None, None
    for line in lines:
        if not line.startswith(b'data:'):
            continue  # blank separators and ': OPENROUTER PROCESSING' keep-alive comments
        data = line[5:].strip()
        if data == b'[DONE]':
            break
        try:
            event = json.loads(data)
        except ValueError:
            raise ValueError('Resposta da OpenRouter em formato inesperado; nada foi salvo.') from None
        if event.get('error'):
            error = event['error']
            message = error.get('message') if isinstance(error, dict) else error
            raise ValueError('A geração falhou no meio do caminho: ' + ' '.join(str(message).split())[:200]
                             + '. Confira em https://openrouter.ai/activity se houve cobrança.')
        generation = event.get('id') or generation
        usage = event.get('usage') or {}
        if usage.get('cost') is not None:
            cost = float(usage['cost'])
        for choice in event.get('choices') or []:
            delta = choice.get('delta') or {}
            audio = delta.get('audio') or {}
            if audio.get('data'):
                pieces.append(audio['data'])
            if delta.get('content'):
                text.append(delta['content'])
    if not pieces:
        raise ValueError('A OpenRouter respondeu sem áudio. Confira em https://openrouter.ai/activity se houve cobrança.')
    try:
        audio = base64.b64decode(''.join(pieces), validate=True)
    except ValueError:
        raise ValueError('O áudio recebido da OpenRouter veio corrompido; nada foi salvo.') from None
    return {'audio': audio, 'text': ''.join(text).strip()[:500], 'cost_usd': cost, 'generation_id': generation}


def openrouter_music(model, prompt):
    """One paid music generation (Google Lyria 3) by streamed chat completion. No retries."""
    payload = {'model': model, 'stream': True, 'modalities': ['text', 'audio'], 'audio': {'format': 'mp3'},
               'messages': [{'role': 'user', 'content': prompt}]}
    session, response = _openrouter_post('/chat/completions', payload, 240)
    try:
        with response:
            return parse_music_stream(_lines(response))
    except requests.RequestException:
        raise ValueError('A conexão com a OpenRouter caiu durante a geração. Não houve nova tentativa; '
                         'confira em https://openrouter.ai/activity se houve cobrança.') from None
    finally:
        session.close()


def openrouter_speech(payload, output):
    """One paid TTS call. Writes the raw audio (not JSON) and returns its content type and generation id."""
    session, response = _openrouter_post('/audio/speech', payload, 240)
    try:
        with response:
            kind = response.headers.get('Content-Type', '')
            if not kind.lower().startswith('audio/'):
                raise ValueError('A OpenRouter não devolveu áudio para a narração; nada foi salvo.')
            with Path(output).open('xb') as stream:
                try:
                    for chunk in _bounded(response):
                        stream.write(chunk)
                except Exception:
                    stream.close(); Path(output).unlink(missing_ok=True)
                    raise
            return {'content_type': kind, 'generation_id': response.headers.get('X-Generation-Id')}
    except requests.RequestException:
        Path(output).unlink(missing_ok=True)
        raise ValueError('A conexão com a OpenRouter caiu durante a narração; não houve nova tentativa.') from None
    finally:
        session.close()


def openrouter_key_status():
    """Free check of the key (no generation). Returns only limits/usage; never the key or its label."""
    session, response = _openrouter_post('/key', None, 30)
    try:
        with response:
            data = json.loads(b''.join(_bounded(response)) or b'{}').get('data') or {}
    except (ValueError, requests.RequestException):
        raise ValueError('Não foi possível ler a resposta da conferência da chave.') from None
    finally:
        session.close()
    return {'ok': True, 'key_accepted': True, 'limit_usd': data.get('limit'), 'limit_remaining_usd': data.get('limit_remaining'),
            'usage_usd': data.get('usage'), 'is_free_tier': data.get('is_free_tier'), 'values_exposed': False}
