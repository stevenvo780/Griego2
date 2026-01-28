from flask import Flask, request, jsonify, send_file
import firebase_admin
from firebase_admin import credentials, storage
import os
import json
import base64
from functools import wraps

app = Flask(__name__)

# Configuración desde variables de entorno
FIREBASE_CREDENTIALS_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
BUCKET_NAME = os.environ.get('FIREBASE_STORAGE_BUCKET', 'udea-filosofia.firebasestorage.app')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

# Inicializar Firebase
if not firebase_admin._apps:
    if FIREBASE_CREDENTIALS_JSON:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    else:
        # Fallback para desarrollo local si existe el archivo
        cred = credentials.Certificate("serviceAccountKey.json") if os.path.exists("serviceAccountKey.json") else None
    
    if cred:
        firebase_admin.initialize_app(cred, {
            'storageBucket': BUCKET_NAME
        })

def check_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No autorizado'}), 401
        
        token = auth_header.split(' ')[1]
        if token != APP_PASSWORD:
             return jsonify({'error': 'Contraseña incorrecta'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    if password == APP_PASSWORD:
        return jsonify({'token': password}) # En un caso real usaría JWT, aquí simple
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/files', methods=['GET'])
@check_auth
def list_files():
    try:
        bucket = storage.bucket()
        # Listar recursivamente
        blobs = bucket.list_blobs()
        files = []
        for blob in blobs:
            if blob.name.endswith('.md'):
                files.append(blob.name)
        files.sort()
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file', methods=['GET'])
@check_auth
def get_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'Falta path'}), 400
    
    try:
        bucket = storage.bucket()
        blob = bucket.blob(path)
        if not blob.exists():
            return jsonify({'error': 'No encontrado'}), 404
        
        content = blob.download_as_text()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
@check_auth
def save_file():
    try:
        data = request.json
        path = data.get('path')
        content = data.get('content')
        
        if not path or content is None:
            return jsonify({'error': 'Datos incompletos'}), 400
            
        bucket = storage.bucket()
        blob = bucket.blob(path)
        blob.upload_from_string(content)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handler for Vercel
@app.errorhandler(500)
def server_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, port=8888)
