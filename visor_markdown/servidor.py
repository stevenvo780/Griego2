#!/usr/bin/env python3
"""
Servidor unificado HTTP + WebSocket en el mismo puerto
Compatible con ngrok y túneles
"""

import asyncio
import json
import os
import mimetypes
from pathlib import Path
from aiohttp import web, WSMsgType

PORT = 8888
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent

# Estado global
clients = {}
file_rooms = {}

# Tipos MIME adicionales
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('image/svg+xml', '.svg')


async def handle_index(request):
    """Sirve index.html"""
    return web.FileResponse(STATIC_DIR / 'index.html')


async def handle_static(request):
    """Sirve archivos estáticos"""
    filename = request.match_info.get('filename', '')
    filepath = STATIC_DIR / filename

    if filepath.exists() and filepath.is_file():
        return web.FileResponse(filepath)
    return web.Response(status=404, text='Not found')


async def handle_api_files(request):
    """Lista archivos del usuario"""
    user_files = []
    allowed_exts = {'.md', '.txt', '.pdf', '.html', '.css', '.js', '.py'}

    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'visor_markdown']

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in allowed_exts:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(BASE_DIR)
                user_files.append(str(rel_path))

    user_files.sort()
    return web.json_response(user_files)


async def handle_raw_file(request):
    """Sirve archivos crudos del usuario (PDFs, imágenes, etc)"""
    rel_path = request.match_info.get('path', '')
    if not rel_path:
        return web.Response(status=404)

    full_path = (BASE_DIR / rel_path).resolve()
    if not str(full_path).startswith(str(BASE_DIR.resolve())):
        return web.Response(status=403)

    if not full_path.exists():
        return web.Response(status=404)

    return web.FileResponse(full_path)


async def handle_api_file(request):
    """Lee contenido de un archivo"""
    rel_path = request.query.get('path', '')

    if not rel_path:
        return web.json_response({'error': 'Falta path'}, status=400)

    try:
        full_path = (BASE_DIR / rel_path).resolve()
        if not str(full_path).startswith(str(BASE_DIR.resolve())):
            return web.json_response({'error': 'Acceso denegado'}, status=403)

        if not full_path.exists():
            return web.json_response({'error': 'No encontrado'}, status=404)

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return web.json_response({'content': content})

    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def handle_api_save(request):
    """Guarda un archivo"""
    try:
        data = await request.json()
        rel_path = data.get('path')
        content = data.get('content')

        if not rel_path or content is None:
            return web.json_response({'error': 'Faltan parámetros'}, status=400)

        full_path = (BASE_DIR / rel_path).resolve()
        if not str(full_path).startswith(str(BASE_DIR.resolve())):
            return web.json_response({'error': 'Acceso denegado'}, status=403)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return web.json_response({'success': True})

    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def handle_api_upload(request):
    """Sube archivos"""
    try:
        reader = await request.multipart()
    except Exception:
        return web.json_response({'error': 'No multipart'}, status=400)

    count = 0
    upload_dir = BASE_DIR / "documentos" # Default upload directory
    if not upload_dir.exists():
        upload_dir.mkdir()

    while True:
        part = await reader.next()
        if part is None:
            break
        
        if part.name == 'files':
            filename = part.filename 
            if not filename: continue
            
            # Simple sanitization
            filename = os.path.basename(filename)
            filepath = upload_dir / filename
            
            with open(filepath, 'wb') as f:
                while True:
                    chunk = await part.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)
            count += 1
    
    return web.json_response({'count': count})

async def handle_websocket(request):
    """Maneja conexiones WebSocket"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    client_id = id(ws)
    clients[client_id] = {'ws': ws, 'file': None}
    print(f'Cliente conectado: {client_id}')

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)

                    if data['type'] == 'join':
                        file_path = data['file']
                        clients[client_id]['file'] = file_path

                        if file_path not in file_rooms:
                            file_rooms[file_path] = []
                        if client_id not in file_rooms[file_path]:
                            file_rooms[file_path].append(client_id)

                        await broadcast_users(file_path)

                    elif data['type'] == 'update':
                        file_path = data['file']

                        for cid in file_rooms.get(file_path, []):
                            if cid != client_id and cid in clients:
                                try:
                                    await clients[cid]['ws'].send_json({
                                        'type': 'update',
                                        'file': file_path,
                                        'content': data['content'],
                                        'clientId': data.get('clientId')
                                    })
                                except:
                                    pass

                except json.JSONDecodeError:
                    pass

            elif msg.type == WSMsgType.ERROR:
                print(f'Error WebSocket: {ws.exception()}')

    finally:
        file_path = clients.get(client_id, {}).get('file')
        if file_path and file_path in file_rooms:
            if client_id in file_rooms[file_path]:
                file_rooms[file_path].remove(client_id)
            await broadcast_users(file_path)

        if client_id in clients:
            del clients[client_id]
        print(f'Cliente desconectado: {client_id}')

    return ws


async def broadcast_users(file_path):
    """Envía lista de usuarios"""
    users = [{'id': str(cid)} for cid in file_rooms.get(file_path, []) if cid in clients]
    message = {'type': 'users', 'users': users}

    for cid in file_rooms.get(file_path, []):
        if cid in clients:
            try:
                await clients[cid]['ws'].send_json(message)
            except:
                pass


def create_app():
    """Crea la aplicación"""
    app = web.Application()

    # Rutas
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', handle_websocket)
    app.router.add_get('/api/files', handle_api_files)
    app.router.add_get('/api/file', handle_api_file)
    app.router.add_post('/api/save', handle_api_save)
    app.router.add_post('/api/upload', handle_api_upload)
    app.router.add_get('/raw/{path:.*}', handle_raw_file)
    app.router.add_get('/{filename:.*}', handle_static)

    return app


def main():
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║      Visor & Editor Colaborativo de Markdown                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║   🌐 HTTP + WebSocket:  http://localhost:{PORT}                  ║
║                                                                ║
║   ✅ Compatible con ngrok (mismo puerto)                       ║
║   ✏️  Edita archivos en tiempo real                            ║
║   👥 Colabora con otros usuarios                               ║
║                                                                ║
║   Presiona Ctrl+C para detener                                 ║
╚════════════════════════════════════════════════════════════════╝
    """)

    app = create_app()
    web.run_app(app, host='0.0.0.0', port=PORT, print=None)


if __name__ == '__main__':
    main()
