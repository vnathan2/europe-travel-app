# utils/gcp_client.py
# Conexión centralizada a todos los servicios GCP
# Se usa desde todos los módulos de la app

import os
from google.cloud import firestore, storage
from dotenv import load_dotenv

# Carga las variables del archivo .env cuando estamos en local
load_dotenv()

# ── Firestore ──────────────────────────────────────────────────────────────
def get_firestore_client():
    """
    Retorna un cliente de Firestore.
    En local usa las credenciales del archivo .env
    En Cloud Run usa las credenciales del servicio automáticamente
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    return firestore.Client(project=project_id)

# ── Cloud Storage ──────────────────────────────────────────────────────────
def get_storage_client():
    """Retorna un cliente de Cloud Storage"""
    return storage.Client(project=os.getenv("GCP_PROJECT_ID"))

def upload_to_bucket(local_file_path: str, destination_blob_name: str) -> str:
    """
    Sube un archivo local al bucket de Cloud Storage.
    Retorna la URL pública del archivo.
    
    Ejemplo:
        upload_to_bucket("/tmp/gastos.xlsx", "exports/gastos_julio.xlsx")
    """
    client = get_storage_client()
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    return f"gs://{bucket_name}/{destination_blob_name}"

def download_from_bucket(blob_name: str, local_path: str):
    """Descarga un archivo del bucket a una ruta local"""
    client = get_storage_client()
    bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)