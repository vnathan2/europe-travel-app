# modules/packing_checker.py
# Módulo 5: Packing Checker
# Lista de equipaje con clima real vía Open-Meteo (gratuita, sin API key)
# Persistencia compartida en Firestore: Giovanna, Camila y Jonathan ven la misma lista.


import requests
import streamlit as st

from utils.gcp_client import get_firestore_client
from utils.logger import get_logger

logger = get_logger(__name__)

COLECCION_PACKING = "packing"
DOC_ID_FAMILIA    = "familia"

# ── Coordenadas de las ciudades del viaje ──────────────────────────────────
CIUDADES_COORDS = {
    "Madrid":    {"lat": 40.4168, "lon": -3.7038, "fechas": "15-18 julio"},
    "Bayona":    {"lat": 43.4929, "lon": -1.4748, "fechas": "19-20 julio"},
    "París":     {"lat": 48.8566, "lon": 2.3522,  "fechas": "21-24 julio"},
    "Bruselas":  {"lat": 50.8503, "lon": 4.3517,  "fechas": "25-26 julio"},
    "Ámsterdam": {"lat": 52.3676, "lon": 4.9041,  "fechas": "26-29 julio"},
}

# ── Lista maestra de equipaje ──────────────────────────────────────────────
EQUIPAJE = {
    "📄 Documentos": {
        "critico": True,
        "items": [
            {"nombre": "Pasaporte (3 personas)", "cantidad": "3", "critico": True},
            {"nombre": "Fotocopia del pasaporte", "cantidad": "3 juegos", "critico": True},
            {"nombre": "Póliza seguro de viaje impresa", "cantidad": "1", "critico": True},
            {"nombre": "Tarjeta de crédito/débito internacional", "cantidad": "2", "critico": True},
            {"nombre": "Efectivo en euros (€200 familia)", "cantidad": "€200", "critico": True},
            {"nombre": "Tickets de trenes (cuando reserves)", "cantidad": "—", "critico": True},
            {"nombre": "Reservas de hoteles impresas", "cantidad": "—", "critico": False},
            {"nombre": "Fotos carnet extra (por si acaso)", "cantidad": "4 c/u", "critico": False},
        ]
    },
    "👔 Ropa Adultos": {
        "critico": False,
        "items": [
            {"nombre": "Pantalones/jeans", "cantidad": "2-3", "critico": False},
            {"nombre": "Camisetas manga corta", "cantidad": "5-6", "critico": False},
            {"nombre": "Camisetas manga larga", "cantidad": "2", "critico": False},
            {"nombre": "Polera/suéter ligero", "cantidad": "2", "critico": False},
            {"nombre": "Chaqueta impermeable", "cantidad": "1 c/u", "critico": True},
            {"nombre": "Ropa interior", "cantidad": "7 c/u", "critico": False},
            {"nombre": "Calcetines", "cantidad": "7 pares c/u", "critico": False},
            {"nombre": "Zapatos cómodos para caminar", "cantidad": "1 par", "critico": True},
            {"nombre": "Zapatos elegantes (para cenas especiales)", "cantidad": "1 par", "critico": False},
            {"nombre": "Sandalias/chanclas", "cantidad": "1 par", "critico": False},
            {"nombre": "Ropa de dormir", "cantidad": "2", "critico": False},
            {"nombre": "Vestido/ropa elegante (cumpleaños)", "cantidad": "1", "critico": True},
            {"nombre": "Gorro/sombrero (sol Madrid)", "cantidad": "1", "critico": False},
        ]
    },
    "👧 Ropa Hija (15 años)": {
        "critico": False,
        "items": [
            {"nombre": "Jeans/pantalones", "cantidad": "2-3", "critico": False},
            {"nombre": "Camisetas variadas", "cantidad": "6", "critico": False},
            {"nombre": "Vestidos/faldas", "cantidad": "2", "critico": False},
            {"nombre": "Chaqueta impermeable", "cantidad": "1", "critico": True},
            {"nombre": "Ropa interior", "cantidad": "7", "critico": False},
            {"nombre": "Calcetines", "cantidad": "7 pares", "critico": False},
            {"nombre": "Zapatillas cómodas", "cantidad": "1 par", "critico": True},
            {"nombre": "Outfit especial cumpleaños (Warner)", "cantidad": "1", "critico": True},
            {"nombre": "Traje de baño (por si acaso)", "cantidad": "1", "critico": False},
        ]
    },
    "💊 Salud y Farmacia": {
        "critico": True,
        "items": [
            {"nombre": "Ibuprofeno/paracetamol", "cantidad": "1 caja", "critico": True},
            {"nombre": "Medicamentos personales habituales", "cantidad": "16 días+", "critico": True},
            {"nombre": "Antidiarreico (viaje)", "cantidad": "1 caja", "critico": True},
            {"nombre": "Antihistamínico (alergias)", "cantidad": "1 caja", "critico": False},
            {"nombre": "Termómetro digital", "cantidad": "1", "critico": False},
            {"nombre": "Protector solar SPF50+", "cantidad": "2", "critico": True},
            {"nombre": "Repelente de insectos", "cantidad": "1", "critico": False},
            {"nombre": "Tiritas/banditas", "cantidad": "1 caja", "critico": False},
            {"nombre": "Crema para rozaduras (caminar mucho)", "cantidad": "1", "critico": True},
            {"nombre": "Gotas oculares (aire acondicionado avión)", "cantidad": "1", "critico": False},
            {"nombre": "Mascarilla (avión)", "cantidad": "5", "critico": False},
        ]
    },
    "🔌 Tecnología": {
        "critico": False,
        "items": [
            {"nombre": "Celulares cargados", "cantidad": "3", "critico": True},
            {"nombre": "Cargadores de celular", "cantidad": "3", "critico": True},
            {"nombre": "Adaptador de enchufe europeo (tipo F)", "cantidad": "2", "critico": True},
            {"nombre": "Power bank / batería externa", "cantidad": "1-2", "critico": True},
            {"nombre": "Auriculares (avión 11h)", "cantidad": "3", "critico": False},
            {"nombre": "Cámara fotográfica", "cantidad": "1", "critico": False},
            {"nombre": "Tarjetas de memoria extra", "cantidad": "2", "critico": False},
            {"nombre": "Laptop/tablet (opcional)", "cantidad": "1", "critico": False},
            {"nombre": "Cable USB multiuso", "cantidad": "2", "critico": False},
            {"nombre": "SIM europea (comprar en Madrid)", "cantidad": "3", "critico": True},
        ]
    },
    "🧴 Higiene y Cuidado": {
        "critico": False,
        "items": [
            {"nombre": "Champú y acondicionador", "cantidad": "tamaño viaje", "critico": False},
            {"nombre": "Gel de ducha", "cantidad": "tamaño viaje", "critico": False},
            {"nombre": "Desodorante", "cantidad": "2", "critico": True},
            {"nombre": "Pasta dental + cepillo", "cantidad": "3 juegos", "critico": True},
            {"nombre": "Hilo dental", "cantidad": "1", "critico": False},
            {"nombre": "Maquillaje básico", "cantidad": "según persona", "critico": False},
            {"nombre": "Hidratante facial y corporal", "cantidad": "1 c/u", "critico": False},
            {"nombre": "Toallitas húmedas", "cantidad": "2 paquetes", "critico": False},
            {"nombre": "Papel higiénico de emergencia", "cantidad": "1 rollo", "critico": False},
            {"nombre": "Perfume (tamaño viaje <100ml)", "cantidad": "1", "critico": False},
        ]
    },
    "🎒 Accesorios de Viaje": {
        "critico": False,
        "items": [
            {"nombre": "Mochila de día (para turismo)", "cantidad": "1-2", "critico": True},
            {"nombre": "Candados para maletas", "cantidad": "2", "critico": True},
            {"nombre": "Bolsas ziploc (organización)", "cantidad": "10", "critico": False},
            {"nombre": "Riñonera antirrobo", "cantidad": "1-2", "critico": True},
            {"nombre": "Paraguas compacto", "cantidad": "1-2", "critico": True},
            {"nombre": "Botella de agua reutilizable", "cantidad": "3", "critico": False},
            {"nombre": "Snacks para el avión", "cantidad": "varios", "critico": False},
            {"nombre": "Almohada de viaje (avión 11h)", "cantidad": "3", "critico": False},
            {"nombre": "Antifaz para dormir", "cantidad": "3", "critico": False},
            {"nombre": "Bolsa de laundry (ropa sucia)", "cantidad": "2", "critico": False},
        ]
    },
}

# ── Persistencia de packing compartida (Firestore) ─────────────────────────
@st.cache_data(ttl=600)
def cargar_packing() -> dict:
    """
    Lee el estado de items_marcados desde Firestore.
    Documento único `packing/familia` compartido entre Jonathan, Giovanna y Camila.
    Cache de 10 min para no consumir reads del free tier en cada rerun.
    """
    try:
        db = get_firestore_client()
        doc = db.collection(COLECCION_PACKING).document(DOC_ID_FAMILIA).get()
        if doc.exists:
            return doc.to_dict().get("items_marcados", {}) or {}
    except Exception:
        logger.exception("No se pudo cargar packing desde Firestore")
    return {}


def guardar_packing(items_marcados: dict) -> bool:
    """
    Persiste items_marcados en Firestore. Last-write-wins entre miembros
    de la familia (aceptable para este flujo de uso).
    """
    try:
        db = get_firestore_client()
        usuario = st.session_state.get("auth_user", {}).get("email", "anonimo")
        db.collection(COLECCION_PACKING).document(DOC_ID_FAMILIA).set({
            "items_marcados":   items_marcados,
            "actualizado_por":  usuario,
        })
        cargar_packing.clear()
        return True
    except Exception:
        logger.exception("No se pudo guardar packing en Firestore")
        return False


# ── Obtener clima real de Open-Meteo ───────────────────────────────────────
def get_clima(ciudad: str) -> dict:
    """
    Consulta el clima de julio en cada ciudad usando Open-Meteo.
    API completamente gratuita, sin API key.
    Usamos datos históricos de julio para proyección.
    """
    coords = CIUDADES_COORDS[ciudad]
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
            f"&timezone=Europe/Madrid"
            f"&forecast_days=16"
        )
        response = requests.get(url, timeout=5)
        data = response.json()
        daily = data.get("daily", {})

        if not daily:
            return None

        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precipitacion = daily.get("precipitation_sum", [])

        return {
            "temp_max_avg": round(sum(temps_max) / len(temps_max), 1) if temps_max else 0,
            "temp_min_avg": round(sum(temps_min) / len(temps_min), 1) if temps_min else 0,
            "temp_max_max": round(max(temps_max), 1) if temps_max else 0,
            "lluvia_dias": sum(1 for p in precipitacion if p > 1),
            "ciudad": ciudad,
            "fechas": coords["fechas"],
        }
    except Exception:
        # Datos históricos de respaldo para julio
        respaldo = {
            "Madrid":    {"temp_max_avg": 34, "temp_min_avg": 20, "temp_max_max": 38, "lluvia_dias": 1},
            "Bayona":    {"temp_max_avg": 24, "temp_min_avg": 17, "temp_max_max": 27, "lluvia_dias": 3},
            "París":     {"temp_max_avg": 26, "temp_min_avg": 16, "temp_max_max": 30, "lluvia_dias": 4},
            "Bruselas":  {"temp_max_avg": 23, "temp_min_avg": 14, "temp_max_max": 27, "lluvia_dias": 5},
            "Ámsterdam": {"temp_max_avg": 22, "temp_min_avg": 14, "temp_max_max": 25, "lluvia_dias": 6},
        }
        datos = respaldo.get(ciudad, {})
        datos["ciudad"] = ciudad
        datos["fechas"] = CIUDADES_COORDS[ciudad]["fechas"]
        return datos

# ── Recomendaciones según clima ────────────────────────────────────────────
def get_recomendaciones_clima(clima: dict) -> list:
    recomendaciones = []
    if clima["temp_max_avg"] > 30:
        recomendaciones.append(f"🌡️ Calor intenso en {clima['ciudad']} (~{clima['temp_max_avg']}°C). Lleva ropa ligera, protector solar SPF50+ y mucha agua.")
    if clima.get("temp_max_max", 0) > 36:
        recomendaciones.append(f"🔥 Posible ola de calor — máximas de hasta {clima['temp_max_max']}°C. Evita actividades al aire libre entre 13:00-17:00.")
    if clima["lluvia_dias"] >= 3:
        recomendaciones.append(f"🌧️ {clima['lluvia_dias']} días de lluvia esperados en {clima['ciudad']}. Lleva paraguas compacto y chaqueta impermeable.")
    if clima["temp_min_avg"] < 16:
        recomendaciones.append(f"🧥 Noches frescas en {clima['ciudad']} (~{clima['temp_min_avg']}°C). Lleva una chaqueta para las salidas nocturnas.")
    return recomendaciones

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("🧳 Packing Checker")
    st.caption("Lista de equipaje inteligente con clima real de cada ciudad")

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_clima, tab_lista, tab_criticos = st.tabs([
        "🌤️ Clima por Ciudad", "✅ Lista de Equipaje", "🚨 Solo Críticos"
    ])

    # ── TAB 1: Clima ───────────────────────────────────────────────────────
    with tab_clima:
        st.subheader("🌡️ Clima esperado en julio 2026")
        st.caption("Datos en tiempo real de Open-Meteo (gratuito, sin API key)")

        with st.spinner("Consultando clima de las 5 ciudades..."):
            climas = {ciudad: get_clima(ciudad) for ciudad in CIUDADES_COORDS}

        # Resumen de temperaturas
        cols = st.columns(5)
        for i, (ciudad, clima) in enumerate(climas.items()):
            if clima:
                with cols[i]:
                    st.metric(
                        label=ciudad,
                        value=f"{clima['temp_max_avg']}°C",
                        delta=f"Mín: {clima['temp_min_avg']}°C"
                    )
                    st.caption(f"🌧️ {clima['lluvia_dias']} días lluvia")
                    st.caption(f"📅 {clima['fechas']}")

        st.divider()

        # Recomendaciones por ciudad
        st.subheader("💡 Recomendaciones según el clima")
        for ciudad, clima in climas.items():
            if clima:
                recs = get_recomendaciones_clima(clima)
                if recs:
                    with st.expander(f"📍 {ciudad} — {clima['fechas']}", expanded=True):
                        for rec in recs:
                            st.warning(rec)

    # Inicializar items_marcados desde Firestore (compartido familia)
    if "items_marcados" not in st.session_state:
        st.session_state.items_marcados   = cargar_packing()
        st.session_state._packing_snapshot = dict(st.session_state.items_marcados)

    # ── TAB 2: Lista completa ──────────────────────────────────────────────
    with tab_lista:
        st.subheader("✅ Lista completa de equipaje")

        total_items = sum(len(cat["items"]) for cat in EQUIPAJE.values())
        marcados = sum(1 for v in st.session_state.items_marcados.values() if v)

        # Barra de progreso
        progreso = marcados / total_items if total_items > 0 else 0
        st.progress(progreso)
        st.caption(f"✅ {marcados} de {total_items} items empacados ({int(progreso*100)}%)")

        if progreso == 1.0:
            st.success("🎉 ¡Todo listo para el viaje!")
            st.balloons()

        # Lista por categoría
        for categoria, contenido in EQUIPAJE.items():
            with st.expander(categoria, expanded=contenido["critico"]):
                for item in contenido["items"]:
                    key = f"{categoria}_{item['nombre']}"
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        checked = st.checkbox(
                            item["nombre"],
                            key=key,
                            value=st.session_state.items_marcados.get(key, False)
                        )
                        st.session_state.items_marcados[key] = checked
                    with col2:
                        st.caption(f"Cantidad: {item['cantidad']}")
                    with col3:
                        if item["critico"]:
                            st.caption("🔴 Crítico")

        # Botón reset
        if st.button("🔄 Reiniciar lista", type="secondary"):
            st.session_state.items_marcados = {}
            guardar_packing({})
            st.session_state._packing_snapshot = {}
            st.rerun()

    # ── TAB 3: Solo críticos ───────────────────────────────────────────────
    with tab_criticos:
        st.subheader("🚨 Items críticos — No puedes olvidarlos")
        st.caption("Estos son los items más importantes del viaje")

        for categoria, contenido in EQUIPAJE.items():
            criticos = [i for i in contenido["items"] if i["critico"]]
            if criticos:
                st.write(f"**{categoria}**")
                for item in criticos:
                    # misma key que tab "Lista completa" → checkboxes sincronizados
                    key = f"crit_{categoria}_{item['nombre']}"
                    estado_key = f"{categoria}_{item['nombre']}"
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        checked = st.checkbox(
                            item["nombre"],
                            key=key,
                            value=st.session_state.items_marcados.get(estado_key, False)
                        )
                        st.session_state.items_marcados[estado_key] = checked
                    with col2:
                        st.caption(item["cantidad"])
                st.divider()

    # ── Persistencia: si hubo cambios en este render, escribir a Firestore ─
    # Last-write-wins entre miembros de la familia. Solo escribe si difiere
    # del snapshot cargado al entrar, para no quemar writes en cada rerun.
    snapshot = st.session_state.get("_packing_snapshot", {})
    if snapshot != st.session_state.items_marcados:
        if guardar_packing(st.session_state.items_marcados):
            st.session_state._packing_snapshot = dict(st.session_state.items_marcados)
