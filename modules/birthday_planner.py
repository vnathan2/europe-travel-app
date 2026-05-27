# modules/birthday_planner.py
# Módulo 4: Birthday Planner
# Planificador especial para los cumpleaños del 17 y 21 de julio

import os
from datetime import date

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

from utils.gcp_client import get_secret
from utils.price_helper import mostrar_precio

load_dotenv()

# ── Datos hardcodeados de los cumpleaños ───────────────────────────────────
CUMPLEANOS = {
    "hija": {
        "nombre": "Camila",
        "fecha": "17 de julio 2026 (Viernes)",
        "edad": 15,
        "ciudad": "Madrid",
        "emoji": "🎀",
        "plan_confirmado": {
            "actividad_principal": "Parque Warner Madrid",
            "detalle": "Día completo en el parque (09:30–18:00), €32.90 pp",
            "traslado": "Taxi desde hotel ~€40, 40 min",
            "cena": "Cena especial en StreetXO (Serrano 52) — €45 pp, rating 4.6/5",
        },
        "perfil": "Adolescente de 15 años, le gustan los parques de diversiones, la música, la moda y las experiencias únicas. Está de viaje por primera vez en Europa.",
        "alternativas_actividades": [
            "Real Madrid Tour + Bernabéu Experience",
            "Escape Room temático en Madrid",
            "Taller de flamenco para adolescentes",
            "Visita al Museo del Videojuego (Museo del Juego)",
            "Compras en Fuencarral + barrio Malasaña",
        ],
        "alternativas_restaurantes": [
            {"nombre": "StreetXO",          "tipo": "Fusión asiática-española", "precio": "€45 pp", "direccion": "Serrano 52"},
            {"nombre": "Hard Rock Cafe",    "tipo": "Americana",                "precio": "€25 pp", "direccion": "Paseo de la Castellana 2"},
            {"nombre": "TGI Fridays",       "tipo": "Americana",                "precio": "€20 pp", "direccion": "Gran Vía 1"},
            {"nombre": "Lateral Gran Vía",  "tipo": "Tapas modernas",           "precio": "€22 pp", "direccion": "Gran Vía 18"},
            {"nombre": "Five Guys Gran Vía","tipo": "Hamburguesería",           "precio": "€15 pp", "direccion": "Gran Vía 30"},
        ],
        "ideas_regalo": [
            "🛍️ Shopping en Zara, Pull&Bear o Bershka en Gran Vía",
            "💄 Kit de maquillaje europeo (MAC, Sephora Madrid)",
            "👟 Zapatillas en una marca española o europea",
            "📸 Cámara instantánea Instax para el viaje",
            "🎧 Auriculares inalámbricos",
            "💍 Joyería española artesanal",
            "🎮 Merchandising oficial del Real Madrid",
        ],
        "presupuesto": [
            ("Parque Warner (x3)",  "€98.70"),
            ("Taxi ida + vuelta",   "€80.00"),
            ("Cena StreetXO (x3)", "€135.00"),
            ("Regalo sorpresa",    "€50–100"),
        ],
        "total": "~€363–413",
    },
    "mama": {
        "nombre": "Giovanna",
        "fecha": "21 de julio 2026 (Martes)",
        "edad": 46,
        "ciudad": "París",
        "emoji": "🌹",
        "plan_confirmado": {
            "actividad_principal": "Llegada a París en TGV desde Bayona",
            "detalle": "Tren sale ~08:00 de Bayona, llega ~13:00 a Gare Montparnasse",
            "tarde": "Torre Eiffel (€28pp) → Arco del Triunfo (€13pp) → Crucero Sena (€20pp)",
            "cena": "Cena especial en Le Train Bleu (Gare de Lyon) — €60 pp, rating 4.7/5",
        },
        "perfil": "Mujer de 46 años que cumple años llegando a París por primera vez. Le gustan la gastronomía, la cultura, los lugares románticos y las experiencias únicas. Es un momento muy especial.",
        "alternativas_actividades": [
            "Tarde de spa en París (tratamiento facial + masaje)",
            "Tour privado por Montmartre al atardecer",
            "Clase de cocina francesa (croissants, macarons)",
            "Visita al Palais Royal + jardines",
            "Paseo en barco privado por el Sena al atardecer",
        ],
        "alternativas_restaurantes": [
            {"nombre": "Le Train Bleu",          "tipo": "Francesa clásica",       "precio": "€60 pp", "direccion": "Gare de Lyon"},
            {"nombre": "Septime",                "tipo": "Francesa moderna",       "precio": "€65 pp", "direccion": "Rue de Charonne 80"},
            {"nombre": "Le Comptoir du Relais",  "tipo": "Bistró francés",         "precio": "€40 pp", "direccion": "Carrefour de l'Odéon"},
            {"nombre": "Angelina Paris",         "tipo": "Té y pasteles",          "precio": "€30 pp", "direccion": "Rue de Rivoli 226"},
            {"nombre": "Frenchie",               "tipo": "Francesa contemporánea", "precio": "€55 pp", "direccion": "Rue du Nil 5"},
        ],
        "ideas_regalo": [
            "🥐 Desayuno especial en Angelina Paris (el mejor chocolate caliente del mundo)",
            "🌹 Ramo de flores frescas del mercado parisino",
            "🧴 Perfume francés original (Chanel, Dior, Lancôme en tiendas oficiales)",
            "👜 Bolso o accesorio de marca francesa",
            "💄 Maquillaje en Sephora Champs-Élysées",
            "🍾 Champagne en la Torre Eiffel",
            "🎨 Retrato artístico en Montmartre",
            "🧁 Macarons de Ladurée personalizados",
        ],
        "presupuesto": [
            ("Tren Bayona→París (x3)", "€180–210"),
            ("Torre Eiffel (x3)",      "€84.00"),
            ("Arco del Triunfo (x3)", "€39.00"),
            ("Crucero Sena (x3)",     "€60.00"),
            ("Cena Le Train Bleu (x3)","€180.00"),
            ("Regalo sorpresa",        "€80–150"),
        ],
        "total": "~€623–723",
    }
}

# ── Inicializar Gemini ─────────────────────────────────────────────────────
@st.cache_resource
def init_gemini_birthday():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = get_secret("GEMINI_API_KEY")
        except Exception:
            return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name="gemini-2.5-flash")

# ── Generar itinerario especial con Gemini ─────────────────────────────────
def generar_itinerario_gemini(model, cumple: dict) -> str:
    prompt = f"""
    Genera un itinerario especial de cumpleaños con este contexto:

    - Festejada: {cumple['nombre']}, cumple {cumple['edad']} años
    - Fecha: {cumple['fecha']}
    - Ciudad: {cumple['ciudad']}
    - Perfil: {cumple['perfil']}
    - Plan ya confirmado: {cumple['plan_confirmado']}

    Por favor genera:
    1. Un mensaje de cumpleaños especial y emotivo (2-3 líneas)
    2. Sugerencias para hacer el día aún más especial considerando el plan confirmado
    3. 3 ideas de sorpresas pequeñas que la familia puede preparar
    4. Un consejo especial para que el día sea inolvidable

    Responde en español, de forma cálida y personal.
    Sé específico con {cumple['ciudad']} como escenario.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"No se pudo generar el itinerario: {e}"

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("🎂 Birthday Planner")
    st.caption("Planificador especial para los dos cumpleaños del viaje")

    # Selector de cumpleaños
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎀 Cumpleaños Camila\n17 julio — Madrid",
                     use_container_width=True, type="primary"):
            st.session_state.cumple_activo = "hija"
    with col2:
        if st.button("🌹 Cumpleaños Giovanna\n21 julio — París",
                     use_container_width=True, type="primary"):
            st.session_state.cumple_activo = "mama"

    if "cumple_activo" not in st.session_state:
        st.session_state.cumple_activo = "hija"

    cumple = CUMPLEANOS[st.session_state.cumple_activo]

    st.divider()

    # Header del cumpleaños activo
    st.subheader(f"{cumple['emoji']} {cumple['nombre']} — {cumple['edad']} años")
    st.caption(f"📅 {cumple['fecha']}  |  📍 {cumple['ciudad']}")

    # Countdown
    hoy = date.today()
    fecha_cumple = date(2026, 7, 17) if st.session_state.cumple_activo == "hija" else date(2026, 7, 21)
    dias_faltan = (fecha_cumple - hoy).days

    if dias_faltan > 0:
        st.info(f"🗓️ Faltan **{dias_faltan} días** para este cumpleaños especial")
    else:
        st.success("🎉 ¡Hoy es el gran día!")

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_plan, tab_restaurantes, tab_regalos, tab_gemini = st.tabs([
        "📋 Plan del Día", "🍽️ Restaurantes", "🎁 Ideas de Regalo", "✨ Sugerencias IA"
    ])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: Plan del día — sin precios (solo info del plan)
    # ══════════════════════════════════════════════════════════════════════
    with tab_plan:
        st.subheader("✅ Plan Confirmado")
        plan = cumple["plan_confirmado"]
        for key, value in plan.items():
            label = key.replace("_", " ").title()
            with st.container(border=True):
                st.write(f"**{label}:** {value}")

        st.divider()
        st.subheader("🎯 Actividades Alternativas")
        st.caption("Opciones adicionales para complementar el día")
        for alt in cumple["alternativas_actividades"]:
            st.write(f"• {alt}")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2: Restaurantes — precio visible solo para ADMIN
    # ══════════════════════════════════════════════════════════════════════
    with tab_restaurantes:
        st.subheader(f"🍽️ Mejores opciones en {cumple['ciudad']}")

        for rest in cumple["alternativas_restaurantes"]:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{rest['nombre']}**")
                    st.caption(f"📍 {rest['direccion']}")
                with col2:
                    st.write(f"🍴 {rest['tipo']}")
                with col3:
                    # ── PRECIO: visible solo para ADMIN ───────────────
                    st.metric("Precio", mostrar_precio(rest["precio"]))

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3: Regalos — presupuesto visible solo para ADMIN
    # ══════════════════════════════════════════════════════════════════════
    with tab_regalos:
        st.subheader(f"🎁 Ideas de Regalo para {cumple['nombre']}")
        st.caption(f"Qué puedes comprar en {cumple['ciudad']}")
        for idea in cumple["ideas_regalo"]:
            st.write(idea)

        st.divider()
        st.subheader("💰 Presupuesto para el día especial")

        # ── PRESUPUESTO: visible solo para ADMIN ──────────────────────
        if st.session_state.get("_show_prices", False):
            for item, precio in cumple["presupuesto"]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {item}")
                with col2:
                    st.write(f"**{precio}**")
            st.success(f"💶 Total estimado del día: **{cumple['total']}**")
        else:
            # Familiar: solo ve los items sin precio
            for item, _ in cumple["presupuesto"]:
                st.write(f"• {item}")
            st.info("💡 Los precios son visibles solo para el administrador.")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4: Sugerencias IA — sin precios, accesible para todos
    # ══════════════════════════════════════════════════════════════════════
    with tab_gemini:
        st.subheader("✨ Ideas personalizadas con Inteligencia Artificial")
        st.caption("Gemini genera sugerencias únicas basadas en el perfil de la festejada")

        if st.button("🪄 Generar sugerencias especiales", type="primary",
                     use_container_width=True):
            model = init_gemini_birthday()
            if model:
                with st.spinner(f"Preparando algo especial para {cumple['nombre']}..."):
                    sugerencias = generar_itinerario_gemini(model, cumple)
                st.markdown(sugerencias)
            else:
                st.error("No se pudo conectar con Gemini. Verifica la API key.")
