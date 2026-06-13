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

# ── Modelo de presupuesto (confirmado por el usuario, jun 2026) ────────────
# El vuelo internacional (Lima↔Madrid) y el seguro se pagaron ANTES. Lo que
# quedó del presupuesto familiar fueron S/.32.000, y de ese pote salen hospedaje,
# travels y atracciones. El resto es el bolsillo libre (comida, ocio, compras,
# transporte local).
PRESUPUESTO_POST_VUELOS_PEN = 32000.0

# Tasa de planificación EUR→PEN para convertir los montos fijos comprometidos.
# El Panorama usa la tasa en tiempo real; esta solo alimenta el Dashboard rápido.
TASA_PLAN_PEN = 4.0

# Fechas del viaje (para el cálculo de gasto diario sugerido)
TRIP_INICIO = date(2026, 7, 15)
TRIP_FIN = date(2026, 7, 30)

# ── Gastos pagados ANTES del pote (informativos, no se descuentan) ─────────
# Fuente: boletos Air Europa (los 3) e Interseguro (los 3). Montos reales en soles.
GASTOS_PREVIOS = [
    {"concepto": "Vuelo Lima↔Madrid (Air Europa, los 3)", "monto": 17500.00, "moneda": "PEN"},
    {"concepto": "Seguro de viaje (Interseguro, los 3)",  "monto": 558.84,   "moneda": "PEN"},
]

# ── Comprometido que SÍ sale del pote de S/.32.000 ─────────────────────────
# Fuente: confirmaciones de Booking, Omio, boleto Iberia y comprobantes de atracciones.
# París (hospedaje) incluye €67,60 de impuesto municipal que se paga on-site.
COMPROMETIDOS = [
    # Hospedaje
    {"concepto": "Hotel Madrid (Gran Central Suites)",        "monto": 464.60,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel Bayona (Appartement Bayonne)",        "monto": 490.77,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel París (Adagio Tour Eiffel)",          "monto": 1177.60, "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    {"concepto": "Hotel Bruselas (Stephanie by Reside)",      "monto": 386.50,  "moneda": "EUR", "categoria": "🏨 Hospedaje",  "estado": "pagado"},
    # Travels
    {"concepto": "Bus ALSA Madrid→Bayona",                    "monto": 117.91,  "moneda": "EUR", "categoria": "🚌 Travels",    "estado": "reservado"},
    {"concepto": "TGV Bayona→París",                          "monto": 238.72,  "moneda": "EUR", "categoria": "🚌 Travels",    "estado": "reservado"},
    {"concepto": "Eurostar París→Bruselas",                   "monto": 216.00,  "moneda": "EUR", "categoria": "🚌 Travels",    "estado": "pagado"},
    {"concepto": "EuroCity Direct Bruselas→Ámsterdam",        "monto": 116.10,  "moneda": "EUR", "categoria": "🚌 Travels",    "estado": "pagado"},
    {"concepto": "Vuelo Ámsterdam→Madrid (IB1346)",           "monto": 540.24,  "moneda": "EUR", "categoria": "🚌 Travels",    "estado": "pagado"},
    # Atracciones
    {"concepto": "Torre Eiffel 2º piso + champán (los 3)",    "monto": 133.50,  "moneda": "EUR", "categoria": "🎢 Atracciones", "estado": "pagado"},
    {"concepto": "Disneyland Paris 1 día/2 parques (los 3)",  "monto": 393.00,  "moneda": "EUR", "categoria": "🎢 Atracciones", "estado": "pagado"},
    {"concepto": "Tour Bernabéu (2 adulto + 1 infantil)",     "monto": 117.00,  "moneda": "EUR", "categoria": "🎢 Atracciones", "estado": "pagado"},
    {"concepto": "Parque Warner (3 entradas + 3 Warren)",     "monto": 149.70,  "moneda": "EUR", "categoria": "🎢 Atracciones", "estado": "pagado"},
    {"concepto": "Pase del Arte Madrid (2 adulto, menor free)", "monto": 77.20, "moneda": "EUR", "categoria": "🎢 Atracciones", "estado": "pagado"},
]

# Comprometido total en EUR (todos los ítems están en EUR) y bolsillo libre en EUR
# a tasa de planificación, para el Dashboard rápido.
_COMPROMETIDO_EUR = sum(g["monto"] for g in COMPROMETIDOS)
BOLSILLO_LIBRE_EUR = round(PRESUPUESTO_POST_VUELOS_PEN / TASA_PLAN_PEN - _COMPROMETIDO_EUR, 2)


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


# ── Proyección de gastos pendientes según el itinerario ────────────────────
_TIPO_LABEL = {
    "restaurante": "🍽️ Comida",
    "atraccion":   "🎭 Atracciones/Ocio",
    "compras":     "🛍️ Compras",
    "transporte":  "🚌 Transporte local",
}


@st.cache_data(ttl=3600)
def _proyeccion_itinerario():
    """Suma los gastos del itinerario que aún NO están pagados (costo > 0 y sin
    'pagado'), agrupados por ciudad y por tipo. Montos en EUR (total familia).
    Fuente: ITINERARIO_CHECKS de travel_concierge. Devuelve None si no se puede leer."""
    itinerario = None
    try:
        from modules.travel_concierge import ITINERARIO_CHECKS as itinerario
    except Exception:
        try:
            from travel_concierge import ITINERARIO_CHECKS as itinerario
        except Exception:
            return None
    if not itinerario:
        return None

    # Tramos inter-ciudad (tren/bus/vuelo): ya están en COMPROMETIDOS, no son
    # bolsillo libre. Se excluyen de la proyección para no contar doble.
    intercity = {"mad_22", "par_01", "bru_01", "bru_11", "ret_02"}
    por_ciudad, por_tipo = {}, {}
    for dia in itinerario:
        ciudad = dia.get("ciudad", "?")
        for act in dia.get("actividades", []):
            if act.get("id") in intercity:
                continue
            costo = act.get("costo", 0) or 0
            if costo <= 0 or act.get("pagado", False):
                continue
            por_ciudad[ciudad] = por_ciudad.get(ciudad, 0.0) + costo
            etq = _TIPO_LABEL.get(act.get("tipo", ""), "📦 Otros")
            por_tipo[etq] = por_tipo.get(etq, 0.0) + costo
    return {
        "por_ciudad": por_ciudad,
        "por_tipo": por_tipo,
        "total": sum(por_ciudad.values()),
    }


# ── Panorama de presupuesto (solo ADMIN) ───────────────────────────────────
def _panorama():
    rates = _rates_panorama()
    tc_pen = rates["PEN"]   # 1 EUR = tc_pen PEN
    tc_usd = rates["USD"]   # 1 EUR = tc_usd USD

    def eur_pen(e: float) -> float:
        return e * tc_pen

    def pen_eur(p: float) -> float:
        return p / tc_pen if tc_pen else 0.0

    st.caption(f"💱 Tasas usadas: 1 EUR = S/.{tc_pen:.3f} = ${tc_usd:.3f} · fuente: {rates['fuente']}")
    st.caption(
        "Modelo: el vuelo internacional y el seguro se pagaron antes. Lo que quedó "
        f"(S/.{PRESUPUESTO_POST_VUELOS_PEN:,.0f}) cubre hospedaje, travels, atracciones "
        "y el bolsillo libre (comida, ocio, compras, transporte local)."
    )

    # ── 1) Pagado antes del pote (informativo) ─────────────────────────
    st.subheader("✅ Pagado antes del presupuesto")
    prev_total_pen = sum(g["monto"] for g in GASTOS_PREVIOS)
    filas_prev = [{"Concepto": g["concepto"], "Soles": f"S/.{g['monto']:,.2f}"} for g in GASTOS_PREVIOS]
    st.dataframe(pd.DataFrame(filas_prev), use_container_width=True, hide_index=True)
    st.caption(
        f"Subtotal previo: S/.{prev_total_pen:,.0f}. Ya está fuera; no sale de los "
        f"S/.{PRESUPUESTO_POST_VUELOS_PEN:,.0f}."
    )

    st.divider()

    # ── 2) Comprometido que SÍ sale del pote ───────────────────────────
    st.subheader("🔒 Comprometido (sale de los S/.32.000)")
    filas, total_eur, grupos = [], 0.0, {}
    for g in COMPROMETIDOS:
        e = g["monto"]  # todos en EUR
        total_eur += e
        grupos[g["categoria"]] = grupos.get(g["categoria"], 0.0) + e
        filas.append({
            "Concepto": g["concepto"],
            "Categoría": g["categoria"],
            "EUR": f"€{e:,.2f}",
            "PEN": f"S/.{eur_pen(e):,.0f}",
            "Estado": g["estado"],
        })
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    comprometido_pen = eur_pen(total_eur)
    cols = st.columns(len(grupos))
    for col, (cat, val) in zip(cols, grupos.items()):
        col.metric(cat, f"€{val:,.0f}", f"S/.{eur_pen(val):,.0f}")
    st.caption(f"Total comprometido: €{total_eur:,.2f} ≈ S/.{comprometido_pen:,.0f}.")

    st.divider()

    # ── 3) El pote y el saldo libre ────────────────────────────────────
    st.subheader(f"🎯 El pote de S/.{PRESUPUESTO_POST_VUELOS_PEN:,.0f}")

    df = obtener_gastos_cached()
    gastado_destino_pen = 0.0
    if not df.empty:
        if "monto_pen" in df.columns:
            gastado_destino_pen = float(df["monto_pen"].sum())
        elif "monto_eur" in df.columns:
            gastado_destino_pen = eur_pen(float(df["monto_eur"].sum()))

    bolsillo_libre_pen = PRESUPUESTO_POST_VUELOS_PEN - comprometido_pen
    saldo_pen = bolsillo_libre_pen - gastado_destino_pen
    usado_pen = comprometido_pen + gastado_destino_pen
    pct = (usado_pen / PRESUPUESTO_POST_VUELOS_PEN * 100) if PRESUPUESTO_POST_VUELOS_PEN else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Presupuesto", f"S/.{PRESUPUESTO_POST_VUELOS_PEN:,.0f}")
    c2.metric("Comprometido", f"S/.{comprometido_pen:,.0f}", f"€{total_eur:,.0f}")
    c3.metric("Bolsillo libre", f"S/.{bolsillo_libre_pen:,.0f}", f"≈€{pen_eur(bolsillo_libre_pen):,.0f}")
    c4.metric("Gastado en destino", f"S/.{gastado_destino_pen:,.0f}")
    st.progress(min(pct / 100, 1.0))
    st.success(
        f"💰 **Saldo disponible (comida · ocio · compras · transporte local): "
        f"S/.{saldo_pen:,.0f}** (≈ €{pen_eur(saldo_pen):,.0f})"
    )
    st.caption(
        "⚠️ No registres hospedaje, travels ni atracciones como gastos diarios: ya están "
        "en 'Comprometido'. Si los anotas también, se duplican."
    )

    st.divider()

    # ── 3b) Proyección de gastos pendientes (según itinerario) ─────────
    proy = _proyeccion_itinerario()
    if proy and proy["total"] > 0:
        st.subheader("🔮 Gastos pendientes proyectados (según el itinerario)")
        st.caption(
            "Estimación de lo que falta gastar en destino (comida, ocio, compras y transporte "
            "local) según el plan. No incluye hospedaje, travels ni atracciones ya pagados."
        )
        total_proy_eur = proy["total"]
        total_proy_pen = eur_pen(total_proy_eur)

        cpa, cpb = st.columns(2)
        with cpa:
            st.markdown("**Por ciudad**")
            filas_pc = [
                {"Ciudad": c, "Proyectado": f"€{v:,.0f}", "S/.": f"S/.{eur_pen(v):,.0f}"}
                for c, v in sorted(proy["por_ciudad"].items(), key=lambda x: -x[1])
            ]
            st.dataframe(pd.DataFrame(filas_pc), use_container_width=True, hide_index=True)
        with cpb:
            st.markdown("**Por tipo**")
            filas_pt = [
                {"Tipo": t, "Proyectado": f"€{v:,.0f}", "S/.": f"S/.{eur_pen(v):,.0f}"}
                for t, v in sorted(proy["por_tipo"].items(), key=lambda x: -x[1])
            ]
            st.dataframe(pd.DataFrame(filas_pt), use_container_width=True, hide_index=True)

        # Lo adicional: ¿el plan cabe en el bolsillo libre?
        esperado_pen = gastado_destino_pen + total_proy_pen
        margen_pen = bolsillo_libre_pen - esperado_pen
        m1, m2, m3 = st.columns(3)
        m1.metric("Proyectado pendiente", f"S/.{total_proy_pen:,.0f}", f"€{total_proy_eur:,.0f}")
        m2.metric("Gasto total esperado", f"S/.{esperado_pen:,.0f}",
                  help="Gastado registrado + proyectado pendiente")
        m3.metric("Margen vs bolsillo libre", f"S/.{margen_pen:,.0f}", f"≈€{pen_eur(margen_pen):,.0f}")
        if margen_pen >= 0:
            st.success(
                f"✅ El plan cabe en el bolsillo libre: queda ~S/.{margen_pen:,.0f} "
                f"(≈ €{pen_eur(margen_pen):,.0f}) de margen para imprevistos."
            )
        else:
            st.warning(
                f"⚠️ El plan proyectado excede el bolsillo libre en ~S/.{abs(margen_pen):,.0f} "
                f"(≈ €{pen_eur(abs(margen_pen)):,.0f}). Conviene recortar gasto o ampliar el pote."
            )
        st.caption(
            "La proyección es una estimación del plan. A medida que registres gastos reales, "
            "el 'Gastado en destino' es la referencia principal."
        )
        st.divider()

    # ── 4) Gastado en destino por ciudad (informativo) ─────────────────
    if not df.empty and "ciudad" in df.columns and "monto_eur" in df.columns:
        st.subheader("🗺️ Gastado en destino por ciudad")
        gc = df.groupby("ciudad")["monto_eur"].sum().to_dict()
        filas_c = [
            {"Ciudad": c, "Gastado": f"€{v:,.0f}", "Gastado S/.": f"S/.{eur_pen(v):,.0f}"}
            for c, v in gc.items()
        ]
        st.dataframe(pd.DataFrame(filas_c), use_container_width=True, hide_index=True)
        st.divider()

    # ── 5) Recomendaciones ─────────────────────────────────────────────
    st.subheader("💡 Recomendaciones")
    hoy = date.today()
    recs = []

    if saldo_pen < 0:
        recs.append(f"🔴 Te pasaste del bolsillo libre por S/.{abs(saldo_pen):,.0f}. Hay que recortar o ampliar el pote.")
    elif bolsillo_libre_pen > 0 and saldo_pen <= 0.1 * bolsillo_libre_pen:
        recs.append(f"🟠 Te queda solo el {saldo_pen / bolsillo_libre_pen * 100:.0f}% del bolsillo libre. Cuida el gasto.")
    elif pct >= 60:
        recs.append(f"🟡 Llevas el {pct:.0f}% del pote usado (comprometido + destino).")
    else:
        recs.append(f"🟢 Vas cómodo: {pct:.0f}% del pote usado. Bolsillo libre sano.")

    dias_viaje = max((TRIP_FIN - TRIP_INICIO).days + 1, 1)
    if hoy < TRIP_INICIO:
        faltan = (TRIP_INICIO - hoy).days
        diario = saldo_pen / dias_viaje if dias_viaje else 0.0
        recs.append(
            f"🗓️ Faltan **{faltan} días** para el viaje. Gasto diario sugerido del bolsillo libre: "
            f"~S/.{diario:,.0f} (€{pen_eur(diario):,.0f}) sobre {dias_viaje} días."
        )
    elif TRIP_INICIO <= hoy <= TRIP_FIN:
        quedan = (TRIP_FIN - hoy).days + 1
        diario = saldo_pen / quedan if quedan else 0.0
        recs.append(
            f"🗓️ Te quedan **{quedan} días** de viaje. Con el saldo puedes gastar "
            f"~S/.{diario:,.0f}/día (€{pen_eur(diario):,.0f})."
        )
    else:
        recs.append("🗓️ El viaje terminó. Revisa el resumen final en el Dashboard.")

    recs.append(
        "💵 Para el bolsillo libre conviene combinar algo de efectivo en euros + tarjeta sin comisión. "
        "Todos los travels (buses, trenes y vuelos) ya están pagados."
    )

    for r in recs:
        st.write(r)

    st.divider()

    # ── 6) Simulador de efectivo ───────────────────────────────────────
    st.subheader("🧮 Simulador de efectivo")
    euros_custom = st.slider("Euros a llevar:", 100, 10000, max(int(pen_eur(saldo_pen)), 100), step=100)
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
            presupuesto_total = BOLSILLO_LIBRE_EUR
            gastado = df["monto_eur"].sum()

            c1, c2 = st.columns(2)
            texto_gasto = f"€{gastado:.2f}"
            c1.metric("Total Gastado", mostrar_precio(texto_gasto))
            c2.metric("Disponible (bolsillo libre)", mostrar_precio(f"€{presupuesto_total - gastado:.2f}"))

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