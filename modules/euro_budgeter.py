# modules/euro_budgeter.py
# Módulo 1: Euro-Budgeter
# Registra gastos del viaje, convierte PEN↔EUR y genera reportes

import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, date
from io import BytesIO
from utils.gcp_client import get_firestore_client, upload_to_bucket

# ── Constantes ─────────────────────────────────────────────────────────────
CATEGORIAS = ["🍽️ Comida", "🚌 Transporte", "🏨 Hospedaje",
               "🎭 Ocio/Turismo", "🛍️ Compras", "💊 Salud", "📦 Otros"]

CIUDADES = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]

COLECCION = "gastos_viaje"  # Nombre de la colección en Firestore

# ── Tipo de cambio ─────────────────────────────────────────────────────────
def get_tipo_cambio() -> float:
    """
    Obtiene el tipo de cambio EUR→PEN del día desde ExchangeRate-API.
    Si la API falla, usa el valor de respaldo del .env
    
    La API gratuita permite 1,500 requests/mes — más que suficiente.
    """
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["PEN"]
    except Exception:
        # Si no hay internet o falla la API, usamos el tipo de cambio de respaldo
        fallback = float(os.getenv("FALLBACK_EUR_PEN_RATE", "4.0"))
        st.warning(f"⚠️ No se pudo obtener tipo de cambio en tiempo real. Usando: 1 EUR = {fallback} PEN")
        return fallback

# ── Firestore: guardar gasto ───────────────────────────────────────────────
def guardar_gasto(gasto: dict):
    """
    Guarda un gasto en Firestore.
    
    Estructura del documento:
    {
        fecha: "2026-07-15",
        ciudad: "Madrid",
        categoria: "Comida",
        descripcion: "Almuerzo en El Botín",
        monto_eur: 35.0,
        monto_pen: 140.0,
        tipo_cambio: 4.0
    }
    """
    db = get_firestore_client()
    db.collection(COLECCION).add({
        **gasto,
        "timestamp": datetime.now()
    })

# ── Firestore: obtener gastos ──────────────────────────────────────────────
def obtener_gastos() -> pd.DataFrame:
    """
    Obtiene todos los gastos guardados en Firestore
    y los retorna como un DataFrame de pandas.
    """
    db = get_firestore_client()
    docs = db.collection(COLECCION).order_by("fecha").stream()
    
    gastos = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id  # guardamos el ID para poder eliminar
        gastos.append(data)
    
    if not gastos:
        return pd.DataFrame()
    
    df = pd.DataFrame(gastos)
    # Limpiamos columnas que no necesitamos mostrar
    cols_mostrar = ["fecha", "ciudad", "categoria", "descripcion",
                    "monto_eur", "monto_pen", "tipo_cambio"]
    return df[[c for c in cols_mostrar if c in df.columns]]

# ── Exportar a Excel ───────────────────────────────────────────────────────
def exportar_excel(df: pd.DataFrame) -> bytes:
    """
    Convierte el DataFrame a Excel en memoria (sin guardar en disco).
    Retorna los bytes del archivo para descarga desde Streamlit.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Gastos Europa 2026")
        
        # Hoja de resumen por categoría
        if not df.empty:
            resumen = df.groupby("categoria")["monto_eur"].sum().reset_index()
            resumen.columns = ["Categoría", "Total EUR"]
            resumen["Total PEN"] = resumen["Total EUR"] * df["tipo_cambio"].mean()
            resumen.to_excel(writer, index=False, sheet_name="Resumen")
    
    return output.getvalue()

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    """
    Función principal que renderiza toda la UI del módulo.
    Se llama desde app.py cuando el usuario selecciona Euro-Budgeter.
    """
    st.title("💶 Euro-Budgeter")
    st.caption("Registra y controla los gastos del viaje a Europa")
    
    # Obtenemos el tipo de cambio del día
    tipo_cambio = get_tipo_cambio()
    st.info(f"💱 Tipo de cambio del día: **1 EUR = {tipo_cambio:.2f} PEN**")
    
    # ── Tabs de la UI ──────────────────────────────────────────────────────
    tab_registrar, tab_dashboard, tab_exportar = st.tabs(
        ["➕ Registrar Gasto", "📊 Dashboard", "📥 Exportar"]
    )
    
    # ── TAB 1: Registrar ───────────────────────────────────────────────────
    with tab_registrar:
        st.subheader("Nuevo Gasto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha", value=date(2026, 7, 14),
                                   min_value=date(2026, 7, 14),
                                   max_value=date(2026, 7, 30))
            ciudad = st.selectbox("Ciudad", CIUDADES)
            categoria = st.selectbox("Categoría", CATEGORIAS)
        
        with col2:
            descripcion = st.text_input("Descripción", 
                                         placeholder="Ej: Almuerzo en El Botín")
            moneda = st.radio("Moneda del gasto", ["EUR €", "PEN S/."],
                               horizontal=True)
            monto = st.number_input("Monto", min_value=0.0, 
                                     step=0.5, format="%.2f")
        
        # Calculamos la conversión en tiempo real
        if monto > 0:
            if moneda == "EUR €":
                monto_eur = monto
                monto_pen = monto * tipo_cambio
            else:
                monto_pen = monto
                monto_eur = monto / tipo_cambio
            
            st.success(f"💱 Equivale a: **€{monto_eur:.2f} EUR** = **S/.{monto_pen:.2f} PEN**")
        
        if st.button("💾 Guardar Gasto", type="primary", use_container_width=True):
            if not descripcion:
                st.error("Por favor ingresa una descripción")
            elif monto <= 0:
                st.error("El monto debe ser mayor a 0")
            else:
                gasto = {
                    "fecha": str(fecha),
                    "ciudad": ciudad,
                    "categoria": categoria,
                    "descripcion": descripcion,
                    "monto_eur": round(monto_eur, 2),
                    "monto_pen": round(monto_pen, 2),
                    "tipo_cambio": round(tipo_cambio, 4),
                }
                guardar_gasto(gasto)
                st.success("✅ Gasto guardado correctamente")
                st.balloons()
    
    # ── TAB 2: Dashboard ───────────────────────────────────────────────────
    with tab_dashboard:
        df = obtener_gastos()
        
        if df.empty:
            st.info("📭 Aún no hay gastos registrados. ¡Empieza a registrar!")
            return
        
        total_eur = df["monto_eur"].sum()
        total_pen = df["monto_pen"].sum()
        presupuesto_eur = 7985.0  # disponible del viaje
        
        # Métricas principales
        col1, col2, col3 = st.columns(3)
        col1.metric("💶 Total gastado", f"€{total_eur:.2f}", 
                    f"S/.{total_pen:.2f}")
        col2.metric("💰 Presupuesto disponible", f"€{presupuesto_eur:.2f}")
        col3.metric("📊 Restante", 
                    f"€{presupuesto_eur - total_eur:.2f}",
                    delta_color="inverse")
        
        # Alerta si se supera el 80% del presupuesto
        if total_eur >= presupuesto_eur * 0.8:
            st.warning("⚠️ Has usado más del 80% del presupuesto disponible")
        
        st.divider()
        
        # Gráfico por categoría
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Gasto por Categoría")
            df_cat = df.groupby("categoria")["monto_eur"].sum().reset_index()
            fig = px.pie(df_cat, values="monto_eur", names="categoria",
                         title="Distribución por categoría (EUR)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Gasto por Ciudad")
            df_ciudad = df.groupby("ciudad")["monto_eur"].sum().reset_index()
            fig2 = px.bar(df_ciudad, x="ciudad", y="monto_eur",
                          title="Gasto por ciudad (EUR)",
                          color="ciudad")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Tabla de todos los gastos
        st.subheader("Todos los gastos")
        st.dataframe(df, use_container_width=True)
    
    # ── TAB 3: Exportar ────────────────────────────────────────────────────
    with tab_exportar:
        st.subheader("Exportar a Excel")
        df = obtener_gastos()
        
        if df.empty:
            st.info("No hay gastos para exportar aún")
            return
        
        st.write(f"📋 Total de gastos registrados: **{len(df)}**")
        
        excel_bytes = exportar_excel(df)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_bytes,
            file_name=f"gastos_europa_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )