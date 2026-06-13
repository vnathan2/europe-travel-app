# modules/conversor_moneda.py
# Conversor de Moneda — conversión en tiempo real PEN ↔ EUR ↔ USD ↔ GBP ↔ CHF
# NOTA: la "Calculadora del Viaje" se movió a Euro-Budgeter (Panorama).
#       Se quitaron las pestañas "Historial" y "Gráfico EUR/PEN".

from datetime import date

import requests
import streamlit as st

# ── Monedas disponibles ────────────────────────────────────────────────────
MONEDAS = {
    "PEN 🇵🇪 Sol peruano":      "PEN",
    "EUR 🇪🇺 Euro":             "EUR",
    "USD 🇺🇸 Dólar americano":  "USD",
    "GBP 🇬🇧 Libra esterlina":  "GBP",
    "CHF 🇨🇭 Franco suizo":     "CHF",
}


# ── Obtener tipos de cambio en tiempo real ─────────────────────────────────
@st.cache_data(ttl=3600)  # cache 1 hora para no abusar la API
def get_tipos_cambio(base: str = "EUR") -> dict:
    """
    Obtiene todos los tipos de cambio desde ExchangeRate-API.
    Gratuita, sin API key. Cache de 1 hora.
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return {
            "rates": data["rates"],
            "base": base,
            "fecha": data.get("date", str(date.today())),
            "fuente": "ExchangeRate-API (tiempo real)",
        }
    except Exception:
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
            "fuente": "⚠️ Datos de respaldo (sin conexión)",
        }


def convertir(monto: float, de: str, a: str, rates_data: dict) -> float:
    """Convierte entre dos monedas usando las tasas obtenidas."""
    if de == a:
        return monto
    rates = rates_data["rates"]
    base = rates_data["base"]
    if de == base:
        return monto * rates.get(a, 1)
    en_base = monto / rates.get(de, 1)
    return en_base * rates.get(a, 1)


# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("💱 Conversor de Moneda")
    st.caption("Tipos de cambio en tiempo real PEN ↔ EUR ↔ USD ↔ GBP ↔ CHF")

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

    # Referencias desde USD y PEN
    usd_pen = convertir(1, "USD", "PEN", rates_eur)
    usd_eur = convertir(1, "USD", "EUR", rates_eur)
    pen_usd = convertir(1, "PEN", "USD", rates_eur)
    pen_eur = convertir(1, "PEN", "EUR", rates_eur)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("1 USD → PEN", f"S/. {usd_pen:.3f}")
    c6.metric("1 USD → EUR", f"€ {usd_eur:.4f}")
    c7.metric("1 PEN → USD", f"$ {pen_usd:.4f}")
    c8.metric("1 PEN → EUR", f"€ {pen_eur:.4f}")

    st.caption(f"🕐 Actualizado: {rates_eur['fecha']} · Fuente: {rates_eur['fuente']}")
    st.divider()

    # ── Tabs (solo Convertir y Multi-moneda) ─────────────────────────────
    tab_conv, tab_multi = st.tabs(["💱 Convertir", "📊 Multi-moneda"])

    # ── TAB 1: Conversor simple ────────────────────────────────────────────
    with tab_conv:
        st.subheader("💱 Conversor Rápido")

        col1, col2 = st.columns(2)
        with col1:
            moneda_origen = st.selectbox("De:", list(MONEDAS.keys()), index=1)
        with col2:
            moneda_destino = st.selectbox("A:", list(MONEDAS.keys()), index=0)

        monto = st.number_input(
            "Monto:", min_value=0.0, value=100.0, step=10.0, format="%.2f"
        )

        cod_origen = MONEDAS[moneda_origen]
        cod_destino = MONEDAS[moneda_destino]

        if monto > 0:
            resultado = convertir(monto, cod_origen, cod_destino, rates_eur)
            tasa_directa = convertir(1, cod_origen, cod_destino, rates_eur)
            tasa_inversa = convertir(1, cod_destino, cod_origen, rates_eur)

            st.success(
                f"### {monto:,.2f} {cod_origen} = **{resultado:,.2f} {cod_destino}**"
            )
            st.caption(
                f"Tasa: 1 {cod_origen} = {tasa_directa:.4f} {cod_destino}  ·  "
                f"1 {cod_destino} = {tasa_inversa:.4f} {cod_origen}"
            )

            # Conversiones rápidas
            st.subheader("Conversiones rápidas")
            montos_rapidos = [10, 20, 50, 100, 200, 500]
            cols = st.columns(3)
            for i, m in enumerate(montos_rapidos):
                res = convertir(m, cod_origen, cod_destino, rates_eur)
                with cols[i % 3]:
                    st.write(f"**{m} {cod_origen}** = {res:.2f} {cod_destino}")

    # ── TAB 2: Multi-moneda ────────────────────────────────────────────────
    with tab_multi:
        st.subheader("📊 Equivalencias en todas las monedas")

        col1, col2 = st.columns(2)
        with col1:
            moneda_base = st.selectbox(
                "Moneda base:", list(MONEDAS.keys()), index=1
            )
            monto_base = st.number_input(
                "Monto:", min_value=0.0, value=100.0, step=10.0,
                format="%.2f", key="monto_multi"
            )

        cod_base = MONEDAS[moneda_base]

        st.subheader(f"💶 {monto_base:,.2f} {cod_base} equivale a:")

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