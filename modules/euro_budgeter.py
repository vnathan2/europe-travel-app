from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st

# Importamos tus utils optimizados
from utils.gcp_client import get_firestore_client
from utils.price_helper import get_exchange_rate, mostrar_precio

# ── Constantes ─────────────────────────────────────────────────────────────
CATEGORIAS = ["🍽️ Comida", "🚌 Transporte", "🏨 Hospedaje", "🎭 Ocio", "🛍️ Compras", "💊 Salud", "📦 Otros"]
CIUDADES = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
COLECCION = "gastos_viaje"

# Presupuesto SOLO en destino (comida, ocio, compras, transporte local).
# NO incluye hoteles, trenes, vuelos ni seguro (esos son costos comprometidos aparte).
PRESUPUESTO_TOTAL_DESTINO = 7985.0
PRESUPUESTO_CIUDAD = {
    "Madrid":    1650.0,
    "Bayona":     750.0,
    "París":     2550.0,
    "Bruselas":   785.0,
    "Ámsterdam": 1130.0,
}
# Suma por ciudad = 6865; el resto hasta 7985 (1120) es colchón/imprevistos.

# Fechas del viaje (para el cálculo de gasto diario sugerido)
TRIP_INICIO = date(2026, 7, 15)
TRIP_FIN = date(2026, 7, 30)

# ── Costos comprometidos (reservas reales ya hechas) ───────────────────────
# Fuente: confirmaciones de Booking, boletos Air Europa/Iberia, Omio e Interseguro.
# París incluye €67,60 de impuesto municipal que se paga on-site.
# Vuelo Lima↔Madrid: tarifa base (no incluye EMD de asientos pre-reservados, ~USD 250).
GASTOS_FIJOS = [
    {"concepto": "Hotel Madrid (Gran Central Suites)",      "monto": 464.60,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel Bayona (Appartement Bayonne)",      "monto": 490.77,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel París (Adagio Tour Eiffel)",        "monto": 1177.60, "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel Bruselas (Stephanie by Reside)",    "monto": 386.50,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Bus ALSA Madrid→Bayona",                  "monto": 117.91,  "moneda": "EUR", "categoria": "🚌 Transporte", "estado": "reservado"},
    {"concepto": "TGV Bayona→París",                        "monto": 238.72,  "moneda": "EUR", "categoria": "🚌 Transporte", "estado": "reservado"},
    {"concepto": "Eurostar París→Bruselas",                 "monto": 212.40,  "moneda": "EUR", "categoria": "🚌 Transporte", "estado": "por comprar"},
    {"concepto": "EuroCity Direct Bruselas→Ámsterdam",      "monto": 116.10,  "moneda": "EUR", "categoria": "🚌 Transporte", "estado": "por comprar"},
    {"concepto": "Vuelo Ámsterdam→Madrid (IB1346)",         "monto": 540.24,  "moneda": "EUR", "categoria": "✈️ Vuelos",     "estado": "pagado"},
    {"concepto": "Vuelo Lima↔Madrid (Air Europa, los 3)",   "monto": 4967.52, "moneda": "USD", "categoria": "✈️ Vuelos",     "estado": "pagado"},
    {"concepto": "Seguro de viaje (Interseguro, los 3)",    "monto": 171.99,  "moneda": "USD", "categoria": "🛡️ Seguro",     "estado": "pagado"},
]


# ── Firestore: Lectura con CACHÉ (Ahorro de dinero) ───────────────────────
@st.cache_data(ttl=600)  # Solo lee de Google cada 10 minutos
def obtener_gastos_cached() -> pd.DataFrame:
    db = get_firestore_client()
    docs = db.collection(COLECCION).order_by("fecha", direction="DESCENDING").limit(500).stream()
    gastos = []
    for doc in docs:
        g = doc.to_dict()
        g["_id"] = doc.id          # ID del documento, necesario para editar/eliminar
        gastos.append(g)
    if not gastos:
        return pd.DataFrame()
    return pd.DataFrame(gastos)


@st.cache_data(ttl=3600)  # tasas para el Panorama (1 hora)
def _rates_panorama() -> dict:
    """1 EUR = PEN soles = USD dólares. Con fallback si no hay conexión."""
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=5).json()["rates"]
        return {"PEN": float(r.get("PEN", 4.0)), "USD": float(r.get("USD", 1.08)), "fuente": "tiempo real"}
    except Exception:
        return {"PEN": 4.0, "USD": 1.08, "fuente": "respaldo (sin conexión)"}


def _es_admin() -> bool:
    """Solo el administrador (rol con precios visibles) ve el panorama y gestiona gastos."""
    return bool(st.session_state.get("_show_prices", False))


# ── Panorama de presupuesto (solo ADMIN) ───────────────────────────────────
def _panorama():
    rates = _rates_panorama()
    tc_pen = rates["PEN"]   # 1 EUR = tc_pen PEN
    tc_usd = rates["USD"]   # 1 EUR = tc_usd USD

    def eur_pen(e: float) -> float:
        return e * tc_pen

    def usd_eur(u: float) -> float:
        return u / tc_usd if tc_usd else 0.0

    def usd_pen(u: float) -> float:
        return eur_pen(usd_eur(u))

    st.caption(f"💱 Tasas usadas: 1 EUR = S/.{tc_pen:.3f} = ${tc_usd:.3f} · fuente: {rates['fuente']}")

    # ── 1) Costos comprometidos (reservas reales) ──────────────────────
    st.subheader("🔒 Costos comprometidos (reservas ya hechas)")
    st.caption("No se descuentan del presupuesto en destino. Son lo que cuesta la infraestructura del viaje.")

    filas, total_eur = [], 0.0
    for g in GASTOS_FIJOS:
        e = g["monto"] if g["moneda"] == "EUR" else usd_eur(g["monto"])
        total_eur += e
        filas.append({
            "Concepto": g["concepto"],
            "Categoría": g["categoria"],
            "Original": f"{g['monto']:,.2f} {g['moneda']}",
            "EUR": f"€{e:,.2f}",
            "PEN": f"S/.{eur_pen(e):,.0f}",
            "Estado": g["estado"],
        })
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    usd_items = sum(g["monto"] for g in GASTOS_FIJOS if g["moneda"] == "USD")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total comprometido", f"€{total_eur:,.0f}", f"S/.{eur_pen(total_eur):,.0f}")
    c2.metric("De eso, en USD", f"${usd_items:,.0f}", f"≈ €{usd_eur(usd_items):,.0f}")
    c3.metric("Ese USD en soles", f"S/.{usd_pen(usd_items):,.0f}")

    st.divider()

    # ── 2) Presupuesto en destino por ciudad ───────────────────────────
    st.subheader("🎯 Presupuesto en destino (comida · ocio · compras · transporte local)")

    df = obtener_gastos_cached()
    gastado_ciudad = {}
    if not df.empty and "ciudad" in df.columns and "monto_eur" in df.columns:
        gastado_ciudad = df.groupby("ciudad")["monto_eur"].sum().to_dict()

    filas2, total_presup, total_gastado = [], 0.0, 0.0
    for ciudad, presup in PRESUPUESTO_CIUDAD.items():
        gast = float(gastado_ciudad.get(ciudad, 0.0))
        pend = presup - gast
        total_presup += presup
        total_gastado += gast
        filas2.append({
            "Ciudad": ciudad,
            "Presupuesto": f"€{presup:,.0f}",
            "Gastado": f"€{gast:,.0f}",
            "Pendiente": f"€{pend:,.0f}",
            "Pendiente S/.": f"S/.{eur_pen(pend):,.0f}",
        })
    st.dataframe(pd.DataFrame(filas2), use_container_width=True, hide_index=True)

    colchon = PRESUPUESTO_TOTAL_DESTINO - total_presup
    pendiente_total = PRESUPUESTO_TOTAL_DESTINO - total_gastado
    pct = (total_gastado / PRESUPUESTO_TOTAL_DESTINO * 100) if PRESUPUESTO_TOTAL_DESTINO else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Presupuesto destino", f"€{PRESUPUESTO_TOTAL_DESTINO:,.0f}")
    c2.metric("Gastado", f"€{total_gastado:,.0f}", f"{pct:.0f}%")
    c3.metric("Pendiente", f"€{pendiente_total:,.0f}", f"S/.{eur_pen(pendiente_total):,.0f}")
    c4.metric("Colchón/imprevistos", f"€{colchon:,.0f}")
    st.progress(min(pct / 100, 1.0))

    # ── Costo total del viaje (panorama completo) ──────────────────────
    gran_total = total_eur + PRESUPUESTO_TOTAL_DESTINO
    st.info(
        f"🧾 **Costo total estimado del viaje:** comprometido €{total_eur:,.0f} + "
        f"presupuesto en destino €{PRESUPUESTO_TOTAL_DESTINO:,.0f} = "
        f"**€{gran_total:,.0f}** (≈ S/.{eur_pen(gran_total):,.0f})"
    )

    st.divider()

    # ── 3) Recomendaciones ─────────────────────────────────────────────
    st.subheader("💡 Recomendaciones")
    hoy = date.today()
    recs = []

    for ciudad, presup in PRESUPUESTO_CIUDAD.items():
        gast = float(gastado_ciudad.get(ciudad, 0.0))
        if gast > presup:
            recs.append(f"⚠️ **{ciudad}** está sobre su presupuesto en destino (€{gast:,.0f} de €{presup:,.0f}).")
        elif presup > 0 and gast >= 0.9 * presup:
            recs.append(f"🟡 **{ciudad}** va al {gast / presup * 100:.0f}% de su presupuesto.")

    if pct >= 90:
        recs.append(f"🔴 Llevas el {pct:.0f}% del presupuesto en destino. Cuida el gasto restante.")
    elif pct >= 60:
        recs.append(f"🟡 Vas en {pct:.0f}% del presupuesto en destino.")
    elif total_gastado > 0:
        recs.append(f"🟢 Vas cómodo: {pct:.0f}% del presupuesto en destino consumido.")

    dias_viaje = max((TRIP_FIN - TRIP_INICIO).days, 1)
    if hoy < TRIP_INICIO:
        faltan = (TRIP_INICIO - hoy).days
        diario = PRESUPUESTO_TOTAL_DESTINO / dias_viaje
        recs.append(
            f"🗓️ Faltan **{faltan} días** para el viaje. Presupuesto diario sugerido en destino: "
            f"~€{diario:,.0f} (S/.{eur_pen(diario):,.0f}) sobre {dias_viaje} días."
        )
    elif TRIP_INICIO <= hoy <= TRIP_FIN:
        quedan = (TRIP_FIN - hoy).days + 1
        diario = pendiente_total / quedan if quedan else 0.0
        recs.append(
            f"🗓️ Te quedan **{quedan} días** de viaje. Con lo pendiente puedes gastar "
            f"~€{diario:,.0f}/día (S/.{eur_pen(diario):,.0f})."
        )
    else:
        recs.append("🗓️ El viaje terminó. Revisa el resumen final en el Dashboard.")

    recs.append(
        f"💵 Para llevar todo el presupuesto en destino en efectivo: €{PRESUPUESTO_TOTAL_DESTINO:,.0f} "
        f"≈ S/.{eur_pen(PRESUPUESTO_TOTAL_DESTINO):,.0f}. Recomendable combinar algo de efectivo + tarjeta sin comisión."
    )

    for r in recs:
        st.write(r)

    st.divider()

    # ── 4) Simulador de efectivo (migrado del Conversor) ───────────────
    st.subheader("🧮 Simulador de efectivo")
    euros_custom = st.slider("Euros a llevar:", 100, 10000, 7000, step=100)
    s1, s2 = st.columns(2)
    s1.metric(f"€{euros_custom:,} en soles", f"S/.{eur_pen(euros_custom):,.0f}")
    s2.metric(f"€{euros_custom:,} en dólares", f"${euros_custom * tc_usd:,.0f}")


# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("💶 Euro-Budgeter")

    tipo_cambio = get_exchange_rate()
    st.info(f"💱 Tipo de cambio (Caché): **1 EUR = {tipo_cambio:.2f} PEN**")

    es_admin = _es_admin()

    labels = ["➕ Registrar", "📊 Dashboard"]
    if es_admin:
        labels += ["🧭 Panorama", "📥 Exportar", "✏️ Gestionar"]
    tabs = st.tabs(labels)
    tab_registrar, tab_dashboard = tabs[0], tabs[1]
    if es_admin:
        tab_panorama, tab_exportar, tab_gestionar = tabs[2], tabs[3], tabs[4]
    else:
        tab_panorama = tab_exportar = tab_gestionar = None

    # ── TAB: Registrar ──────────────────────────────────────────────────
    with tab_registrar:
        with st.form("form_gasto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", value=date(2026, 7, 14))
                ciudad = st.selectbox("Ciudad", CIUDADES)
                categoria = st.selectbox("Categoría", CATEGORIAS)
            with col2:
                desc = st.text_input("Descripción")
                monto = st.number_input("Monto", min_value=0.0, step=1.0)
                moneda = st.radio("Moneda", ["EUR", "PEN"], horizontal=True)

            submit = st.form_submit_button("💾 Guardar", type="primary")

            if submit:
                m_eur = monto if moneda == "EUR" else monto / tipo_cambio
                m_pen = monto if moneda == "PEN" else monto * tipo_cambio

                nuevo_gasto = {
                    "fecha": str(fecha),
                    "ciudad": ciudad,
                    "categoria": categoria,
                    "descripcion": desc,
                    "monto_eur": round(m_eur, 2),
                    "monto_pen": round(m_pen, 2),
                    "tipo_cambio": round(tipo_cambio, 4),
                    "usuario": st.session_state.get("_user_name", "Desconocido"),
                    "timestamp": datetime.now(),
                }
                get_firestore_client().collection(COLECCION).add(nuevo_gasto)
                obtener_gastos_cached.clear()
                st.success("✅ Gasto registrado!")

    # ── TAB: Dashboard ──────────────────────────────────────────────────
    with tab_dashboard:
        df = obtener_gastos_cached()
        if not df.empty:
            presupuesto_total = PRESUPUESTO_TOTAL_DESTINO
            gastado = df["monto_eur"].sum()

            c1, c2 = st.columns(2)
            texto_gasto = f"€{gastado:.2f}"
            c1.metric("Total Gastado", mostrar_precio(texto_gasto))
            c2.metric("Disponible", mostrar_precio(f"€{presupuesto_total - gastado:.2f}"))

            st.bar_chart(df.groupby("categoria")["monto_eur"].sum())
            st.dataframe(df[["fecha", "ciudad", "descripcion", "monto_eur"]])
        else:
            st.info("Aún no hay gastos registrados.")

    # ── TAB: Panorama (solo ADMIN) ──────────────────────────────────────
    if tab_panorama is not None:
        with tab_panorama:
            _panorama()

    # ── TAB: Exportar (solo ADMIN, contiene montos) ─────────────────────
    if tab_exportar is not None:
        with tab_exportar:
            df = obtener_gastos_cached()
            if df.empty:
                st.info("No hay gastos para exportar.")
            else:
                columnas = [c for c in ["fecha", "ciudad", "categoria", "descripcion",
                                        "monto_eur", "monto_pen", "tipo_cambio", "usuario"]
                            if c in df.columns]
                csv = df[columnas].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Descargar CSV", data=csv,
                    file_name="gastos_viaje.csv", mime="text/csv",
                )

    # ── TAB: Gestionar — editar / eliminar (solo ADMIN) ─────────────────
    if tab_gestionar is not None:
        with tab_gestionar:
            df = obtener_gastos_cached()
            if df.empty:
                st.info("No hay gastos para gestionar.")
            else:
                opciones = {}
                for _, fila in df.iterrows():
                    etiqueta = (
                        f"{fila.get('fecha', '?')} · {fila.get('ciudad', '?')} · "
                        f"{fila.get('categoria', '?')} · {fila.get('descripcion', '(sin desc.)')} · "
                        f"€{float(fila.get('monto_eur', 0) or 0):.2f}"
                    )
                    opciones[etiqueta] = fila["_id"]

                etiqueta_sel = st.selectbox("Selecciona el gasto", list(opciones.keys()))
                doc_id = opciones[etiqueta_sel]
                fila_sel = df[df["_id"] == doc_id].iloc[0]

                st.divider()

                with st.form("form_editar_gasto"):
                    st.markdown("**✏️ Editar gasto**")
                    col1, col2 = st.columns(2)
                    with col1:
                        try:
                            fecha_val = date.fromisoformat(str(fila_sel.get("fecha")))
                        except (ValueError, TypeError):
                            fecha_val = date(2026, 7, 14)
                        e_fecha = st.date_input("Fecha", value=fecha_val)

                        ciudad_actual = fila_sel.get("ciudad", CIUDADES[0])
                        idx_ciudad = CIUDADES.index(ciudad_actual) if ciudad_actual in CIUDADES else 0
                        e_ciudad = st.selectbox("Ciudad", CIUDADES, index=idx_ciudad)

                        cat_actual = fila_sel.get("categoria", CATEGORIAS[0])
                        idx_cat = CATEGORIAS.index(cat_actual) if cat_actual in CATEGORIAS else 0
                        e_categoria = st.selectbox("Categoría", CATEGORIAS, index=idx_cat)
                    with col2:
                        e_desc = st.text_input("Descripción", value=str(fila_sel.get("descripcion", "")))
                        e_monto_eur = st.number_input(
                            "Monto (EUR)", min_value=0.0, step=1.0,
                            value=float(fila_sel.get("monto_eur", 0.0) or 0.0),
                        )

                    guardar = st.form_submit_button("💾 Guardar cambios", type="primary")

                    if guardar:
                        tc = float(fila_sel.get("tipo_cambio", tipo_cambio) or tipo_cambio)
                        cambios = {
                            "fecha": str(e_fecha),
                            "ciudad": e_ciudad,
                            "categoria": e_categoria,
                            "descripcion": e_desc,
                            "monto_eur": round(e_monto_eur, 2),
                            "monto_pen": round(e_monto_eur * tc, 2),
                            "editado_por": st.session_state.get("_user_name", "Desconocido"),
                            "editado_en": datetime.now(),
                        }
                        get_firestore_client().collection(COLECCION).document(doc_id).update(cambios)
                        obtener_gastos_cached.clear()
                        st.success("✅ Gasto actualizado.")
                        st.rerun()

                st.divider()
                st.markdown("**🗑️ Eliminar gasto**")
                st.caption("Esta acción no se puede deshacer.")
                confirmar = st.checkbox("Confirmo que quiero eliminar este gasto")
                if st.button("🗑️ Eliminar definitivamente", disabled=not confirmar):
                    get_firestore_client().collection(COLECCION).document(doc_id).delete()
                    obtener_gastos_cached.clear()
                    st.success("✅ Gasto eliminado.")
                    st.rerun()