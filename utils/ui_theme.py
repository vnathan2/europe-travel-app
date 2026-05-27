# utils/ui_theme.py
# Sistema de temas por ciudad, animaciones, menú sofisticado y modo offline

import time

import streamlit as st

CITY_THEMES = {
    "madrid": {
        "nombre":    "Madrid",
        "emoji":     "🇪🇸",
        "fechas":    "15–18 Jul",
        "primary":   "#C8102E",
        "secondary": "#FF6B35",
        "accent":    "#FFD700",
        "bg_dark":   "#1a0508",
        "bg_card":   "#2d0a10",
        "gradient":  "linear-gradient(135deg, #C8102E 0%, #8B0000 100%)",
        "sidebar_bg":"linear-gradient(180deg, #1a0508 0%, #2d0a10 100%)",
    },
    "bayona": {
        "nombre":    "Bayona",
        "emoji":     "🇫🇷",
        "fechas":    "19–20 Jul",
        "primary":   "#4A90D9",
        "secondary": "#2E6DA4",
        "accent":    "#E8C547",
        "bg_dark":   "#050d1a",
        "bg_card":   "#0a1a2d",
        "gradient":  "linear-gradient(135deg, #4A90D9 0%, #1a3a5c 100%)",
        "sidebar_bg":"linear-gradient(180deg, #050d1a 0%, #0a1a2d 100%)",
    },
    "paris": {
        "nombre":    "París",
        "emoji":     "🇫🇷",
        "fechas":    "21–24 Jul",
        "primary":   "#5B9BD5",
        "secondary": "#C9A227",
        "accent":    "#E8C547",
        "bg_dark":   "#05080f",
        "bg_card":   "#0d1520",
        "gradient":  "linear-gradient(135deg, #5B9BD5 0%, #C9A227 100%)",
        "sidebar_bg":"linear-gradient(180deg, #05080f 0%, #0d1520 100%)",
    },
    "bruselas": {
        "nombre":    "Bruselas",
        "emoji":     "🇧🇪",
        "fechas":    "25–26 Jul",
        "primary":   "#F5A623",
        "secondary": "#E8340A",
        "accent":    "#000000",
        "bg_dark":   "#1a0f00",
        "bg_card":   "#2d1a00",
        "gradient":  "linear-gradient(135deg, #F5A623 0%, #E8340A 100%)",
        "sidebar_bg":"linear-gradient(180deg, #1a0f00 0%, #2d1a00 100%)",
    },
    "amsterdam": {
        "nombre":    "Ámsterdam",
        "emoji":     "🇳🇱",
        "fechas":    "27–30 Jul",
        "primary":   "#E8453C",
        "secondary": "#1F5C99",
        "accent":    "#FFFFFF",
        "bg_dark":   "#1a0505",
        "bg_card":   "#2d0a0a",
        "gradient":  "linear-gradient(135deg, #E8453C 0%, #1F5C99 100%)",
        "sidebar_bg":"linear-gradient(180deg, #1a0505 0%, #2d0a0a 100%)",
    },
    "default": {
        "nombre":    "Europa",
        "emoji":     "✈️",
        "fechas":    "Jul 2026",
        "primary":   "#1A73E8",
        "secondary": "#0D47A1",
        "accent":    "#FFD700",
        "bg_dark":   "#05080f",
        "bg_card":   "#0d1520",
        "gradient":  "linear-gradient(135deg, #1A73E8 0%, #0D47A1 100%)",
        "sidebar_bg":"linear-gradient(180deg, #05080f 0%, #0d1520 100%)",
    },
}

MODULO_CIUDAD = {
    "euro_budgeter":    "default",
    "travel_concierge": "default",
    "emergency_card":   "default",
    "birthday_planner": "paris",
    "packing_checker":  "default",
    "voice_translator": "default",
    "train_optimizer":  "default",
    "trip_journal":     "default",
    "phrase_pocket":    "default",
    "itinerary_tracker":"default",
    "shopping_guide":   "default",
    "night_life":       "amsterdam",
    "admin_panel":      "default",
}


def get_theme(modulo_id: str) -> dict:
    ciudad_key = MODULO_CIUDAD.get(modulo_id, "default")
    return CITY_THEMES.get(ciudad_key, CITY_THEMES["default"])


def apply_theme(theme: dict):
    """Inyecta CSS global con el tema de ciudad activo."""
    modo_oscuro = st.session_state.get("modo_oscuro", True)

    if modo_oscuro:
        bg_main    = "#0e1117"
        bg_sidebar = theme['sidebar_bg']
        text_main  = "#fafafa"
        text_muted = "#aaa"
        card_bg    = "#1c1f26"
        border_col = "#333"
    else:
        bg_main    = "#f4f4f0"
        bg_sidebar = "linear-gradient(180deg, #e8e8e2 0%, #ddddd6 100%)"
        text_main  = "#2c2c2c"
        text_muted = "#666"
        card_bg    = "#efefea"
        border_col = "#c8c8c0"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background-color: {bg_main} !important;
    }}
    .stApp > * {{
        color: {text_main} !important;
    }}
    .stTextInput input, .stTextArea textarea, .stSelectbox select {{
        background-color: {card_bg} !important;
        color: {text_main} !important;
        border-color: {border_col} !important;
    }}
    [data-testid="stExpander"] {{
        background-color: {card_bg} !important;
    }}
    [data-testid="stChatMessage"] {{
        background-color: {card_bg} !important;
        border: 1px solid {border_col} !important;
    }}
    .stCaption, small {{
        color: {text_muted} !important;
    }}
    [data-testid="stAlert"] {{
        border-left: 4px solid {theme['primary']} !important;
    }}

    [data-testid="stSidebar"] {{
        background: {bg_sidebar} !important;
        border-right: 1px solid {theme['primary']}33;
    }}
    [data-testid="stSidebar"] * {{
        color: {'#ffffff' if modo_oscuro else '#1a1a2e'} !important;
    }}

    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 4px;
        background: transparent;
        border-bottom: 2px solid {theme['primary']}33;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0 !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stTabs"] [aria-selected="true"] {{
        background: {theme['gradient']} !important;
        color: white !important;
    }}

    [data-testid="stButton"] > button[kind="primary"] {{
        background: {theme['gradient']} !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px {theme['primary']}44 !important;
    }}
    [data-testid="stButton"] > button[kind="primary"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px {theme['primary']}66 !important;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {theme['primary']}33 !important;
        border-radius: 12px !important;
        background: {card_bg} !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {theme['primary']}88 !important;
    }}

    [data-testid="stMetric"] {{
        background: {theme['primary']}11 !important;
        border: 1px solid {theme['primary']}33 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {theme['primary']} !important;
        font-weight: 700 !important;
    }}

    [data-testid="stProgressBar"] > div > div {{
        background: {theme['gradient']} !important;
    }}

    [data-testid="stExpander"] summary {{
        border-left: 3px solid {theme['primary']} !important;
        padding-left: 10px !important;
    }}

    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: {theme['primary']}66;
        border-radius: 3px;
    }}

    .main .block-container {{
        animation: fadeInUp 0.4s ease forwards;
    }}
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}

    .city-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        background: {theme['gradient']};
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: white;
        letter-spacing: 0.5px;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_menu_fab():
    """Stub — mantenido por compatibilidad con app.py."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
# ANIMACIONES DE CARGA
# ══════════════════════════════════════════════════════════════════════════════

LOADING_MESSAGES = {
    "travel_concierge": [
        "☕ Cleo está preparando su café parisino...",
        "🗺️ Consultando los mejores rincones de Europa...",
        "✈️ Revisando horarios de vuelo...",
        "🎭 Buscando experiencias únicas para la familia...",
    ],
    "train_optimizer": [
        "🚄 Calculando la ruta más rápida...",
        "🇪🇺 Consultando Renfe, SNCF y Eurostar...",
        "⏱️ Comparando tiempos y precios...",
        "🎫 Verificando disponibilidad de asientos...",
    ],
    "birthday_planner": [
        "🎂 Preparando algo muy especial...",
        "🌹 Buscando los mejores restaurantes de París...",
        "🎀 Diseñando el día perfecto para Camila...",
        "✨ Agregando un toque mágico...",
    ],
    "night_life": [
        "🌙 Preparando la guía nocturna...",
        "🎵 Consultando los mejores clubs...",
        "☕ Verificando horarios de coffee shops...",
        "🍸 Seleccionando los mejores bares...",
    ],
    "default": [
        "✈️ Cargando tu Europa...",
        "🌍 Preparando la información...",
        "🗺️ Un momento por favor...",
        "⚡ Casi listo...",
    ],
}

def get_loading_message(modulo_id: str) -> str:
    import random
    msgs = LOADING_MESSAGES.get(modulo_id, LOADING_MESSAGES["default"])
    return random.choice(msgs)


def show_loading_animation(modulo_id: str, duration: float = 0.8):
    theme = get_theme(modulo_id)
    msg   = get_loading_message(modulo_id)

    placeholder = st.empty()
    placeholder.markdown(f"""
    <div style="
        display:flex; flex-direction:column;
        align-items:center; justify-content:center;
        padding: 60px 20px; text-align:center;
    ">
        <div style="
            width: 60px; height: 60px;
            border: 3px solid {theme['primary']}33;
            border-top: 3px solid {theme['primary']};
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-bottom: 20px;
        "></div>
        <p style="
            color: {theme['primary']};
            font-size: 16px;
            font-weight: 500;
            margin: 0;
            animation: pulse 1.5s ease-in-out infinite;
        ">{msg}</p>
    </div>
    <style>
        @keyframes spin {{
            0%   {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0.5; }}
        }}
    </style>
    """, unsafe_allow_html=True)

    time.sleep(duration)
    placeholder.empty()


# ══════════════════════════════════════════════════════════════════════════════
# MODO OFFLINE
# ══════════════════════════════════════════════════════════════════════════════

OFFLINE_DATA = {
    "emergencias": {
        "título": "🚨 Números de Emergencia",
        "datos": {
            "🇪🇸 España":       {"Policía": "091", "Emergencias": "112", "Ambulancia": "061"},
            "🇫🇷 Francia":      {"Policía": "17",  "Emergencias": "112", "Ambulancia": "15"},
            "🇧🇪 Bélgica":      {"Policía": "101", "Emergencias": "112", "Ambulancia": "100"},
            "🇳🇱 Países Bajos": {"Policía": "0900","Emergencias": "112", "Ambulancia": "112"},
        }
    },
    "frases": {
        "título": "🗣️ Frases de Emergencia",
        "datos": {
            "¡Ayuda!":                  {"FR": "Au secours!", "NL": "Help!", "EN": "Help!"},
            "Llama a la policía":       {"FR": "Appelez la police", "NL": "Bel de politie", "EN": "Call the police"},
            "Necesito un médico":       {"FR": "J'ai besoin d'un médecin", "NL": "Ik heb een dokter nodig", "EN": "I need a doctor"},
            "Me perdí":                 {"FR": "Je suis perdu", "NL": "Ik ben verdwaald", "EN": "I'm lost"},
            "¿Dónde está el hospital?": {"FR": "L'hôpital?", "NL": "Het ziekenhuis?", "EN": "Hospital?"},
        }
    },
    "itinerario_rapido": {
        "título": "📅 Itinerario Rápido",
        "datos": {
            "15–18 Jul": "🇪🇸 Madrid — Prado, Palacio Real, Warner, Bernabéu",
            "19–20 Jul": "🇫🇷 Bayona — Catedral, Musée Basque, Chocolat",
            "21–24 Jul": "🇫🇷 París — Eiffel, Louvre, Versalles, Disneyland",
            "25–26 Jul": "🇧🇪 Bruselas — Grand Place, Atomium, Delirium",
            "27–30 Jul": "🇳🇱 Ámsterdam — Ana Frank, Van Gogh, Canales",
        }
    },
    "hoteles": {
        "título": "🏨 Hoteles y Direcciones",
        "datos": {
            "Madrid":    "Confirmar al reservar — cerca Gran Vía recomendado",
            "Bayona":    "Confirmar al reservar — centro histórico",
            "París":     "Confirmar al reservar — cerca Gare Montparnasse",
            "Bruselas":  "Confirmar al reservar — cerca Grand Place",
            "Ámsterdam": "🏠 Casa familiar — dirección guardada en contactos",
        }
    },
    "vuelos": {
        "título": "✈️ Vuelos",
        "datos": {
            "Ida":      "LIM → MAD | 14 Jul 10:20am → 15 Jul 05:10am",
            "Vuelta 1": "AMS → MAD | 30 Jul ~15:00",
            "Vuelta 2": "MAD → LIM | 30 Jul 23:45",
            "Terminal": "Barajas T4 para vuelo de regreso",
        }
    },
}


def show_offline_panel():
    with st.expander("📡 Datos Offline", expanded=False):
        st.caption("Disponible sin conexión a internet")

        tab_sos, tab_frases, tab_viaje, tab_vuelos = st.tabs([
            "🚨 SOS", "🗣️ Frases", "📅 Viaje", "✈️ Vuelos"
        ])

        with tab_sos:
            data = OFFLINE_DATA["emergencias"]["datos"]
            for pais, nums in data.items():
                st.caption(pais)
                for servicio, numero in nums.items():
                    col1, col2 = st.columns([2, 1])
                    col1.caption(servicio)
                    color = "🔴" if servicio == "Emergencias" else "🔵"
                    col2.markdown(f"**{color} {numero}**")
                st.divider()

        with tab_frases:
            data = OFFLINE_DATA["frases"]["datos"]
            for frase, traducciones in data.items():
                st.markdown(f"**{frase}**")
                for idioma, texto in traducciones.items():
                    col1, col2 = st.columns([1, 3])
                    col1.caption(f"`{idioma}`")
                    col2.caption(texto)
                st.divider()

        with tab_viaje:
            data = OFFLINE_DATA["itinerario_rapido"]["datos"]
            for fechas, desc in data.items():
                st.caption(f"**{fechas}**")
                st.caption(desc)
                st.divider()

        with tab_vuelos:
            data = OFFLINE_DATA["vuelos"]["datos"]
            for key, val in data.items():
                st.caption(f"**{key}**")
                st.caption(val)
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# MENÚ SOFISTICADO
# ══════════════════════════════════════════════════════════════════════════════

MENU_SECTIONS = [
    {
        "seccion": "💰 Finanzas",
        "items": [
            {"key": "💰 Euro-Budgeter",      "id": "euro_budgeter",    "desc": "Presupuesto y gastos"},
            {"key": "💱 Conversor de Moneda", "id": "phrase_pocket",    "desc": "EUR ↔ PEN en tiempo real"},
        ]
    },
    {
        "seccion": "🗺️ Planificación",
        "items": [
            #{"key": "🤖 Travel Concierge",    "id": "travel_concierge", "desc": "Cleo + itinerario + alertas"},
            {"key": "📋 Itinerario",          "id": "itinerary_tracker","desc": "Checks del día"},
            {"key": "🚄 Trenes",              "id": "train_optimizer",  "desc": "Rutas y horarios"},
        ]
    },
    {
        "seccion": "🎉 Especiales",
        "items": [
            {"key": "🎂 Cumpleaños",          "id": "birthday_planner", "desc": "Camila & Giovanna"},
            {"key": "🛒 Shopping Guide",       "id": "shopping_guide",   "desc": "Tiendas · Ofertas · Souvenirs"},
            {"key": "🧳 Equipaje",            "id": "packing_checker",  "desc": "Lista de packing"},
            {"key": "📔 Diario",              "id": "trip_journal",     "desc": "Fotos y memorias"},
        ]
    },
    {
        "seccion": "🛟 Utilidades",
        "items": [
            {"key": "🗣️ Traductor",           "id": "voice_translator", "desc": "Voz + texto"},
            {"key": "🚨 Emergencias",         "id": "emergency_card",   "desc": "SOS y contactos"},
        ]
    },
]

MENU_ADMIN = {
    "seccion": "🔐 Admin",
    "items": [
        {"key": "🌙 Night Life",  "id": "night_life",  "desc": "Exclusivo Jonathan"},
        {"key": "⚙️ Admin Panel", "id": "admin_panel", "desc": "Ingesta · Stats · Limpieza KB"},
    ]
}


def render_sidebar_menu(is_admin_user: bool, user: dict) -> str:
    """Renderiza el menú en el sidebar. Retorna el módulo_id seleccionado."""
    theme = CITY_THEMES["default"]

    # ── Perfil ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="
        background: {theme['primary']}11;
        border: 1px solid {theme['primary']}33;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 4px;
    ">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:28px;">{'👑' if is_admin_user else '👤'}</div>
            <div>
                <div style="font-weight:700; font-size:14px; color:white;">
                    {user['name']}
                </div>
                <div style="font-size:11px; color:#aaa;">
                    {'Administrador' if is_admin_user else 'Familia'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Ciudad actual ──────────────────────────────────────────────────────
    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ciudad_hoy = "En camino a Europa 🌍"
    CIUDAD_POR_FECHA = {
        "2026-07-15": "🇪🇸 Madrid",    "2026-07-16": "🇪🇸 Madrid",
        "2026-07-17": "🇪🇸 Madrid",    "2026-07-18": "🇪🇸 Madrid",
        "2026-07-19": "🇫🇷 Bayona",    "2026-07-20": "🇫🇷 Bayona",
        "2026-07-21": "🇫🇷 París",     "2026-07-22": "🇫🇷 París",
        "2026-07-23": "🇫🇷 París",     "2026-07-24": "🇫🇷 París",
        "2026-07-25": "🇧🇪 Bruselas",  "2026-07-26": "🇧🇪 Bruselas",
        "2026-07-27": "🇳🇱 Ámsterdam", "2026-07-28": "🇳🇱 Ámsterdam",
        "2026-07-29": "🇳🇱 Ámsterdam", "2026-07-30": "🇳🇱 Ámsterdam",
    }
    if fecha_hoy in CIUDAD_POR_FECHA:
        ciudad_hoy = CIUDAD_POR_FECHA[fecha_hoy]

    st.markdown(f"""
    <div style="text-align:center; font-size:12px; color:#aaa; padding:6px 0 10px 0;">
        📍 Hoy: <strong style="color:white">{ciudad_hoy}</strong>
        &nbsp;·&nbsp; ✈️ <strong style="color:white">Jul 2026</strong>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Menú por secciones ─────────────────────────────────────────────────
    # ── Menú por secciones ─────────────────────────────────────────────────
    if "modulo_activo" not in st.session_state:
        st.session_state.modulo_activo = "travel_concierge"

    secciones = MENU_SECTIONS.copy()
    if is_admin_user:
        secciones.append(MENU_ADMIN)

    for seccion in secciones:
        st.markdown(f"""
        <div style="
            font-size:10px; font-weight:700; letter-spacing:1.5px;
            color:#888; text-transform:uppercase; padding:8px 4px 4px 4px;
        ">{seccion['seccion']}</div>
        """, unsafe_allow_html=True)

        for item in seccion["items"]:
            # Si el botón es el activo, podemos darle un estilo diferente o simplemente detectar el click
            if st.button(
                item["key"],
                key=f"menu_{item['id']}",
                use_container_width=True,
                help=item["desc"],
            ):
                st.session_state.modulo_activo = item["id"]
                # Al hacer clic, marcamos que queremos que se cierre el sidebar
                st.session_state.sidebar_state = "collapsed"
                st.rerun()

        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

    # ── Datos offline ──────────────────────────────────────────────────────
    show_offline_panel()

    st.divider()

    # ── Toggle tema claro/oscuro ───────────────────────────────────────────
    modo_oscuro = st.session_state.get("modo_oscuro", True)
    label_modo  = "☀️ Modo claro" if modo_oscuro else "🌙 Modo oscuro"
    if st.button(label_modo, use_container_width=True, type="secondary"):
        st.session_state.modo_oscuro = not modo_oscuro
        st.rerun()

    # ── Logout ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
        from auth.google_oauth import logout
        logout()

    return st.session_state.get("modulo_activo", "travel_concierge")
