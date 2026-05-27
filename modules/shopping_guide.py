# modules/shopping_guide.py
# 🛒 Shopping Guide — Tiendas, ofertas y souvenirs por ciudad
# Categorías: Ropa, Zapatos/Carteras, Souvenirs, Tecnología/Comics/Anime,
#             Gastronomía para llevar, Perfumes/Cosméticos, Joyería, Outlets

import json
import os

import requests
import streamlit as st

from utils.price_helper import mostrar_precio

# ══════════════════════════════════════════════════════════════════════════
# LADY FALLBACK — búsqueda inteligente vía Gemini + Tavily
# ══════════════════════════════════════════════════════════════════════════

def _buscar_con_lady(busqueda: str, ciudad: str, para: str) -> str:
    """
    Cuando la búsqueda local no encuentra resultados,
    Lady usa Tavily + Gemini para buscar en internet.
    """
    try:
        # 1. Buscar con Tavily
        from tavily import TavilyClient

        from utils.gcp_client import get_secret

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            api_key = get_secret("TAVILY_API_KEY")

        client = TavilyClient(api_key=api_key)

        # Construir query orientada a compras
        ciudad_en = {
            "Madrid": "Madrid Spain", "Bayona": "Bayonne France",
            "París": "Paris France", "Bruselas": "Brussels Belgium",
            "Ámsterdam": "Amsterdam Netherlands", "Europa": "Europe"
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
        # 2. Lady procesa y formatea con Gemini
        import google.generativeai as genai

        from utils.gcp_client import get_secret as gs

        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            gemini_key = gs("GEMINI_API_KEY")
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

        respuesta = model.generate_content(prompt).text
        return respuesta

    except Exception as e:
        return f"🐾 ¡Woof! No pude conectarme ahora mismo para buscar. Error: {e}\n\nIntenta buscar directamente en Google Maps: **{busqueda} {ciudad}**"

# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def maps_url(nombre: str, ciudad: str) -> str:
    q = requests.utils.quote(f"{nombre} {ciudad}")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

def precio_tag(nivel: int) -> str:
    return "€" * nivel + "·" * (3 - nivel)

CATEGORIA_EMOJI = {
    "Ropa y Moda":          "👗",
    "Zapatos y Carteras":   "👠",
    "Souvenirs":            "🎁",
    "Tecnología / Geek":    "🎮",
    "Gastronomía":          "🍫",
    "Perfumes y Cosméticos":"💄",
    "Joyería y Accesorios": "💎",
    "Outlets y Ofertas":    "🏷️",
}

PARA_QUIEN = {
    "Jonathan": "👑",
    "Camila":   "🎀",
    "Giovanna": "🌹",
    "Todos":    "👨‍👩‍👧",
}

# ══════════════════════════════════════════════════════════════════════════
# BASE DE DATOS DE TIENDAS
# ══════════════════════════════════════════════════════════════════════════

def _cargar_tiendas() -> dict:
    # Catalogo de tiendas en data/shopping.json (editable sin tocar Python ni redeploy de codigo).
    ruta = os.path.join(os.path.dirname(__file__), "..", "data", "shopping.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


TIENDAS = _cargar_tiendas()

# ══════════════════════════════════════════════════════════════════════════
# UI PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

def render_tienda_card(tienda: dict, ciudad: str):
    """Renderiza una card de tienda."""
    with st.container(border=True):
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            cat_emoji = CATEGORIA_EMOJI.get(tienda["categoria"], "🛍️")
            st.markdown(f"### {cat_emoji} {tienda['nombre']}")
            st.caption(f"📍 {tienda['direccion']}")
        with col2:
            st.metric("Rating", f"{tienda['rating']}/5")
        with col3:
            niveles = {"€": "Económico", "€€": "Moderado", "€€€": "Lujo"}
            precio_str = "€" * tienda["precio"]
            st.metric("Precio", mostrar_precio(precio_str), mostrar_precio(niveles.get(precio_str, ""), ""))

        # Para quién
        para_tags = " ".join([
            f"{PARA_QUIEN.get(p, '👤')} {p}"
            for p in tienda["para"]
        ])
        st.caption(f"**Para:** {para_tags}")

        # Horario
        st.caption(f"🕐 {tienda['horario']}")

        st.divider()

        # Productos destacados
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**🛍️ Qué comprar:**")
            for prod in tienda["productos"]:
                st.caption(f"• {prod}")

        with col2:
            # Botón Maps
            url = maps_url(tienda["nombre"], ciudad)
            st.link_button(
                "📍 Ver en Maps",
                url,
                use_container_width=True,
                type="primary"
            )
            st.write("")

        # Tip de ahorro
        if tienda.get("tip"):
            st.info(tienda["tip"])

        # Comentario
        if tienda.get("comentario"):
            st.caption(f"💬 _{tienda['comentario']}_")


def mostrar():
    st.title("🛒 Shopping Guide")
    st.caption("Tiendas, ofertas y souvenirs curados para la familia — por ciudad y categoría")

    # ── Filtros en la parte superior ──────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        ciudad_sel = st.selectbox(
            "📍 Ciudad:",
            ["Todas"] + list(TIENDAS.keys()),
            key="shop_ciudad"
        )
    with col2:
        todas_cats = sorted(set(
            t["categoria"]
            for tiendas in TIENDAS.values()
            for t in tiendas
        ))
        cat_sel = st.selectbox(
            "🏷️ Categoría:",
            ["Todas"] + todas_cats,
            key="shop_cat"
        )
    with col3:
        persona_sel = st.selectbox(
            "👤 Para quién:",
            ["Todos", "Jonathan", "Camila", "Giovanna"],
            key="shop_persona"
        )

    # Búsqueda rápida
    busqueda = st.text_input(
        "🔍 Buscar tienda o producto...",
        placeholder="ej: chocolate, manga, perfume...",
        key="shop_busqueda"
    )

    st.divider()

    # ── Aplicar filtros ───────────────────────────────────────────────────
    ciudades_mostrar = (
        list(TIENDAS.keys()) if ciudad_sel == "Todas"
        else [ciudad_sel]
    )

    total_tiendas = 0

    for ciudad in ciudades_mostrar:
        tiendas_ciudad = TIENDAS.get(ciudad, [])

        # Filtrar por categoría
        if cat_sel != "Todas":
            tiendas_ciudad = [t for t in tiendas_ciudad if t["categoria"] == cat_sel]

        # Filtrar por persona
        if persona_sel != "Todos":
            tiendas_ciudad = [t for t in tiendas_ciudad if persona_sel in t["para"]]

        # Filtrar por búsqueda
        if busqueda:
            busq = busqueda.lower()
            tiendas_ciudad = [
                t for t in tiendas_ciudad
                if busq in t["nombre"].lower()
                or busq in t["comentario"].lower()
                or any(busq in p.lower() for p in t["productos"])
                or busq in t["categoria"].lower()
            ]

        if not tiendas_ciudad:
            continue

        total_tiendas += len(tiendas_ciudad)

        # Header de ciudad
        CIUDAD_EMOJIS = {
            "Madrid": "🇪🇸", "Bayona": "🇫🇷", "París": "🇫🇷",
            "Bruselas": "🇧🇪", "Ámsterdam": "🇳🇱"
        }
        emoji = CIUDAD_EMOJIS.get(ciudad, "📍")

        st.markdown(f"## {emoji} {ciudad}")
        st.caption(f"{len(tiendas_ciudad)} tienda(s) encontrada(s)")

        # Agrupar por categoría dentro de la ciudad
        categorias_ciudad = dict()
        for t in tiendas_ciudad:
            cat = t["categoria"]
            if cat not in categorias_ciudad:
                categorias_ciudad[cat] = []
            categorias_ciudad[cat].append(t)

        for cat, tiendas_cat in categorias_ciudad.items():
            cat_emoji = CATEGORIA_EMOJI.get(cat, "🛍️")
            with st.expander(f"{cat_emoji} {cat} — {len(tiendas_cat)} tienda(s)", expanded=True):
                for tienda in tiendas_cat:
                    render_tienda_card(tienda, ciudad)

        st.divider()

    if total_tiendas == 0:
        if busqueda:
            # ── Lady fallback: busca en internet ──────────────────────
            ciudad_busqueda = ciudad_sel if ciudad_sel != "Todas" else "Europa"
            st.warning(f"🔍 No encontré **'{busqueda}'** en mi base de datos para {ciudad_busqueda}.")
            st.markdown("### 🐾 Lady busca en internet por ti...")

            cache_key = f"lady_search_{busqueda}_{ciudad_busqueda}"
            if cache_key not in st.session_state:
                st.session_state[cache_key] = None

            if st.session_state[cache_key]:
                st.success("🐾 Lady encontró esto:")
                st.markdown(st.session_state[cache_key])
            else:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.caption(
                        f"Lady buscará tiendas de **'{busqueda}'** en **{ciudad_busqueda}** "
                        f"con direcciones, horarios y tips reales."
                    )
                with col2:
                    if st.button("🐾 Buscar con Lady", type="primary", use_container_width=True):
                        with st.spinner("🐾 Lady está olfateando las mejores tiendas..."):
                            resultado = _buscar_con_lady(busqueda, ciudad_busqueda, persona_sel)
                        st.session_state[cache_key] = resultado
                        st.rerun()
        else:
            st.info("🔍 No se encontraron tiendas con los filtros seleccionados. Prueba con otros filtros.")

    # ── Resumen de tips Tax Free ──────────────────────────────────────────
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
