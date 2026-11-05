#!/bin/bash
# ORA AI Explorer — iniciador para macOS.
# Doble clic: abre el apartamento 104 (Torre 1) en 3D en tu navegador predeterminado.
# Sirve los archivos solo para este equipo (127.0.0.1); nada queda expuesto a la red.
# Para cerrarlo, cierra esta ventana de Terminal o pulsa Control + C.

cd "$(dirname "$0")" || exit 1
if [ -f index.html ]; then ROOT="$PWD"; elif [ -f ../index.html ]; then ROOT="$(cd .. && pwd)"; else
  echo "No encuentro index.html junto a este archivo. Descomprime el ZIP completo y vuelve a intentarlo."
  read -r -p "Pulsa Enter para cerrar…" _; exit 1
fi

# Python solo se usa si ya está instalado de verdad: el python3 de macOS sin herramientas
# de desarrollo abre un instalador, y eso no debe ocurrir al abrir una demo.
PY=""
if command -v python3 >/dev/null 2>&1; then
  if [ "$(command -v python3)" != "/usr/bin/python3" ] || xcode-select -p >/dev/null 2>&1; then PY="python3"; fi
fi

if [ -z "$PY" ]; then
  echo "Abriendo el apartamento 104 directamente desde el archivo…"
  open "$ROOT/apartamento-104/index.html"
  sleep 2; exit 0
fi

echo "ORA AI Explorer · Apartamento 104 en 3D"
echo "Carpeta: $ROOT"
exec "$PY" - "$ROOT" <<'PYTHON'
import http.server, os, socket, sys, threading, webbrowser

root = sys.argv[1]
os.chdir(root)

class Handler(http.server.SimpleHTTPRequestHandler):
    """Servidor estático con soporte de rangos, necesario para que Safari reproduzca videos."""
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.mp4': 'video/mp4', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml'}

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        rng = self.headers.get('Range')
        if not rng or not os.path.isfile(path) or not rng.startswith('bytes='):
            return super().send_head()
        size = os.path.getsize(path)
        start_s, _, end_s = rng[6:].split(',')[0].strip().partition('-')
        try:
            if start_s:
                start, end = int(start_s), int(end_s) if end_s else size - 1
            else:
                start, end = max(0, size - int(end_s)), size - 1
        except ValueError:
            return super().send_head()
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.end_headers()
            return None
        f = open(path, 'rb')
        f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, '_remaining', None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self._remaining = None

with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]

server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
url = f'http://127.0.0.1:{port}/apartamento-104/'
print(f'Abierto en {url}')
print('Para cerrar: cierra esta ventana o pulsa Control + C.')
threading.Timer(0.6, lambda: webbrowser.open(url)).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
PYTHON
