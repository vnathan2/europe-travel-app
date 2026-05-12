# modules/admin_panel.py
# Panel de administración — solo visible para ADMIN
# Permite ejecutar ingesta de conocimiento sin usar PowerShell

import streamlit as st
import time
from datetime import datetime

# Límite conservador: dejamos 200 créditos libres para el chat concierge
TAVILY_BUDGET_INGESTA = 80

def run_ingesta_ciudad(ciudad: str, fuentes: list) -> dict:
    """
    Ejecuta el pipeline de ingesta para una ciudad y fuentes seleccionadas.
    Retorna dict con resultados por fuente.
    """
    from utils.knowledge_base import (
        init_embeddings, fetch_wikipedia, fetch_opentripmap,
        fetch_tavily, guardar_documento, CIUDADES
    )

    # ── Queries por ciudad y categoría ────────────────────────────────────
    # Cada lista tiene queries específicas que Tavily buscará en:
    # TripAdvisor, Lonely Planet, blogs latinos, foros de viaje, etc.
    TEMAS_TAVILY = {
        "Madrid": {
            "TripAdvisor":      [
                "site:tripadvisor.com Madrid restaurantes mejor valorados",
                "site:tripadvisor.com Madrid atracciones turísticas",
                "site:tripadvisor.com Madrid hoteles centro",
            ],
            "Blogs latinos":    [
                "Madrid consejos viajeros latinoamericanos 2025 2026",
                "Madrid qué hacer familia viaje latino blog",
                "Madrid compras Gran Vía Zara Mango latinos",
                "Madrid tapas baratas recomendaciones viajeros",
            ],
            "Transporte":       [
                "metro Madrid cómo funciona tarjeta turista precio",
                "aeropuerto Barajas terminal 4 cómo llegar centro Madrid",
                "Madrid Atocha trenes AVE cómo reservar",
            ],
            "Gastronomía":      [
                "mejores restaurantes Madrid auténticos no turísticos 2025",
                "mercado San Miguel Madrid qué comer precios",
                "tapas Madrid barrio La Latina recomendaciones",
                "desayuno tradicional Madrid mejor cafetería",
            ],
            "Tips familia":     [
                "Madrid con familia niños adolescentes qué hacer",
                "Parque Warner Madrid guía completa consejos",
                "Madrid seguridad consejos turistas latinoamericanos",
            ],
        },
        "Bayona": {
            "TripAdvisor":      [
                "site:tripadvisor.com Bayonne France restaurantes",
                "site:tripadvisor.com Bayonne atracciones turísticas",
            ],
            "Blogs latinos":    [
                "Bayona Francia qué ver hacer viajeros hispanohablantes",
                "País Vasco francés Bayona guía viaje español",
                "Bayona Francia gastronomía vasca pintxos jambon",
            ],
            "Transporte":       [
                "tren Madrid Hendaya Bayona cómo viajar precio",
                "Bayona Francia transporte local cómo moverse",
            ],
            "Gastronomía":      [
                "mejores restaurantes Bayona Francia auténticos",
                "chocolate Bayona dónde comprarlo musée du chocolat",
                "pintxos bares Bayona País Vasco francés",
            ],
            "Tips familia":     [
                "Bayona Francia visita familia consejos",
                "Bayona qué hacer día de turismo completo itinerario",
            ],
        },
        "París": {
            "TripAdvisor":      [
                "site:tripadvisor.com Paris restaurantes mejor valorados latinos",
                "site:tripadvisor.com Torre Eiffel consejos evitar colas",
                "site:tripadvisor.com Paris museos mejores tips",
            ],
            "Blogs latinos":    [
                "París consejos viajeros latinoamericanos primera vez 2025",
                "París con familia qué hacer adolescentes guía",
                "París barato ahorrar dinero viajero latino tips",
                "París compras souvenirs dónde no ser estafado",
                "Versalles guía completa consejos cómo llegar evitar colas",
                "Disneyland París consejos familia precio tips 2025",
            ],
            "Transporte":       [
                "metro París cómo funciona tarjeta Navigo turista precio",
                "París transporte público aeropuerto Charles de Gaulle",
                "RER B París aeropuerto centro cómo tomar",
            ],
            "Gastronomía":      [
                "mejores restaurantes París no turísticos auténticos 2025",
                "París dónde comer barato bueno recomendaciones",
                "croissant baguette París mejor panadería boulangerie",
                "Le Train Bleu París restaurante Gare de Lyon experiencia",
            ],
            "Tips familia":     [
                "Torre Eiffel París consejos familia colas precio subir",
                "Louvre París guía completa qué ver no perderse tiempo",
                "París seguridad turistas carteristas consejos",
                "cumpleaños romántico París ideas sorpresa pareja",
            ],
        },
        "Bruselas": {
            "TripAdvisor":      [
                "site:tripadvisor.com Bruselas restaurantes mejor valorados",
                "site:tripadvisor.com Bruselas atracciones turísticas",
            ],
            "Blogs latinos":    [
                "Bruselas qué ver hacer viajeros latinos guía",
                "Bruselas en un día itinerario completo recomendaciones",
                "Bruselas baratos consejos ahorro viajero hispanohablante",
                "Atomium Bruselas guía consejos visita",
            ],
            "Transporte":       [
                "Bruselas transporte público metro tram precio turista",
                "tren París Bruselas Eurostar Thalys precio reserva",
                "Bruselas aeropuerto centro cómo llegar transporte",
            ],
            "Gastronomía":      [
                "mejores restaurantes Bruselas auténticos no turísticos",
                "cerveza belga Bruselas mejores bares Delirium",
                "chocolate belga Bruselas dónde comprar mejores marcas",
                "Grand Place Bruselas restaurantes alrededor consejos",
                "waffles Bruselas dónde comer mejores auténticos",
            ],
            "Tips familia":     [
                "Bruselas familia qué hacer adolescentes turismo",
                "Grand Place Bruselas historia consejos visita",
            ],
        },
        "Ámsterdam": {
            "TripAdvisor":      [
                "site:tripadvisor.com Amsterdam restaurantes mejor valorados",
                "site:tripadvisor.com Amsterdam atracciones turísticas",
                "site:tripadvisor.com Casa Ana Frank Amsterdam consejos",
            ],
            "Blogs latinos":    [
                "Ámsterdam consejos viajeros latinoamericanos guía 2025",
                "Ámsterdam primera vez qué hacer ver itinerario",
                "Ámsterdam barato ahorrar tips viajero hispano",
                "Zaanse Schans molinos viento Ámsterdam guía cómo llegar",
                "canales Ámsterdam crucero precio cuál elegir",
            ],
            "Transporte":       [
                "Ámsterdam transporte público tram metro OV-chipkaart",
                "aeropuerto Schiphol Ámsterdam centro cómo llegar tren",
                "bicicleta Ámsterdam alquiler precio consejos turistas",
            ],
            "Gastronomía":      [
                "mejores restaurantes Ámsterdam auténticos no turísticos",
                "Ámsterdam qué comer gastronomía holandesa típica",
                "mercado Ámsterdam Albert Cuyp food tips",
                "De Kas Ámsterdam restaurante sostenible experiencia",
            ],
            "Tips familia":     [
                "Ámsterdam familia qué hacer con adolescentes",
                "Museo Van Gogh Ámsterdam guía completa consejos reserva",
                "Rijksmuseum Ámsterdam tips entradas evitar colas",
                "Casa Ana Frank Ámsterdam reserva entradas anticipado",
            ],
        },
    }

    init_embeddings()
    resultados = {}

    for fuente in fuentes:
        docs = []

        if fuente == "Wikipedia":
            docs = fetch_wikipedia(ciudad)

        elif fuente == "OpenStreetMap":
            docs = fetch_opentripmap(ciudad)

        elif fuente == "Tavily Web":
            queries_ciudad = TEMAS_TAVILY.get(ciudad, {})
            temas_planos = []
            for categoria, queries in queries_ciudad.items():
                temas_planos.extend(queries)
            docs = fetch_tavily(ciudad, temas_planos)

        elif fuente == "TripAdvisor":
            queries_ciudad = TEMAS_TAVILY.get(ciudad, {})
            temas = queries_ciudad.get("TripAdvisor", [])
            docs = fetch_tavily(ciudad, temas)

        elif fuente == "Blogs latinos":
            queries_ciudad = TEMAS_TAVILY.get(ciudad, {})
            temas = (queries_ciudad.get("Blogs latinos", []) +
                     queries_ciudad.get("Tips familia", []))
            docs = fetch_tavily(ciudad, temas)

        elif fuente == "Gastronomía":
            queries_ciudad = TEMAS_TAVILY.get(ciudad, {})
            temas = queries_ciudad.get("Gastronomía", [])
            docs = fetch_tavily(ciudad, temas)

        elif fuente == "Transporte":
            queries_ciudad = TEMAS_TAVILY.get(ciudad, {})
            temas = queries_ciudad.get("Transporte", [])
            docs = fetch_tavily(ciudad, temas)

        ok = skip = error = 0
        for doc in docs:
            resultado = guardar_documento(doc)
            if resultado.startswith("OK"):
                ok += 1
            elif resultado.startswith("SKIP"):
                skip += 1
            else:
                error += 1

        resultados[fuente] = {
            "total": len(docs),
            "nuevos": ok,
            "existentes": skip,
            "errores": error,
        }

    return resultados


def contar_queries_tavily(ciudades: list, fuentes: list) -> int:
    """Cuenta exactamente cuántas llamadas a Tavily se harán antes de ejecutar."""
    TEMAS_TAVILY_REF = {
        "Madrid":    {"TripAdvisor": 3, "Blogs latinos": 4, "Transporte": 3, "Gastronomía": 4, "Tips familia": 3},
        "Bayona":    {"TripAdvisor": 2, "Blogs latinos": 3, "Transporte": 2, "Gastronomía": 3, "Tips familia": 2},
        "París":     {"TripAdvisor": 3, "Blogs latinos": 6, "Transporte": 3, "Gastronomía": 4, "Tips familia": 4},
        "Bruselas":  {"TripAdvisor": 2, "Blogs latinos": 4, "Transporte": 3, "Gastronomía": 5, "Tips familia": 2},
        "Ámsterdam": {"TripAdvisor": 3, "Blogs latinos": 5, "Transporte": 3, "Gastronomía": 4, "Tips familia": 4},
    }
    total = 0
    for ciudad in ciudades:
        ref = TEMAS_TAVILY_REF.get(ciudad, {})
        for fuente in fuentes:
            if fuente == "Tavily Web":
                total += sum(ref.values())
            elif fuente in ref:
                q = ref[fuente]
                if fuente == "Blogs latinos":
                    q += ref.get("Tips familia", 0)
                total += q
    return total


def get_stats_kb() -> dict:
    """Obtiene estadísticas actuales de la knowledge base."""
    try:
        from utils.gcp_client import get_firestore_client
        db = get_firestore_client()
        docs = list(db.collection("knowledge_base").stream())

        stats = {"total": len(docs), "por_ciudad": {}, "por_fuente": {}}
        for doc in docs:
            data = doc.to_dict()
            ciudad = data.get("ciudad", "?")
            fuente = data.get("fuente", "?")
            stats["por_ciudad"][ciudad] = stats["por_ciudad"].get(ciudad, 0) + 1
            stats["por_fuente"][fuente]  = stats["por_fuente"].get(fuente, 0) + 1

        return stats
    except Exception as e:
        return {"total": 0, "por_ciudad": {}, "por_fuente": {}, "error": str(e)}


def limpiar_ciudad(ciudad: str) -> int:
    """Elimina todos los documentos de una ciudad de la KB."""
    try:
        from utils.gcp_client import get_firestore_client
        db = get_firestore_client()
        docs = (db.collection("knowledge_base")
                  .where("ciudad", "==", ciudad)
                  .stream())
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        return count
    except Exception as e:
        st.error(f"Error limpiando {ciudad}: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════
# UI Principal
# ══════════════════════════════════════════════════════════════════════════
def mostrar():
    st.title("⚙️ Admin Panel")
    st.caption("Panel exclusivo de administración — solo visible para Jonathan")

    tab_ingesta, tab_stats, tab_limpiar = st.tabs([
        "🔄 Ingesta de Datos", "📊 Estado Knowledge Base", "🗑️ Limpiar Datos"
    ])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: INGESTA
    # ══════════════════════════════════════════════════════════════════════
    with tab_ingesta:
        st.subheader("🔄 Ingesta Manual de Conocimiento")
        st.info(
            "Ejecuta el pipeline de datos para alimentar la base de conocimiento "
            "del Travel Concierge Bot. Antes del viaje, corre todas las ciudades."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📍 Ciudades**")
            ciudades_sel = []
            todas = st.checkbox("Todas las ciudades", value=False)
            if todas:
                ciudades_sel = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
                for c in ciudades_sel:
                    st.checkbox(c, value=True, disabled=True, key=f"c_{c}")
            else:
                for ciudad in ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]:
                    if st.checkbox(ciudad, key=f"c_{ciudad}"):
                        ciudades_sel.append(ciudad)

        with col2:
            st.markdown("**🔌 Fuentes de datos**")
            fuentes_sel = []

            st.caption("📚 **Base estructurada**")
            for fuente, desc in [
                ("Wikipedia",     "Artículos generales de cada ciudad"),
                ("OpenStreetMap", "Atracciones y lugares turísticos"),
            ]:
                if st.checkbox(fuente, value=True, key=f"f_{fuente}"):
                    fuentes_sel.append(fuente)

            st.caption("🌐 **Web en español latino** (via Tavily)")
            for fuente, desc in [
                ("TripAdvisor",   "Restaurantes y atracciones con ratings"),
                ("Blogs latinos", "Experiencias reales + tips para familias"),
                ("Gastronomía",   "Dónde comer, qué probar, precios"),
                ("Transporte",    "Metro, trenes, aeropuertos, precios"),
            ]:
                if st.checkbox(f"{fuente}", value=True,
                               key=f"f_{fuente}", help=desc):
                    fuentes_sel.append(fuente)

            # Opción todo Tavily de una
            st.caption("⚡ **O todo en uno**")
            if st.checkbox("Tavily Web completo (todas las categorías)",
                           key="f_Tavily Web"):
                # Si selecciona esta, quita las individuales de Tavily
                fuentes_sel = [f for f in fuentes_sel if f in
                               ["Wikipedia", "OpenStreetMap"]]
                fuentes_sel.append("Tavily Web")

        st.divider()

        # Botón principal
        if not ciudades_sel:
            st.warning("⚠️ Selecciona al menos una ciudad.")
        elif not fuentes_sel:
            st.warning("⚠️ Selecciona al menos una fuente.")
        else:
            # Estimado de tiempo
            tavily_count = sum(1 for f in fuentes_sel
                               if f not in ["Wikipedia", "OpenStreetMap"])
            base = len(ciudades_sel) * (
                len([f for f in fuentes_sel if f in ["Wikipedia", "OpenStreetMap"]]) * 1
                + tavily_count * 3
            )
            st.caption(f"⏱️ Tiempo estimado: ~{base}–{base*2} minutos · "
                       f"{len(fuentes_sel)} fuente(s) seleccionadas")

            # Estimado de cuota Tavily
            queries_tavily = contar_queries_tavily(ciudades_sel, fuentes_sel)
            if queries_tavily > 0:
                color = "🔴" if queries_tavily > TAVILY_BUDGET_INGESTA else "🟡" if queries_tavily > 40 else "🟢"
                st.caption(f"{color} Llamadas Tavily estimadas: **{queries_tavily}** / {TAVILY_BUDGET_INGESTA} recomendado por ejecución")
                if queries_tavily > TAVILY_BUDGET_INGESTA:
                    st.warning(
                        f"⚠️ Esta selección usará **{queries_tavily} créditos Tavily**. "
                        f"El límite recomendado por ejecución es {TAVILY_BUDGET_INGESTA} "
                        f"para dejar margen al chat del Travel Concierge. "
                        f"Considera ingestar por ciudad o reducir fuentes."
                    )

            if st.button(
                f"🚀 Iniciar ingesta — {len(ciudades_sel)} ciudad(es) × {len(fuentes_sel)} fuente(s)",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.ingesta_running = True
                log_container = st.container(border=True)
                progress = st.progress(0)
                total_pasos = len(ciudades_sel) * len(fuentes_sel)
                paso = 0
                resumen_global = []

                with log_container:
                    st.markdown("**📋 Log de ingesta:**")
                    log_placeholder = st.empty()
                    logs = []

                    inicio = datetime.now()

                    for ciudad in ciudades_sel:
                        logs.append(f"▶️ **{ciudad}** — iniciando...")
                        log_placeholder.markdown("\n\n".join(logs))

                        try:
                            resultados = run_ingesta_ciudad(ciudad, fuentes_sel)

                            for fuente, res in resultados.items():
                                paso += 1
                                progress.progress(paso / total_pasos)

                                if res["errores"] == 0:
                                    icono = "✅"
                                elif res["nuevos"] > 0:
                                    icono = "⚠️"
                                else:
                                    icono = "❌"

                                log_line = (
                                    f"{icono} `{ciudad} / {fuente}` → "
                                    f"**{res['nuevos']} nuevos** · "
                                    f"{res['existentes']} ya existían · "
                                    f"{res['errores']} errores "
                                    f"({res['total']} docs totales)"
                                )
                                logs.append(log_line)
                                log_placeholder.markdown("\n\n".join(logs))
                                resumen_global.append(
                                    (ciudad, fuente, res)
                                )

                        except Exception as e:
                            logs.append(f"❌ Error en **{ciudad}**: `{e}`")
                            log_placeholder.markdown("\n\n".join(logs))

                    # Resumen final
                    duracion = (datetime.now() - inicio).seconds
                    mins = duracion // 60
                    segs = duracion % 60
                    dur_str = f"{mins}m {segs}s" if mins > 0 else f"{segs}s"
                    total_nuevos = sum(r["nuevos"] for _, _, r in resumen_global)
                    total_skip   = sum(r["existentes"] for _, _, r in resumen_global)
                    total_err    = sum(r["errores"] for _, _, r in resumen_global)

                    logs.append("---")
                    logs.append(
                        f"🏁 **Completado en {dur_str}** — "
                        f"{total_nuevos} documentos nuevos · "
                        f"{total_skip} ya existían · "
                        f"{total_err} errores"
                    )
                    log_placeholder.markdown("\n\n".join(logs))
                    progress.progress(1.0)

                if total_nuevos > 0:
                    # Invalidar cache de RAG para que Lady use los docs nuevos sin esperar 10 min
                    from utils.knowledge_base import invalidar_cache_kb
                    invalidar_cache_kb()
                    st.success(
                        f"✅ Ingesta completada. "
                        f"**{total_nuevos} documentos nuevos** "
                        f"agregados a la Knowledge Base."
                    )
                else:
                    st.info(
                        "ℹ️ No se agregaron documentos nuevos. "
                        "Puede que todos ya existieran."
                    )

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2: ESTADÍSTICAS
    # ══════════════════════════════════════════════════════════════════════
    with tab_stats:
        st.subheader("📊 Estado actual de la Knowledge Base")

        if st.button("🔄 Actualizar estadísticas", type="primary"):
            st.session_state.kb_stats = get_stats_kb()

        if "kb_stats" not in st.session_state:
            with st.spinner("Cargando estadísticas..."):
                st.session_state.kb_stats = get_stats_kb()

        stats = st.session_state.kb_stats

        if "error" in stats:
            st.error(f"Error conectando a Firestore: {stats['error']}")
        else:
            # Métrica principal
            st.metric("📚 Total documentos en KB", stats["total"])

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📍 Por ciudad:**")
                ciudades_ord = sorted(
                    stats["por_ciudad"].items(),
                    key=lambda x: x[1], reverse=True
                )
                for ciudad, count in ciudades_ord:
                    pct = int(count / stats["total"] * 100) if stats["total"] else 0
                    st.write(f"`{ciudad}` — **{count}** docs ({pct}%)")
                    st.progress(pct / 100)

            with col2:
                st.markdown("**🔌 Por fuente:**")
                fuentes_ord = sorted(
                    stats["por_fuente"].items(),
                    key=lambda x: x[1], reverse=True
                )
                for fuente, count in fuentes_ord:
                    pct = int(count / stats["total"] * 100) if stats["total"] else 0
                    st.write(f"`{fuente}` — **{count}** docs ({pct}%)")
                    st.progress(pct / 100)

            # Cobertura por ciudad
            st.divider()
            st.markdown("**🎯 Cobertura por ciudad:**")
            todas_ciudades = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
            cols = st.columns(5)
            for i, ciudad in enumerate(todas_ciudades):
                count = stats["por_ciudad"].get(ciudad, 0)
                estado = "✅" if count >= 10 else ("⚠️" if count > 0 else "❌")
                cols[i].metric(ciudad, f"{estado} {count}")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3: LIMPIAR
    # ══════════════════════════════════════════════════════════════════════
    with tab_limpiar:
        st.subheader("🗑️ Limpiar Knowledge Base")
        st.warning(
            "⚠️ Esta acción elimina documentos de Firestore de forma permanente. "
            "Necesitarás volver a ejecutar la ingesta para recuperarlos."
        )

        col1, col2 = st.columns(2)
        with col1:
            ciudad_limpiar = st.selectbox(
                "Ciudad a limpiar:",
                ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"],
                key="ciudad_limpiar"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            confirmar = st.checkbox(
                f"Confirmo que quiero eliminar todos los docs de **{ciudad_limpiar}**"
            )

        if confirmar:
            if st.button(
                f"🗑️ Eliminar documentos de {ciudad_limpiar}",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(f"Eliminando documentos de {ciudad_limpiar}..."):
                    count = limpiar_ciudad(ciudad_limpiar)
                st.success(f"✅ Eliminados **{count} documentos** de {ciudad_limpiar}.")
                # Invalidar caché de stats
                st.session_state.pop("kb_stats", None)
                st.rerun()