# modules/train_optimizer.py
# Módulo 7: Route Optimizer
# Rutas de tren del viaje con horarios, precios y links de reserva

import streamlit as st

from utils.price_helper import mostrar_precio

# ── Rutas del viaje ────────────────────────────────────────────────────────
RUTAS = [
{
        "id": "mad_bay_alsa",
        "origen": "Madrid", "destino": "Bayona",
        "fecha": "18 julio 2026 (Sábado, bus nocturno) → llega 19 jul",
        "emoji_origen": "🇪🇸", "emoji_destino": "🇫🇷",
        "operador": "ALSA (bus nocturno)",
        "salida": "23:00 (T4 Aeropuerto Madrid)",
        "llegada": "04:50 (Bayonne, Quai de Lesseps)",
        "duracion": "~6h",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "€39.30",
        "precio_familia": "€117.91",
        "precio_pen": "~S/.472",
        "clase": "Bus nocturno",
        "reservar_url": "https://www.alsa.com",
        "alternativa_url": "https://www.flixbus.es",
        "estado": "✅ Reservado",
        "consejos": [
            "Tickets ya comprados en ALSA",
            "Sale desde T4 Aeropuerto Barajas — taxi ~€35-40 desde Malasaña, salir ~20:30",
            "Lleven almohada de cuello y abrigo: se duerme en el bus",
            "Llegan a Quai de Lesseps 04:50 — familia los recoge",
        ],
        "color": "orange",
    },
    {
        "id": "bay_par",
        "origen": "Bayona",
        "destino": "París",
        "fecha": "21 julio 2026 (Martes) 🎂 Cumpleaños Mamá",
        "emoji_origen": "🇫🇷",
        "emoji_destino": "🇫🇷",
        "operador": "TGV INOUI 8534 (SNCF)",
        "salida": "10:11 (Gare de Bayonne)",
        "llegada": "14:22 (Gare Montparnasse 1 et 2, París)",
        "duracion": "4h 11min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "~€80 prom. (2 adultos + 1 joven)",
        "precio_familia": "€238.72 los 3 (Omio)",
        "precio_pen": "S/.~955",
        "clase": "2ª clase · Semi Flexible",
        "reservar_url": "https://www.omio.com",
        "alternativa_url": "https://www.sncf-connect.com",
        "estado": "✅ Reservado (RC3BKM)",
        "consejos": [
            "Reserva RC3BKM · Coche 16 · asientos 612, 613 y 616 (ya asignados)",
            "Sale Bayonne 10:11 · llega Montparnasse 1&2 14:22 · 4h11",
            "Billete en la app de Omio (también el PDF offline) · llegar a la estación con 20 min de margen",
            "Tarifa Semi Flexible: cambio/reembolso gratis hasta 7 días antes; después con cargo (€19 TGV)",
            "Desde Montparnasse al apartamento (15e, junto a Torre Eiffel): metro L6 hasta Dupleix · ~15 min",
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
        "salida": "08:55 (París Gare du Nord)",
        "llegada": "10:17 (Bruxelles-Midi)",
        "duracion": "1h 22min",
        "cambio": "Directo — sin cambio de tren",
        "precio_pp": "€72.00",
        "precio_familia": "€216.00 (Omio, incl. Savings Pass −€20)",
        "precio_pen": "S/.~864",
        "clase": "Standard (Turista)",
        "reservar_url": "https://www.omio.com",
        "alternativa_url": "https://www.eurostar.com",
        "estado": "✅ Reservado (X7FNNK)",
        "consejos": [
            "Reserva X7FNNK · Tren 9317 · Coche 7 · asientos Victor 12 / Giovanna 16 / Camila 15",
            "Llegar a Gare du Nord a las 08:25 (Eurostar deja de embarcar 10 min antes de salir)",
            "Sin control de pasaportes (zona Schengen); ten el QR y el DNI/pasaporte a mano",
            "Equipaje: 2 maletas (hasta 75 cm) + 1 de mano por persona",
            "Desde Bruxelles-Midi a tu apartamento en Louise: metro/tranvía ~10 min",
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
        "operador": "EuroCity Direct (Omio)",
        "salida": "07:49 (Bruxelles-Midi)",
        "llegada": "10:09 (Amsterdam Centraal)",
        "duracion": "2h 20min",
        "cambio": "1 transbordo fácil (tramo final a Centraal en tren local NS)",
        "precio_pp": "€39.90 adultos / €34.70 joven",
        "precio_familia": "€116.10 (Omio, incl. Savings Pass −€12.90)",
        "precio_pen": "S/.~464",
        "clase": "2ª clase (Saver)",
        "reservar_url": "https://www.omio.com",
        "alternativa_url": "https://www.nsinternational.com",
        "estado": "✅ Reservado (JTHDBFR)",
        "consejos": [
            "Reserva JTHDBFR · Tren 9527 · 07:49 desde Bruxelles-Midi · 2ª clase",
            "Sale de Bruxelles-Midi, a ~5 min de tu apartamento en Louise",
            "1 transbordo en Schiphol (~6 min): EuroCity 9527 llega 09:47 → Sprinter 8226 09:53 → Centraal 10:09",
            "Tarifa Saver: cambiable sin costo y reembolsable con €5 hasta el día antes",
            "Camila viaja con tarifa joven (Saver Youth, <26 años): €34.70",
            "Llega a Centraal 10:09; coordina el traslado a la casa familiar",
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
        "operador": "Iberia IB1346 (op. Air Nostrum)",
        "salida": "15:00 (AMS Schiphol)",
        "llegada": "17:40 (Madrid Barajas T4)",
        "duracion": "2h 40min",
        "cambio": "Vuelo directo",
        "precio_pp": "€180.08",
        "precio_familia": "€540.24",
        "precio_pen": "~S/.2,160",
        "clase": "Turista · Tarifa Óptima · 1 maleta facturada (1PC)",
        "reservar_url": "https://www.iberia.com",
        "alternativa_url": "https://www.iberia.com",
        "estado": "✅ Pagado (billetes emitidos)",
        "consejos": [
            "Billetes emitidos · localizador JMNLJ · 3 pasajeros confirmados",
            "IB1346 sale Schiphol 15:00 · llega Barajas T4 17:40 (2h40) · operado por Air Nostrum (YW)",
            "Equipaje por pasajero: 1 maleta facturada de 23 kg (máx. 32 kg con recargo) + 1 de mano ≤10 kg + accesorio personal",
            "Llega a Schiphol ~2.5h antes: en verano el control de seguridad es lento",
            "⚠️ Boletos separados (JMNLJ Iberia + 8ULKTI Air Europa): NO hay conexión protegida. Retiren las maletas en Barajas T4 y vuelvan a facturarlas con Air Europa (probable T1) para el UX175",
            "Conexión MAD→LIM (UX175, 23:45): ~6h de margen, suficiente para el cambio de terminal y re-facturar",
        ],
        "color": "purple",
    },
]

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
    for _r in RUTAS:
        _k = f"reservado_{_r['id']}"
        if _k not in st.session_state:
            st.session_state[_k] = _r["estado"].startswith("✅")
    st.title("🚄 Route Optimizer")
    st.caption("Rutas de transporte del viaje con horarios, precios y links de reserva")

    _pendientes = sum(
        1 for _r in RUTAS
        if not st.session_state.get(f"reservado_{_r['id']}", False)
    )
    if _pendientes:
        st.warning(
            f"⏳ Tienes **{_pendientes} trayecto"
            f"{'s' if _pendientes != 1 else ''} por reservar**. "
            "Hazlo con anticipación para mejores precios."
        )
    else:
        st.success("✅ Todos los trayectos están reservados.")

    st.markdown("### 🗺️ Rutas del Viaje")
    rutas_box = st.container()
    with rutas_box:
        for ruta in RUTAS:
            _ya_lbl = st.session_state.get(f"reservado_{ruta['id']}", False)
            _est_lbl = "✅ Reservado" if _ya_lbl else ruta["estado"]
            label = (
                f"{ruta['emoji_origen']} {ruta['origen']} → "
                f"{ruta['emoji_destino']} {ruta['destino']}  ·  📅 {ruta['fecha']}  ·  {_est_lbl}"
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
                    _ya = st.session_state.get(f"reservado_{ruta['id']}", False)
                    st.write("✅ Reservado" if _ya else ruta["estado"])

                st.divider()

                # Tabla compacta de detalles
                tabla_detalles(ruta)

                if ruta["cambio"] not in ("Directo — sin cambio de tren", "Vuelo directo"):
                    st.warning(f"🔄 Cambio: {ruta['cambio']}")
                else:
                    st.success(f"✅ {ruta['cambio']}")

                st.markdown("**💡 Consejos para este trayecto:**")
                for consejo in ruta["consejos"]:
                    st.write(f"• {consejo}")

                ya_reservado = st.session_state.get(f"reservado_{ruta['id']}", False)
                if not ya_reservado:
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