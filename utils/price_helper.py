import streamlit as st
import os
import requests
from utils.logger import get_logger

logger = get_logger(__name__)

# Default razonable del fallback EUR/PEN (actualizado 2026-05).
# Sobreescribible via env var FALLBACK_EUR_PEN_RATE sin tocar código.
# Fuente de referencia: BCRP (https://www.bcrp.gob.pe/) y exchangerate-api.com.
DEFAULT_FALLBACK_EUR_PEN = 3.95


# 1. Función de visibilidad (la que ya tenías, mantenida)
def mostrar_precio(precio_str: str, fallback: str = "🔒") -> str:
    """Retorna precio si admin, fallback si familiar."""
    if st.session_state.get("_show_prices", False):  # default False = seguro
        return precio_str
    return fallback


# 2. Función de Tipo de Cambio con "Cero Costo"
@st.cache_data(ttl=21600)  # 6h: 4 llamadas/día = 120/mes, lejos del límite gratuito
def get_exchange_rate() -> float:
    """
    Obtiene el tipo de cambio EUR -> PEN.

    Cache 6h: con 4 llamadas/día estamos en ~120/mes, muy por debajo del
    plan gratuito de exchangerate-api (1500 req/mes).

    Si la API falla, registra warning y usa el fallback (env o default).
    Útil monitorearlo en Cloud Logging para detectar caídas sostenidas.
    """
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return float(response.json()["rates"]["PEN"])
    except Exception:
        fallback = float(os.getenv("FALLBACK_EUR_PEN_RATE", DEFAULT_FALLBACK_EUR_PEN))
        logger.warning(
            "exchangerate-api no respondió; usando fallback EUR/PEN=%.4f. "
            "Cualquier cálculo de presupuesto durante esta ventana usará esta tasa.",
            fallback,
        )
        return fallback


# 3. Utilidad para convertir montos
def convert_eur_to_pen(amount_eur):
    """Convierte euros a soles usando el rate cacheado."""
    rate = get_exchange_rate()
    return amount_eur * rate