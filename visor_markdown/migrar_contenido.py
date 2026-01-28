import firebase_admin
from firebase_admin import credentials, storage
import os
import json
from pathlib import Path

# Configuración
# Coloca el contenido del JSON de la cuenta de servicio aquí o en un archivo 'serviceAccountKey.json'
credentials_path = 'serviceAccountKey.json' 
# Si no existe, intenta leer de variable de entorno
service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

bucket_name = 'udea-filosofia.firebasestorage.app'
root_dir = Path(__file__).parent.parent.resolve() # Sube desde la raíz del proyecto (Griego2)

def upload_files():
    cred = None
    if os.path.exists(credentials_path):
        cred = credentials.Certificate(credentials_path)
    elif service_account_json:
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
    
    if not cred:
        print("Error: No se encontraron credenciales. Guarda el JSON como 'serviceAccountKey.json' o configura FIREBASE_SERVICE_ACCOUNT.")
        return

    firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })

    bucket = storage.bucket()
    
    print(f"Subiendo archivos desde {root_dir}...")
    
    # Directorios a ignorar
    ignore_dirs = ['.git', 'visor_markdown', 'deploy', '__pycache__', '.vercel']
    
    count = 0
    for root, dirs, files in os.walk(root_dir):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                local_path = Path(root) / file
                # Calcular ruta relativa para usar como nombre en el bucket
                relative_path = local_path.relative_to(root_dir)
                blob_name = str(relative_path) # Usa la estructura de carpetas como nombre del blob
                
                print(f"Subiendo: {blob_name}")
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(local_path))
                count += 1
                
    print(f"\n¡Completado! {count} archivos subidos.")

if __name__ == '__main__':
    upload_files()
