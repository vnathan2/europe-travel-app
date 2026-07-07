# modules/shopping_guide.py
# 🛒 Shopping Guide — Tiendas, ofertas y souvenirs por ciudad
# Vista alineada con el módulo Attractions: cards con gradiente por ciudad,
# rating en estrellas, badges de precio y de "para quién", productos, tip y
# link a Maps. Filtros: ciudad, categoría, persona y búsqueda. Conserva el
# fallback de Lady (Tavily + Gemini) y las guías de Tax Free / equipaje.

import json
import os

import requests
import streamlit as st

from utils.price_helper import mostrar_precio

# ══════════════════════════════════════════════════════════════════════════
# LADY FALLBACK — búsqueda inteligente vía Gemini + Tavily
# ══════════════════════════════════════════════════════════════════════════

def _buscar_con_lady(busqueda: str, ciudad: str, para: str) -> str:
    """Cuando la búsqueda local no encuentra resultados, Lady busca en internet."""
    try:
        from tavily import TavilyClient

        from utils.gcp_client import get_secret

        api_key = os.getenv("TAVILY_API_KEY") or get_secret("TAVILY_API_KEY")
        client = TavilyClient(api_key=api_key)

        ciudad_en = {
            "Madrid": "Madrid Spain", "Bayona": "Bayonne France",
            "París": "Paris France", "Bruselas": "Brussels Belgium",
            "Ámsterdam": "Amsterdam Netherlands", "Europa": "Europe",
        }.get(ciudad, ciudad)

        query = f"tiendas donde comprar {busqueda} en {ciudad_en} turistas dirección precio"
        response = client.search(query=query, search_depth="basic", max_results=5)

        resultados_txt = ""
        if response.get("answer"):
            resultados_txt += f"Respuesta directa: {response['answer']}\n\n"
        for r in response.get("results", []):
            resultados_txt += f"- {r.get('title','')}: {r.get('content','')[:200]}\n"
    except Exception as e:
        resultados_txt = f"No se pudo buscar en internet: {e}"

    try:
        import google.generativeai as genai

        from utils.gcp_client import get_secret as gs

        gemini_key = os.getenv("GEMINI_API_KEY") or gs("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        perfil_para = {
            "Jonathan": "Jonathan (46 años, le encantan: fútbol, tecnología, Transformers, comics, manga, anime, videojuegos, lucha libre)",
            "Camila":   "Camila (15 años, le encantan: anime, manga, kpop, One Piece, cultura japonesa, maquillaje, ropa, accesorios)",
            "Giovanna": "Giovanna (46 años, le encantan: carteras, zapatos, ropa, maquillaje, perfumes, gastronomía, ofertas)",
            "Todos":    "toda la familia (Jonathan, Giovanna y Camila)",
        }.get(para, "la familia")

        prompt = f"""Eres Lady 🐾, una schnauzer viajera experta en compras en Europa.

La familia busca: "{busqueda}" en {ciudad}
Búsqueda para: {perfil_para}

Información encontrada en internet:
{resultados_txt}

Basándote en esa información, dame una respuesta útil con:
1. 2-3 tiendas específicas donde encontrar "{busqueda}" en {ciudad}
   - Nombre de la tienda
   - Dirección aproximada o zona
   - Qué tienen exactamente
   - Rango de precio (€/€€/€€€)
2. Un tip de compra personalizado para {perfil_para}
3. Si hay algo especial o único que no conseguirían en Perú

Responde en español, con tu estilo simpático de perrita viajera, con emojis.
Máximo 300 palabras. Si no encontraste información suficiente, sé honesta y sugiere alternativas."""

        return model.generate_content(prompt).text
    except Exception as e:
        return (f"🐾 ¡Woof! No pude conectarme ahora mismo para buscar. Error: {e}\n\n"
                f"Intenta buscar directamente en Google Maps: **{busqueda} {ciudad}**")

# ══════════════════════════════════════════════════════════════════════════
# DATOS Y TEMA VISUAL (alineado con attractions.py y utils/ui_theme.py)
# ══════════════════════════════════════════════════════════════════════════

def _cargar_tiendas() -> dict:
    ruta = os.path.join(os.path.dirname(__file__), "..", "data", "shopping.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


TIENDAS = _cargar_tiendas()

_CIUDAD_TEMA = {
    "Madrid":    {"grad": "linear-gradient(135deg, #C8102E 0%, #8B0000 100%)", "emoji": "🇪🇸", "accent": "#FFD700"},
    "Bayona":    {"grad": "linear-gradient(135deg, #4A90D9 0%, #1a3a5c 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "París":     {"grad": "linear-gradient(135deg, #5B9BD5 0%, #C9A227 100%)", "emoji": "🇫🇷", "accent": "#E8C547"},
    "Bruselas":  {"grad": "linear-gradient(135deg, #F5A623 0%, #E8340A 100%)", "emoji": "🇧🇪", "accent": "#FFD700"},
    "Ámsterdam": {"grad": "linear-gradient(135deg, #E8453C 0%, #1F5C99 100%)", "emoji": "🇳🇱", "accent": "#FF6B35"},
}
_DEFAULT_TEMA = {"grad": "linear-gradient(135deg, #1A73E8 0%, #0D47A1 100%)", "emoji": "📍", "accent": "#FFD700"}

CATEGORIA_EMOJI = {
    "Ropa y Moda":          "👗",
    "Zapatos y Carteras":   "👠",
    "Souvenirs":            "🎁",
    "Tecnología / Geek":    "🎮",
    "Gastronomía":          "🍫",
    "Perfumes y Cosméticos": "💄",
    "Joyería y Accesorios": "💎",
    "Outlets y Ofertas":    "🏷️",
}

PARA_QUIEN = {
    "Jonathan": "👑",
    "Camila":   "🎀",
    "Giovanna": "🌹",
    "Todos":    "👨‍👩‍👧",
}


def _maps_url(nombre: str, ciudad: str) -> str:
    q = requests.utils.quote(f"{nombre} {ciudad}")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _estrellas(rating):
    if not rating:
        return "Sin calificación"
    llenas = int(rating)
    media = 1 if (rating - llenas) >= 0.5 else 0
    vacias = 5 - llenas - media
    return "★" * llenas + ("⯪" if media else "") + "☆" * vacias


def _card(t: dict, ciudad: str, tema: dict):
    """Card visual de una tienda, con el mismo estilo que Attractions."""
    accent = tema["accent"]
    rating = t.get("rating")
    cat_emoji = CATEGORIA_EMOJI.get(t["categoria"], "🛍️")

    rating_txt = (
        f"<span style='color:{accent}; font-size:15px; letter-spacing:1px;'>{_estrellas(rating)}</span>"
        f"<span style='color:#ddd; font-weight:700; margin-left:8px;'>{rating:.1f}</span>"
        if rating else
        "<span style='color:#999; font-size:13px;'>Sin calificación</span>"
    )

    nivel = int(t.get("precio", 1))
    precio_lbl = {1: "€ · Económico", 2: "€€ · Moderado", 3: "€€€ · Lujo"}.get(nivel, "€")
    precio_txt = mostrar_precio(precio_lbl)

    # Badges "para quién"
    para_badges = " ".join(
        f"<span style='background:rgba(255,255,255,.12); color:#e6ebf2; font-size:11px; "
        f"font-weight:600; padding:2px 9px; border-radius:20px; margin:0 2px 2px 0; "
        f"display:inline-block;'>{PARA_QUIEN.get(p, '👤')} {p}</span>"
        for p in t.get("para", [])
    )

    # Productos
    productos_html = "".join(
        f"<div style='color:#cfd6e0; font-size:13px; line-height:1.5;'>• {p}</div>"
        for p in t.get("productos", [])
    )

    tip = t.get("tip", "")
    tip_html = (
        f"<div style='color:#9aa4b2; font-size:12.5px; line-height:1.45; margin-top:10px; "
        f"border-left:3px solid {accent}; padding-left:10px;'>{tip}</div>"
        if tip else ""
    )
    comentario = t.get("comentario", "")
    coment_html = (
        f"<div style='color:#7f8a99; font-size:12.5px; font-style:italic; margin-top:8px;'>💬 {comentario}</div>"
        if comentario else ""
    )

    maps = _maps_url(t["nombre"], ciudad)

    st.markdown(f"""
    <div style="
        border-radius:16px; overflow:hidden; margin-bottom:16px;
        border:1px solid rgba(255,255,255,.08);
        box-shadow:0 4px 18px rgba(0,0,0,.28);
        background:#0e1420;
    ">
      <div style="background:{tema['grad']}; padding:16px 18px 14px 18px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
          <div style="font-size:32px; line-height:1;">{cat_emoji}</div>
          <span style="background:rgba(255,255,255,.15); color:white; font-size:11px;
                       font-weight:600; padding:3px 10px; border-radius:20px;">{t['categoria']}</span>
        </div>
        <div style="font-family:'Barlow Condensed','Barlow',sans-serif; font-weight:700;
                    font-size:23px; color:white; margin-top:8px; line-height:1.05;">
          {t['nombre']}
        </div>
      </div>
      <div style="padding:14px 18px 16px 18px;">
        <div style="margin-bottom:10px;">{rating_txt}</div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
          <span style="background:{accent}22; color:{accent}; font-size:13px; font-weight:700;
                       padding:5px 12px; border-radius:8px;">💶 {precio_txt}</span>
          <span style="background:rgba(255,255,255,.06); color:#cfd6e0; font-size:12px;
                       padding:5px 12px; border-radius:8px;">🕒 {t.get('horario','')}</span>
        </div>
        <div style="margin-bottom:10px;">{para_badges}</div>
        <div style="color:{accent}; font-size:12px; font-weight:700; letter-spacing:.5px; margin-bottom:4px;">🛍️ QUÉ COMPRAR</div>
        {productos_html}
        {tip_html}
        {coment_html}
        <div style="color:#7f8a99; font-size:12px; margin-top:12px;">
          📍 {t['direccion']} ·
          <a href="{maps}" target="_blank" style="color:{accent}; text-decoration:none;">Ver en Maps ↗</a>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# UI PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

def mostrar():
    st.title("🛒 Shopping Guide")
    st.caption("Tiendas, ofertas y souvenirs curados para la familia, por ciudad y categoría.")

    ciudades = list(TIENDAS.keys())

    # ── Filtros ────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        ciudad_sel = st.selectbox("📍 Ciudad", ["Todas"] + ciudades, key="shop_ciudad")
    with col2:
        todas_cats = sorted({t["categoria"] for tds in TIENDAS.values() for t in tds})
        cat_sel = st.selectbox("🏷️ Categoría", ["Todas"] + todas_cats, key="shop_cat")
    with col3:
        persona_sel = st.selectbox("👤 Para quién", ["Todos", "Jonathan", "Camila", "Giovanna"], key="shop_persona")

    busqueda = st.text_input(
        "🔍 Buscar tienda o producto",
        placeholder="ej: chocolate, manga, perfume...",
        key="shop_busqueda",
    )

    ciudades_mostrar = ciudades if ciudad_sel == "Todas" else [ciudad_sel]

    # ── Aplicar filtros ─────────────────────────────────────────────────────
    filtradas = {}
    for ciudad in ciudades_mostrar:
        tiendas_ciudad = TIENDAS.get(ciudad, [])
        if cat_sel != "Todas":
            tiendas_ciudad = [t for t in tiendas_ciudad if t["categoria"] == cat_sel]
        if persona_sel != "Todos":
            tiendas_ciudad = [t for t in tiendas_ciudad if persona_sel in t.get("para", [])]
        if busqueda:
            b = busqueda.lower()
            tiendas_ciudad = [
                t for t in tiendas_ciudad
                if b in t["nombre"].lower()
                or b in t.get("comentario", "").lower()
                or any(b in p.lower() for p in t.get("productos", []))
                or b in t["categoria"].lower()
            ]
        if tiendas_ciudad:
            filtradas[ciudad] = tiendas_ciudad

    total = sum(len(v) for v in filtradas.values())
    st.markdown(
        f"<div style='color:#9aa4b2; font-size:13px; margin:4px 0 14px 0;'>{total} tienda"
        f"{'s' if total != 1 else ''} encontrada{'s' if total != 1 else ''}</div>",
        unsafe_allow_html=True,
    )

    # ── Render de cards ──────────────────────────────────────────────────────
    for ciudad in ciudades_mostrar:
        items = filtradas.get(ciudad)
        if not items:
            continue
        tema = _CIUDAD_TEMA.get(ciudad, _DEFAULT_TEMA)

        if ciudad_sel == "Todas":
            st.markdown(
                f"<h3 style='margin:18px 0 10px 0;'>{tema['emoji']} {ciudad} "
                f"<span style='color:#7f8a99; font-size:14px; font-weight:400;'>· {len(items)} tiendas</span></h3>",
                unsafe_allow_html=True,
            )

        # Orden por rating desc
        items = sorted(items, key=lambda x: -(x.get("rating") or 0))
        col_izq, col_der = st.columns(2)
        for i, t in enumerate(items):
            with (col_izq if i % 2 == 0 else col_der):
                _card(t, ciudad, tema)

    # ── Fallback de Lady si no hay resultados ────────────────────────────────
    if total == 0:
        if busqueda:
            ciudad_busqueda = ciudad_sel if ciudad_sel != "Todas" else "Europa"
            st.warning(f"🔍 No encontré **'{busqueda}'** en mi base de datos para {ciudad_busqueda}.")
            st.markdown("### 🐾 Lady busca en internet por ti...")

            cache_key = f"lady_search_{busqueda}_{ciudad_busqueda}"
            st.session_state.setdefault(cache_key, None)

            if st.session_state[cache_key]:
                st.success("🐾 Lady encontró esto:")
                st.markdown(st.session_state[cache_key])
            else:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.caption(
                        f"Lady buscará tiendas de **'{busqueda}'** en **{ciudad_busqueda}** "
                        f"con direcciones, horarios y tips reales."
                    )
                with c2:
                    if st.button("🐾 Buscar con Lady", type="primary", use_container_width=True):
                        with st.spinner("🐾 Lady está olfateando las mejores tiendas..."):
                            st.session_state[cache_key] = _buscar_con_lady(busqueda, ciudad_busqueda, persona_sel)
                        st.rerun()
        else:
            st.info("🔍 No se encontraron tiendas con los filtros seleccionados. Prueba con otros filtros.")

    # ── Guías Tax Free y equipaje ────────────────────────────────────────────
    with st.expander("💡 Guía Tax Free — Recupera hasta 12% de tus compras", expanded=False):
        st.markdown("""
**¿Qué es el Tax Free?**
Como turistas fuera de la UE, pueden recuperar el IVA de sus compras al salir de Europa.

**Cómo funciona:**
1. Al comprar +€100 en una misma tienda, pide el **formulario de Tax Free**
2. La tienda sella el formulario
3. Al salir por el aeropuerto (Schiphol o Barajas), busca el mostrador **Tax Refund / Détaxe**
4. Sella el formulario con Aduana y cobra el reembolso en efectivo o tarjeta

**Cuánto recuperas:**
- España: ~13% del precio de compra
- Francia: ~12% del precio de compra
- Bélgica: ~13% del precio de compra
- Países Bajos: ~15% del precio de compra

**Tiendas que aplican:**
- El Corte Inglés ✅ | Galeries Lafayette ✅ | Louis Vuitton ✅
- Zara ✅ | Sephora ✅ | Camper ✅ | La mayoría de tiendas grandes

**💡 Tip:** Agrupa compras en menos tiendas para superar el mínimo más fácilmente.
        """)

    with st.expander("🧳 Tips para llevar compras a Lima", expanded=False):
        st.markdown("""
**Productos que pasan sin problema:**
- ✅ Ropa y calzado (sin restricción)
- ✅ Cosméticos y perfumes sellados
- ✅ Chocolate y dulces empaquetados
- ✅ Quesos al vacío sin corteza
- ✅ Jamón al vacío etiquetado
- ✅ Vinos y licores (límite: 3 litros por persona)
- ✅ Manga, comics y libros
- ✅ Figuras y juguetes
- ✅ Cerámica (bien embalada)

**Con declaración/certificado:**
- ⚠️ Bulbos de tulipán: necesitan certificado fitosanitario del vendedor

**Límite de equipaje sugerido:**
- Reserva al menos 10kg de capacidad de regreso para compras
- Las maletas adicionales en Iberia desde Ámsterdam cuestan ~€50
        """)