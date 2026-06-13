from datetime import date, datetime

import pandas as pd
import streamlit as st

# Importamos tus utils optimizados
from utils.gcp_client import get_firestore_client
from utils.price_helper import get_exchange_rate, mostrar_precio

# ── Constantes ─────────────────────────────────────────────────────────────
CATEGORIAS = ["🍽️ Comida", "🚌 Transporte", "🏨 Hospedaje", "🎭 Ocio", "🛍️ Compras", "💊 Salud", "📦 Otros"]
CIUDADES = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
COLECCION = "gastos_viaje"


# ── Firestore: Lectura con CACHÉ (Ahorro de dinero) ───────────────────────
@st.cache_data(ttl=600)  # Solo lee de Google cada 10 minutos
def obtener_gastos_cached() -> pd.DataFrame:
    db = get_firestore_client()
    # Limitar la consulta para no traer basura si la colección crece mucho
    docs = db.collection(COLECCION).order_by("fecha", direction="DESCENDING").limit(500).stream()

    gastos = []
    for doc in docs:
        g = doc.to_dict()
        g["_id"] = doc.id          # ← ID del documento, necesario para editar/eliminar
        gastos.append(g)

    if not gastos:
        return pd.DataFrame()

    return pd.DataFrame(gastos)


def _es_admin() -> bool:
    """Solo el administrador (rol con precios visibles) gestiona gastos."""
    return bool(st.session_state.get("_show_prices", False))


# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("💶 Euro-Budgeter")

    # Usamos el helper que ya tiene caché de 24h y fallback
    tipo_cambio = get_exchange_rate()
    st.info(f"💱 Tipo de cambio (Caché): **1 EUR = {tipo_cambio:.2f} PEN**")

    es_admin = _es_admin()

    # Las pestañas de exportación y gestión solo se arman para ADMIN
    labels = ["➕ Registrar", "📊 Dashboard", "📥 Exportar"]
    if es_admin:
        labels.append("✏️ Gestionar")
    tabs = st.tabs(labels)
    tab_registrar, tab_dashboard, tab_exportar = tabs[0], tabs[1], tabs[2]
    tab_gestionar = tabs[3] if es_admin else None

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
                # Lógica de guardado (convertir montos antes de enviar)
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
            # MÉTRICAS CON "SHOW_PRICES"
            presupuesto_total = 7985.0
            gastado = df["monto_eur"].sum()

            c1, c2 = st.columns(2)
            # Solo mostramos el monto real si es Admin usando tu helper
            texto_gasto = f"€{gastado:.2f}"
            c1.metric("Total Gastado", mostrar_precio(texto_gasto))
            c2.metric("Disponible", mostrar_precio(f"€{presupuesto_total - gastado:.2f}"))

            # GRÁFICOS (Streamlit native es más rápido que Plotly para móvil)
            st.bar_chart(df.groupby("categoria")["monto_eur"].sum())
            st.dataframe(df[["fecha", "ciudad", "descripcion", "monto_eur"]])
        else:
            st.info("Aún no hay gastos registrados.")

    # ── TAB: Exportar (solo ADMIN, contiene montos) ─────────────────────
    with tab_exportar:
        if not es_admin:
            st.warning("🔒 Solo el administrador puede exportar los gastos.")
        else:
            df = obtener_gastos_cached()
            if df.empty:
                st.info("No hay gastos para exportar.")
            else:
                columnas = [c for c in ["fecha", "ciudad", "categoria", "descripcion",
                                        "monto_eur", "monto_pen", "tipo_cambio", "usuario"]
                            if c in df.columns]
                csv = df[columnas].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Descargar CSV",
                    data=csv,
                    file_name="gastos_viaje.csv",
                    mime="text/csv",
                )

    # ── TAB: Gestionar — editar / eliminar (solo ADMIN) ─────────────────
    if tab_gestionar is not None:
        with tab_gestionar:
            df = obtener_gastos_cached()
            if df.empty:
                st.info("No hay gastos para gestionar.")
            else:
                # Etiquetas legibles para elegir el gasto a editar/eliminar
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

                # ── Editar ──────────────────────────────────────────
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
                        # Recalcula PEN con el tipo de cambio guardado del registro (o el actual)
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

                # ── Eliminar (con confirmación) ─────────────────────
                st.markdown("**🗑️ Eliminar gasto**")
                st.caption("Esta acción no se puede deshacer.")
                confirmar = st.checkbox("Confirmo que quiero eliminar este gasto")
                if st.button("🗑️ Eliminar definitivamente", disabled=not confirmar):
                    get_firestore_client().collection(COLECCION).document(doc_id).delete()
                    obtener_gastos_cached.clear()
                    st.success("✅ Gasto eliminado.")
                    st.rerun()