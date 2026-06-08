# modules/hoteles.py
# Tracking de hoteles del viaje + búsqueda asistida por Lady (Gemini + Tavily)

import os
from datetime import date, datetime

import streamlit as st

from utils.gcp_client import get_firestore_client, get_secret
from utils.logger import get_logger
from utils.price_helper import mostrar_precio

logger = get_logger(__name__)

COLECCION = "hoteles"

CIUDADES_VIAJE = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]

# Ciudades con hospedaje familiar: sin reserva, sin costo, sin búsqueda de Lady
CIUDADES_FAMILIARES = {"Bayona", "Ámsterdam"}

CIUDAD_EMOJI = {
    "Madrid": "🇪🇸", "Bayona": "🇫🇷", "París": "🇫🇷",
    "Bruselas": "🇧🇪", "Ámsterdam": "🇳🇱",
}

# Fechas planeadas por ciudad: (check-in default, check-out default, # noches)
# Basado en CLAUDE.md "Hoja de ruta del viaje". Bayona y Ámsterdam = casa familiar.
RANGO_POR_CIUDAD = {
    "Madrid":    (date(2026, 7, 15), date(2026, 7, 18), 3),
    "Bayona":    (date(2026, 7, 19), date(2026, 7, 21), 2),
    "París":     (date(2026, 7, 21), date(2026, 7, 25), 4),
    "Bruselas":  (date(2026, 7, 25), date(2026, 7, 27), 2),
    "Ámsterdam": (date(2026, 7, 27), date(2026, 7, 30), 3),
}


# ── 1. PERSISTENCIA EN FIRESTORE ──────────────────────────────────────────
@st.cache_data(ttl=600)  # 10 min, cuotas free-tier amistosas
def cargar_hoteles() -> dict:
    """Devuelve dict {ciudad: hotel_data} desde Firestore."""
    try:
        db = get_firestore_client()
        return {doc.id: doc.to_dict() for doc in db.collection(COLECCION).stream()}
    except Exception as e:
        logger.warning("No se pudo cargar hoteles: %s", e)
        return {}


def guardar_hotel(ciudad: str, data: dict):
    """Persiste un hotel (un documento por ciudad)."""
    db = get_firestore_client()
    db.collection(COLECCION).document(ciudad).set({
        **data,
        "actualizado_en": datetime.now(),
        "actualizado_por": st.session_state.get("_user_name", "?"),
    })
    cargar_hoteles.clear()


def hotel_por_fecha(fecha: date, hoteles: dict | None = None):
    """Devuelve (ciudad, hotel_dict) según fecha. (None, None) si no estás en viaje."""
    if hoteles is None:
        hoteles = cargar_hoteles()
    for ciudad, (inicio, fin, _) in RANGO_POR_CIUDAD.items():
        if inicio <= fecha < fin:  # check-in inclusivo, check-out exclusivo
            return ciudad, hoteles.get(ciudad)
    return None, None


# ── 2. BÚSQUEDA CON LADY (Tavily + Gemini) ────────────────────────────────
def buscar_con_lady(ciudad: str, check_in: date, check_out: date) -> str:
    """Sugerencia de hoteles vía Gemini + Tavily. Texto markdown."""
    # 1) Buscar en internet con Tavily (opcional)
    contexto = ""
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY") or get_secret("TAVILY_API_KEY")
        if api_key and api_key.startswith("tvly-"):
            client = TavilyClient(api_key=api_key)
            query = (
                f"mejores hoteles familia 3 personas centro {ciudad} "
                f"del {check_in:%d %b} al {check_out:%d %b %Y} con desayuno"
            )
            resp = client.search(
                query=query, search_depth="basic",
                max_results=5, include_answer=True,
            )
            if resp.get("answer"):
                contexto += f"Respuesta directa: {resp['answer']}\n\n"
            for r in resp.get("results", []):
                contexto += f"- {r.get('title','')}: {r.get('content','')[:250]}\n"
    except Exception as e:
        logger.warning("Tavily falló buscando hoteles en %s: %s", ciudad, e)

    # 2) Pasar por Gemini para formatear
    try:
        import google.generativeai as genai

        gemini_key = os.getenv("GEMINI_API_KEY") or get_secret("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""Eres Lady 🐾, una schnauzer viajera. La familia (Jonathan 46, Giovanna 46, Camila 15)
busca hotel en {ciudad} del {check_in:%d %b %Y} al {check_out:%d %b %Y}.

Información encontrada en internet:
{contexto if contexto else '(sin datos frescos; sugiere desde tu conocimiento general)'}

Da 3-5 opciones concretas con este formato por opción:
- 🏨 **Nombre del hotel**
- 📍 Zona/dirección aproximada
- 💰 Rango: € / €€ / €€€
- ✨ Por qué le sirve a esta familia (metro cerca, family room, desayuno, etc.)
- 🔗 Búsqueda en Booking.com (link genérico al search está bien)

Responde en markdown, máximo 300 palabras. Si no tienes info fiable, sé honesta y sugiere
buscar directamente en Booking con un link de búsqueda."""

        return model.generate_content(
            prompt, request_options={"timeout": 30}
        ).text
    except Exception as e:
        logger.warning("Lady falló buscando hoteles en %s: %s", ciudad, e)
        url_busqueda = (
            f"https://www.booking.com/searchresults.html?ss="
            f"{ciudad.replace(' ', '+')}"
            f"&checkin={check_in:%Y-%m-%d}&checkout={check_out:%Y-%m-%d}"
            f"&group_adults=3"
        )
        return (
            f"🐾 No pude buscar en línea ahora mismo. Te dejo el link directo a Booking "
            f"para **{ciudad}** del {check_in:%d %b} al {check_out:%d %b}: "
            f"[Buscar en Booking.com]({url_busqueda})"
        )


# ── 3. UI ─────────────────────────────────────────────────────────────────
def _form_hotel(ciudad: str, hotel_actual: dict, ci_def, co_def, es_familiar: bool):
    """Form de edición para un hotel. Devuelve dict con valores actuales del form."""
    ci_actual = (
        date.fromisoformat(hotel_actual["check_in"])
        if hotel_actual.get("check_in") else ci_def
    )
    co_actual = (
        date.fromisoformat(hotel_actual["check_out"])
        if hotel_actual.get("check_out") else co_def
    )

    with st.form(f"form_hotel_{ciudad}", clear_on_submit=False):
        nombre = st.text_input(
            "Nombre del hotel:",
            value=hotel_actual.get("nombre", "Casa familiar 🏠" if es_familiar else ""),
        )
        direccion = st.text_input("Dirección:", value=hotel_actual.get("direccion", ""))

        c1, c2 = st.columns(2)
        with c1:
            check_in = st.date_input("Check-in:", value=ci_actual)
        with c2:
            check_out = st.date_input("Check-out:", value=co_actual)

        c1, c2 = st.columns(2)
        with c1:
            num_reserva = st.text_input(
                "# de reserva:",
                value=hotel_actual.get("num_reserva", ""),
                placeholder="Ej: ABC123",
            )
        with c2:
            telefono = st.text_input(
                "Teléfono:", value=hotel_actual.get("telefono", "")
            )

        link = st.text_input(
            "Link de reserva:",
            value=hotel_actual.get("link", ""),
            placeholder="https://booking.com/... o https://hotel.com/...",
        )

        # Costo: solo visible/editable para quien ve precios (admin)
        show_prices = st.session_state.get("_show_prices", False)
        if show_prices:
            costo = st.number_input(
                "Costo total (EUR):",
                min_value=0.0,
                value=float(hotel_actual.get("costo", 0.0)),
                step=10.0,
                format="%.2f",
            )
        else:
            costo = float(hotel_actual.get("costo", 0.0))  # mantener valor previo

        estado_actual = hotel_actual.get("estado", "pendiente")
        estado = st.selectbox(
            "Estado:",
            ["pendiente", "reservado"],
            index=0 if estado_actual == "pendiente" else 1,
        )
        notas = st.text_area(
            "Notas:", value=hotel_actual.get("notas", ""), height=80,
            placeholder="Horarios de check-in, traslados, breakfast incluido, etc."
        )

        guardar = st.form_submit_button(
            "💾 Guardar", type="primary", use_container_width=True
        )

    return {
        "nombre": nombre.strip(),
        "direccion": direccion.strip(),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "num_reserva": num_reserva.strip(),
        "telefono": telefono.strip(),
        "link": link.strip(),
        "costo": costo,
        "estado": estado,
        "notas": notas.strip(),
        "_submit": guardar,
    }


def mostrar():
    st.title("🏨 Hoteles del Viaje")
    st.caption("Tracking de reservas + búsqueda con Lady")

    hoteles = cargar_hoteles()

    # Resumen al tope
    reservados = sum(
        1 for h in hoteles.values() if h.get("estado") == "reservado"
    )
    total = len(CIUDADES_VIAJE)
    col1, col2 = st.columns(2)
    col1.metric("📅 Ciudades", total)
    col2.metric("✅ Reservados", f"{reservados}/{total}")
    st.progress(reservados / total if total else 0)

    st.divider()

    # Una sección por ciudad
    for ciudad in CIUDADES_VIAJE:
        emoji = CIUDAD_EMOJI.get(ciudad, "📍")
        ci_def, co_def, noches = RANGO_POR_CIUDAD[ciudad]
        hotel_actual = hoteles.get(ciudad, {})
        es_familiar = ciudad in CIUDADES_FAMILIARES

        estado_emoji = "✅" if hotel_actual.get("estado") == "reservado" else "⏳"
        nombre_label = hotel_actual.get("nombre") or "Sin reservar"

        with st.expander(
            f"{emoji} {ciudad}  ·  {ci_def:%d %b} → {co_def:%d %b} "
            f"({noches}n)  ·  {estado_emoji} {nombre_label}",
            expanded=False,
        ):
            if es_familiar:
                st.info(
                    "🏠 **Casa familiar** — sin reserva ni costo. "
                    "Solo confirma la dirección y teléfono de contacto."
                )

            form_result = _form_hotel(ciudad, hotel_actual, ci_def, co_def, es_familiar)

            if form_result["_submit"]:
                payload = {k: v for k, v in form_result.items() if not k.startswith("_")}
                try:
                    guardar_hotel(ciudad, payload)
                    st.success(f"✅ Hotel de {ciudad} guardado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

            # Acciones rápidas (fuera del form)
            if hotel_actual.get("nombre"):
                c1, c2 = st.columns(2)
                with c1:
                    q = f"{hotel_actual['nombre']} {ciudad}".replace(" ", "+")
                    st.link_button(
                        "📍 Ver en Maps",
                        f"https://www.google.com/maps/search/?api=1&query={q}",
                        use_container_width=True,
                    )
                with c2:
                    if hotel_actual.get("link"):
                        st.link_button(
                            "🔗 Ver reserva",
                            hotel_actual["link"],
                            use_container_width=True,
                        )

            # Lady búsqueda (no aplica para ciudades con casa familiar)
            if not es_familiar:
                st.markdown("---")
                ci_para_lady = (
                    date.fromisoformat(hotel_actual["check_in"])
                    if hotel_actual.get("check_in") else ci_def
                )
                co_para_lady = (
                    date.fromisoformat(hotel_actual["check_out"])
                    if hotel_actual.get("check_out") else co_def
                )
                cache_key = (
                    f"lady_hoteles_{ciudad}_"
                    f"{ci_para_lady.isoformat()}_{co_para_lady.isoformat()}"
                )

                if cache_key in st.session_state:
                    st.markdown("### 🐾 Sugerencias de Lady")
                    st.markdown(st.session_state[cache_key])
                    if st.button(
                        "🔄 Volver a buscar",
                        key=f"rebuscar_{ciudad}",
                    ):
                        del st.session_state[cache_key]
                        st.rerun()
                else:
                    if st.button(
                        f"🐾 Lady, búscame hoteles en {ciudad}",
                        key=f"buscar_{ciudad}",
                        use_container_width=True,
                    ):
                        with st.spinner(
                            f"🐾 Lady está olfateando hoteles en {ciudad}..."
                        ):
                            st.session_state[cache_key] = buscar_con_lady(
                                ciudad, ci_para_lady, co_para_lady
                            )
                        st.rerun()

    # Resumen al final: costo total (solo si ve precios)
    st.divider()
    total_eur = sum(float(h.get("costo", 0.0) or 0) for h in hoteles.values())
    st.metric(
        "💰 Costo total estimado",
        mostrar_precio(f"€{total_eur:,.2f}"),
    )
