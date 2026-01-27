#!/usr/bin/env python3
"""
Servidor web para visualizar archivos Markdown
Ejecutar: python3 servidor.py
Abrir: http://localhost:8080
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from pathlib import Path

PORT = 8888
BASE_DIR = Path(__file__).parent.parent  # Directorio Griego2

class MarkdownHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/api/files':
            self.send_file_list()
        elif parsed.path == '/api/file':
            query = urllib.parse.parse_qs(parsed.query)
            if 'path' in query:
                self.send_file_content(query['path'][0])
            else:
                self.send_error(400, 'Falta parámetro path')
        else:
            super().do_GET()

    def send_file_list(self):
        """Lista todos los archivos .md"""
        md_files = []

        for root, dirs, files in os.walk(BASE_DIR):
            # Ignorar carpetas ocultas y el visor
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'visor_markdown']

            for file in files:
                if file.endswith('.md'):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(BASE_DIR)
                    md_files.append(str(rel_path))

        md_files.sort()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(md_files).encode())

    def send_file_content(self, rel_path):
        """Envía el contenido de un archivo"""
        try:
            # Seguridad: evitar path traversal
            full_path = (BASE_DIR / rel_path).resolve()
            if not str(full_path).startswith(str(BASE_DIR)):
                self.send_error(403, 'Acceso denegado')
                return

            if not full_path.exists():
                self.send_error(404, 'Archivo no encontrado')
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'content': content}).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Mostrar logs más limpios"""
        if '/api/' not in args[0]:
            return
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    with socketserver.TCPServer(("", PORT), MarkdownHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════════╗
║     Visor de Markdown para Griego - Servidor Activo        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║   Abre en tu navegador:  http://localhost:{PORT}             ║
║                                                            ║
║   Presiona Ctrl+C para detener el servidor                 ║
╚════════════════════════════════════════════════════════════╝
        """)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n¡Servidor detenido!")


if __name__ == "__main__":
    main()
