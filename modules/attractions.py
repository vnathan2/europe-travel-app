# modules/attractions.py
# Módulo: Attractions
# Catálogo visual de las principales atracciones del viaje, con filtro por
# ciudad. Datos en data/attractions.json (rating y reseñas de Google Places;
# precios reales para lo ya pagado, referencia por adulto para el resto).
#
# Patrón de render: def mostrar() — igual que el resto de módulos.
# Precios pasan por mostrar_precio() para respetar el rol FAMILIAR/ADMIN.

import json
import os

import streamlit as st

from utils.price_helper import mostrar_precio

# ── Carga de datos ──────────────────────────────────────────────────────────
_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "attractions.json",
)


@st.cache_data(show_spinner=False)
def _cargar_atracciones():
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Tema visual por ciudad (alineado con utils/ui_theme.py) ──────────────────
_CIUDAD_TEMA = {
    "Madrid":    {"grad": "linear-gradient(135deg, #C8102E 0%, #8B0000 100%)", "emoji": "🇪🇸", "accent": "#FFD700"},
    "Bayona":    {"grad": "linear-gradient(135deg, #4A90D9 0%, #1a3a5c 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "París":     {"grad": "linear-gradient(135deg, #5B9BD5 0%, #C9A227 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "Bruselas":  {"grad": "linear-gradient(135deg, #F5A623 0%, #E8340A 100%)", "emoji": "🇧🇪", "accent": "#FFD700"},
    "Ámsterdam": {"grad": "linear-gradient(135deg, #E8453C 0%, #1F5C99 100%)", "emoji": "🇳🇱", "accent": "#FF6B35"},
}
_DEFAULT_TEMA = {"grad": "linear-gradient(135deg, #1A73E8 0%, #0D47A1 100%)", "emoji": "📍", "accent": "#FFD700"}


def _estrellas(rating):
    if not rating:
        return "Sin calificación"
    llenas = int(rating)
    media = 1 if (rating - llenas) >= 0.5 else 0
    vacias = 5 - llenas - media
    return "★" * llenas + ("⯪" if media else "") + "☆" * vacias


def _card(a: dict, tema: dict):
    """Renderiza una card visual de una atracción."""
    accent = tema["accent"]
    rating = a.get("rating")
    rc = a.get("rating_count")
    rating_txt = (
        f"<span style='color:{accent}; font-size:15px; letter-spacing:1px;'>{_estrellas(rating)}</span>"
        f"<span style='color:#ddd; font-weight:700; margin-left:8px;'>{rating:.1f}</span>"
        f"<span style='color:#999; font-size:12px; margin-left:6px;'>({rc:,} reseñas)</span>"
        if rating else
        "<span style='color:#999; font-size:13px;'>Sin calificación de Google</span>"
    )

    precio_txt = mostrar_precio(a["precio_ref"])
    badge_pagado = (
        "<span style='background:#15917F; color:white; font-size:10px; font-weight:700; "
        "padding:3px 9px; border-radius:20px; letter-spacing:.5px;'>✓ PAGADO</span>"
        if a.get("pagado") else ""
    )
    badge_itin = (
        "<span style='background:rgba(255,255,255,.15); color:white; font-size:10px; "
        "font-weight:600; padding:3px 9px; border-radius:20px; margin-left:6px;'>📋 En el plan</span>"
        if a.get("en_itinerario") else ""
    )

    maps_url = f"https://www.google.com/maps/search/?api=1&query={a['lat']},{a['lng']}"

    st.markdown(f"""
    <div style="
        border-radius:16px; overflow:hidden; margin-bottom:16px;
        border:1px solid rgba(255,255,255,.08);
        box-shadow:0 4px 18px rgba(0,0,0,.28);
        background:#0e1420;
    ">
      <div style="background:{tema['grad']}; padding:16px 18px 14px 18px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
          <div style="font-size:34px; line-height:1;">{a.get('emoji','📍')}</div>
          <div style="text-align:right;">{badge_pagado}{badge_itin}</div>
        </div>
        <div style="font-family:'Barlow Condensed','Barlow',sans-serif; font-weight:700;
                    font-size:24px; color:white; margin-top:8px; line-height:1.05;">
          {a['nombre']}
        </div>
        <div style="color:rgba(255,255,255,.85); font-size:12px; font-weight:600;
                    text-transform:uppercase; letter-spacing:.8px; margin-top:2px;">
          {a['categoria']}
        </div>
      </div>
      <div style="padding:14px 18px 16px 18px;">
        <div style="margin-bottom:10px;">{rating_txt}</div>
        <div style="color:#cfd6e0; font-size:14px; line-height:1.5; margin-bottom:12px;">
          {a['detalle']}
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;">
          <span style="background:{accent}22; color:{accent}; font-size:13px; font-weight:700;
                       padding:5px 12px; border-radius:8px;">💶 {precio_txt}</span>
          <span style="background:rgba(255,255,255,.06); color:#cfd6e0; font-size:12px;
                       padding:5px 12px; border-radius:8px;">🕒 {a['horario']}</span>
        </div>
        <div style="color:#9aa4b2; font-size:13px; line-height:1.45; border-left:3px solid {accent};
                    padding-left:10px; margin-bottom:12px;">
          <strong style="color:{accent};">Tip:</strong> {a['tip']}
        </div>
        <div style="color:#7f8a99; font-size:12px;">
          📍 {a['direccion']} ·
          <a href="{maps_url}" target="_blank" style="color:{accent}; text-decoration:none;">Ver en Maps ↗</a>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _card_evento(e: dict, tema: dict):
    """Renderiza una card de evento/festival."""
    accent = tema["accent"]
    coincide = e.get("coincide")
    badge = (
        "<span style='background:#15917F; color:white; font-size:10px; font-weight:700; "
        "padding:3px 10px; border-radius:20px; letter-spacing:.5px;'>✓ COINCIDE CON TU VIAJE</span>"
        if coincide else
        "<span style='background:rgba(255,255,255,.12); color:#cfd6e0; font-size:10px; "
        "font-weight:600; padding:3px 10px; border-radius:20px;'>✗ Fuera de tus fechas</span>"
    )
    borde = "#15917F" if coincide else "rgba(255,255,255,.12)"
    nota = e.get("nota")
    nota_html = (
        f"<div style='color:#9aa4b2; font-size:12.5px; line-height:1.45; margin-top:8px; "
        f"border-left:3px solid {accent}; padding-left:10px;'>{nota}</div>"
        if nota else ""
    )
    st.markdown(f"""
    <div style="
        border-radius:14px; overflow:hidden; margin-bottom:14px;
        border:1px solid {borde}; background:#0e1420;
        box-shadow:0 3px 14px rgba(0,0,0,.25);
    ">
      <div style="padding:14px 16px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
          <div style="font-size:15px; font-weight:700; color:white; line-height:1.15;">
            {e.get('emoji','🎉')} {e['nombre']}
          </div>
          <div style="white-space:nowrap;">{badge}</div>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin:8px 0;">
          <span style="background:{accent}22; color:{accent}; font-size:12px; font-weight:700;
                       padding:3px 10px; border-radius:8px;">📅 {e['fechas']}</span>
          <span style="background:rgba(255,255,255,.06); color:#cfd6e0; font-size:12px;
                       padding:3px 10px; border-radius:8px;">{e['tipo']}</span>
        </div>
        <div style="color:#cfd6e0; font-size:13.5px; line-height:1.5;">{e['detalle']}</div>
        {nota_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── UI Principal ─────────────────────────────────────────────────────────────
def mostrar():
    data = _cargar_atracciones()
    atracciones = data["atracciones"]
    eventos = data.get("eventos", [])
    ciudades = data["ciudades"]

    st.title("🎭 Attractions")
    st.caption("Las principales atracciones del viaje, con calificación, precio, horario y tips.")

    # Filtro por ciudad
    opciones = ["🌍 Todas"] + [f"{_CIUDAD_TEMA.get(c, _DEFAULT_TEMA)['emoji']} {c}" for c in ciudades]
    sel = st.radio("Ciudad", opciones, horizontal=True, label_visibility="collapsed")

    if sel == "🌍 Todas":
        ciudades_mostrar = ciudades
    else:
        ciudades_mostrar = [c for c in ciudades if c in sel]

    total = sum(1 for a in atracciones if a["ciudad"] in ciudades_mostrar)
    pagadas = sum(1 for a in atracciones if a["ciudad"] in ciudades_mostrar and a.get("pagado"))
    ev_coincide = sum(1 for e in eventos if e["ciudad"] in ciudades_mostrar and e.get("coincide"))
    resumen = f"{total} atracciones · {pagadas} ya en el plan/pagadas"
    if ev_coincide:
        resumen += f" · 🎉 {ev_coincide} evento{'s' if ev_coincide != 1 else ''} durante tu viaje"
    st.markdown(
        f"<div style='color:#9aa4b2; font-size:13px; margin:4px 0 14px 0;'>{resumen}</div>",
        unsafe_allow_html=True,
    )

    for ciudad in ciudades_mostrar:
        items = [a for a in atracciones if a["ciudad"] == ciudad]
        if not items:
            continue
        tema = _CIUDAD_TEMA.get(ciudad, _DEFAULT_TEMA)

        if sel == "🌍 Todas":
            st.markdown(
                f"<h3 style='margin:18px 0 10px 0;'>{tema['emoji']} {ciudad} "
                f"<span style='color:#7f8a99; font-size:14px; font-weight:400;'>· {len(items)} atracciones</span></h3>",
                unsafe_allow_html=True,
            )

        # Eventos de la ciudad (primero los que coinciden con el viaje)
        eventos_ciudad = [e for e in eventos if e["ciudad"] == ciudad]
        if eventos_ciudad:
            eventos_ciudad.sort(key=lambda x: not x.get("coincide"))
            st.markdown(
                f"<div style='font-size:13px; font-weight:700; color:{tema['accent']}; "
                f"margin:6px 0 8px 0; letter-spacing:.5px;'>🎉 EVENTOS Y FESTIVALES</div>",
                unsafe_allow_html=True,
            )
            for e in eventos_ciudad:
                _card_evento(e, tema)
            st.markdown(
                f"<div style='font-size:13px; font-weight:700; color:{tema['accent']}; "
                f"margin:14px 0 8px 0; letter-spacing:.5px;'>📍 ATRACCIONES</div>",
                unsafe_allow_html=True,
            )

        # Orden: primero las que están en el plan, luego por rating desc
        items.sort(key=lambda x: (not x.get("en_itinerario"), -(x.get("rating") or 0)))

        col_izq, col_der = st.columns(2)
        for i, a in enumerate(items):
            with (col_izq if i % 2 == 0 else col_der):
                _card(a, tema)

    st.caption(
        "ℹ️ Calificación y nº de reseñas: Google Places. Precios en verde = monto real ya pagado (familia). "
        "Los precios 'ref.' son referencia por adulto; confirma el valor final en la web oficial de cada atracción."
    )