# modules/night_life.py
# Módulo exclusivo ADMIN — Vida nocturna por ciudad + Coffee Shops Ámsterdam

import streamlit as st

# ── Datos: Discotecas y Bares ──────────────────────────────────────────────
BARES_DISCOTECAS = {
    "Madrid": [
        {
            "local": "Teatro Kapital",
            "direccion": "Calle de Atocha 125",
            "tipo": "Discoteca",
            "precio": "€20–30 entrada + consumo",
            "rating": "4.7/5",
            "comentario": "Club icónico de 7 plantas, cada una con música distinta, ambiente internacional.",
            "emoji": "🏛️",
        },
        {
            "local": "BarCo",
            "direccion": "Calle del Barco 34, Malasaña",
            "tipo": "Bar / Música en vivo",
            "precio": "€15–25",
            "rating": "4.6/5",
            "comentario": "Conciertos de jazz, funk y rock, ambiente alternativo.",
            "emoji": "🎸",
        },
        {
            "local": "El Viajero",
            "direccion": "Plaza de la Cebada 11, La Latina",
            "tipo": "Terraza / Bar",
            "precio": "€20–30",
            "rating": "4.5/5",
            "comentario": "Terraza con vistas, ideal para tarde-noche relajada.",
            "emoji": "🌙",
        },
    ],
    "Bayona": [
        {
            "local": "Le Caveau",
            "direccion": "Rue des Tonneliers 12",
            "tipo": "Bar / Pub",
            "precio": "€10–20",
            "rating": "4.5/5",
            "comentario": "Bar histórico en el centro, ambiente local y música variada.",
            "emoji": "🍺",
        },
        {
            "local": "Le Makila",
            "direccion": "Quai Galuperie 14",
            "tipo": "Discoteca",
            "precio": "€15–25",
            "rating": "4.4/5",
            "comentario": "Club popular entre jóvenes, música electrónica y latina.",
            "emoji": "🎵",
        },
        {
            "local": "Café des Pyrénées",
            "direccion": "Place des Basques",
            "tipo": "Bar",
            "precio": "€10–15",
            "rating": "4.3/5",
            "comentario": "Clásico café-bar con ambiente relajado, punto de encuentro local.",
            "emoji": "☕",
        },
    ],
    "París": [
        {
            "local": "Rex Club",
            "direccion": "5 Boulevard Poissonnière",
            "tipo": "Discoteca",
            "precio": "€20–30",
            "rating": "4.7/5",
            "comentario": "Referente de la electrónica en Europa, DJs internacionales.",
            "emoji": "🎧",
        },
        {
            "local": "Le Comptoir Général",
            "direccion": "80 Quai de Jemmapes",
            "tipo": "Bar cultural",
            "precio": "€20–35",
            "rating": "4.6/5",
            "comentario": "Espacio alternativo con decoración africana, cócteles creativos.",
            "emoji": "🍹",
        },
        {
            "local": "Le Baron",
            "direccion": "6 Avenue Marceau",
            "tipo": "Club exclusivo",
            "precio": "€30–50",
            "rating": "4.5/5",
            "comentario": "Ambiente sofisticado, acceso selectivo, música house y electro.",
            "emoji": "🥂",
        },
    ],
    "Bruselas": [
        {
            "local": "Fuse",
            "direccion": "Rue Blaes 208",
            "tipo": "Discoteca",
            "precio": "€20–30",
            "rating": "4.7/5",
            "comentario": "Club techno legendario, reconocido en Europa.",
            "emoji": "⚡",
        },
        {
            "local": "Delirium Café",
            "direccion": "Impasse de la Fidélité 4",
            "tipo": "Bar cervecero",
            "precio": "€15–25",
            "rating": "4.8/5",
            "comentario": "Más de 2000 cervezas en carta, ambiente festivo.",
            "emoji": "🍻",
        },
        {
            "local": "Spirito Brussels",
            "direccion": "Rue de Stassart 18",
            "tipo": "Discoteca",
            "precio": "€25–40",
            "rating": "4.6/5",
            "comentario": "Club en antigua iglesia, ambiente elegante y exclusivo.",
            "emoji": "🕍",
        },
    ],
    "Ámsterdam": [
        {
            "local": "Paradiso",
            "direccion": "Weteringschans 6-8",
            "tipo": "Sala de conciertos / Club",
            "precio": "€20–35",
            "rating": "4.8/5",
            "comentario": "Icono cultural, conciertos y fiestas nocturnas.",
            "emoji": "🎶",
        },
        {
            "local": "Melkweg",
            "direccion": "Lijnbaansgracht 234a",
            "tipo": "Sala de conciertos / Club",
            "precio": "€20–30",
            "rating": "4.7/5",
            "comentario": "Música variada, desde rock hasta electrónica.",
            "emoji": "🥛",
        },
        {
            "local": "Jimmy Woo",
            "direccion": "Korte Leidsedwarsstraat 18",
            "tipo": "Discoteca",
            "precio": "€25–40",
            "rating": "4.6/5",
            "comentario": "Club exclusivo, diseño asiático, ambiente sofisticado.",
            "emoji": "🀄",
        },
    ],
}

# ── Datos: Coffee Shops Ámsterdam ──────────────────────────────────────────
COFFEE_SHOPS = [
    {
        "shop": "The Bulldog",
        "direccion": "Oudezijds Voorburgwal 90, Barrio Rojo",
        "rating": "4.5/5",
        "productos": [
            {"producto": "Brownie clásico",            "precio": "€8 / S/.32",  "thc": "10–15 mg",            "comentario": "Suave, ideal principiantes"},
            {"producto": "Galleta infusionada",        "precio": "€7 / S/.28",  "thc": "10–20 mg",            "comentario": "Dulce, efecto moderado"},
            {"producto": "Pre-roll estándar",          "precio": "€10 / S/.40", "thc": "0.5–1 g flor",        "comentario": "Consumo inmediato, clásico turístico"},
            {"producto": "Bebida caliente infusionada","precio": "€6 / S/.24",  "thc": "5–10 mg",             "comentario": "Ligero, discreto"},
        ],
    },
    {
        "shop": "Grey Area",
        "direccion": "Oude Leliestraat 2, Jordaan",
        "rating": "4.7/5",
        "productos": [
            {"producto": "Chocolate artesanal",   "precio": "€10 / S/.40", "thc": "20–25 mg",    "comentario": "Potente, gourmet"},
            {"producto": "Caramelos infusionados","precio": "€6 / S/.24",  "thc": "5–10 mg",     "comentario": "Microdosis, discreto"},
            {"producto": "Flores premium (1g)",   "precio": "€12 / S/.48", "thc": "Alta potencia","comentario": "Variedades importadas"},
            {"producto": "Hash artesanal (1g)",   "precio": "€15 / S/.60", "thc": "Muy fuerte",  "comentario": "Tradicional, calidad alta"},
        ],
    },
    {
        "shop": "Dampkring",
        "direccion": "Handboogstraat 29, Centro",
        "rating": "4.6/5",
        "productos": [
            {"producto": "Space cake (choco/vainilla)", "precio": "€9 / S/.36",  "thc": "20–30 mg",            "comentario": "Muy fuerte, prolongado"},
            {"producto": "Muffin infusionado",          "precio": "€8 / S/.32",  "thc": "15–20 mg",            "comentario": "Potencia media"},
            {"producto": "Vaporizador (uso en local)",  "precio": "€15 / S/.60", "thc": "Alta biodisponibilidad","comentario": "Efecto rápido"},
        ],
    },
    {
        "shop": "Barney's Coffeeshop",
        "direccion": "Haarlemmerstraat 102",
        "rating": "4.7/5",
        "productos": [
            {"producto": "Muffin gourmet",           "precio": "€12 / S/.48", "thc": "25–30 mg",    "comentario": "Alta potencia, gourmet"},
            {"producto": "Trufas infusionadas",      "precio": "€12 / S/.48", "thc": "25–30 mg",    "comentario": "Premium, sofisticadas"},
            {"producto": "Flores galardonadas (1g)", "precio": "€14 / S/.56", "thc": "Alta potencia","comentario": "Cannabis Cup"},
            {"producto": "Hash de alta calidad (1g)","precio": "€16 / S/.64", "thc": "Muy potente", "comentario": "Reconocido internacionalmente"},
        ],
    },
    {
        "shop": "Paradox",
        "direccion": "Eerste Bloemdwarsstraat 2, Jordaan",
        "rating": "4.6/5",
        "productos": [
            {"producto": "Space cake casero",       "precio": "€8 / S/.32", "thc": "15–20 mg","comentario": "Artesanal, equilibrado"},
            {"producto": "Tarta pequeña infusionada","precio": "€9 / S/.36","thc": "15–20 mg","comentario": "Potencia media"},
            {"producto": "Infusión de hierbas",     "precio": "€6 / S/.24", "thc": "5–10 mg", "comentario": "Ligero, relajante"},
        ],
    },
    {
        "shop": "Green House",
        "direccion": "Tolstraat 91, Barrio Rojo",
        "rating": "4.7/5",
        "productos": [
            {"producto": "Cupcake infusionado",  "precio": "€10 / S/.40", "thc": "20–25 mg",    "comentario": "Balanceado"},
            {"producto": "Brownie premiado",     "precio": "€12 / S/.48", "thc": "25–30 mg",    "comentario": "Alta potencia, famoso"},
            {"producto": "Flores premiadas (1g)","precio": "€14 / S/.56", "thc": "Alta potencia","comentario": "Cannabis Cup"},
            {"producto": "Aceite comestible",    "precio": "€15 / S/.60", "thc": "30–40 mg",    "comentario": "Muy fuerte, extracto"},
        ],
    },
    {
        "shop": "Amnesia",
        "direccion": "Herengracht 133",
        "rating": "4.6/5",
        "productos": [
            {"producto": "Galleta dulce",         "precio": "€7 / S/.28", "thc": "10–15 mg","comentario": "Ligero, ideal acompañar café"},
            {"producto": "Muffin infusionado",    "precio": "€8 / S/.32", "thc": "15–20 mg","comentario": "Potencia media"},
            {"producto": "Bebida fría infusionada","precio": "€7 / S/.28","thc": "10–15 mg","comentario": "Refrescante"},
        ],
    },
    {
        "shop": "Abraxas",
        "direccion": "Jonge Roelensteeg 12, Centro",
        "rating": "4.5/5",
        "productos": [
            {"producto": "Space cake orgánico", "precio": "€9 / S/.36", "thc": "15–20 mg","comentario": "Natural, orgánico"},
            {"producto": "Galleta vegana",      "precio": "€8 / S/.32", "thc": "10–15 mg","comentario": "Suave, alternativa saludable"},
            {"producto": "Smoothie infusionado","precio": "€9 / S/.36", "thc": "15–20 mg","comentario": "Refrescante, diferente"},
        ],
    },
    {
        "shop": "Boerejongens",
        "direccion": "Baarsjesweg 239 (varios locales)",
        "rating": "4.8/5",
        "productos": [
            {"producto": "Bombón de chocolate","precio": "€12 / S/.48", "thc": "25–35 mg","comentario": "Premium, muy potente"},
            {"producto": "Brownie boutique",   "precio": "€12 / S/.48", "thc": "25–30 mg","comentario": "Alta potencia, gourmet"},
            {"producto": "Hash premium (1g)",  "precio": "€18 / S/.72", "thc": "Muy fuerte","comentario": "Boutique, calidad máxima"},
            {"producto": "Extracto/aceite",    "precio": "€20 / S/.80", "thc": "40–50 mg","comentario": "Potencia máxima"},
        ],
    },
    {
        "shop": "Hunter's Coffeeshop",
        "direccion": "Warmoesstraat 24, Barrio Rojo",
        "rating": "4.5/5",
        "productos": [
            {"producto": "Brownie básico",        "precio": "€6 / S/.24", "thc": "10–15 mg",   "comentario": "Económico, accesible"},
            {"producto": "Caramelos infusionados","precio": "€6 / S/.24", "thc": "5–10 mg",    "comentario": "Microdosis, discreto"},
            {"producto": "Pre-roll",              "precio": "€9 / S/.36", "thc": "0.5–1 g flor","comentario": "Consumo inmediato"},
        ],
    },
]

COLORES_CIUDAD = {
    "Madrid":    "#C8102E",
    "Bayona":    "#4A90D9",   # azul más claro que el original
    "París":     "#5B9BD5",   # azul Francia más visible
    "Bruselas":  "#F5A623",   # naranja dorado — visible en oscuro y claro
    "Ámsterdam": "#E8453C",
}

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("🌙 Night Life")
    st.caption("Vida nocturna exclusiva por ciudad + Coffee Shops de Ámsterdam")

    st.info(
        "🔒 **Contenido exclusivo** — Solo visible para el administrador.",
        icon="🔐"
    )

    tab_bares, tab_coffee = st.tabs([
        "🍸 Bares y Discotecas", "☕ Coffee Shops — Ámsterdam"
    ])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: BARES Y DISCOTECAS
    # ══════════════════════════════════════════════════════════════════════
    with tab_bares:
        st.subheader("🍸 Bares y Discotecas por Ciudad")

        # Métricas globales
        total_locales = sum(len(v) for v in BARES_DISCOTECAS.values())
        col1, col2, col3 = st.columns(3)
        col1.metric("📍 Ciudades", len(BARES_DISCOTECAS))
        col2.metric("🏛️ Locales", total_locales)
        col3.metric("🌟 Mejor rating", "4.8/5 — Delirium Café")

        st.divider()

        # Filtro ciudad
        ciudades = ["Todas"] + list(BARES_DISCOTECAS.keys())
        ciudad_sel = st.selectbox(
            "Filtrar por ciudad:", ciudades, key="nl_ciudad"
        )

        ciudades_mostrar = (
            list(BARES_DISCOTECAS.keys())
            if ciudad_sel == "Todas"
            else [ciudad_sel]
        )

        for ciudad in ciudades_mostrar:
            color = COLORES_CIUDAD.get(ciudad, "#333")
            st.markdown(
                f"<h3 style='color:{color}'>📍 {ciudad}</h3>",
                unsafe_allow_html=True
            )

            cols = st.columns(min(len(BARES_DISCOTECAS[ciudad]), 3))
            for i, local in enumerate(BARES_DISCOTECAS[ciudad]):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(
                            f"### {local['emoji']} {local['local']}"
                        )
                        st.caption(f"📍 {local['direccion']}")
                        st.markdown(f"**Tipo:** {local['tipo']}")
                        st.markdown(
                            f"**Precio:** `{local['precio']}`"
                        )
                        st.markdown(
                            f"**Rating:** ⭐ {local['rating']}"
                        )
                        st.info(local["comentario"])

                        maps_url = (
                            f"https://www.google.com/maps/search/"
                            f"{local['local'].replace(' ', '+')}+"
                            f"{ciudad.replace(' ', '+')}"
                        )
                        st.link_button(
                            "📍 Ver en Maps",
                            maps_url,
                            use_container_width=True
                        )
            st.divider()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2: COFFEE SHOPS
    # ══════════════════════════════════════════════════════════════════════
    with tab_coffee:
        st.subheader("☕ Coffee Shops — Ámsterdam")

        st.error(
            "🚫 **PROHIBIDO importar cannabis o derivados al Perú.** "
            "El transporte transfronterizo es delito según el Decreto Legislativo "
            "N° 1126 y la Ley N° 28305. La pena por tráfico ilícito de drogas en "
            "Perú es de 8 a 15 años de prisión (Código Penal Art. 296).",
            icon="🚫"
        )
        st.warning(
            "⚠️ **Marco legal en Países Bajos:** los coffee shops operan bajo "
            "una política de tolerancia (gedoogbeleid) para mayores de 18 años. "
            "El consumo está permitido únicamente dentro del local. Está prohibido "
            "fumar en espacios públicos y en muchos coffee shops de Ámsterdam "
            "el acceso a turistas se ha restringido en algunos barrios "
            "(verificar reglas vigentes al momento del viaje).",
            icon="⚠️"
        )
        st.info(
            "ℹ️ **Esta información es solo educativa** para consumo personal "
            "responsable y dentro del marco legal neerlandés. No constituye "
            "una recomendación de adquisición ni de transporte.",
            icon="ℹ️"
        )

        # Métricas
        total_productos = sum(len(s["productos"]) for s in COFFEE_SHOPS)
        col1, col2, col3 = st.columns(3)
        col1.metric("🏪 Coffee Shops", len(COFFEE_SHOPS))
        col2.metric("🛍️ Productos", total_productos)
        col3.metric("🏆 Mejor rated", "4.8/5 — Boerejongens")

        st.divider()

        # Filtro por tipo de producto
        tipos = ["Todos", "Edibles (comestibles)", "Flores / Pre-rolls", "Hash", "Bebidas", "Extractos"]
        tipo_sel = st.selectbox(
            "Filtrar por tipo:", tipos, key="nl_tipo"
        )

        def filtrar_productos(productos: list) -> list:
            if tipo_sel == "Todos":
                return productos
            filtros = {
                "Edibles (comestibles)": ["brownie", "galleta", "muffin", "cake", "cupcake", "tarta", "bombón", "chocolate", "trufa", "caramelo"],
                "Flores / Pre-rolls":    ["flor", "pre-roll"],
                "Hash":                  ["hash"],
                "Bebidas":               ["bebida", "smoothie", "infusión"],
                "Extractos":             ["aceite", "extracto", "vaporizador"],
            }
            keywords = filtros.get(tipo_sel, [])
            return [
                p for p in productos
                if any(k in p["producto"].lower() for k in keywords)
            ]

        for shop in COFFEE_SHOPS:
            productos_filtrados = filtrar_productos(shop["productos"])
            if not productos_filtrados:
                continue

            with st.expander(
                f"🏪 **{shop['shop']}** — ⭐ {shop['rating']} · {shop['direccion']}",
                expanded=False
            ):
                # Tabla de productos
                cols_header = st.columns([3, 2, 2, 3])
                cols_header[0].markdown("**Producto**")
                cols_header[1].markdown("**Precio**")
                cols_header[2].markdown("**THC aprox.**")
                cols_header[3].markdown("**Comentario**")
                st.divider()

                for prod in productos_filtrados:
                    cols_row = st.columns([3, 2, 2, 3])
                    cols_row[0].write(prod["producto"])
                    cols_row[1].write(f"`{prod['precio']}`")
                    cols_row[2].write(prod["thc"])
                    cols_row[3].caption(prod["comentario"])

                maps_url = (
                    f"https://www.google.com/maps/search/"
                    f"{shop['shop'].replace(' ', '+')}+Amsterdam"
                )
                st.link_button(
                    f"📍 {shop['shop']} en Google Maps",
                    maps_url,
                    use_container_width=False
                )