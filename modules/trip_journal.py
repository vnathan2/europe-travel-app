import hashlib
import os
from datetime import date, datetime
from io import BytesIO

import streamlit as st
from google.cloud.firestore_v1.base_query import FieldFilter
from PIL import Image

from utils.gcp_client import get_firestore_client, get_signed_url, get_storage_client

# ── 1. CONFIGURACIÓN Y CONSTANTES ──────────────────────────────────────────
CIUDADES = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
EMOJIS_CIUDAD = {
    "Madrid": "🇪🇸", "Bayona": "🇫🇷", "París": "🇫🇷",
    "Bruselas": "🇧🇪", "Ámsterdam": "🇳🇱"
}
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "europe-travel-app-bucket")
COLECCION = "journal_entries"
MAX_IMG_SIZE = 1200   # px máximo para ahorro de espacio
IMG_QUALITY = 75      # Balance perfecto entre peso y calidad

# ── 2. LÓGICA DE IMÁGENES (STORAGE) ────────────────────────────────────────
def comprimir_imagen(imagen_bytes: bytes) -> bytes:
    """Comprime y redimensiona para mantener la app en Capa Gratuita."""
    img = Image.open(BytesIO(imagen_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if max(img.size) > MAX_IMG_SIZE:
        ratio = MAX_IMG_SIZE / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    output = BytesIO()
    img.save(output, format="JPEG", quality=IMG_QUALITY, optimize=True)
    return output.getvalue()

def subir_foto(imagen_bytes: bytes, original_name: str, ciudad: str) -> str:
    """Sube a GCS sin hacerla pública. Retorna el blob path (no URL pública)."""
    imagen_comprimida = comprimir_imagen(imagen_bytes)

    file_hash = hashlib.md5(imagen_comprimida).hexdigest()[:10]
    nombre_blob = f"journal/{ciudad}/{datetime.now().strftime('%Y%m%d')}_{file_hash}.jpg"

    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(nombre_blob)
    blob.upload_from_string(imagen_comprimida, content_type="image/jpeg")
    # Sin make_public() — las fotos son privadas

    return nombre_blob  # Guardamos el path, no la URL pública

def _blob_path_desde_valor(valor: str) -> str:
    """Compatibilidad con entradas antiguas que guardaban URL pública."""
    if valor.startswith("http"):
        return valor.split(f"{BUCKET_NAME}/")[1]
    return valor

@st.cache_data(ttl=3600)
def descargar_foto(blob_path: str) -> bytes:
    """Descarga foto privada desde GCS. Cacheada 1 hora para no repetir lecturas."""
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(_blob_path_desde_valor(blob_path))
    return blob.download_as_bytes()

def foto_src(blob_path: str):
    """Fuente para st.image: URL firmada (el navegador baja directo de GCS, sin
    pasar bytes por Cloud Run) o, si la firma falla, los bytes descargados."""
    path = _blob_path_desde_valor(blob_path)
    url = get_signed_url(path)
    return url if url else descargar_foto(blob_path)

# ── 3. LÓGICA DE DATOS (FIRESTORE CON CACHÉ) ───────────────────────────────
@st.cache_data(ttl=600)
def obtener_entradas(ciudad_filtro: str = "Todas"):
    """Lee de Firestore usando caché para evitar exceder cuotas gratuitas."""
    db = get_firestore_client()
    if ciudad_filtro != "Todas":
        query = db.collection(COLECCION).where(filter=FieldFilter("ciudad", "==", ciudad_filtro))
    else:
        query = db.collection(COLECCION)

    docs = query.order_by("fecha", direction="DESCENDING").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

def eliminar_entrada_completa(doc_id: str, fotos: list):
    """Borra el documento y sus fotos físicas para no llenar el Bucket."""
    db = get_firestore_client()
    bucket = get_storage_client().bucket(BUCKET_NAME)

    for valor in fotos:
        try:
            bucket.blob(_blob_path_desde_valor(valor)).delete()
        except Exception:
            pass  # Continuar si la foto ya no existe

    db.collection(COLECCION).document(doc_id).delete()
    obtener_entradas.clear()

# ── 4. INTERFAZ DE USUARIO (STREAMLIT) ─────────────────────────────────────
def mostrar():
    st.title("📔 Trip Journal")
    st.caption("Recuerdos del viaje de 15 años de Camila")

    tab_nueva, tab_ver, tab_galeria = st.tabs(["✍️ Nueva Entrada", "📖 Ver Diario", "🖼️ Galería"])

    with tab_nueva:
        with st.form("form_diario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", value=date.today())
                ciudad = st.selectbox("Ciudad", CIUDADES)
                titulo = st.text_input("Título", placeholder="¿Qué pasó hoy?")
            with col2:
                autor = st.selectbox("Autor", ["Papá", "Mamá", "Camila"])
                animo = st.select_slider("Ánimo", options=["😴", "😐", "🙂", "😊", "🤩"])
                rating = st.slider("Rating", 1, 10, 10)

            texto = st.text_area("Crónica del día", height=150)
            highlight = st.text_input("🌟 Momento inolvidable")
            fotos = st.file_uploader("Fotos (máx 5)", type=["jpg", "png", "webp"], accept_multiple_files=True)

            enviar = st.form_submit_button("💾 Guardar en el Diario", type="primary", use_container_width=True)

        if enviar:
            if not titulo or not texto:
                st.error("Título y crónica son obligatorios.")
            else:
                with st.spinner("Subiendo fotos y guardando momentos..."):
                    paths = [subir_foto(f.read(), f.name, ciudad) for f in (fotos[:5] if fotos else [])]
                    entrada = {
                        "fecha": str(fecha), "ciudad": ciudad, "titulo": titulo,
                        "texto": texto, "highlight": highlight, "autor": autor,
                        "animo": animo, "rating": rating, "fotos": paths,
                        "timestamp": datetime.now()
                    }
                    get_firestore_client().collection(COLECCION).add(entrada)
                    obtener_entradas.clear()
                    st.success("✅ ¡Entrada guardada!")
                    st.balloons()

    with tab_ver:
        ciudad_filtro = st.selectbox("Filtrar por parada", ["Todas"] + CIUDADES)
        entradas = obtener_entradas(ciudad_filtro)

        for e in entradas:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(f"{EMOJIS_CIUDAD.get(e['ciudad'], '📍')} {e['titulo']}")
                if c2.button("🗑️", key=f"del_{e['id']}"):
                    eliminar_entrada_completa(e['id'], e.get('fotos', []))
                    st.rerun()

                st.caption(f"📅 {e['fecha']} | ✍️ {e['autor']} | {e['animo']} {e['rating']}/10")
                st.write(e['texto'])
                if e.get('highlight'):
                    st.info(f"🌟 **Highlight:** {e['highlight']}")

                if e.get('fotos'):
                    cols = st.columns(len(e['fotos']))
                    for idx, blob_path in enumerate(e['fotos']):
                        try:
                            cols[idx].image(foto_src(blob_path), use_column_width=True)
                        except Exception:
                            cols[idx].caption("⚠️ Foto no disponible")

    with tab_galeria:
        todas = obtener_entradas("Todas")
        fotos_galeria = [{"path": p, "ciudad": e['ciudad']} for e in todas for p in e.get('fotos', [])]

        if fotos_galeria:
            cols = st.columns(3)
            for i, f in enumerate(fotos_galeria):
                with cols[i % 3]:
                    try:
                        st.image(foto_src(f['path']), caption=f["ciudad"], use_column_width=True)
                    except Exception:
                        st.caption("⚠️ Foto no disponible")
        else:
            st.info("No hay fotos en la galería aún.")
