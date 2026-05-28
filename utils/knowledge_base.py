# utils/knowledge_base.py
# RAG Engine: pipeline de datos + embeddings + búsqueda semántica
# Fuentes: Wikipedia + OpenTripMap + Tavily
# Vector store: Firestore + Gemini Embeddings

import os
import time
from datetime import datetime

import google.generativeai as genai
import numpy as np
import requests
import streamlit as st
from dotenv import load_dotenv
from google.cloud.firestore_v1.base_query import FieldFilter

from utils.gcp_client import get_firestore_client, get_secret
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

# ── Configuración ──────────────────────────────────────────────────────────
CIUDADES = {
    "Madrid":    {"lat": 40.4168, "lon": -3.7038, "lang": "es",
                  "wikipedia": "Madrid", "otm_id": "Q2807"},
    "Bayona":    {"lat": 43.4929, "lon": -1.4748, "lang": "fr",
                  "wikipedia": "Bayonne", "otm_id": "Q13698"},
    "París":     {"lat": 48.8566, "lon": 2.3522,  "lang": "fr",
                  "wikipedia": "Paris",  "otm_id": "Q90"},
    "Bruselas":  {"lat": 50.8503, "lon": 4.3517,  "lang": "fr",
                  "wikipedia": "Bruxelles", "otm_id": "Q239"},
    "Ámsterdam": {"lat": 52.3676, "lon": 4.9041,  "lang": "nl",
                  "wikipedia": "Amsterdam", "otm_id": "Q727"},
}

COLECCION_KB = "knowledge_base"
COLECCION_EMB = "embeddings_cache"

# ── Inicializar Gemini para embeddings ────────────────────────────────────
def init_embeddings():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = get_secret("GEMINI_API_KEY")
        except Exception:
            pass
    genai.configure(api_key=api_key)

# ── Generar embedding de un texto ─────────────────────────────────────────
def get_embedding(texto: str) -> list:
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texto,
            task_type="retrieval_document"
        )
        return result["embedding"]
    except Exception:
        logger.exception("Error generando embedding de documento")
        return []

def get_query_embedding(query: str) -> list:
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        return result["embedding"]
    except Exception:
        logger.exception("Error generando embedding de query")
        return []

# ── Similaridad coseno ─────────────────────────────────────────────────────
def cosine_similarity(v1: list, v2: list) -> float:
    """Calcula similitud coseno entre dos vectores"""
    a = np.array(v1)
    b = np.array(v2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ══════════════════════════════════════════════════════════════════════════
# FUENTE 1: Wikipedia
# ══════════════════════════════════════════════════════════════════════════
def fetch_wikipedia(ciudad: str, tema: str = None) -> list:
    documentos = []
    termino = tema if tema else ciudad

    # Wikipedia requiere User-Agent para no bloquear
    headers = {
        "User-Agent": "EuropeTravelApp/1.0 (travel planning bot; contact@example.com)",
        "Accept": "application/json",
    }

    try:
        # Resumen corto
        url = ("https://es.wikipedia.org/api/rest_v1/page/summary/" +
               requests.utils.quote(termino))
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            texto = data.get("extract", "")
            if texto and len(texto) > 100:
                documentos.append({
                    "ciudad": ciudad,
                    "fuente": "wikipedia",
                    "titulo": data.get("title", termino),
                    "texto": texto,
                    "url": data.get("content_urls", {})
                           .get("desktop", {}).get("page", ""),
                    "categoria": "informacion_general",
                    "fecha_ingesta": str(datetime.now().date()),
                })

        # Artículo completo
        url_full = "https://es.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": termino,
            "prop": "extracts",
            "exintro": False,
            "explaintext": True,
            "exsectionformat": "plain",
        }
        r = requests.get(url_full, params=params,
                         headers=headers, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                if page_id == "-1":
                    continue
                texto_full = page.get("extract", "")
                if texto_full and len(texto_full) > 500:
                    chunks = _dividir_en_chunks(texto_full, 1000)
                    for i, chunk in enumerate(chunks[:6]):
                        documentos.append({
                            "ciudad": ciudad,
                            "fuente": "wikipedia_full",
                            "titulo": f"{termino} — parte {i+1}",
                            "texto": chunk,
                            "url": (f"https://es.wikipedia.org/wiki/"
                                    f"{requests.utils.quote(termino)}"),
                            "categoria": "informacion_detallada",
                            "fecha_ingesta": str(datetime.now().date()),
                        })

    except Exception:
        logger.exception("Error Wikipedia ciudad=%s termino=%s", ciudad, termino)

    return documentos

def _dividir_en_chunks(texto: str, max_chars: int) -> list:
    """Divide texto en chunks respetando párrafos"""
    parrafos = texto.split("\n\n")
    chunks = []
    chunk_actual = ""

    for parrafo in parrafos:
        if len(chunk_actual) + len(parrafo) < max_chars:
            chunk_actual += parrafo + "\n\n"
        else:
            if chunk_actual:
                chunks.append(chunk_actual.strip())
            chunk_actual = parrafo + "\n\n"

    if chunk_actual:
        chunks.append(chunk_actual.strip())

    return [c for c in chunks if len(c) > 100]

# ══════════════════════════════════════════════════════════════════════════
# FUENTE 2: OpenTripMap — Atracciones turísticas
# ══════════════════════════════════════════════════════════════════════════
def fetch_opentripmap(ciudad: str) -> list:
    """
    Obtiene atracciones usando la API gratuita de OpenTripMap.
    Usa API key gratuita obtenida en opentripmap.com/register
    Si no hay key, usa Overpass (OpenStreetMap) como fallback.
    """
    documentos = []
    api_key = os.getenv("OPENTRIPMAP_API_KEY", "")

    if api_key:
        documentos = _fetch_opentripmap_con_key(ciudad, api_key)
    else:
        documentos = _fetch_overpass_fallback(ciudad)

    return documentos

def _fetch_opentripmap_con_key(ciudad: str, api_key: str) -> list:
    documentos = []
    coords = CIUDADES[ciudad]
    try:
        url = "https://api.opentripmap.com/0.1/en/places/radius"
        params = {
            "radius": 3000,
            "lon": coords["lon"],
            "lat": coords["lat"],
            "kinds": "interesting_places,museums,cultural,historic",
            "rate": "3",
            "format": "json",
            "limit": 20,
            "apikey": api_key,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            for lugar in r.json()[:15]:
                nombre = lugar.get("name", "").strip()
                if not nombre:
                    continue
                xid = lugar.get("xid", "")
                if xid:
                    detalle = fetch_opentripmap_detail(xid, api_key)
                    if detalle:
                        documentos.append({
                            "ciudad": ciudad,
                            "fuente": "opentripmap",
                            "titulo": nombre,
                            "texto": detalle,
                            "url": "",
                            "categoria": "atraccion_turistica",
                            "fecha_ingesta": str(datetime.now().date()),
                        })
                    time.sleep(0.3)
    except Exception:
        logger.exception("Error OpenTripMap ciudad=%s", ciudad)
    return documentos

def _fetch_overpass_fallback(ciudad: str) -> list:
    """
    Fallback usando Overpass API (OpenStreetMap) — 100% gratuita.
    Obtiene lugares turísticos, museos y restaurantes populares.
    """
    documentos = []
    coords = CIUDADES[ciudad]

    queries = [
        # Museos y turismo
        f"""
        [out:json][timeout:10];
        node["tourism"="museum"]
            (around:3000,{coords['lat']},{coords['lon']});
        out 10;
        """,
        # Atracciones turísticas
        f"""
        [out:json][timeout:10];
        node["tourism"="attraction"]
            (around:3000,{coords['lat']},{coords['lon']});
        out 10;
        """,
    ]

    for query in queries:
        try:
            r = requests.post(
                "https://overpass-api.de/api/interpreter",
                data=query, timeout=15
            )
            if r.status_code == 200:
                elementos = r.json().get("elements", [])
                for el in elementos[:8]:
                    tags = el.get("tags", {})
                    nombre = tags.get("name", "")
                    if not nombre:
                        continue
                    descripcion = tags.get("description", "")
                    wikipedia = tags.get("wikipedia", "")
                    tipo = tags.get("tourism", tags.get("amenity", ""))

                    texto = f"{nombre} es un lugar de interés en {ciudad}."
                    if descripcion:
                        texto += f" {descripcion}"
                    if tipo:
                        texto += f" Tipo: {tipo}."
                    if wikipedia:
                        texto += f" Wikipedia: {wikipedia}."

                    if len(texto) > 50:
                        documentos.append({
                            "ciudad": ciudad,
                            "fuente": "openstreetmap",
                            "titulo": nombre,
                            "texto": texto,
                            "url": "",
                            "categoria": "atraccion_turistica",
                            "fecha_ingesta": str(datetime.now().date()),
                        })
            time.sleep(1)  # respetar rate limit Overpass
        except Exception:
            logger.exception("Error Overpass ciudad=%s", ciudad)

    return documentos

def fetch_opentripmap_detail(xid: str, api_key: str = "") -> str:
    try:
        url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
        params = {"apikey": api_key}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            info = (data.get("wikipedia_extracts", {})
                        .get("text", ""))
            if not info:
                info = data.get("info", {}).get("descr", "")
            nombre = data.get("name", "")
            kinds = data.get("kinds", "").replace(",", ", ")
            if info:
                return (f"{nombre}: {info[:600]} "
                        f"(Categorías: {kinds})")
    except Exception:
        pass
    return ""

# ══════════════════════════════════════════════════════════════════════════
# FUENTE 3: Tavily — Artículos web recientes
# ══════════════════════════════════════════════════════════════════════════
def fetch_tavily(ciudad: str, temas: list) -> list:
    """
    Busca artículos web recientes sobre cada ciudad usando Tavily.
    Ya tienes la API key configurada.
    """
    documentos = []
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    for tema in temas:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)
            query = f"{tema} {ciudad} 2026 viajeros consejos"

            response = client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True,
            )

            if response.get("answer"):
                documentos.append({
                    "ciudad": ciudad,
                    "fuente": "tavily",
                    "titulo": f"{tema} en {ciudad}",
                    "texto": response["answer"],
                    "url": "",
                    "categoria": _categorizar_tema(tema),
                    "fecha_ingesta": str(datetime.now().date()),
                })

            for resultado in response.get("results", [])[:2]:
                contenido = resultado.get("content", "")
                if contenido and len(contenido) > 200:
                    documentos.append({
                        "ciudad": ciudad,
                        "fuente": "tavily_web",
                        "titulo": resultado.get("title", tema),
                        "texto": contenido[:1000],
                        "url": resultado.get("url", ""),
                        "categoria": _categorizar_tema(tema),
                        "fecha_ingesta": str(datetime.now().date()),
                    })

            time.sleep(0.5)  # respetar rate limit

        except Exception:
            logger.exception("Error Tavily ciudad=%s tema=%s", ciudad, tema)

    return documentos

def _categorizar_tema(tema: str) -> str:
    if any(w in tema.lower() for w in
           ["restaurante", "comida", "gastronomía", "comer"]):
        return "gastronomia"
    if any(w in tema.lower() for w in
           ["transporte", "metro", "bus", "tram", "tren"]):
        return "transporte"
    if any(w in tema.lower() for w in
           ["hotel", "airbnb", "hospedaje", "alojamiento"]):
        return "hospedaje"
    if any(w in tema.lower() for w in
           ["museo", "atracción", "visitar", "turismo"]):
        return "turismo"
    return "tips_generales"

# ══════════════════════════════════════════════════════════════════════════
# GUARDAR EN FIRESTORE CON EMBEDDING
# ══════════════════════════════════════════════════════════════════════════
def guardar_documento(doc: dict) -> str:
    """
    Guarda un documento en Firestore con su embedding.
    Genera un ID único basado en ciudad + titulo para evitar duplicados.
    """
    db = get_firestore_client()

    # ID único para evitar duplicados
    doc_id = (f"{doc['ciudad']}_{doc['fuente']}_"
              f"{doc['titulo'][:30]}").replace(" ", "_").replace("/", "_")

    # Verificar si ya existe
    ref = db.collection(COLECCION_KB).document(doc_id)
    existing = ref.get()
    if existing.exists:
        return f"SKIP: {doc_id}"

    # Generar embedding
    texto_para_embedding = f"{doc['titulo']} {doc['texto']}"
    embedding = get_embedding(texto_para_embedding)

    if not embedding:
        return f"ERROR_EMBEDDING: {doc_id}"

    # Guardar documento con embedding
    ref.set({
        **doc,
        "embedding": embedding,
        "timestamp": datetime.now(),
    })

    return f"OK: {doc_id}"

# ══════════════════════════════════════════════════════════════════════════
# BÚSQUEDA SEMÁNTICA
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def _cargar_docs_kb(ciudad: str | None) -> list:
    """
    Carga los documentos de la KB desde Firestore, cacheados 10 min.
    La KB cambia con la ingesta (proceso manual), no en runtime, así que
    una cache de 10 min mantiene los reads de Firestore dentro de la
    capa gratuita aun con muchas preguntas al chat de Lady.
    """
    db = get_firestore_client()
    if ciudad:
        stream = (db.collection(COLECCION_KB)
                    .where(filter=FieldFilter("ciudad", "==", ciudad))
                    .stream())
    else:
        stream = db.collection(COLECCION_KB).stream()

    return [doc.to_dict() for doc in stream]


def buscar_conocimiento(query: str, ciudad: str = None,
                        top_k: int = 5) -> list:
    """
    Busca documentos relevantes usando similitud coseno.

    1. Genera embedding de la query
    2. Compara contra los documentos cacheados (10 min) de Firestore
    3. Retorna los top_k más similares
    """
    init_embeddings()
    query_emb = get_query_embedding(query)
    if not query_emb:
        return []

    docs = _cargar_docs_kb(ciudad)

    resultados = []
    for data in docs:
        doc_emb = data.get("embedding", [])
        if not doc_emb:
            continue

        similitud = cosine_similarity(query_emb, doc_emb)
        if similitud > 0.5:  # umbral mínimo de relevancia
            resultados.append({
                "titulo": data.get("titulo", ""),
                "texto": data.get("texto", ""),
                "ciudad": data.get("ciudad", ""),
                "categoria": data.get("categoria", ""),
                "fuente": data.get("fuente", ""),
                "url": data.get("url", ""),
                "similitud": similitud,
            })

    resultados.sort(key=lambda x: x["similitud"], reverse=True)
    return resultados[:top_k]


def invalidar_cache_kb():
    """Invalida la cache de la KB. Llamar desde el admin panel luego de ingestar."""
    _cargar_docs_kb.clear()

def formatear_conocimiento(resultados: list) -> str:
    """Convierte resultados de búsqueda en contexto para Gemini"""
    if not resultados:
        return ""

    texto = "\n\nCONOCIMIENTO ADICIONAL DE LA BASE DE DATOS:\n"
    for r in resultados:
        texto += f"\n📍 [{r['ciudad']} — {r['titulo']}]\n"
        texto += f"{r['texto'][:500]}\n"
        if r.get("url"):
            texto += f"Fuente: {r['url']}\n"

    return texto
