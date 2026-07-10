# modules/safety_guide.py
# 🛡️ Seguridad — Estafas comunes, zonas de precaución y tips por ciudad.
# Vista alineada con attractions.py y shopping_guide.py: cards con gradiente
# por ciudad, filtro superior, contenido claro y accionable.

import json
import os

import streamlit as st

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "safety.json",
)


@st.cache_data(show_spinner=False)
def _cargar_datos():
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_CIUDAD_TEMA = {
    "Madrid":    {"grad": "linear-gradient(135deg, #C8102E 0%, #8B0000 100%)", "emoji": "🇪🇸", "accent": "#FFD700"},
    "Bayona":    {"grad": "linear-gradient(135deg, #4A90D9 0%, #1a3a5c 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "París":     {"grad": "linear-gradient(135deg, #5B9BD5 0%, #C9A227 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "Bruselas":  {"grad": "linear-gradient(135deg, #F5A623 0%, #E8340A 100%)", "emoji": "🇧🇪", "accent": "#FFD700"},
    "Ámsterdam": {"grad": "linear-gradient(135deg, #E8453C 0%, #1F5C99 100%)", "emoji": "🇳🇱", "accent": "#FF6B35"},
}
_DEFAULT_TEMA = {"grad": "linear-gradient(135deg, #1A73E8 0%, #0D47A1 100%)", "emoji": "🛡️", "accent": "#FFD700"}

_RIESGO_COLOR = {
    "Bajo": "#15917F",
    "Bajo-Medio": "#E8A33D",
    "Medio": "#E8340A",
    "Alto": "#B00020",
}


def _card_resumen(ciudad: str, data: dict, tema: dict, nivel_riesgo: str, emergencia: str):
    accent = tema["accent"]
    riesgo_color = _RIESGO_COLOR.get(nivel_riesgo, accent)
    zonas_html = "".join(
        f"<div style='color:#cfd6e0; font-size:13px; line-height:1.6;'>⚠️ {z}</div>"
        for z in data.get("zonas_precaucion", [])
    )
    if not zonas_html:
        zonas_html = "<div style='color:#7f8a99; font-size:13px;'>Sin zonas de riesgo relevantes reportadas.</div>"

    st.markdown(f"""
    <div style="
        border-radius:16px; overflow:hidden; margin-bottom:16px;
        border:1px solid rgba(255,255,255,.08);
        box-shadow:0 4px 18px rgba(0,0,0,.28);
        background:#0e1420;
    ">
      <div style="background:{tema['grad']}; padding:16px 18px 14px 18px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="font-family:'Barlow Condensed','Barlow',sans-serif; font-weight:700;
                      font-size:24px; color:white;">{tema['emoji']} {ciudad}</div>
          <span style="background:{riesgo_color}; color:white; font-size:11px; font-weight:700;
                       padding:4px 12px; border-radius:20px;">Riesgo: {nivel_riesgo}</span>
        </div>
      </div>
      <div style="padding:14px 18px 16px 18px;">
        <div style="color:#cfd6e0; font-size:14px; line-height:1.5; margin-bottom:12px;">{data.get('resumen','')}</div>
        <div style="color:{accent}; font-size:12px; font-weight:700; letter-spacing:.5px; margin-bottom:6px;">📍 ZONAS DE PRECAUCIÓN</div>
        {zonas_html}
        <div style="color:#7f8a99; font-size:12px; margin-top:12px; border-top:1px solid rgba(255,255,255,.08); padding-top:10px;">
          🚨 Emergencias: {emergencia}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _card_estafa(estafa: dict, tema: dict):
    accent = tema["accent"]
    st.markdown(f"""
    <div style="
        border-radius:14px; overflow:hidden; margin-bottom:12px;
        border:1px solid rgba(255,255,255,.08); background:#0e1420;
        box-shadow:0 3px 14px rgba(0,0,0,.22);
    ">
      <div style="padding:14px 16px;">
        <div style="font-size:15px; font-weight:700; color:white; margin-bottom:8px;">⚠️ {estafa['nombre']}</div>
        <div style="color:#cfd6e0; font-size:13px; line-height:1.5; margin-bottom:8px;">
          <strong style="color:{accent};">Cómo funciona:</strong> {estafa['como_funciona']}
        </div>
        <div style="color:#cfd6e0; font-size:13px; line-height:1.5; border-left:3px solid {accent}; padding-left:10px;">
          <strong style="color:{accent};">Cómo evitarla:</strong> {estafa['como_evitar']}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def mostrar():
    data = _cargar_datos()
    ciudades = data["ciudades"]

    st.title("🛡️ Seguridad")
    st.caption("Zonas de precaución, estafas comunes y cómo evitarlas — por ciudad. Ninguna de estas ciudades tiene un riesgo real alto; son precauciones estándar de cualquier destino turístico.")

    opciones = ["🌍 Todas"] + [f"{_CIUDAD_TEMA.get(c, _DEFAULT_TEMA)['emoji']} {c}" for c in ciudades]
    sel = st.radio("Ciudad", opciones, horizontal=True, label_visibility="collapsed")
    ciudades_mostrar = ciudades if sel == "🌍 Todas" else [c for c in ciudades if c in sel]

    for ciudad in ciudades_mostrar:
        cdata = data["ciudades_data"].get(ciudad)
        if not cdata:
            continue
        tema = _CIUDAD_TEMA.get(ciudad, _DEFAULT_TEMA)
        nivel = data["nivel_riesgo"].get(ciudad, "—")
        emerg = data["emergencia"].get(ciudad, "—")

        _card_resumen(ciudad, cdata, tema, nivel, emerg)

        estafas = cdata.get("estafas", [])
        if estafas:
            accent = tema["accent"]
            st.markdown(
                f"<div style='color:{accent}; font-size:12px; font-weight:700; "
                f"letter-spacing:.5px; margin:4px 0 8px 4px;'>ESTAFAS COMUNES EN {ciudad.upper()}</div>",
                unsafe_allow_html=True,
            )
            col_izq, col_der = st.columns(2)
            for i, e in enumerate(estafas):
                with (col_izq if i % 2 == 0 else col_der):
                    _card_estafa(e, tema)

        tips = cdata.get("tips_generales", [])
        if tips:
            with st.expander(f"💡 Tips generales — {ciudad}", expanded=False):
                for t in tips:
                    st.markdown(f"- {t}")

        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    with st.expander("🆘 Qué hacer si les pasa algo", expanded=False):
        st.markdown("""
**Si les roban o clonan la tarjeta:**
1. Bloqueen la tarjeta de inmediato llamando a su banco (línea internacional 24h)
2. Guarden evidencia (recibo del cajero, hora, lugar)
3. Denuncien en la policía local — pidan copia del reporte, la necesitan para el seguro

**Si pierden el pasaporte:**
1. Denuncien primero en la policía local (piden copia del DNI/pasaporte para aceptar la denuncia en Bélgica)
2. Vayan a la embajada o consulado peruano más cercano con la denuncia
3. Contacten a su seguro de viaje (Interseguro, voucher A66-8JIEDM)

**Si son víctimas de una estafa:**
- No confronten al estafador, especialmente si están solos o en zona poco concurrida
- Aléjense de la situación con calma
- Reporten a la policía local si hubo pérdida de dinero o documentos

**Contacto de su seguro de viaje:** Interseguro, WhatsApp +18-632-042-770, assistance@ilsols.com
        """)