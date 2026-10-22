"""Explicit paid ElevenLabs calls. No import-time keys, retries, redirects, or body logging."""
from pathlib import Path
import json
import time
import requests
from service_keys import api_key
MAX_RESPONSE_BYTES = 128 * 1024 * 1024


def eleven_request(endpoint, output=None, payload=None, audio=None, method='POST'):
    if endpoint not in ('/v1/audio-isolation', '/v1/music', '/v2/voices') and not endpoint.startswith('/v1/text-to-speech/'):
        raise ValueError('Endpoint ElevenLabs não permitido.')
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
                        if size > limit or time.monotonic() - started > 600:
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
