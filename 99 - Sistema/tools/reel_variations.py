#!/usr/bin/env python3
"""Variações de um reel para teste (A/B) — qualquer formato, qualquer quantidade.

Pedido do autor (20/10/2026): "cria um processo de criar variações para reels de teste, assim como você fez 5 reels do
Felca. Qualquer pessoa pode querer fazer algo semelhante na quantidade que quiser." Processo: workflows/REEL_VARIATIONS.md.

Duas estratégias (podem ser misturadas no mesmo plano):
- hook: a edição é refeita com outro gancho visual nos primeiros segundos E com detalhes diferentes no resto
  (legenda, transições, B-roll equivalente, cor, trilha, cartela final). Mesma voz e cortes.
- post: o vídeo pronto é embalado como print de post (mecânica do F19 Print Repost): cabeçalho com foto, nome e @,
  frase-gancho com destaque e uma foto chamativa parada ao lado do vídeo. Cada variação troca a foto e/ou a frase.

Comandos (local, sem rede):
  plan  --out <job>/variations/plan.json --count N [--strategy hook|post|mixed] [--base-name NOME]
        cria o plano com N linhas já distribuídas (ganchos, legendas, transições e cores diferentes) para preencher.
  check --plan <plan.json>           confere se nenhuma variação repete outra e se os campos obrigatórios existem.
  post  --plan <plan.json> --var 03 --identity ID05 [--root <instalação>]
        gera a variação "post" com as cores e a fonte da ID visual escolhida (nunca de um formato).
Caminhos dentro do plano são relativos à pasta do trabalho (a pasta acima de variations/).
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ENGINE = TOOLS.parent

HOOKS = [
    ('tarja-pergunta', 'Tela dividida: mídia do assunto em cima, tarja com a pergunta-gancho na emenda, pessoa embaixo.'),
    ('react-recorte', 'React: vídeo do assunto em tela cheia e a pessoa recortada (sem fundo) no canto.'),
    ('anel-quem-e', 'Prova em cartão com anel/seta no detalhe e rótulo curto ("QUEM É ELA?"); pessoa em círculo.'),
    ('revelacao-escrita', 'A revelação escrita em letras grandes desde o 1º quadro sobre a mídia (ex.: scanner/HUD).'),
    ('ache-a-diferenca', 'Duas versões lado a lado ("vídeo 1 × vídeo 2") desde o 1º quadro.'),
    ('contagem', 'Relógio/contagem regressiva até o momento-chave da história.'),
    ('manchetes', 'Manchetes reais entrando em sequência com a linha relevante marcada.'),
    ('expectativa-realidade', 'Expectativa × realidade em tela dividida desde o 1º quadro.'),
    ('numero-gigante', 'O número mais forte do vídeo em tela cheia, contando até o valor.'),
    ('pergunta-direta', 'A pessoa em tela cheia fazendo a pergunta, com a frase escrita grande.'),
]
CAPTIONS = ['branca-sublinhado-4-palavras', 'caixa-cor-maiusculas-3', 'uma-palavra-grande', 'karaoke-2-linhas',
            'mono-caixa-escura', 'contorno-6-palavras']
TRANSITIONS = ['zoom-suave', 'deslize-lateral', 'flash', 'zoom-para-fora', 'entrada-desfoque', 'corte-seco']
GRADES = ['neutra', 'saturacao+', 'levemente-quente', 'contraste+', 'levemente-fria', 'suave']


def var_id(i: int) -> str:
    return f'VAR{i:02d}'


def plan(count: int, strategy: str = 'hook', base_name: str = 'video') -> dict:
    if count < 1:
        raise ValueError('count deve ser ≥ 1')
    rows = []
    for i in range(count):
        kind = strategy if strategy != 'mixed' else ('hook' if i % 2 == 0 else 'post')
        vid = var_id(i + 1)
        if kind == 'hook':
            slug, desc = HOOKS[i % len(HOOKS)]
            rows.append({'id': vid, 'strategy': 'hook', 'hook': slug, 'hook_description': desc,
                         'caption_style': CAPTIONS[i % len(CAPTIONS)], 'transition': TRANSITIONS[i % len(TRANSITIONS)],
                         'grade': GRADES[i % len(GRADES)], 'music': f'trilha-{i + 1:02d}', 'end_card_text': '',
                         'broll_offsets': 'variar pontos de entrada equivalentes', 'output': f'{base_name}_{vid}-{slug}.mp4'})
        else:
            rows.append({'id': vid, 'strategy': 'post', 'video': '', 'photo': {'src': '', 't': None, 'crop': None, 'fit': 'cover', 'ring': None},
                         'lines': [[['', False]], [['', False], ['', True]]], 'emoji': '', 'output': f'{base_name}_{vid}-post.mp4'})
    return {'version': 1, 'base_name': base_name, 'strategy': strategy, 'count': count,
            'header': {'name': '', 'handle': '', 'avatar': '', 'avatar_crop': None, 'verified': False},
            'notes': 'Preencher cada linha; rodar `check`; mesma voz/fatos em todas; nada de foto/frase enganosa.',
            'variations': rows}


def _phrase(row: dict) -> str:
    return ' '.join(''.join(t for t, _ in line) for line in row.get('lines', [])).strip().casefold()


def check(p: dict) -> dict:
    problems, warnings = [], []
    rows = p.get('variations', [])
    ids = [r.get('id') for r in rows]; outs = [r.get('output') for r in rows]
    if len(set(ids)) != len(ids):
        problems.append('ids repetidos')
    if len(set(outs)) != len(outs) or not all(outs):
        problems.append('nomes de saída vazios ou repetidos')
    hooks = [r for r in rows if r.get('strategy') == 'hook']
    combos = {}
    for r in hooks:
        key = (r.get('hook'), r.get('caption_style'), r.get('transition'), r.get('grade'), r.get('music'))
        if key in combos:
            problems.append(f"{r['id']} repete a combinação de {combos[key]}")
        combos[key] = r['id']
        for f in ('hook', 'caption_style', 'transition', 'grade'):
            if not r.get(f):
                problems.append(f"{r['id']}: falta {f}")
    names = [r.get('hook') for r in hooks]
    if len(set(names)) < len(names):
        warnings.append('há ganchos repetidos; o resto (legenda/transição/cor/trilha) precisa diferenciar essas variações')
    posts = [r for r in rows if r.get('strategy') == 'post']
    seen_pair, seen_photo, seen_phrase = {}, {}, {}
    for r in posts:
        ph = r.get('photo') or {}
        photo = json.dumps([ph.get('src'), ph.get('t'), ph.get('crop')])
        phrase = _phrase(r)
        if not ph.get('src'):
            problems.append(f"{r['id']}: falta a foto")
        if not phrase:
            problems.append(f"{r['id']}: falta a frase")
        if not r.get('video'):
            problems.append(f"{r['id']}: falta o vídeo pronto")
        if len(r.get('lines', [])) > 2:
            problems.append(f"{r['id']}: a frase deve ter no máximo 2 linhas")
        if not any(hi and t.strip() for line in r.get('lines', []) for t, hi in line):
            warnings.append(f"{r['id']}: nenhum trecho destacado na frase")
        if (photo, phrase) in seen_pair:
            problems.append(f"{r['id']} tem a mesma foto e a mesma frase de {seen_pair[(photo, phrase)]}")
        seen_pair[(photo, phrase)] = r['id']
        if photo in seen_photo:
            warnings.append(f"{r['id']} repete a foto de {seen_photo[photo]} (mude a frase com força)")
        if phrase and phrase in seen_phrase:
            warnings.append(f"{r['id']} repete a frase de {seen_phrase[phrase]} (mude a foto)")
        seen_photo.setdefault(photo, r['id']); seen_phrase.setdefault(phrase, r['id'])
    if posts and not (p.get('header') or {}).get('name'):
        problems.append('cabeçalho sem nome/@: informe a conta que vai postar (nunca inventar)')
    return {'ok': not problems, 'count': len(rows), 'problems': problems, 'warnings': warnings}


# ---------------------------------------------------------------- post (F19 mechanics)
W, H = 1080, 1920
PX, PY, PW, PH = 32, 710, 1016, 888          # painel 0.370–0.832 da altura, 0.94 da largura (medido no exemplo do F19)


def _rgb(h: str) -> tuple:
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _font_path(identity: dict, family: str) -> Path:
    for f in identity.get('font_faces', []):
        if f['family'] == family and str(f['path']).endswith(('.ttf', '.otf')):
            return ENGINE / f['path']
    raise ValueError(f'A ID não tem arquivo TTF/OTF local para {family}; cadastre a fonte na ID antes do post.')


def layer(row: dict, header: dict, identity: dict, base: Path, photo_img=None):
    """Static layer (PIL): background, header, phrase with highlight, photo panel. Returns the RGB image."""
    from PIL import Image, ImageDraw, ImageFont
    pal = identity['palette']; BG, TXT, HI = _rgb(pal['background']), _rgb(pal['text']), _rgb(pal['primary'])
    MUT = _rgb(pal.get('muted', pal['text']))
    fpath = _font_path(identity, identity['typography']['headline'])

    def font(size, weight):
        f = ImageFont.truetype(str(fpath), size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        return f
    c = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(c)
    ay, asz = 352, 106
    if header.get('avatar'):
        av = Image.open(base / header['avatar']).convert('RGB')
        if header.get('avatar_crop'):
            av = av.crop(tuple(header['avatar_crop']))
        av = av.resize((asz, asz), Image.LANCZOS)
        m = Image.new('L', (asz * 4, asz * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, asz * 4, asz * 4), fill=255)
        c.paste(av, (60, ay), m.resize((asz, asz), Image.LANCZOS))
    fn, fh = font(52, 800), font(44, 500)
    d.text((190, ay + 4), header.get('name', ''), font=fn, fill=TXT)
    if header.get('verified'):
        bx, by, br = 190 + d.textlength(header['name'], font=fn) + 30, ay + 36, 20
        d.ellipse((bx - br, by - br, bx + br, by + br), fill=(29, 155, 240))
        d.line([(bx - 9, by), (bx - 2, by + 8), (bx + 10, by - 7)], fill=(255, 255, 255), width=5, joint='curve')
    d.text((190, ay + 62), header.get('handle', ''), font=fh, fill=MUT)
    fp = font(56, 800); y0, lh = 540, 66
    for k, line in enumerate(row['lines']):
        x = 60
        for txt, hi in line:
            d.text((x, y0 + k * lh), txt, font=fp, fill=HI if hi else TXT); x += d.textlength(txt, font=fp)
        if x > W - 40:
            raise ValueError(f"{row['id']}: a linha {k + 1} passa da largura; encurte a frase")
        if k == len(row['lines']) - 1 and row.get('emoji'):
            try:
                ef = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', 160)
                e = Image.new('RGBA', (180, 180), (0, 0, 0, 0)); ImageDraw.Draw(e).text((0, 0), row['emoji'], font=ef, embedded_color=True)
                e = e.crop(e.getbbox()).resize((58, 58), Image.LANCZOS); c.paste(e, (round(x + 14), y0 + k * lh + 6), e)
            except Exception:
                pass   # emoji é opcional; sem a fonte colorida o texto segue sem ele
    half = (PW - 3) // 2
    img = photo_img if photo_img is not None else _photo(row['photo'], base)
    ph = row['photo']
    if ph.get('fit') == 'contain':
        s = min(half / img.width, PH / img.height) * 0.94
        im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
        photo = Image.new('RGB', (half, PH), _rgb(ph.get('bg', pal['text']))); photo.paste(im, ((half - im.width) // 2, (PH - im.height) // 2))
    else:
        s = max(half / img.width, PH / img.height)
        im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
        x, y = (im.width - half) // 2, (im.height - PH) // 2; photo = im.crop((x, y, x + half, y + PH))
    if ph.get('ring'):
        rx, ry, dm = ph['ring']; R = dm * half / 2; cx, cy = rx * half, ry * PH; pd = ImageDraw.Draw(photo)
        for wdt, col in ((16, (255, 255, 255)), (10, (227, 23, 10))):
            pd.ellipse((cx - R, cy - R, cx + R, cy + R), outline=col, width=wdt)
    c.paste(photo, (PX, PY)); d.rectangle((PX + half, PY, PX + half + 2, PY + PH - 1), fill=BG)
    return c


def _photo(spec: dict, base: Path):
    from PIL import Image
    src = base / spec['src']
    if src.suffix.lower() in ('.mp4', '.mov', '.webm', '.mkv'):
        with tempfile.TemporaryDirectory() as t:
            png = Path(t) / 'f.png'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{spec.get('t') or 0:.3f}", '-i', str(src), '-frames:v', '1', str(png)], check=True)
            img = Image.open(png).convert('RGB'); img.load()
    else:
        img = Image.open(src).convert('RGB')
    if spec.get('crop'):
        x, y, w, h = spec['crop']; img = img.crop((x, y, x + w, y + h))
    return img


def post(plan_path: Path, vid: str, identity: dict) -> dict:
    p = json.loads(plan_path.read_text()); base = plan_path.resolve().parent.parent
    row = next(r for r in p['variations'] if r['id'].lower() in (vid.lower(), f'var{int(vid):02d}' if vid.isdigit() else ''))
    if row.get('strategy') != 'post':
        raise ValueError(f"{row['id']} não é uma variação 'post'")
    img = layer(row, p['header'], identity, base)
    out_dir = base / 'renders'; out_dir.mkdir(exist_ok=True)
    lay = plan_path.parent / f"layer_{row['id']}.png"; img.save(lay)
    src = base / row['video']
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)], capture_output=True, text=True).stdout)
    half = (PW - 3) // 2; vx, vw = PX + half + 3, PW - half - 3
    fc = (f'[1:v]scale={vw}:-2:flags=lanczos,crop={vw}:{PH},setsar=1[v];[0:v][v]overlay={vx}:{PY}:shortest=1,format=yuv420p[o];'
          '[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84:attack=5:release=80:level=disabled[a]')
    out = out_dir / row['output']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-i', str(lay), '-i', str(src), '-filter_complex', fc,
                    '-map', '[o]', '-map', '[a]', '-t', f'{dur:.3f}', '-r', '30', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', str(out)], check=True)
    return {'id': row['id'], 'output': str(out), 'layer': str(lay), 'duration': round(dur, 2), 'identity': identity['code']}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = ap.add_subparsers(dest='cmd', required=True)
    a1 = sub.add_parser('plan'); a1.add_argument('--out', required=True); a1.add_argument('--count', type=int, required=True)
    a1.add_argument('--strategy', choices=['hook', 'post', 'mixed'], default='hook'); a1.add_argument('--base-name', default='video')
    a2 = sub.add_parser('check'); a2.add_argument('--plan', required=True)
    a3 = sub.add_parser('post'); a3.add_argument('--plan', required=True); a3.add_argument('--var', required=True)
    a3.add_argument('--identity', required=True); a3.add_argument('--root', default=str(ENGINE.parent))
    a = ap.parse_args(argv)
    if a.cmd == 'plan':
        out = Path(a.out)
        if out.exists():
            raise SystemExit('O plano já existe; edite-o ou escolha outro nome.')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan(a.count, a.strategy, a.base_name), ensure_ascii=False, indent=1), encoding='utf-8')
        print(json.dumps({'ok': True, 'plan': str(out), 'count': a.count}, ensure_ascii=False))
    elif a.cmd == 'check':
        r = check(json.loads(Path(a.plan).read_text())); print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r['ok'] else 1
    else:
        sys.path.insert(0, str(TOOLS))
        from design_catalog import visual_identity
        print(json.dumps(post(Path(a.plan), a.var, visual_identity(Path(a.root), a.identity)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
