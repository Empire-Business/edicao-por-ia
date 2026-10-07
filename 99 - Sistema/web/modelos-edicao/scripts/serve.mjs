import http from 'node:http';
import path from 'node:path';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const production = process.argv[2] === 'dist';
const port = Number(process.env.PORT || 4173);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };
http.createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (pathname.includes('..') || !['GET', 'HEAD'].includes(request.method)) throw Error('Invalid request');
    const name = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
    const roots = production ? [path.join(root, 'dist')] : [path.join(root, 'src'), path.join(root, 'public')];
    let file;
    for (const candidate of roots) {
      const possible = path.join(candidate, name);
      try { if ((await stat(possible)).isFile()) { file = possible; break; } } catch {}
    }
    if (!file) { response.writeHead(404); response.end('Não encontrado'); return; }
    const bytes = await readFile(file);
    const headers = { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache' };
    const range = request.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
    if (range) {
      const start = Number(range[1]);
      const end = Math.min(Number(range[2] || bytes.length - 1), bytes.length - 1);
      if (start > end || start >= bytes.length) { response.writeHead(416, { 'Content-Range': `bytes */${bytes.length}` }); response.end(); return; }
      response.writeHead(206, { ...headers, 'Content-Range': `bytes ${start}-${end}/${bytes.length}`, 'Content-Length': end - start + 1 });
      response.end(request.method === 'HEAD' ? undefined : bytes.subarray(start, end + 1));
    } else { response.writeHead(200, { ...headers, 'Content-Length': bytes.length }); response.end(request.method === 'HEAD' ? undefined : bytes); }
  } catch { response.writeHead(400); response.end('Pedido inválido'); }
}).listen(port, '127.0.0.1', () => console.log(`Biblioteca disponível em http://127.0.0.1:${port}`));
