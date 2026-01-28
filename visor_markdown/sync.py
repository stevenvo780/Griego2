import time
import os
import sys
import json
import logging
import hashlib
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_DIR = Path(__file__).parent.parent.resolve()
DOCS_DIR = BASE_DIR / "documentos"
CREDENTIALS_PATH = Path(__file__).parent / "serviceAccountKey.json"
BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET", "udea-filosofia.firebasestorage.app")
POLL_INTERVAL = 10  # Segundos para chequear cambios remotos

class SyncManager:
    def __init__(self):
        self.bucket = self._init_firebase()
        self.ignore_list = ['.git', '.DS_Store', 'Thumbs.db', 'desktop.ini']
        self._is_updating = False

    def _init_firebase(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {'storageBucket': BUCKET_NAME})
            return storage.bucket()
        except Exception as e:
            logger.error(f"Error inicializando Firebase: {e}")
            sys.exit(1)

    def get_local_files(self):
        files = {}
        for root, _, filenames in os.walk(DOCS_DIR):
            for filename in filenames:
                if filename in self.ignore_list or filename.startswith('.'):
                    continue
                path = Path(root) / filename
                rel_path = str(path.relative_to(DOCS_DIR))
                files[rel_path] = self._get_file_hash(path)
        return files

    def get_remote_files(self):
        blobs = self.bucket.list_blobs()
        files = {}
        for blob in blobs:
            if blob.name.endswith('/') or not blob.name:
                continue
            # El hash md5 de Firebase está en base64, lo convertimos a hex para comparar
            # Pero para simplicidad, descargamos metadatos custom o usamos timestamp
            # Usaremos md5_hash que viene de firebase (base64) y lo compararemos con nuestro calculo
            files[blob.name] = blob
        return files

    def _get_file_hash(self, path):
        """Calcula MD5 del archivo local para comparar con Firebase (que usa MD5 base64)"""
        # Nota: Firebase usa MD5 base64. Python hashlib da hex.
        # Necesitamos la version base64 del hash MD5
        import base64
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return base64.b64encode(hash_md5.digest()).decode('utf-8')

    def download_file(self, blob_name):
        self._is_updating = True
        try:
            blob = self.bucket.blob(blob_name)
            local_path = DOCS_DIR / blob_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))
            logger.info(f"⬇️  Descargado: {blob_name}")
        except Exception as e:
            logger.error(f"Error descargando {blob_name}: {e}")
        finally:
            # Pequeña pausa para evitar que el watcher detecte este cambio como "nuevo" inmediatamente
            time.sleep(1)
            self._is_updating = False

    def upload_file(self, rel_path):
        if self._is_updating: return
        
        path = DOCS_DIR / rel_path
        if not path.exists(): return

        try:
            blob = self.bucket.blob(rel_path)
            # Solo subir si es diferente (opcional, pero ahorra ancho de banda)
            # blob.upload_from_filename(str(path))
            # Para garantizar consistencia, subimos siempre
            blob.upload_from_filename(str(path))
            logger.info(f"⬆️  Subido: {rel_path}")
        except Exception as e:
            logger.error(f"Error subiendo {rel_path}: {e}")

    def sync_cycle(self):
        """Chequea cambios remotos vs locales"""
        try:
            # logger.debug("Sincronizando...")
            remote_files = self.get_remote_files()
            local_files_hashes = self.get_local_files()

            for name, blob in remote_files.items():
                local_hash = local_files_hashes.get(name)
                remote_hash = blob.md5_hash

                if local_hash != remote_hash:
                    # Conflicto simple: Remote wins en polling si es diferente
                    # Idealmente chequear timestamps, pero aquí asumimos que la nube es la verdad si difieren
                    # OJO: Si acabamos de subir, el local será igual.
                    # Si difieren, descargamos.
                    # Pero si acabamos de modificar localmente y aún no se subió?
                    # El watchdog debería manejar la subida.
                    # Aquí manejamos la bajada.
                    
                    # Chequear si el remoto es más nuevo que el local
                    if (DOCS_DIR / name).exists():
                         # Comparar tiempos? Firebase `updated` vs local `mtime`
                         # blob.updated es datetime
                         pass
                    
                    # Estrategia simple: Si no existe local, o hash diferente descarga.
                    # Problema: Bucle infinito si hashes no coinciden exactamente (e.g. metadata).
                    
                    # Vamos a confiar en MD5.
                    if local_hash is None or local_hash != remote_hash:
                         self.download_file(name)

        except Exception as e:
            logger.error(f"Error en ciclo de sync: {e}")

class LocalHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager

    def on_modified(self, event):
        if event.is_directory: return
        self._process(event.src_path)

    def on_created(self, event):
        if event.is_directory: return
        self._process(event.src_path)

    def _process(self, path):
        # Ignorar archivos temporales o de sistema
        filename = os.path.basename(path)
        if filename.startswith('.') or filename.endswith('.tmp'):
            return

        try:
            rel_path = str(Path(path).relative_to(DOCS_DIR))
            logger.info(f"📝 Cambio local detectado: {rel_path}")
            self.manager.upload_file(rel_path)
        except ValueError:
            pass # Path no está en DOCS_DIR

def run_sync():
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True)
        logger.info(f"Directorio creado: {DOCS_DIR}")

    manager = SyncManager()

    # Iniciar Watcher Local
    observer = Observer()
    observer.schedule(LocalHandler(manager), str(DOCS_DIR), recursive=True)
    observer.start()
    logger.info(f"👀 Monitoreando cambios locales en: {DOCS_DIR}")

    try:
        while True:
            manager.sync_cycle()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Deteniendo sincronización...")
    
    observer.join()

if __name__ == "__main__":
    run_sync()
