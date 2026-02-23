# app.py
# Punto de entrada principal de la aplicación
# Muestra el menú y carga el módulo seleccionado

import streamlit as st

# Configuración de la página — debe ser lo primero
st.set_page_config(
    page_title="Europe Travel App 2026",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importamos los módulos disponibles
from modules.euro_budgeter import mostrar as mostrar_budgeter

# ── Sidebar: menú de navegación ────────────────────────────────────────────
st.sidebar.title("✈️ Europe Travel App")
st.sidebar.caption("Madrid · Bayona · París · Bruselas · Ámsterdam")
st.sidebar.divider()

MODULOS = {
    "💶 Euro-Budgeter": "euro_budgeter",
    "🤖 Travel Concierge Bot": "proximamente",
    "🆘 Emergency Card": "proximamente",
    "🎂 Birthday Planner": "proximamente",
    "🧳 Packing Checker": "proximamente",
    "🚄 Train-Route Optimizer": "proximamente",
    "📔 Trip Journal": "proximamente",
    "💬 Phrase Pocket": "proximamente",
}

seleccion = st.sidebar.radio("Módulos", list(MODULOS.keys()))

st.sidebar.divider()
st.sidebar.caption("🗓️ Viaje: 14–30 julio 2026")
st.sidebar.caption("👨‍👩‍👧 Familia de 3 personas")

# ── Renderizar módulo seleccionado ─────────────────────────────────────────
if MODULOS[seleccion] == "euro_budgeter":
    mostrar_budgeter()
else:
    st.title(seleccion)
    st.info("🚧 Este módulo está en construcción. ¡Próximamente!")