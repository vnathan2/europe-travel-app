# modules/train_optimizer.py
# Módulo 7: Train-Route Optimizer
# Rutas de tren del viaje con horarios, precios y links de reserva

import streamlit as st

from utils.price_helper import mostrar_precio

# ── Rutas del viaje ────────────────────────────────────────────────────────
RUTAS = [
    {
        "id": "mad_bay",
        "origen": "Madrid",
        "destino": "Bayona",
        "fecha": "19 julio 2026 (Domingo)",
        "emoji_origen": "🇪🇸",
        "emoji_destino": "🇫🇷",
        "operador": "Renfe AVE + SNCF",
        "salida": "~08:00 (Estación Atocha)",
        "llegada": "~13:30 (Gare de Bayonne)",
        "duracion": "~5h 30min",
        "cambio": "Hendaya (Francia) — cambio de tren",
        "precio_pp": "€70–80",
        "precio_familia": "€210–240",
        "precio_pen": "S/.840–960",
        "clase": "Turista",
        "reservar_url": "https://www.renfe.com/es/es/viajar/informacion-util/billetes-internacionales",
        "alternativa_url": "https://www.sncf-connect.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "Reserva con al menos 2 meses de anticipación — los precios suben mucho",
            "El cambio en Hendaya es rápido pero asegúrate de tener las maletas listas",
            "Lleva snacks — el coche restaurante es caro",
            "El billete Renfe cubre hasta Hendaya, el SNCF desde Hendaya a Bayona",
        ],
        "color": "red",
    },
    {
        "id": "bay_par",
        "origen": "Bayona",
        "destino": "París",
        "fecha": "21 julio 2026 (Martes) 🎂 Cumpleaños Mamá",
        "emoji_origen": "🇫🇷",
        "emoji_destino": "🇫🇷",
        "operador": "TGV (SNCF)",
        "salida": "~08:00 (Gare de Bayonne)",
        "llegada": "~12:30–13:00 (Gare Montparnasse, París)",
        "duracion": "~4h 30min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "€60–70",
        "precio_familia": "€180–210",
        "precio_pen": "S/.720–840",
        "clase": "Turista (2ª clase)",
        "reservar_url": "https://www.sncf-connect.com",
        "alternativa_url": "https://www.trainline.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "El TGV es puntual — llega 15 min antes al andén",
            "Reserva asientos juntos — los trenes TGV tienen asientos numerados",
            "Este día es especial — considera reservar 1ª clase como regalo de cumpleaños",
            "Desde Gare Montparnasse al centro de París: taxi ~€20-25 o metro línea 6",
        ],
        "color": "blue",
    },
    {
        "id": "par_bru",
        "origen": "París",
        "destino": "Bruselas",
        "fecha": "25 julio 2026 (Sábado)",
        "emoji_origen": "🇫🇷",
        "emoji_destino": "🇧🇪",
        "operador": "Eurostar / Thalys",
        "salida": "~09:00 (Gare du Nord, París)",
        "llegada": "~10:30 (Bruxelles-Midi)",
        "duracion": "~1h 30min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "€35–50",
        "precio_familia": "€105–150",
        "precio_pen": "S/.420–600",
        "clase": "Turista (Standard)",
        "reservar_url": "https://www.eurostar.com",
        "alternativa_url": "https://www.thalys.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "Hay control de pasaportes — llega 45 min antes de la salida",
            "La Gare du Nord está en el centro de París — fácil de llegar en metro",
            "El trayecto es muy corto — puedes llevar el desayuno del hotel",
            "Desde Bruxelles-Midi al centro: taxi ~€20 o metro línea 2/6",
        ],
        "color": "orange",
    },
    {
        "id": "bru_ams",
        "origen": "Bruselas",
        "destino": "Ámsterdam",
        "fecha": "26 julio 2026 (Domingo)",
        "emoji_origen": "🇧🇪",
        "emoji_destino": "🇳🇱",
        "operador": "Eurostar / IC Direct",
        "salida": "~09:00 (Bruxelles-Midi)",
        "llegada": "~11:00 (Amsterdam Centraal)",
        "duracion": "~2h",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "€30–50",
        "precio_familia": "€90–150",
        "precio_pen": "S/.360–600",
        "clase": "Turista",
        "reservar_url": "https://www.eurostar.com",
        "alternativa_url": "https://www.nsinternational.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "Amsterdam Centraal está en el corazón de la ciudad — todo a pie",
            "El IC Direct no requiere reserva previa — puedes comprar el día antes",
            "El Eurostar sí requiere reserva y control de pasaportes",
            "Desde Centraal a la casa familiar: coordina con anticipación",
        ],
        "color": "green",
    },
    {
        "id": "ams_mad",
        "origen": "Ámsterdam",
        "destino": "Madrid",
        "fecha": "30 julio 2026 (Jueves) — REGRESO",
        "emoji_origen": "🇳🇱",
        "emoji_destino": "🇪🇸",
        "operador": "Vuelo low-cost (Vueling/Iberia/Ryanair)",
        "salida": "~15:00–17:00 (AMS Schiphol)",
        "llegada": "~18:00–20:00 (Madrid Barajas T4)",
        "duracion": "~2h 30min",
        "cambio": "Vuelo directo",
        "precio_pp": "€80–120",
        "precio_familia": "€240–360",
        "precio_pen": "S/.960–1,440",
        "clase": "Económica",
        "reservar_url": "https://www.vueling.com",
        "alternativa_url": "https://www.skyscanner.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "Llega al aeropuerto Schiphol 2.5h antes — es grande y los controles son lentos",
            "Vueling y Iberia Express tienen más conexiones Madrid-Ámsterdam",
            "Confirma que la maleta de bodega está incluida — muchas low-cost la cobran extra",
            "Desde Barajas T4 tienes el vuelo MAD→LIM a las 23:45 — hay tiempo suficiente",
        ],
        "color": "purple",
    },
]

# ── Resumen de costos ──────────────────────────────────────────────────────
def mostrar_resumen_costos():
    st.subheader("💰 Resumen de Costos de Transporte")
    total_min = sum([210, 180, 105, 90, 240])
    total_max = sum([240, 210, 150, 150, 360])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total mínimo familia", mostrar_precio(f"€{total_min}", "—"))
    col2.metric("Total máximo familia", mostrar_precio(f"€{total_max}", "—"))
    col3.metric("Promedio por persona", mostrar_precio(f"€{int((total_min+total_max)/2/3)}", "—"))

# ── Tabla compacta de detalles ─────────────────────────────────────────────
def tabla_detalles(ruta: dict):
    precio_familia = mostrar_precio(ruta['precio_familia'])
    precio_pen     = mostrar_precio(ruta['precio_pen'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🕐 **Salida**")
        st.markdown(f"`{ruta['salida']}`")
    with col2:
        st.markdown("🏁 **Llegada**")
        st.markdown(f"`{ruta['llegada']}`")
    with col3:
        st.markdown("💶 **Precio familia**")
        st.markdown(f"**:blue[{precio_familia}]**")
    with col4:
        st.markdown("🪙 **En soles**")
        st.markdown(f"**:green[{precio_pen}]**")

# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("🚄 Train-Route Optimizer")
    st.caption("Rutas de transporte del viaje con horarios, precios y links de reserva")

    st.warning("⏳ Tienes **5 trayectos por reservar**. Hazlo con anticipación para mejores precios.")

    tab_rutas, tab_resumen, tab_tips = st.tabs([
        "🗺️ Rutas del Viaje", "💰 Resumen de Costos", "💡 Tips de Viaje en Tren"
    ])

    # ── TAB 1: Rutas ───────────────────────────────────────────────────────
    with tab_rutas:
        for ruta in RUTAS:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.subheader(
                        f"{ruta['emoji_origen']} {ruta['origen']} → "
                        f"{ruta['emoji_destino']} {ruta['destino']}"
                    )
                    st.caption(f"📅 {ruta['fecha']}")
                with col2:
                    st.write(f"🚄 **{ruta['operador']}**")
                    st.write(f"⏱️ {ruta['duracion']}")
                with col3:
                    st.write(ruta["estado"])

                st.divider()

                # Tabla compacta de detalles
                tabla_detalles(ruta)

                if ruta["cambio"] != "Directo — sin cambio de tren":
                    st.warning(f"🔄 Cambio: {ruta['cambio']}")
                else:
                    st.success(f"✅ {ruta['cambio']}")

                with st.expander("💡 Consejos para este trayecto"):
                    for consejo in ruta["consejos"]:
                        st.write(f"• {consejo}")

                col1, col2 = st.columns(2)
                with col1:
                    st.link_button(
                        f"🎫 Reservar en {ruta['operador'].split('/')[0].strip()}",
                        ruta["reservar_url"],
                        use_container_width=True,
                        type="primary"
                    )
                with col2:
                    st.link_button(
                        "🔍 Ver alternativas",
                        ruta["alternativa_url"],
                        use_container_width=True,
                    )

                reservado = st.checkbox(
                    "✅ Ya reservé este trayecto",
                    key=f"reservado_{ruta['id']}"
                )
                if reservado:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input(
                            "Número de reserva / localizador:",
                            key=f"localizador_{ruta['id']}",
                            placeholder="Ej: ABC123"
                        )
                    with col2:
                        st.text_input(
                            "Hora exacta de salida:",
                            key=f"hora_{ruta['id']}",
                            placeholder="Ej: 08:15"
                        )
                    st.success("✅ ¡Trayecto reservado! Guarda el localizador.")

    # ── TAB 2: Resumen ─────────────────────────────────────────────────────
    with tab_resumen:
        mostrar_resumen_costos()

    # ── TAB 3: Tips ────────────────────────────────────────────────────────
    with tab_tips:
        st.subheader("💡 Tips Generales para Viajar en Tren por Europa")

        with st.expander("🎫 Reservas y Billetes", expanded=True):
            tips = [
                "Reserva con 2-3 meses de anticipación para mejores precios",
                "Los precios suben drásticamente en los últimos 30 días",
                "El Interrail Pass puede ser conveniente si tienes muchos trayectos",
                "Descarga los tickets en PDF — guárdalos offline en el celular",
                "Trainline y Omio comparan precios entre operadores",
            ]
            for tip in tips:
                st.write(f"• {tip}")

        with st.expander("🧳 Equipaje en el tren"):
            tips = [
                "Los trenes europeos no tienen límite de equipaje pero sí de espacio",
                "Pon las maletas grandes en el portaequipajes sobre el asiento",
                "Nunca pierdas de vista las maletas — especialmente en estaciones",
                "Las mochilas pequeñas van debajo del asiento delantero",
                "En el TGV hay espacio para maletas al inicio de cada vagón",
            ]
            for tip in tips:
                st.write(f"• {tip}")

        with st.expander("⏰ Puntualidad y Conexiones"):
            tips = [
                "Los trenes europeos son muy puntuales — llega al andén 10 min antes",
                "Si el tren llega tarde y pierdes conexión, el operador te busca alternativa",
                "El cambio en Hendaya (Madrid→Bayona) requiere bajar y subir con maletas",
                "Los Eurostar tienen control de pasaportes — llega 45 min antes mínimo",
                "Guarda siempre el ticket hasta salir de la estación destino",
            ]
            for tip in tips:
                st.write(f"• {tip}")

        with st.expander("📱 Apps útiles para el viaje en tren"):
            apps = [
                ("Trainline", "Compra tickets de múltiples operadores europeos"),
                ("SNCF Connect", "Trenes en Francia — TGV, Intercités"),
                ("Renfe", "Trenes en España — AVE, Alvia"),
                ("Eurostar", "Trenes internacionales UK-Europa"),
                ("Omio", "Comparador de trenes, buses y vuelos"),
                ("DB Navigator", "Trenes alemanes — funciona bien en toda Europa"),
            ]
            for app, desc in apps:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**{app}**")
                with col2:
                    st.write(desc)
