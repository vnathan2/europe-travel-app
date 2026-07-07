# utils/ui_theme.py
# Sistema de temas por ciudad, animaciones, menú sofisticado y modo offline

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
    "conversor_moneda":    "default",
    "itinerary_tracker":"default",
    "shopping_guide":   "default",
    "attractions": "default",
    "night_life":       "amsterdam",
    "admin_panel":      "default",
}


def get_theme(modulo_id: str) -> dict:
    ciudad_key = MODULO_CIUDAD.get(modulo_id, "default")
    return CITY_THEMES.get(ciudad_key, CITY_THEMES["default"])


_BASE_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@600;700&family=Barlow+Semi+Condensed:wght@500;600&display=swap');

:root{
  --et-bg:__BGMAIN__; --et-card:__CARD__; --et-ink:__TEXT__; --et-muted:__MUTED__;
  --et-line:__BORDER__; --et-primary:__PRIMARY__; --et-grad:__GRADIENT__;
  --et-terra:#DB5E39; --et-terra-d:__TERRAD__;
  --et-teal:#15917F;  --et-teal-d:__TEALD__;
  --et-gold:#DA9B33;  --et-gold-d:__GOLDD__;
}

html, body, [class*="css"], .stApp, button, input, textarea, select{
  font-family:'Barlow', system-ui, sans-serif;
}
.stApp{
  background-color:var(--et-bg) !important;
  background-image:radial-gradient(circle at 16% -4%, __GRADA__ 0%, transparent 42%),
                   radial-gradient(circle at 96% 6%, __GRADB__ 0%, transparent 38%);
}
.stApp p, .stApp li, .stApp span, .stApp label, .stApp div{ color:var(--et-ink); }
.stApp h1, .stApp h2, .stApp h3{
  font-family:'Barlow Condensed', sans-serif !important; font-weight:700 !important;
  letter-spacing:.01em; color:var(--et-ink) !important;
}
.stApp h1{ font-size:2.1rem; line-height:1.02; }
.stCaption, small{ color:var(--et-muted) !important; }

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"]>div{
  background-color:var(--et-card) !important; color:var(--et-ink) !important;
  border-color:var(--et-line) !important; border-radius:12px !important;
}
[data-testid="stExpander"]{ background:var(--et-card) !important; border:1px solid var(--et-line) !important; border-radius:14px !important; }
[data-testid="stExpander"] summary{ border-left:3px solid var(--et-primary) !important; padding-left:10px !important; }
[data-testid="stChatMessage"]{ background:var(--et-card) !important; border:1px solid var(--et-line) !important; border-radius:14px !important; }
[data-testid="stAlert"]{ border-left:4px solid var(--et-terra) !important; border-radius:0 12px 12px 0 !important; }

section[data-testid="stSidebar"]{ background:__SIDEBAR__ !important; border-right:1px solid #ffffff1f; }
section[data-testid="stSidebar"] > div:first-child, [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"]{ background:transparent !important; }
section[data-testid="stSidebar"] *{ color:#ffffff !important; }
section[data-testid="stSidebar"] [data-testid="stButton"]>button{ background:#ffffff17 !important; border:1px solid #ffffff2b !important; color:#fff !important; border-radius:12px !important; }
section[data-testid="stSidebar"] [data-testid="stButton"]>button:hover{ background:#ffffff2e !important; transform:none !important; filter:none !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"]{ background:#ffffff12 !important; border:1px solid #ffffff24 !important; }

[data-testid="stTabs"] [data-baseweb="tab-list"]{ gap:8px; background:transparent; border-bottom:none; }
[data-testid="stTabs"] [data-baseweb="tab"]{
  border:1px solid var(--et-line) !important; border-radius:30px !important; padding:7px 15px !important;
  background:var(--et-card) !important; font-weight:500 !important; color:var(--et-muted) !important; transition:.18s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"]{ background:var(--et-terra) !important; color:#fff !important; border-color:var(--et-terra) !important; }

[data-testid="stButton"]>button[kind="primary"]{
  background:var(--et-terra) !important; border:none !important; border-radius:12px !important;
  font-weight:600 !important; color:#fff !important; transition:.18s ease !important;
}
[data-testid="stButton"]>button[kind="primary"]:hover{ transform:translateY(-1px) !important; filter:brightness(1.05); }
[data-testid="stButton"]>button[kind="secondary"]{ border-radius:12px !important; border:1px solid var(--et-line) !important; }

[data-testid="stVerticalBlockBorderWrapper"]{ border-color:var(--et-line) !important; border-radius:16px !important; background:var(--et-card) !important; }

[data-testid="stMetric"]{ background:var(--et-card) !important; border:1px solid var(--et-line) !important; border-radius:14px !important; padding:12px 14px !important; }
[data-testid="stMetricValue"]{ color:var(--et-teal-d) !important; font-family:'Barlow Condensed' !important; font-weight:700 !important; font-size:1.5rem !important; }
[data-testid="stMetricLabel"]{ color:var(--et-muted) !important; }

[data-testid="stProgressBar"]>div{ background:var(--et-line) !important; border-radius:6px !important; }
[data-testid="stProgressBar"]>div>div{ background:var(--et-grad) !important; border-radius:6px !important; }
hr{ border:none !important; border-top:1px solid var(--et-line) !important; background:transparent !important; }
[data-testid="stTabs"] [data-baseweb="tab"] p{ color:inherit !important; margin:0; }
[data-testid="stTabs"] [aria-selected="true"] p{ color:#fff !important; }

::-webkit-scrollbar{ width:7px; } ::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:var(--et-line); border-radius:4px; }

.main .block-container{ animation:fadeInUp .4s ease forwards; }
@keyframes fadeInUp{ from{ opacity:0; transform:translateY(12px); } to{ opacity:1; transform:none; } }

.city-badge{ display:inline-flex; align-items:center; gap:7px; padding:7px 14px; background:rgba(219,94,57,.13); border:1px solid rgba(219,94,57,.42); border-radius:30px; font:600 12.5px 'Barlow'; color:var(--et-terra-d); letter-spacing:.02em; }

.et-hero{ position:relative; overflow:hidden; border-radius:22px; padding:22px 20px 18px; color:#fff; background:var(--et-grad); }
.et-hero::after{ content:""; position:absolute; top:-60px; right:-50px; width:190px; height:190px; border-radius:50%; background:radial-gradient(circle, #ffffff38, transparent 70%); }
.et-eyebrow{ font:600 12px/1 'Barlow Semi Condensed'; letter-spacing:.16em; text-transform:uppercase; color:#ffffffcc; }
.et-hero h1, .et-hero-title{ font:700 33px/.98 'Barlow Condensed' !important; margin:6px 0 2px; color:#fff !important; }
.et-hero .sub{ font-size:13.5px; color:#ffffffd9; }
.et-route{ display:flex; align-items:center; gap:4px; margin:16px 0; }
.et-stop{ display:flex; flex-direction:column; align-items:center; gap:3px; }
.et-dot{ width:9px; height:9px; border-radius:50%; background:#fff; box-shadow:0 0 0 3px #ffffff3b; }
.et-stop small{ font:500 10.5px/1 'Barlow Semi Condensed' !important; color:#ffffffd9 !important; white-space:nowrap; }
.et-seg{ flex:1; height:2px; border-top:2px dotted #ffffff59; }
.et-stats{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.et-stat{ background:#ffffff1a; border:1px solid #ffffff29; border-radius:13px; padding:9px 6px; text-align:center; }
.et-stat b{ display:block; font:700 17px/1 'Barlow Condensed'; color:#fff; }
.et-stat span{ font:500 9.5px/1.1 'Barlow Semi Condensed'; color:#ffffffcc; text-transform:uppercase; letter-spacing:.04em; }

.et-card{ background:var(--et-card); border:1px solid var(--et-line); border-radius:18px; }
.et-label{ font:600 11px/1 'Barlow Semi Condensed'; letter-spacing:.14em; text-transform:uppercase; color:var(--et-muted); }
.et-budget-hero{ display:flex; align-items:flex-end; justify-content:space-between; padding:16px 18px 12px; }
.et-big{ font:700 30px/1 'Barlow Condensed'; color:var(--et-teal-d); }
.et-big small{ font:600 14px 'Barlow'; color:var(--et-teal); }
.et-chip{ font:600 11px/1 'Barlow'; color:var(--et-teal-d); background:rgba(21,145,127,.14); padding:6px 10px; border-radius:20px; }
.et-bgrid{ display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--et-line); border-top:1px solid var(--et-line); }
.et-bcell{ background:var(--et-card); padding:11px 18px; }
.et-bcell .n{ font:600 16px 'Barlow'; color:var(--et-ink); }
.et-bcell .k{ font-size:11.5px; color:var(--et-muted); }
.et-note{ display:flex; gap:9px; background:rgba(218,155,51,.16); border-radius:0 0 18px 18px; padding:12px 18px; font-size:12.5px; color:var(--et-gold-d); }

.et-citybar{ position:relative; overflow:hidden; border-radius:18px; padding:16px 18px; background:var(--et-grad); color:#fff; }
.et-citybar::before{ content:""; position:absolute; left:0; top:0; bottom:0; width:6px; background:var(--et-gold); }
.et-citybar h2, .et-citybar-title{ font:700 26px/1 'Barlow Condensed' !important; color:#fff !important; margin:0 !important; }
.et-citybar .meta{ font:500 13px 'Barlow Semi Condensed'; color:#ffffffe0; margin-top:3px; }

.et-callout{ display:flex; gap:11px; background:var(--et-card); border:1px solid var(--et-line); border-left:4px solid var(--et-terra); border-radius:0 14px 14px 0; padding:13px 16px; }
.et-callout .ico{ flex:0 0 auto; width:30px; height:30px; border-radius:9px; background:rgba(219,94,57,.14); color:var(--et-terra-d); display:flex; align-items:center; justify-content:center; font-size:16px; }
.et-callout p{ font-size:13px; color:var(--et-ink); margin:0; }
.et-callout b{ font-weight:600; color:var(--et-terra-d); }

.et-daybar{ display:flex; align-items:center; gap:10px; margin:18px 0 4px; }
.et-daypill{ font:600 12px/1 'Barlow Semi Condensed'; letter-spacing:.05em; text-transform:uppercase; background:var(--et-terra); color:#fff; padding:7px 11px; border-radius:9px; }
.et-daybar h3, .et-daybar .title{ font:600 16px 'Barlow' !important; color:var(--et-ink) !important; margin:0 !important; }
.et-daybar .line{ flex:1; height:1px; background:var(--et-line); }

.et-tl{ position:relative; margin-top:8px; }
.et-ev{ position:relative; display:grid; grid-template-columns:54px 1fr; gap:12px; padding-bottom:14px; }
.et-ev::before{ content:""; position:absolute; left:60px; top:24px; bottom:-2px; width:2px; background:var(--et-line); }
.et-ev:last-child::before{ display:none; }
.et-time{ font:600 13px 'Barlow'; color:var(--et-muted); text-align:right; padding-top:13px; }
.et-ec{ position:relative; background:var(--et-card); border:1px solid var(--et-line); border-radius:14px; padding:12px 14px; transition:.18s; }
.et-ec:hover{ transform:translateY(-1px); }
.et-tl .et-ec::before{ content:""; position:absolute; left:-19px; top:16px; width:11px; height:11px; border-radius:50%; background:var(--et-card); border:3px solid var(--et-terra); }
.et-tl .et-ec.free::before{ border-color:var(--et-teal); }
.et-ec .row{ display:flex; align-items:center; gap:9px; }
.et-badge{ flex:0 0 auto; width:30px; height:30px; border-radius:9px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:15px; }
.et-b-trans{ background:#4a6b8a; } .et-b-food{ background:var(--et-terra); } .et-b-see{ background:var(--et-gold); }
.et-ec h4, .et-ec .title{ font:600 14.5px 'Barlow' !important; color:var(--et-ink) !important; margin:0 !important; }
.et-ec .addr{ font-size:12px; color:var(--et-muted); }
.et-tags{ display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.et-t{ font:500 11px 'Barlow'; padding:4px 9px; border-radius:7px; }
.et-t-free{ background:rgba(21,145,127,.14); color:var(--et-teal-d); }
.et-t-rate{ background:rgba(218,155,51,.16); color:var(--et-gold-d); }
.et-t-info{ background:rgba(120,120,120,.12); color:var(--et-muted); }

@media (max-width: 640px){
  [data-testid="stHorizontalBlock"]{ flex-direction:column !important; gap:8px !important; }
  [data-testid="stHorizontalBlock"]>[data-testid="column"], [data-testid="column"]{ width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
  [data-testid="stMetric"]{ padding:8px 10px !important; }
  [data-testid="stMetricValue"]{ font-size:1.5rem !important; }
  .stApp h1{ font-size:1.8rem !important; } .stApp h2{ font-size:1.4rem !important; } .stApp h3{ font-size:1.15rem !important; }
  .main .block-container, [data-testid="stMainBlockContainer"]{ padding:1rem .6rem !important; }
  .et-stat b{ font-size:15px; }
}
"""


def _editorial_css(theme: dict, modo_oscuro: bool) -> str:
    """CSS del sistema de diseño 'editorial de viaje' (paleta cálida + Barlow).
    Usa el acento de la ciudad activa (theme['primary'] / theme['gradient'])."""
    if modo_oscuro:
        bg_main, text_main, text_muted = "#1A1714", "#F3ECE0", "#A99C88"
        card_bg, border_col            = "#241F1A", "#3A332B"
        terra_d, teal_d, gold_d        = "#F0997B", "#5DCAA5", "#E6C27A"
        grad_a, grad_b                 = "#ffffff10", "#ffffff08"
    else:
        bg_main, text_main, text_muted = "#F4ECDD", "#23262F", "#8A8275"
        card_bg, border_col            = "#FFFDF9", "#E7DCC8"
        terra_d, teal_d, gold_d        = "#A8431F", "#0B5E50", "#8F6310"
        grad_a, grad_b                 = "#fff7ea", "#f3e2cf"

    css = _BASE_CSS
    repl = {
        "__BGMAIN__": bg_main, "__TEXT__": text_main, "__MUTED__": text_muted,
        "__CARD__": card_bg, "__BORDER__": border_col,
        "__PRIMARY__": theme["primary"], "__GRADIENT__": theme["gradient"],
        "__SIDEBAR__": theme["sidebar_bg"],
        "__TERRAD__": terra_d, "__TEALD__": teal_d, "__GOLDD__": gold_d,
        "__GRADA__": grad_a, "__GRADB__": grad_b,
    }
    for k, v in repl.items():
        css = css.replace(k, v)
    return css


def apply_theme(theme: dict):
    """Inyecta el CSS global del sistema de diseno editorial con el acento de la ciudad activa."""
    modo_oscuro = st.session_state.get("modo_oscuro", True)
    st.markdown("<style>" + _editorial_css(theme, modo_oscuro) + "</style>",
                unsafe_allow_html=True)


def render_menu_fab():
    """Stub — mantenido por compatibilidad con app.py."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
# ANIMACIONES DE CARGA
# ══════════════════════════════════════════════════════════════════════════════

LOADING_MESSAGES = {
    "travel_concierge": [
        "☕ Lady está preparando su café parisino...",
        "🗺️ Consultando los mejores rincones de Europa...",
        "✈️ Revisando horarios de vuelo...",
        "🎭 Buscando experiencias únicas para la familia...",
    ],
    "train_optimizer": [
        "🚄 Calculando la ruta más rápida...",
        "🇪🇺 Consultando Alsa, SNCF y Eurostar...",
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


def show_loading_animation(modulo_id: str):
    # Muestra el spinner temático y DEVUELVE el placeholder. El caller lo limpia
    # cuando termina la carga real del módulo. Sin time.sleep: el spinner es
    # visible solo durante el import real, no un delay artificial de servidor.
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

    return placeholder


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
            "Bayona":    "🏠 Casa familiar — dirección guardada en contactos",
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
            "Terminal": "Barajas T1 (Air Europa, ida y vuelta)",
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
            {"key": "💱 Conversor de Moneda", "id": "conversor_moneda",    "desc": "EUR ↔ PEN en tiempo real"},
        ]
    },
    {
        "seccion": "🗺️ Planificación",
        "items": [
            #{"key": "🤖 Travel Concierge",    "id": "travel_concierge", "desc": "Lady + itinerario + alertas"},
            {"key": "📋 Lady Travel itinerary",          "id": "itinerary_tracker","desc": "Checks del día"},
            {"key": "🚄 Travels",              "id": "train_optimizer",  "desc": "Rutas y horarios"},
            {"key": "🏨 Hotels",             "id": "hoteles",          "desc": "Reservas por ciudad"},
            {"key": "🎭 Attractions", "id": "attractions", "desc": "Atracciones por ciudad"},
        ]
    },
    {
        "seccion": "🎉 Especiales",
        "items": [
            {"key": "🎂 Birthday Planner",          "id": "birthday_planner", "desc": "Camila & Giovanna"},
            {"key": "🛒 Shopping Guide",       "id": "shopping_guide",   "desc": "Tiendas · Ofertas · Souvenirs"},
            {"key": "🧳 Packing Checker",            "id": "packing_checker",  "desc": "Lista de packing"},
            {"key": "📔 Trip Journal",              "id": "trip_journal",     "desc": "Fotos y memorias"},
        ]
    },
    {
        "seccion": "🛟 Utilidades",
        "items": [
            {"key": "🗣️ Translator",           "id": "voice_translator", "desc": "Voz + texto"},
            {"key": "🚨 Emergencies",         "id": "emergency_card",   "desc": "SOS y contactos"},
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
        # OJO: usar el ID del menú (itinerary_tracker), no el nombre del archivo
        # (travel_concierge). El router en app.py mapea itinerary_tracker → modules.travel_concierge.
        st.session_state.modulo_activo = "itinerary_tracker"

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

    # ── Logout ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
        from auth.google_oauth import logout
        logout()

    return st.session_state.get("modulo_activo", "travel_concierge")