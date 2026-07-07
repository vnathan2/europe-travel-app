import importlib
import os
import sys

import streamlit as st

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(__file__))

# ── 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO) ──────────────────────────
st.set_page_config(
    page_title="Europe Travel 2026 ✈️",
    page_icon="✈️",
    layout="wide",
    # "auto" = colapsado en móvil, expandido en escritorio. La navegación
    # principal en móvil es el selector al tope de la página, no el sidebar.
    initial_sidebar_state="auto",
)

# ── 2. GESTIÓN DE ENTORNO Y SEGURIDAD ─────────────────────────────────────
# Usamos una variable explícita para desarrollo
APP_MODE = os.getenv("APP_MODE", "PRODUCTION")
IS_LOCAL = APP_MODE == "DEVELOPMENT"

if IS_LOCAL:
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = {
            "email": "dev@local.com",
            "name":  "Dev Local",
            "pic":   "",
            "role":  "ADMIN",
        }

from auth.google_oauth import auth_gate, get_current_user, is_admin, show_prices

# Ejecutar el portal de autenticación
auth_gate()

# Si no hay usuario después del gate, detenemos todo por seguridad
user = get_current_user()
if not user:
    st.warning("Por favor, inicia sesión para continuar.")
    st.stop()

# ── 3. UI Y TEMAS ──────────────────────────────────────────────────────────
from utils.ui_theme import (
    apply_theme,
    get_theme,
    render_menu_fab,
    render_sidebar_menu,
    show_loading_animation,
)

# Sincronizar estado ANTES de renderizar la UI
st.session_state["_show_prices"] = show_prices()
st.session_state["_is_admin"]    = is_admin()
st.session_state["_user_name"]   = user["name"]

with st.sidebar:
    modulo_id = render_sidebar_menu(is_admin(), user)

theme = get_theme(modulo_id)
apply_theme(theme)
render_menu_fab()

# Badge de ciudad
_, col_badge = st.columns([5, 1])
with col_badge:
    st.markdown(f"""
    <div style="text-align:right; padding-top:8px;">
        <span class="city-badge">
            {theme['emoji']} {theme['nombre']} · {theme['fechas']}
        </span>
    </div>
    """, unsafe_allow_html=True)

# Display automático del hotel actual (sale solo si estás en fechas del viaje)
# Import perezoso para no cargar modules.hoteles en cada rerun fuera del viaje.
try:
    from datetime import date as _date

    from modules.hoteles import hotel_por_fecha
    _ciudad_h, _hotel_h = hotel_por_fecha(_date.today())
    if _hotel_h and _hotel_h.get("nombre"):
        st.caption(
            f"🏨 Hoy te alojas en: **{_hotel_h['nombre']}** · {_ciudad_h}"
        )
except Exception:
    pass  # no romper la UI si hoteles falla (Firestore down, etc.)

# Detectar si hubo cambio de módulo en este rerun (para spinner y auto-cierre del sidebar)
_prev_modulo = st.session_state.get("_ultimo_modulo")
_modulo_cambio = _prev_modulo is not None and _prev_modulo != modulo_id

# Spinner temático visible solo mientras se importa el módulo (sin sleep artificial)
_loading_ph = None
if _prev_modulo != modulo_id:
    st.session_state["_ultimo_modulo"] = modulo_id
    _loading_ph = show_loading_animation(modulo_id)

# Auto-cerrar el sidebar SOLO en móvil tras cambiar de módulo (no en primer load).
# Streamlit no expone control programático del sidebar, así que clickeamos el
# botón de cerrar vía JS desde un iframe transparente. En desktop no se cierra.
if _modulo_cambio:
    st.components.v1.html(
        """
        <script>
        (function() {
          if (window.parent.innerWidth > 768) return;  // solo móvil
          const doc = window.parent.document;
          const selectores = [
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="stSidebarCollapsedControl"]',
            '[data-testid="collapsedControl"]',
            'section[data-testid="stSidebar"] button[kind="header"]',
            'section[data-testid="stSidebar"] button[aria-label*="Close"]',
            'section[data-testid="stSidebar"] button[aria-label*="Cerrar"]'
          ];
          for (const s of selectores) {
            const btn = doc.querySelector(s);
            if (btn) { btn.click(); return; }
          }
        })();
        </script>
        """,
        height=0,
    )

# ── 4. ENRUTAMIENTO DINÁMICO (DICCIONARIO) ────────────────────────────────
MODULOS = {
    "euro_budgeter": "modules.euro_budgeter",
    "emergency_card": "modules.emergency_card",
    "birthday_planner": "modules.birthday_planner",
    "shopping_guide": "modules.shopping_guide",
    "packing_checker": "modules.packing_checker",
    "voice_translator": "modules.voice_translator",
    "train_optimizer": "modules.train_optimizer",
    "trip_journal": "modules.trip_journal",
    "conversor_moneda": "modules.conversor_moneda",
    "itinerary_tracker": "modules.travel_concierge",
    "hoteles": "modules.hoteles",
    "attractions": "modules.attractions",
    "night_life": "modules.night_life",
    "admin_panel": "modules.admin_panel"
}

# Módulos restringidos para ADMIN
RESTRICCIONES = ["night_life", "admin_panel"]

if modulo_id in MODULOS:
    if modulo_id in RESTRICCIONES and not is_admin():
        if _loading_ph:
            _loading_ph.empty()
        st.error("⛔ No tienes acceso a este módulo.")
    else:
        # Importación dinámica (Lazy Loading) — el spinner se ve durante esto
        target_module = importlib.import_module(MODULOS[modulo_id])
        if _loading_ph:
            _loading_ph.empty()
        target_module.mostrar()
else:
    if _loading_ph:
        _loading_ph.empty()
    st.info("Selecciona un módulo en el menú para comenzar.")
