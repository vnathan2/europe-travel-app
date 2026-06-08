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
            "cena": "Cena especial en StreetXO (Serrano 47) — €45 pp, rating 4.6/5",
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
            {"nombre": "StreetXO", "tipo": "Fusión asiática", "precio": "€45 pp",
             "direccion": "El Corte Inglés, Serrano 47 (3ª planta)",
             "distincion": "Sol Repsol",
             "destacado": "Street food de alta cocina de Dabiz Muñoz, chef de DiverXO (3★ Michelin). Fusión asiática salvaje y divertida.",
             "nota": "Reserva imprescindible. Cocina de 20:00 a 23:00. Ambiente vibrante, perfecto para una noche especial."},
            {"nombre": "Hard Rock Cafe", "tipo": "Americana", "precio": "€25 pp",
             "direccion": "Paseo de la Castellana 2",
             "destacado": "Hamburguesas, costillas y ambiente rock con memorabilia.",
             "nota": "Familiar y animado. Suele haber cola; se puede reservar online."},
            {"nombre": "TGI Fridays", "tipo": "Americana", "precio": "€20 pp",
             "direccion": "Gran Vía 1",
             "destacado": "Comida americana informal: alitas, hamburguesas, postres generosos.",
             "nota": "Casual y rápido, en pleno centro."},
            {"nombre": "Lateral Gran Vía", "tipo": "Tapas modernas", "precio": "€22 pp",
             "direccion": "Gran Vía 18",
             "destacado": "Tapas españolas modernas y raciones para compartir.",
             "nota": "Ambiente relajado, buena opción para picar sin reserva."},
            {"nombre": "Five Guys Gran Vía", "tipo": "Hamburguesería", "precio": "€15 pp",
             "direccion": "Gran Vía 30",
             "destacado": "Hamburguesas y papas al estilo americano, hechas al momento.",
             "nota": "Comida rápida de calidad. Sin reserva."},
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
            {"nombre": "Le Train Bleu", "tipo": "Francesa clásica", "precio": "€60 pp",
             "direccion": "Gare de Lyon, Hall 1 (1er piso)",
             "distincion": "Monumento histórico",
             "destacado": "Joya Belle Époque de 1901 dentro de Gare de Lyon. Cocina tradicional con Michel Rostang: gigot de cordero trinchado en sala y baba al ron.",
             "nota": "Reserva esencial. Decoración espectacular y servicio con flambeados. Ideal para un cumpleaños memorable."},
            {"nombre": "Septime", "tipo": "Francesa moderna", "precio": "€65 pp",
             "direccion": "80 Rue de Charonne (11e)",
             "distincion": "★ 1 estrella Michelin",
             "destacado": "Neobistró de Bertrand Grébaut, cocina de temporada vegetal. Una de las mesas más codiciadas de París.",
             "nota": "Reserva durísima: abren online a las 10:00, 3 semanas antes. El 21/07 es martes y sí abre."},
            {"nombre": "Le Comptoir du Relais", "tipo": "Bistró francés", "precio": "€40 pp",
             "direccion": "Carrefour de l'Odéon (6e)",
             "destacado": "Bistró icónico de Yves Camdeborde, cuna de la bistronomía parisina.",
             "nota": "Almuerzo tipo brasserie sin reserva; cena con menú y reserva anticipada."},
            {"nombre": "Angelina Paris", "tipo": "Té y pasteles", "precio": "€30 pp",
             "direccion": "226 Rue de Rivoli (1er)",
             "destacado": "Salón de té histórico (1903). Famoso por su chocolate caliente l'Africain y el pastel Mont-Blanc.",
             "nota": "Perfecto para un desayuno o merienda de cumpleaños. Suele haber cola; mejor temprano."},
            {"nombre": "Frenchie", "tipo": "Francesa contemporánea", "precio": "€55 pp",
             "direccion": "5 Rue du Nil (2e)",
             "destacado": "Neobistró de Grégory Marchand, cocina francesa contemporánea de producto.",
             "nota": "Muy demandado; reserva con antelación. En una calle peatonal gastronómica."},
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
    hoy = date.today()
    fecha_cumple = date(2026, 7, 17) if st.session_state.cumple_activo == "hija" else date(2026, 7, 21)
    dias_faltan = (fecha_cumple - hoy).days
    if dias_faltan > 0:
        cuenta = f"🗓️ Faltan {dias_faltan} días para el gran día"
    elif dias_faltan == 0:
        cuenta = "🎉 ¡Hoy es el gran día!"
    else:
        cuenta = "💖 Cumpleaños celebrado"
    st.markdown(
        '<div class="et-citybar">'
        f'<h2>{cumple["emoji"]} {cumple["nombre"]} · {cumple["edad"]} años</h2>'
        f'<div class="meta">📅 {cumple["fecha"]}  ·  📍 {cumple["ciudad"]}</div>'
        f'<div class="meta">{cuenta}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_plan, tab_restaurantes, tab_regalos, tab_gemini = st.tabs([
        "📋 Plan del Día", "🍽️ Restaurantes", "🎁 Ideas de Regalo", "✨ Sugerencias IA"
    ])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: Plan del día — sin precios (solo info del plan)
    # ══════════════════════════════════════════════════════════════════════
    with tab_plan:
        st.subheader("✅ Plan Confirmado")
        _ICONOS_PLAN = [
            (("actividad", "principal"), "🎯", "et-b-see"),
            (("traslado", "transporte", "tren"), "🚆", "et-b-trans"),
            (("cena", "comida", "almuerzo", "restaurante"), "🍽️", "et-b-food"),
            (("tarde", "noche", "mañana", "manana"), "🌆", "et-b-see"),
            (("detalle",), "📝", "et-b-see"),
        ]

        def _icono_plan(k: str):
            kl = k.lower()
            for claves, emoji, clase in _ICONOS_PLAN:
                if any(c in kl for c in claves):
                    return emoji, clase
            return "📌", "et-b-see"

        _cards = []
        for key, value in cumple["plan_confirmado"].items():
            label = key.replace("_", " ").title()
            emoji, clase = _icono_plan(key)
            _cards.append(
                '<div class="et-ec"><div class="row">'
                f'<span class="et-badge {clase}">{emoji}</span>'
                '<div style="flex:1">'
                f'<div class="title">{label}</div>'
                f'<div style="font:500 13px Barlow; color:var(--et-ink); margin-top:2px">{value}</div>'
                '</div></div></div>'
            )
        st.markdown(
            '<div style="display:flex; flex-direction:column; gap:9px">'
            + "".join(_cards) + "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.subheader("🎯 Actividades Alternativas")
        st.caption("Opciones adicionales para complementar el día")
        _alts = []
        for alt in cumple["alternativas_actividades"]:
            _alts.append(
                '<div class="et-ec" style="padding:9px 13px"><div class="row">'
                '<span class="et-badge et-b-see" style="width:24px; height:24px; font-size:12px">✦</span>'
                f'<div class="title" style="font-size:13.5px">{alt}</div>'
                '</div></div>'
            )
        st.markdown(
            '<div style="display:flex; flex-direction:column; gap:7px">'
            + "".join(_alts) + "</div>",
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════════════════════════════════════
    # TAB 2: Restaurantes — precio visible solo para ADMIN
    # ═══════════════════════════════════════════════════════════════
    with tab_restaurantes:
        st.subheader(f"🍽️ Mejores opciones en {cumple['ciudad']}")
        st.caption("⭐ La primera opción es la cena confirmada del día")

        _rcards = []
        for idx, rest in enumerate(cumple["alternativas_restaurantes"]):
            precio_txt = (mostrar_precio(rest["precio"]) or "").strip()
            chips = ""
            if idx == 0:
                chips += '<span class="et-t et-t-free">⭐ Cena confirmada</span>'
            if rest.get("distincion"):
                chips += f'<span class="et-t et-t-rate">{rest["distincion"]}</span>'
            chips += f'<span class="et-t et-t-info">🍴 {rest["tipo"]}</span>'
            if precio_txt:
                chips += f'<span class="et-t" style="background:rgba(219,94,57,.13); color:var(--et-terra-d)">💶 {precio_txt}</span>'
            dest = f'<div style="font:500 12.5px Barlow; color:var(--et-ink); margin-top:5px">{rest["destacado"]}</div>' if rest.get("destacado") else ""
            nota = f'<div style="font:500 12px Barlow; color:var(--et-muted); margin-top:5px">🔖 {rest["nota"]}</div>' if rest.get("nota") else ""
            _rcards.append(
                '<div class="et-ec"><div class="row">'
                '<span class="et-badge et-b-food">🍽️</span>'
                '<div style="flex:1">'
                f'<div class="title">{rest["nombre"]}</div>'
                f'<div class="addr">📍 {rest["direccion"]}</div>'
                f'{dest}'
                f'{nota}'
                f'<div class="et-tags">{chips}</div>'
                '</div></div></div>'
            )
        st.markdown(
            '<div style="display:flex; flex-direction:column; gap:9px">'
            + "".join(_rcards) + "</div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3: Regalos — presupuesto visible solo para ADMIN
    # ══════════════════════════════════════════════════════════════════════
    with tab_regalos:
        st.subheader(f"🎁 Ideas de Regalo para {cumple['nombre']}")
        st.caption(f"Qué puedes comprar en {cumple['ciudad']}")
        def _cat_regalo(txt: str):
            t = txt.lower()
            if any(w in t for w in ["maquillaje", "sephora", "mac", "perfume", "chanel", "dior", "lancôme", "lancome"]):
                return "Belleza", "et-t-rate"
            if any(w in t for w in ["joyería", "joyeria", "anillo", "bolso", "accesorio"]):
                return "Joyería", "et-t-rate"
            if any(w in t for w in ["zara", "pull", "bershka", "zapatill", "ropa", "moda", "merchandising"]):
                return "Moda", "et-t-info"
            if any(w in t for w in ["auricular", "cámara", "camara", "instax"]):
                return "Tech", "et-t-info"
            if any(w in t for w in ["champagne", "champán", "macaron", "chocolate", "desayuno", "ladurée", "laduree"]):
                return "Gastronomía", "et-t-free"
            if any(w in t for w in ["retrato", "flores", "ramo", "artístico", "artistico", "spa", "tour"]):
                return "Experiencia", "et-t-free"
            return "Idea", "et-t-info"

        _gcards = []
        for idea in cumple["ideas_regalo"]:
            partes = idea.split(" ", 1)
            emoji = partes[0]
            texto = partes[1] if len(partes) > 1 else idea
            cat, clase = _cat_regalo(texto)
            _gcards.append(
                '<div class="et-ec" style="padding:10px 13px"><div class="row">'
                f'<span class="et-badge et-b-see">{emoji}</span>'
                '<div style="flex:1">'
                f'<div class="title" style="font-size:13.5px">{texto}</div>'
                f'<div class="et-tags"><span class="et-t {clase}">{cat}</span></div>'
                '</div></div></div>'
            )
        st.markdown(
            '<div style="display:flex; flex-direction:column; gap:8px">'
            + "".join(_gcards) + "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="et-callout" style="margin-top:12px">'
            '<div style="font-size:20px">🧾</div>'
            '<div>'
            '<div style="font:700 14px Barlow; color:var(--et-ink)">Tax Free: recuperen el IVA de los regalos</div>'
            '<div style="font:500 12.5px Barlow; color:var(--et-muted); margin-top:3px">'
            'Como residentes fuera de la UE pueden pedir la devolución del IVA en compras de productos, no en comidas ni servicios. '
            'Mínimo por país: España sin mínimo, Francia €100 por tienda, Bélgica €125, Países Bajos €50. '
            'Pidan el formulario Tax Free con el pasaporte al comprar y valídenlo al salir de la UE, en su caso en Barajas antes de volar a Lima. Reembolso neto aproximado 12-15%.'
            '</div></div></div>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.subheader("💰 Presupuesto del día especial")
        _mostrar = st.session_state.get("_show_prices", False)
        _filas = []
        for item, precio in cumple["presupuesto"]:
            monto = f'<span class="et-t et-t-rate">{precio}</span>' if _mostrar else ""
            _filas.append(
                '<div class="et-ec" style="padding:10px 14px"><div class="row" style="justify-content:space-between; gap:12px">'
                f'<div class="title" style="font-size:13.5px">{item}</div>'
                f'{monto}'
                '</div></div>'
            )
        st.markdown(
            '<div style="display:flex; flex-direction:column; gap:7px">'
            + "".join(_filas) + "</div>",
            unsafe_allow_html=True,
        )
        if _mostrar:
            st.markdown(
                '<div class="et-callout" style="border-left-color:var(--et-teal); margin-top:12px">'
                '<div style="font-size:20px">💶</div>'
                f'<div><div style="font:700 16px Barlow; color:var(--et-ink)">Total estimado: {cumple["total"]}</div>'
                '<div style="font:500 12px Barlow; color:var(--et-muted); margin-top:2px">Para 3 personas. Estimado referencial, sin incluir el regalo final salvo lo indicado.</div></div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("💡 Los montos son visibles solo para el administrador.")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4: Sugerencias IA — sin precios, accesible para todos
    # ══════════════════════════════════════════════════════════════════════
    with tab_gemini:
        st.subheader("✨ Ideas personalizadas con Inteligencia Artificial")
        st.caption("Gemini genera sugerencias únicas basadas en el perfil de la festejada")

        st.markdown(
            '<div class="et-callout" style="margin-bottom:10px">'
            '<div style="font-size:20px">🎂</div>'
            f'<div><div style="font:700 14px Barlow; color:var(--et-ink)">Perfil de {cumple["nombre"]}</div>'
            f'<div style="font:500 12.5px Barlow; color:var(--et-muted); margin-top:3px">{cumple["perfil"]}</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.button("🪄 Generar sugerencias especiales", type="primary",
                     use_container_width=True):
            model = init_gemini_birthday()
            if model:
                with st.spinner(f"Preparando algo especial para {cumple['nombre']}..."):
                    sugerencias = generar_itinerario_gemini(model, cumple)
                st.markdown(sugerencias)
            else:
                st.error("No se pudo conectar con Gemini. Verifica la API key.")