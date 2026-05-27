# modules/emergency_card.py
# Módulo 3: Emergency Card
# Información de emergencia accesible sin internet.
# Los datos por país y consejos están hardcodeados; los datos personales
# (pasaportes, hoteles, contacto Lima) se persisten en Firestore para que
# sigan disponibles tras un reload del navegador.

import streamlit as st

from utils.gcp_client import get_firestore_client

COLECCION_PERFIL = "perfil_familia"
DOC_PERFIL_ID    = "viaje_2026"

# ── Datos de emergencia por país ───────────────────────────────────────────
EMERGENCIAS = {
    "🇪🇸 España": {
        "color": "#AA151B",
        "ciudad": "Madrid",
        "numeros": {
            "🚨 Emergencias general": "112",
            "👮 Policía Nacional": "091",
            "🚒 Bomberos": "080",
            "🚑 Ambulancia": "061",
            "🛣️ Guardia Civil": "062",
        },
        "embajada_peru": {
            "nombre": "Embajada del Perú en Madrid",
            "direccion": "C/ Príncipe de Vergara 36, 2º dcha, 28001 Madrid",
            "telefono": "+34 914 314 242",
            "email": "embajada@embajadaperu.es",
            "horario": "Lunes a Viernes: 09:00 – 14:00",
            "emergencias_24h": "+34 914 314 242",
        },
        "hospitales": [
            {"nombre": "Hospital Universitario La Paz", "telefono": "+34 917 277 000", "direccion": "Paseo de la Castellana 261"},
            {"nombre": "Hospital Gregorio Marañón", "telefono": "+34 915 868 000", "direccion": "C/ del Doctor Esquerdo 46"},
            {"nombre": "Hospital Fundación Jiménez Díaz", "telefono": "+34 915 499 400", "direccion": "Av. Reyes Católicos 2"},
        ],
        "consejos": [
            "El 112 funciona en toda Europa, incluso sin saldo en el celular",
            "Los taxis oficiales en Madrid son blancos con franja roja diagonal",
            "El metro de Madrid tiene servicio 24h los fines de semana",
            "Lleva siempre fotocopia del pasaporte — nunca el original",
        ]
    },
    "🇫🇷 Francia": {
        "color": "#002395",
        "ciudad": "Bayona y París",
        "numeros": {
            "🚨 Emergencias general": "112",
            "👮 Policía": "17",
            "🚒 Bomberos": "18",
            "🚑 SAMU (Ambulancia)": "15",
            "🆘 Emergencias europeas": "112",
        },
        "embajada_peru": {
            "nombre": "Embajada del Perú en París",
            "direccion": "50 Avenue Kléber, 75116 París",
            "telefono": "+33 1 53 70 42 00",
            "email": "leparis@rree.gob.pe",
            "horario": "Lunes a Viernes: 09:00 – 13:00",
            "emergencias_24h": "+33 1 53 70 42 00",
        },
        "hospitales": [
            {"nombre": "Hôpital Lariboisière (París)", "telefono": "+33 1 49 95 65 65", "direccion": "2 Rue Ambroise Paré"},
            {"nombre": "American Hospital of Paris", "telefono": "+33 1 46 41 25 25", "direccion": "63 Bd Victor Hugo, Neuilly"},
            {"nombre": "Centre Hospitalier de Bayonne", "telefono": "+33 5 59 44 35 35", "direccion": "13 Av. de l'Interne Loëb, Bayonne"},
        ],
        "consejos": [
            "En París, el RER B conecta el aeropuerto Charles de Gaulle con el centro",
            "Guarda el ticket del metro — te lo pueden pedir hasta la salida",
            "En Bayona, la mayoría habla euskera y francés — el inglés es limitado",
            "Las farmacias tienen una cruz verde iluminada — venden medicamentos sin receta",
        ]
    },
    "🇧🇪 Bélgica": {
        "color": "#000000",
        "ciudad": "Bruselas",
        "numeros": {
            "🚨 Emergencias general": "112",
            "👮 Policía": "101",
            "🚒 Bomberos": "100",
            "🚑 Ambulancia": "100",
        },
        "embajada_peru": {
            "nombre": "Embajada del Perú en Bruselas",
            "direccion": "Av. de Tervueren 179, 1150 Bruselas",
            "telefono": "+32 2 733 33 19",
            "email": "embajada@embajadaperu.be",
            "horario": "Lunes a Viernes: 09:00 – 13:00",
            "emergencias_24h": "+32 2 733 33 19",
        },
        "hospitales": [
            {"nombre": "Cliniques Universitaires Saint-Luc", "telefono": "+32 2 764 11 11", "direccion": "Av. Hippocrate 10"},
            {"nombre": "Hôpital Erasme", "telefono": "+32 2 555 31 11", "direccion": "Route de Lennik 808"},
        ],
        "consejos": [
            "Bruselas tiene 3 idiomas oficiales: francés, neerlandés y alemán",
            "El transporte público STIB/MIVB cubre metro, tram y bus",
            "La Grand Place es el corazón — todo está a poca distancia caminando",
            "El chocolate belga es famoso — Neuhaus y Godiva son las marcas icónicas",
        ]
    },
    "🇳🇱 Países Bajos": {
        "color": "#AE1C28",
        "ciudad": "Ámsterdam",
        "numeros": {
            "🚨 Emergencias general": "112",
            "👮 Policía": "0900-8844",
            "🚒 Bomberos": "112",
            "🚑 Ambulancia": "112",
        },
        "embajada_peru": {
            "nombre": "Embajada del Perú en La Haya",
            "direccion": "Nassauplein 4, 2585 EA La Haya",
            "telefono": "+31 70 365 3500",
            "email": "embajada@embajadaperu.nl",
            "horario": "Lunes a Viernes: 09:00 – 13:00",
            "emergencias_24h": "+31 70 365 3500",
        },
        "hospitales": [
            {"nombre": "Amsterdam UMC", "telefono": "+31 20 566 9111", "direccion": "Meibergdreef 9"},
            {"nombre": "OLVG Hospital", "telefono": "+31 20 599 9111", "direccion": "Oosterpark 9"},
        ],
        "consejos": [
            "Los ciclistas tienen prioridad — cuidado al cruzar carriles bici",
            "Los tranvías (tram) son el transporte más práctico en el centro",
            "El GVB es la empresa de transporte — compra el OV-chipkaart",
            "La mayoría de holandeses habla inglés perfectamente",
        ]
    },
}

# ── Datos del seguro de viaje ──────────────────────────────────────────────
SEGURO = {
    "costo": "S/. 558.84",
    "cobertura": "3 personas — toda la familia",
    "nota": "Guarda el número de póliza y teléfono de asistencia en tu celular",
    "consejos": [
        "Guarda una foto de la póliza en Google Photos",
        "Anota el número de asistencia 24h antes de salir de Lima",
        "En caso de emergencia médica, llama primero al seguro antes de ir al hospital",
        "Guarda todos los recibos médicos — son necesarios para el reembolso",
    ]
}

# ── Datos de la familia ────────────────────────────────────────────────────
FAMILIA = {
    "members": [
        {"nombre": "Jonathan", "edad": 46, "pasaporte": "Anotar aquí"},
        {"nombre": "Giovanna", "edad": 46, "pasaporte": "Anotar aquí"},
        {"nombre": "Camila", "edad": 15, "pasaporte": "Anotar aquí"},
    ],
    "contacto_lima": "Anotar número de familiar en Lima",
    "hotel_madrid": "Anotar cuando reserves",
    "hotel_bayona": "Anotar cuando reserves",
    "hotel_paris": "Anotar cuando reserves",
    "hotel_bruselas": "Anotar cuando reserves",
}

# ── Persistencia en Firestore ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def cargar_perfil_familia() -> dict:
    """
    Lee el perfil persistido. Cache de 5 min para evitar reads en cada
    rerender de Streamlit sin perder la actualización entre miembros.
    """
    try:
        db = get_firestore_client()
        snap = db.collection(COLECCION_PERFIL).document(DOC_PERFIL_ID).get()
        return snap.to_dict() if snap.exists else {}
    except Exception:
        return {}


def guardar_perfil_familia(datos: dict) -> bool:
    """Guarda el perfil completo (merge) y limpia la cache de lectura."""
    try:
        db = get_firestore_client()
        db.collection(COLECCION_PERFIL).document(DOC_PERFIL_ID).set(
            datos, merge=True
        )
        cargar_perfil_familia.clear()
        return True
    except Exception as e:
        st.error(f"No se pudo guardar el perfil: {e}")
        return False


# ── UI Principal ───────────────────────────────────────────────────────────
def mostrar():
    st.title("🆘 Emergency Card")
    st.caption("Información crítica de emergencia — disponible sin internet")

    # Alerta visual importante
    st.error("🚨 En cualquier emergencia en Europa: llama al **112**")

    # ── Tabs principales ───────────────────────────────────────────────────
    tab_paises, tab_seguro, tab_familia, tab_consejos = st.tabs([
        "🌍 Por País", "🛡️ Seguro de Viaje", "👨‍👩‍👧 Datos Familia", "💡 Consejos"
    ])

    # ── TAB 1: Por País ────────────────────────────────────────────────────
    with tab_paises:
        pais = st.selectbox(
            "Selecciona el país donde estás",
            list(EMERGENCIAS.keys())
        )

        datos = EMERGENCIAS[pais]

        st.subheader(f"Estás en: {datos['ciudad']}")

        # Números de emergencia — lo más importante primero
        st.subheader("📞 Números de Emergencia")
        cols = st.columns(len(datos["numeros"]))
        for i, (servicio, numero) in enumerate(datos["numeros"].items()):
            with cols[i]:
                st.metric(servicio, numero)

        st.divider()

        # Embajada peruana
        st.subheader("🇵🇪 Embajada del Perú")
        emb = datos["embajada_peru"]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{emb['nombre']}**")
            st.write(f"📍 {emb['direccion']}")
            st.write(f"📞 {emb['telefono']}")
        with col2:
            st.write(f"📧 {emb['email']}")
            st.write(f"🕐 {emb['horario']}")
            st.error(f"🚨 Emergencias 24h: **{emb['emergencias_24h']}**")

        st.divider()

        # Hospitales cercanos
        st.subheader("🏥 Hospitales Cercanos")
        for hosp in datos["hospitales"]:
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{hosp['nombre']}**")
                    st.write(f"📍 {hosp['direccion']}")
                with col2:
                    st.write(f"📞 {hosp['telefono']}")

        st.divider()

        # Consejos locales
        st.subheader("💡 Consejos Locales")
        for consejo in datos["consejos"]:
            st.info(f"ℹ️ {consejo}")

    # ── TAB 2: Seguro ──────────────────────────────────────────────────────
    with tab_seguro:
        st.subheader("🛡️ Tu Seguro de Viaje")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Costo pagado", SEGURO["costo"])
        with col2:
            st.metric("Cobertura", SEGURO["cobertura"])

        st.warning(f"⚠️ {SEGURO['nota']}")

        st.subheader("Qué hacer en caso de emergencia médica")
        pasos = [
            "1️⃣ Llama al 112 si es urgente",
            "2️⃣ Llama al número de asistencia 24h de tu seguro",
            "3️⃣ Ve al hospital más cercano indicado por el seguro",
            "4️⃣ Guarda TODOS los recibos y documentos médicos",
            "5️⃣ Notifica a la embajada peruana si es grave",
        ]
        for paso in pasos:
            st.write(paso)

        st.divider()
        st.subheader("📋 Checklist antes de salir")
        checks = [
            "Número de póliza guardado en el celular",
            "Teléfono de asistencia 24h guardado",
            "Foto de la póliza en Google Photos",
            "Todos conocen dónde está el documento físico",
        ]
        for check in checks:
            st.checkbox(check)

    # ── TAB 3: Datos Familia ───────────────────────────────────────────────
    with tab_familia:
        st.subheader("👨‍👩‍👧 Datos de la Familia")
        st.info("💡 Completa estos datos antes de viajar. Son críticos en una emergencia y se guardan en la nube para todos los miembros.")

        perfil = cargar_perfil_familia()
        miembros_guardados = perfil.get("miembros", {})
        hoteles_guardados  = perfil.get("hoteles", {})

        with st.form("form_perfil_familia", clear_on_submit=False):
            nuevos_miembros = {}
            for miembro in FAMILIA["members"]:
                nombre = miembro["nombre"]
                datos_prev = miembros_guardados.get(nombre, {})
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**{nombre}**")
                        st.write(f"Edad: {miembro['edad']} años")
                    with col2:
                        pasaporte = st.text_input(
                            "N° Pasaporte",
                            value=datos_prev.get("pasaporte", ""),
                            key=f"pasaporte_{nombre}",
                            placeholder="Ej: C123456",
                        )
                    with col3:
                        sangre = st.text_input(
                            "Tipo de sangre",
                            value=datos_prev.get("sangre", ""),
                            key=f"sangre_{nombre}",
                            placeholder="Ej: O+",
                        )
                nuevos_miembros[nombre] = {
                    "pasaporte": pasaporte,
                    "sangre":    sangre,
                }

            st.divider()
            st.subheader("📍 Hospedajes")
            col1, col2 = st.columns(2)
            with col1:
                hotel_madrid = st.text_input(
                    "Hotel Madrid",
                    value=hoteles_guardados.get("madrid", ""),
                    placeholder="Nombre, dirección, teléfono",
                )
                hotel_bayona = st.text_input(
                    "Hotel Bayona",
                    value=hoteles_guardados.get("bayona", ""),
                    placeholder="Nombre, dirección, teléfono",
                )
            with col2:
                hotel_paris = st.text_input(
                    "Hotel París",
                    value=hoteles_guardados.get("paris", ""),
                    placeholder="Nombre, dirección, teléfono",
                )
                hotel_bruselas = st.text_input(
                    "Hotel Bruselas",
                    value=hoteles_guardados.get("bruselas", ""),
                    placeholder="Nombre, dirección, teléfono",
                )

            contacto_lima = st.text_input(
                "📞 Contacto de emergencia en Lima",
                value=perfil.get("contacto_lima", ""),
                placeholder="Nombre y teléfono de familiar en Lima",
            )

            if st.form_submit_button("💾 Guardar perfil", type="primary", use_container_width=True):
                ok = guardar_perfil_familia({
                    "miembros": nuevos_miembros,
                    "hoteles": {
                        "madrid":   hotel_madrid,
                        "bayona":   hotel_bayona,
                        "paris":    hotel_paris,
                        "bruselas": hotel_bruselas,
                    },
                    "contacto_lima": contacto_lima,
                })
                if ok:
                    st.success("✅ Perfil guardado. Disponible para toda la familia.")

    # ── TAB 4: Consejos Generales ──────────────────────────────────────────
    with tab_consejos:
        st.subheader("💡 Consejos Generales para Europa")

        with st.expander("🎒 Documentos — llevar siempre", expanded=True):
            docs = [
                "✅ Pasaporte original con al menos 6 meses de vigencia",
                "✅ Fotocopia del pasaporte (sepárate del original)",
                "✅ Foto digital del pasaporte en Google Photos",
                "✅ Póliza del seguro de viaje impresa y en el celular",
                "✅ Tarjeta de crédito/débito internacional",
                "✅ Algo de efectivo en euros (€50-100 por persona)",
            ]
            for doc in docs:
                st.write(doc)

        with st.expander("💳 Dinero y pagos"):
            tips = [
                "💳 Visa y Mastercard se aceptan en casi todos lados",
                "💶 Ten siempre €20-30 en efectivo para mercados y pequeños negocios",
                "🏧 Los cajeros del aeropuerto tienen comisiones altas — usa los del centro",
                "📱 Avisa a tu banco antes de viajar para que no bloqueen la tarjeta",
                "💱 No cambies dinero en casas de cambio del aeropuerto — la tasa es mala",
            ]
            for tip in tips:
                st.write(tip)

        with st.expander("📱 Conectividad"):
            tips = [
                "📶 Compra una SIM europea en el aeropuerto de Madrid al llegar",
                "🌐 Orange, Vodafone y Movistar tienen planes desde €15 para turistas",
                "📡 La SIM europea funciona en España, Francia, Bélgica y Países Bajos",
                "💾 Descarga los mapas offline de Google Maps antes de salir",
                "🗺️ Maps.me es excelente para navegación sin internet",
            ]
            for tip in tips:
                st.write(tip)

        with st.expander("🚨 Si pierdes el pasaporte"):
            pasos = [
                "1️⃣ Ve inmediatamente a la embajada o consulado peruano más cercano",
                "2️⃣ Lleva la fotocopia del pasaporte y una foto carnet",
                "3️⃣ Denuncia la pérdida ante la policía local (necesitas el parte policial)",
                "4️⃣ La embajada te emitirá un pasaporte de emergencia en 24-48h",
                "5️⃣ Notifica a tu seguro de viaje — puede cubrir los gastos",
            ]
            for paso in pasos:
                st.write(paso)

        with st.expander("🏥 Si necesitas atención médica"):
            pasos = [
                "1️⃣ Para emergencias graves: llama al 112",
                "2️⃣ Para emergencias menores: busca una farmacia (cruz verde)",
                "3️⃣ Llama al seguro ANTES de ir al hospital para autorización",
                "4️⃣ Guarda todos los documentos: recibos, diagnósticos, recetas",
                "5️⃣ Pide siempre la documentación en inglés si es posible",
            ]
            for paso in pasos:
                st.write(paso)
