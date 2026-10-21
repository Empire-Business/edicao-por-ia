#!/usr/bin/env python3
"""Flare (vazamento de luz) de transição do F20 React, medido quadro a quadro no exemplo do autor (30 fps).

  antes do corte  5 quadros: luz vermelha subindo de baixo (metade de baixo toda vermelha)
  no corte       ~7 quadros: estouro laranja-amarelado bem claro + faixa magenta diagonal no alto à esquerda
  depois         ~5 quadros: cai para laranja/vermelho e some            (total ≈ 0,55 s)

A luz é somada em modo 'screen' quadro a quadro (o filtro blend do ffmpeg perdeu a sincronia no corte).
usage:
  python tools/flare_transition.py apply ENTRADA.mp4 SAIDA.mp4 --cut 155 --cut 2755
      --cut = índice do primeiro quadro DEPOIS do corte. Só o vídeo é processado; o áudio é copiado.
  python tools/flare_transition.py layer SAIDA.mov [--width 1080 --height 1920]
      grava só a camada de luz (preto = nada), quadro 0 = 5 quadros antes do corte.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
import numpy as np

PRE, POST = 5, 13
RED, ORANGE, GOLD, MAGENTA = (np.array(c, np.float32) for c in ([1, .08, .14], [1, .42, .10], [1, .70, .28], [1, .15, .45]))
BURST = [1.0, 1.0, .98, .96, .93, .88, .80, .68, .52, .36, .22, .12, .05]


class Flare:
    def __init__(self, width, height):
        y, x = np.mgrid[0:height, 0:width].astype(np.float32)
        self.Y, self.X, self.cache = y / height, x / width, {}

    def blob(self, cx, cy, rx, ry):
        return np.exp(-(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2))

    def frame(self, n):
        """Camada de luz RGB em 0..1 para o quadro n relativo ao corte (n<0 antes, n>=0 depois)."""
        if n in self.cache: return self.cache[n]
        X, Y = self.X, self.Y
        L = np.zeros(X.shape + (3,), np.float32)
        if n < 0:
            k = min(1.0, (n + PRE + 1) / (PRE - 1))
            L += RED * (k * np.clip((Y - (0.80 - 0.45 * k)) / 0.25, 0, 1))[..., None]
            L += RED * (0.25 * k)
        else:
            burst = BURST[min(n, len(BURST) - 1)]
            warm = float(np.clip((n - 4) / 6, 0, 1))
            col = GOLD * (1 - warm) + ORANGE * warm if warm < .6 else ORANGE * (1 - (warm - .6) / .4) + RED * ((warm - .6) / .4)
            L += col * (0.9 * burst * (0.55 + 0.45 * self.blob(0.55, 0.52, 0.9, 0.7)))[..., None]
            if n <= 8:
                streak = np.exp(-(((X * 0.8 + Y) - 0.35) / 0.09) ** 2) * np.clip(1 - Y / 0.45, 0, 1)
                L += MAGENTA * (0.75 * burst * streak)[..., None]
            if n >= 6:
                L += RED * (0.5 * burst * np.clip((Y - 0.45) / 0.55, 0, 1))[..., None]
        self.cache[n] = np.clip(L, 0, 1)
        return self.cache[n]


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                        '-of', 'json', path], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)['streams'][0]; a, b = s['r_frame_rate'].split('/')
    return s['width'], s['height'], float(a) / float(b)


def apply(src, dst, cuts):
    w, h, fps = probe(src); fl = Flare(w, h)
    want = {c + n: n for c in cuts for n in range(-PRE, POST)}
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', f'{fps}', '-i', '-',
                            '-i', src, '-map', '0:v', '-map', '1:a?', '-c:a', 'copy', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
    size, i = w * h * 3, 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size: break
        if i in want:
            B = np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(np.float32) / 255
            buf = ((1 - (1 - B) * (1 - fl.frame(want[i]))) * 255 + 0.5).astype(np.uint8).tobytes()
        enc.stdin.write(buf); i += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    if enc.returncode: sys.exit('Falha ao gravar ' + dst)
    print(json.dumps({'out': dst, 'frames': i, 'cuts': cuts, 'flare_frames': PRE + POST}))


def layer(dst, w, h, fps=30):
    fl = Flare(w, h)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps),
                          '-i', '-', '-c:v', 'qtrle', dst], stdin=subprocess.PIPE)
    for n in range(-PRE, POST): p.stdin.write((fl.frame(n) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print(json.dumps({'out': dst, 'frames': PRE + POST}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='command', required=True)
    a = sp.add_parser('apply'); a.add_argument('src'); a.add_argument('dst'); a.add_argument('--cut', type=int, action='append', required=True)
    b = sp.add_parser('layer'); b.add_argument('dst'); b.add_argument('--width', type=int, default=1080); b.add_argument('--height', type=int, default=1920)
    args = ap.parse_args()
    if args.command == 'apply': apply(args.src, args.dst, sorted(args.cut))
    else: layer(args.dst, args.width, args.height)


if __name__ == '__main__':
    main()
