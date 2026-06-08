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
        "fecha": "18 julio 2026 (Sábado, bus nocturno) → llega 19 jul",
        "emoji_origen": "🇪🇸",
        "emoji_destino": "🇫🇷",
        "operador": "ALSA (bus nocturno)",
        "salida": "23:00 (Estación Sur - Méndez Álvaro)",
        "llegada": "~05:00 del 19 jul (Bayonne)",
        "duracion": "~6h",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "~€39",
        "precio_familia": "€117.91",
        "precio_pen": "~S/.472",
        "clase": "Bus turista",
        "reservar_url": "https://www.alsa.es",
        "alternativa_url": "https://www.flixbus.es/rutas/madrid-bayona",
        "estado": "⏳ Por reservar",
        "consejos": [
            "No hay tren nocturno directo Madrid–Bayona; la opción real es bus (Alsa/FlixBus)",
            "Sale 23:00 del 18 y llega ~05:00 del 19 — lleguen ~30 min antes a Méndez Álvaro",
            "Lleven almohada de cuello y abrigo: se duerme en el bus",
            "El hospedaje en Bayona es familiar, así que el check-in puede esperar a la mañana",
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
        "operador": "TGV INOUI (SNCF)",
        "salida": "10:00 (Gare de Bayonne)",
        "llegada": "14:30 (Gare Montparnasse, París)",
        "duracion": "~4h 30min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "~€78",
        "precio_familia": "€235.19",
        "precio_pen": "~S/.941",
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
        "operador": "Eurostar",
        "salida": "08:50 (Gare du Nord, París)",
        "llegada": "10:20 (Bruxelles-Midi)",
        "duracion": "~1h 30min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "~€59",
        "precio_familia": "€177.49",
        "precio_pen": "~S/.710",
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
        "fecha": "27 julio 2026 (Lunes)",
        "emoji_origen": "🇧🇪",
        "emoji_destino": "🇳🇱",
        "operador": "Eurostar",
        "salida": "08:20 (Bruxelles-Midi)",
        "llegada": "10:20 (Amsterdam Centraal)",
        "duracion": "~2h",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "~€62",
        "precio_familia": "€186.49",
        "precio_pen": "~S/.746",
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
        "operador": "Iberia 15:00 (recomendado) o KLM",
        "salida": "15:00 (AMS Schiphol)",
        "llegada": "17:40 (Madrid Barajas T4 con Iberia)",
        "duracion": "~2h 35min",
        "cambio": "Vuelo directo",
        "precio_pp": "~€204",
        "precio_familia": "€613.19 (Iberia 15:00)",
        "precio_pen": "~S/.2,453",
        "clase": "Económica",
        "reservar_url": "https://www.iberia.com",
        "alternativa_url": "https://www.skyscanner.com",
        "estado": "⏳ Por reservar",
        "consejos": [
            "OJO: este vuelo y el MAD→LIM de Air Europa (UX175, 23:45, sale de la T1) son TICKETS SEPARADOS, sin protección de conexión",
            "El de Lima sale de la T1: KLM aterriza en la T2 (al lado, se va caminando); Iberia aterriza en la T4 (bus entre terminales, ~15–20 min)",
            "Iberia 15:00 (€613.19) cuesta casi igual que el KLM 17:00 (€607.99) y da 5–6h de margen: con ese colchón el bus T4→T1 no es problema",
            "KLM 15:00 (€649.99, €37 más) te deja en la T2, más cómodo; cualquiera de los dos a las 15:00 es seguro",
            "Recoge las maletas y vuelve a hacer check-in internacional en la T1 (cierra ~22:45)",
        ],
        "color": "purple",
    },
]

# ── Resumen de costos ──────────────────────────────────────────────────────
def mostrar_resumen_costos():
    st.subheader("💰 Resumen de Costos de Transporte")
    total_min = round(sum([117.91, 235.19, 177.49, 186.49, 613.19]), 2)  # vuelo Iberia 15:00
    total_max = round(sum([117.91, 235.19, 177.49, 186.49, 649.99]), 2)  # vuelo KLM 15:00

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
            label = (
                f"{ruta['emoji_origen']} {ruta['origen']} → "
                f"{ruta['emoji_destino']} {ruta['destino']}  ·  📅 {ruta['fecha']}"
            )
            with st.expander(label, expanded=False):
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

                st.markdown("**💡 Consejos para este trayecto:**")
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
                "El bus nocturno Madrid→Bayona (sale 23:00) llega ~05:00; el hospedaje es familiar, descansen al llegar",
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
