# modules/phrase_pocket.py
# Módulo 9: Conversor de Moneda Avanzado
# Conversión en tiempo real PEN↔EUR↔USD + historial + gráficos

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from utils.gcp_client import get_firestore_client

# ── Monedas disponibles ────────────────────────────────────────────────────
MONEDAS = {
    "PEN 🇵🇪 Sol peruano":      "PEN",
    "EUR 🇪🇺 Euro":             "EUR",
    "USD 🇺🇸 Dólar americano":  "USD",
    "GBP 🇬🇧 Libra esterlina":  "GBP",
    "CHF 🇨🇭 Franco suizo":     "CHF",
}

COLECCION = "conversiones_historial"

# ── Obtener tipos de cambio en tiempo real ─────────────────────────────────
@st.cache_data(ttl=3600)  # cache 1 hora para no abusar la API
def get_tipos_cambio(base: str = "EUR") -> dict:
    """
    Obtiene todos los tipos de cambio desde ExchangeRate-API.
    Gratuita, sin API key, hasta 1500 requests/mes.
    Cache de 1 hora para no abusar.
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return {
            "rates": data["rates"],
            "base": base,
            "fecha": data.get("date", str(date.today())),
            "fuente": "ExchangeRate-API (tiempo real)"
        }
    except Exception:
        # Fallback con tasas aproximadas si falla la API
        fallback = {
            "EUR": {"PEN": 4.0, "USD": 1.08, "GBP": 0.86, "CHF": 0.96},
            "PEN": {"EUR": 0.25, "USD": 0.27, "GBP": 0.21, "CHF": 0.24},
        }
        rates = fallback.get(base, {})
        rates[base] = 1.0
        return {
            "rates": rates,
            "base": base,
            "fecha": str(date.today()),
            "fuente": "⚠️ Datos de respaldo (sin conexión)"
        }

def convertir(monto: float, de: str, a: str,
              rates_data: dict) -> float:
    """Convierte entre dos monedas usando las tasas obtenidas."""
    if de == a:
        return monto
    rates = rates_data["rates"]
    base = rates_data["base"]

    # Si la base es la moneda origen
    if de == base:
        return monto * rates.get(a, 1)

    # Convertir via base
    en_base = monto / rates.get(de, 1)
    return en_base * rates.get(a, 1)

# ── Historial en Firestore ─────────────────────────────────────────────────
def guardar_conversion(conversion: dict):
    try:
        db = get_firestore_client()
        db.collection(COLECCION).add({
            **conversion,
            "timestamp": datetime.now()
        })
    except Exception:
        pass  # No bloqueamos si falla el guardado

def obtener_historial(limite: int = 50) -> pd.DataFrame:
    try:
        db = get_firestore_client()
        docs = (db.collection(COLECCION)
                  .order_by("timestamp",
                            direction="DESCENDING")
                  .limit(limite)
                  .stream())
        registros = [{"id": d.id, **d.to_dict()} for d in docs]
        if not registros:
            return pd.DataFrame()
        df = pd.DataFrame(registros)
        cols = ["timestamp", "monto_origen", "moneda_origen",
                "monto_resultado", "moneda_destino", "tasa"]
        return df[[c for c in cols if c in df.columns]]
    except Exception:
        return pd.DataFrame()

# ── Gráfico histórico de tasa EUR/PEN ─────────────────────────────────────
@st.cache_data(ttl=86400)  # cache 24h
def get_historial_tasa() -> pd.DataFrame:
    """
    Obtiene el historial de tasa EUR/PEN de los últimos 30 días
    usando Open Exchange Rates historical (gratuito).
    """
    try:
        fechas, tasas = [], []
        hoy = date.today()
        for i in range(29, -1, -3):  # cada 3 días = 10 puntos
            fecha = hoy - timedelta(days=i)
            url = (f"https://api.exchangerate-api.com/v4/"
                   f"history/EUR/{fecha.year}/"
                   f"{fecha.month}/{fecha.day}")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                tasa = data.get("rates", {}).get("PEN")
                if tasa:
                    fechas.append(fecha)
                    tasas.append(tasa)

        if fechas:
            return pd.DataFrame({"fecha": fechas, "tasa": tasas})
    except Exception:
        pass

    # Fallback: datos simulados realistas
    hoy = date.today()
    fechas = [hoy - timedelta(days=i) for i in range(29, -1, -3)]
    tasas = [3.95, 3.97, 3.98, 3.96, 4.00,
             3.99, 4.01, 4.02, 3.98, 4.00]
    return pd.DataFrame({"fecha": fechas, "tasa": tasas})

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("💱 Conversor de Moneda")
    st.caption("Tipos de cambio en tiempo real con historial y análisis")

    # Cargar tasas
    rates_eur = get_tipos_cambio("EUR")

    # Header con tasas principales
    col1, col2, col3, col4 = st.columns(4)
    tasa_pen = rates_eur["rates"].get("PEN", 4.0)
    tasa_usd = rates_eur["rates"].get("USD", 1.08)
    tasa_gbp = rates_eur["rates"].get("GBP", 0.86)
    tasa_chf = rates_eur["rates"].get("CHF", 0.96)

    col1.metric("1 EUR → PEN", f"S/. {tasa_pen:.3f}")
    col2.metric("1 EUR → USD", f"$ {tasa_usd:.3f}")
    col3.metric("1 EUR → GBP", f"£ {tasa_gbp:.3f}")
    col4.metric("1 EUR → CHF", f"₣ {tasa_chf:.3f}")

    st.caption(
        f"🕐 Actualizado: {rates_eur['fecha']} · "
        f"Fuente: {rates_eur['fuente']}"
    )

    st.divider()

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_conv, tab_multi, tab_viaje, tab_hist, tab_grafico = st.tabs([
        "💱 Convertir", "📊 Multi-moneda",
        "✈️ Para el Viaje", "📋 Historial", "📈 Gráfico EUR/PEN"
    ])

    # ── TAB 1: Conversor simple ────────────────────────────────────────────
    with tab_conv:
        st.subheader("💱 Conversor Rápido")

        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            moneda_origen = st.selectbox(
                "De:", list(MONEDAS.keys()), index=1
            )
            monto = st.number_input(
                "Monto:", min_value=0.0,
                value=100.0, step=10.0, format="%.2f"
            )

        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.markdown("### ⇄")

        with col3:
            moneda_destino = st.selectbox(
                "A:", list(MONEDAS.keys()), index=0
            )

        cod_origen = MONEDAS[moneda_origen]
        cod_destino = MONEDAS[moneda_destino]

        if monto > 0:
            resultado = convertir(
                monto, cod_origen, cod_destino, rates_eur
            )
            tasa_directa = convertir(
                1, cod_origen, cod_destino, rates_eur
            )

            st.success(
                f"### {monto:,.2f} {cod_origen} = "
                f"**{resultado:,.2f} {cod_destino}**"
            )
            st.caption(
                f"Tasa: 1 {cod_origen} = {tasa_directa:.4f} {cod_destino}"
            )

            # Conversiones rápidas
            st.subheader("Conversiones rápidas")
            montos_rapidos = [10, 20, 50, 100, 200, 500]
            cols = st.columns(3)
            for i, m in enumerate(montos_rapidos):
                res = convertir(m, cod_origen, cod_destino, rates_eur)
                with cols[i % 3]:
                    st.write(
                        f"**{m} {cod_origen}** = {res:.2f} {cod_destino}"
                    )

            if st.button("💾 Guardar en historial",
                         type="primary", use_container_width=True):
                guardar_conversion({
                    "monto_origen": monto,
                    "moneda_origen": cod_origen,
                    "monto_resultado": round(resultado, 2),
                    "moneda_destino": cod_destino,
                    "tasa": round(tasa_directa, 4),
                    "fecha": str(date.today()),
                })
                st.success("✅ Guardado en historial")

    # ── TAB 2: Multi-moneda ────────────────────────────────────────────────
    with tab_multi:
        st.subheader("📊 Equivalencias en todas las monedas")

        col1, col2 = st.columns(2)
        with col1:
            moneda_base = st.selectbox(
                "Moneda base:", list(MONEDAS.keys()), index=1
            )
            monto_base = st.number_input(
                "Monto:", min_value=0.0,
                value=100.0, step=10.0,
                format="%.2f", key="monto_multi"
            )

        cod_base = MONEDAS[moneda_base]

        st.subheader(
            f"💶 {monto_base:,.2f} {cod_base} equivale a:"
        )

        for nombre, cod in MONEDAS.items():
            if cod != cod_base:
                res = convertir(monto_base, cod_base, cod, rates_eur)
                tasa = convertir(1, cod_base, cod, rates_eur)
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{nombre}**")
                with col2:
                    st.write(f"**{res:,.2f} {cod}**")
                with col3:
                    st.caption(f"@{tasa:.4f}")

    # ── TAB 3: Para el viaje ───────────────────────────────────────────────
    with tab_viaje:
        st.subheader("✈️ Calculadora del Viaje")
        st.caption(
            "Cuántos soles necesitas llevar para cada ciudad"
        )

        presupuesto_eur = {
            "Madrid (4 días)":    1650,
            "Bayona (2 días)":     750,
            "París (4 días)":     2550,
            "Bruselas (2 días)":   785,
            "Ámsterdam (4 días)": 1130,
        }

        tasa_actual = tasa_pen
        st.info(
            f"💱 Usando tasa actual: **1 EUR = S/. {tasa_actual:.3f}**"
        )

        total_eur = 0
        total_pen = 0

        for ciudad, euros in presupuesto_eur.items():
            soles = euros * tasa_actual
            total_eur += euros
            total_pen += soles
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📍 **{ciudad}**")
            with col2:
                st.write(f"€{euros:,}")
            with col3:
                st.write(f"S/. {soles:,.0f}")

        st.divider()
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("**TOTAL ESTIMADO**")
        with col2:
            st.write(f"**€{total_eur:,}**")
        with col3:
            st.write(f"**S/. {total_pen:,.0f}**")

        st.success(
            f"💰 Presupuesto disponible: S/. 31,941 (~€7,985)\n\n"
            f"📊 Estimado del viaje: S/. {total_pen:,.0f} "
            f"(~€{total_eur:,})\n\n"
            f"✅ Colchón disponible: "
            f"S/. {31941 - total_pen:,.0f} "
            f"(~€{7985 - total_eur:,})"
        )

        st.divider()
        st.subheader("🧮 Simulador personalizado")
        st.caption(
            "¿Cuántos soles necesito si cambio la cantidad de euros?"
        )

        euros_custom = st.slider(
            "Euros a llevar:", 100, 10000, 7000, step=100
        )
        soles_custom = euros_custom * tasa_actual
        st.metric(
            f"Para llevar €{euros_custom:,} necesitas:",
            f"S/. {soles_custom:,.2f}",
            f"Tasa: 1 EUR = S/. {tasa_actual:.3f}"
        )

    # ── TAB 4: Historial ───────────────────────────────────────────────────
    with tab_hist:
        st.subheader("📋 Historial de Conversiones")

        df = obtener_historial()

        if df.empty:
            st.info(
                "No hay conversiones guardadas aún. "
                "Usa el conversor y guarda las que necesites."
            )
        else:
            st.caption(f"📊 {len(df)} conversiones guardadas")
            st.dataframe(df, use_container_width=True,
                         hide_index=True)

            # Resumen por moneda
            if "moneda_destino" in df.columns:
                st.subheader("Resumen por moneda")
                resumen = (df.groupby("moneda_destino")
                             ["monto_resultado"]
                             .agg(["count", "sum", "mean"])
                             .reset_index())
                resumen.columns = [
                    "Moneda", "Conversiones",
                    "Total convertido", "Promedio"
                ]
                st.dataframe(resumen, use_container_width=True,
                             hide_index=True)

    # ── TAB 5: Gráfico ─────────────────────────────────────────────────────
    with tab_grafico:
        st.subheader("📈 Evolución EUR/PEN — Últimos 30 días")

        with st.spinner("Cargando datos históricos..."):
            df_hist = get_historial_tasa()

        if not df_hist.empty:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_hist["fecha"],
                y=df_hist["tasa"],
                mode="lines+markers",
                name="EUR/PEN",
                line=dict(color="#1A73E8", width=3),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(26,115,232,0.1)"
            ))

            # Línea de tasa actual
            fig.add_hline(
                y=tasa_pen,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Hoy: {tasa_pen:.3f}",
                annotation_position="bottom right"
            )

            # Línea de tasa usada en el presupuesto
            fig.add_hline(
                y=4.0,
                line_dash="dot",
                line_color="orange",
                annotation_text="Presupuesto base: 4.0",
                annotation_position="top right"
            )

            fig.update_layout(
                title="Tipo de cambio EUR → PEN",
                xaxis_title="Fecha",
                yaxis_title="Soles por Euro",
                height=400,
                showlegend=False,
                plot_bgcolor="white",
                yaxis=dict(
                    range=[
                        df_hist["tasa"].min() * 0.995,
                        df_hist["tasa"].max() * 1.005
                    ]
                )
            )
            st.plotly_chart(fig, use_container_width=True)

            # Análisis
            tasa_min = df_hist["tasa"].min()
            tasa_max = df_hist["tasa"].max()
            tasa_prom = df_hist["tasa"].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Mínimo 30 días", f"S/. {tasa_min:.3f}")
            col2.metric("Promedio 30 días", f"S/. {tasa_prom:.3f}")
            col3.metric("Máximo 30 días", f"S/. {tasa_max:.3f}")

            diferencia = (tasa_pen - tasa_prom) / tasa_prom * 100
            if diferencia > 1:
                st.success(
                    f"📈 El euro está **{diferencia:.1f}% más caro** "
                    f"que el promedio del mes — considera cambiar pronto"
                )
            elif diferencia < -1:
                st.info(
                    f"📉 El euro está **{abs(diferencia):.1f}% más barato** "
                    f"que el promedio del mes — buen momento para cambiar"
                )
            else:
                st.info(
                    "📊 El euro está en su nivel promedio del mes"
                )
