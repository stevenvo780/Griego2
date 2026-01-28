#!/usr/bin/env python3
"""
Servidor web con WebSockets para edición colaborativa de Markdown
Ejecutar: python3 servidor.py
Abrir: http://localhost:8888
"""

import asyncio
import json
import os
import urllib.parse
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
import threading
import http.server
import socketserver

PORT = 8888
WS_PORT = 8889
BASE_DIR = Path(__file__).parent.parent  # Directorio Griego2

# Clientes WebSocket conectados
clients = {}
file_rooms = {}  # {file_path: [client_ids]}

class MarkdownHandler(SimpleHTTPRequestHandler):
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

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/api/save':
            self.save_file()
        else:
            self.send_error(404, 'Not found')

    def send_file_list(self):
        md_files = []

        for root, dirs, files in os.walk(BASE_DIR):
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
        try:
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

    def save_file(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            rel_path = data.get('path')
            content = data.get('content')

            if not rel_path or content is None:
                self.send_error(400, 'Faltan parámetros')
                return

            full_path = (BASE_DIR / rel_path).resolve()
            if not str(full_path).startswith(str(BASE_DIR)):
                self.send_error(403, 'Acceso denegado')
                return

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        pass  # Silenciar logs


# WebSocket server usando asyncio
async def ws_handler(websocket, path=None):
    client_id = id(websocket)
    clients[client_id] = {'ws': websocket, 'file': None}

    try:
        async for message in websocket:
            try:
                data = json.loads(message)

                if data['type'] == 'join':
                    # Cliente se une a un archivo
                    file_path = data['file']
                    clients[client_id]['file'] = file_path

                    if file_path not in file_rooms:
                        file_rooms[file_path] = []
                    if client_id not in file_rooms[file_path]:
                        file_rooms[file_path].append(client_id)

                    # Notificar a todos los usuarios del archivo
                    await broadcast_users(file_path)

                elif data['type'] == 'update':
                    # Broadcast de cambios a otros clientes del mismo archivo
                    file_path = data['file']

                    for cid in file_rooms.get(file_path, []):
                        if cid != client_id and cid in clients:
                            try:
                                await clients[cid]['ws'].send(json.dumps({
                                    'type': 'update',
                                    'file': file_path,
                                    'content': data['content'],
                                    'clientId': data.get('clientId')
                                }))
                            except:
                                pass

            except json.JSONDecodeError:
                pass

    except Exception as e:
        pass
    finally:
        # Limpiar al desconectar
        file_path = clients.get(client_id, {}).get('file')
        if file_path and file_path in file_rooms:
            if client_id in file_rooms[file_path]:
                file_rooms[file_path].remove(client_id)
            await broadcast_users(file_path)

        if client_id in clients:
            del clients[client_id]


async def broadcast_users(file_path):
    """Envía lista de usuarios a todos los del archivo"""
    users = []
    for cid in file_rooms.get(file_path, []):
        if cid in clients:
            users.append({'id': str(cid)})

    message = json.dumps({'type': 'users', 'users': users})

    for cid in file_rooms.get(file_path, []):
        if cid in clients:
            try:
                await clients[cid]['ws'].send(message)
            except:
                pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_http_server():
    """Ejecuta el servidor HTTP en un thread separado"""
    with ReusableTCPServer(("", PORT), MarkdownHandler) as httpd:
        httpd.serve_forever()


async def main():
    # Importar websockets aquí
    try:
        import websockets
    except ImportError:
        print("Instalando websockets...")
        os.system("pip install websockets --quiet")
        import websockets

    # Iniciar servidor HTTP en thread separado
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║      Visor & Editor Colaborativo de Markdown                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║   🌐 Abre en tu navegador:  http://localhost:{PORT}              ║
║   🔌 WebSocket:             ws://localhost:{WS_PORT}              ║
║                                                                ║
║   ✏️  Edita archivos en tiempo real                            ║
║   👥 Colabora con otros usuarios                               ║
║   💾 Autoguardado cada 2 segundos                              ║
║                                                                ║
║   Presiona Ctrl+C para detener                                 ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Iniciar servidor WebSocket
    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await asyncio.Future()  # Correr indefinidamente


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n¡Servidor detenido!")
