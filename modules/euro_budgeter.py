import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, date
from io import BytesIO

# Importamos tus utils optimizados
from utils.gcp_client import get_firestore_client
from utils.price_helper import get_exchange_rate, mostrar_precio

# ── Constantes ─────────────────────────────────────────────────────────────
CATEGORIAS = ["🍽️ Comida", "🚌 Transporte", "🏨 Hospedaje", "🎭 Ocio", "🛍️ Compras", "💊 Salud", "📦 Otros"]
CIUDADES = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
COLECCION = "gastos_viaje"

# ── Firestore: Lectura con CACHÉ (Ahorro de dinero) ───────────────────────
@st.cache_data(ttl=600)  # Solo lee de Google cada 10 minutos
def obtener_gastos_cached() -> pd.DataFrame:
    db = get_firestore_client()
    # Limitar la consulta para no traer basura si la colección crece mucho
    docs = db.collection(COLECCION).order_by("fecha", direction="DESCENDING").limit(500).stream()
    
    gastos = [doc.to_dict() for doc in docs]
    if not gastos: return pd.DataFrame()
    
    df = pd.DataFrame(gastos)
    return df

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("💶 Euro-Budgeter")
    
    # Usamos el helper que ya tiene caché de 24h y fallback
    tipo_cambio = get_exchange_rate()
    st.info(f"💱 Tipo de cambio (Caché): **1 EUR = {tipo_cambio:.2f} PEN**")
    
    tab_registrar, tab_dashboard, tab_exportar = st.tabs(["➕ Registrar", "📊 Dashboard", "📥 Exportar"])
    
    with tab_registrar:
        with st.form("form_gasto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", value=date(2026, 7, 14))
                ciudad = st.selectbox("Ciudad", CIUDADES)
                categoria = st.selectbox("Categoría", CATEGORIAS)
            with col2:
                desc = st.text_input("Descripción")
                monto = st.number_input("Monto", min_value=0.0, step=1.0)
                moneda = st.radio("Moneda", ["EUR", "PEN"], horizontal=True)
            
            submit = st.form_submit_button("💾 Guardar", type="primary")
            
            if submit:
                # Lógica de guardado (convertir montos antes de enviar)
                m_eur = monto if moneda == "EUR" else monto / tipo_cambio
                m_pen = monto if moneda == "PEN" else monto * tipo_cambio
                
                nuevo_gasto = {
                    "fecha": str(fecha),
                    "ciudad": ciudad,
                    "categoria": categoria,
                    "descripcion": desc,
                    "monto_eur": round(m_eur, 2),
                    "monto_pen": round(m_pen, 2),
                    "tipo_cambio": round(tipo_cambio, 4),
                    "usuario": st.session_state.get("_user_name", "Desconocido"),
                    "timestamp": datetime.now()
                }
                
                get_firestore_client().collection(COLECCION).add(nuevo_gasto)
                obtener_gastos_cached.clear()
                st.success("✅ Gasto registrado!")

    with tab_dashboard:
        df = obtener_gastos_cached()
        if not df.empty:
            # MÉTRICAS CON "SHOW_PRICES"
            presupuesto_total = 7985.0
            gastado = df["monto_eur"].sum()
            
            c1, c2 = st.columns(2)
            # Solo mostramos el monto real si es Admin usando tu helper
            texto_gasto = f"€{gastado:.2f}"
            c1.metric("Total Gastado", mostrar_precio(texto_gasto))
            c2.metric("Disponible", mostrar_precio(f"€{presupuesto_total - gastado:.2f}"))
            
            # GRÁFICOS (Streamlit native es más rápido que Plotly para móvil)
            st.bar_chart(df.groupby("categoria")["monto_eur"].sum())
            st.dataframe(df[["fecha", "ciudad", "descripcion", "monto_eur"]])