import os
import streamlit as st
from google.cloud import firestore, storage, secretmanager
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# ── Clientes con Caché (Crucial para la Capa Gratuita) ──────────────────────
@st.cache_resource
def get_firestore_client():
    """
    Mantiene una única conexión abierta. 
    Ahorra latencia y evita múltiples Handshakes de red.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    return firestore.Client(project=project_id)

@st.cache_resource
def get_storage_client():
    return storage.Client(project=os.getenv("GCP_PROJECT_ID"))

@st.cache_resource
def get_secret_client():
    return secretmanager.SecretManagerServiceClient()

# ── Cloud Storage ──────────────────────────────────────────────────────────
def upload_to_bucket(local_file_path: str, destination_blob_name: str) -> str:
    client = get_storage_client()
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    return f"gs://{bucket_name}/{destination_blob_name}"

# ── Secret Manager ─────────────────────────────────────────────────────────
# Valores NO sensibles — se leen directo de env vars (no consumen cuota de Secret Manager)
_ENV_VARS_ONLY = {"OAUTH_REDIRECT_URI", "ADMIN_EMAIL", "FAMILIAR_EMAIL_1", "FAMILIAR_EMAIL_2"}

@st.cache_data(ttl=3600)  # Cacheamos el secreto por 1 hora para no llamar a la API cada vez
def get_secret(secret_name: str) -> str:
    if secret_name in _ENV_VARS_ONLY:
        return os.getenv(secret_name, "")
    client = get_secret_client()
    project_id = os.getenv("GCP_PROJECT_ID")
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        # En local o si Secret Manager no responde, leemos del .env como respaldo.
        # Logueamos como warning para detectarlo en producción si pasa de forma sostenida.
        fallback = os.getenv(secret_name, "")
        logger.warning(
            "Secret Manager no respondió para %s, usando env var. "
            "Valor presente: %s",
            secret_name,
            bool(fallback),
        )
        return fallback