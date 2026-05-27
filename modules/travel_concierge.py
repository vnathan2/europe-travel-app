# modules/travel_concierge.py
import os
import re
from datetime import datetime

import google.generativeai as genai
import requests
import streamlit as st
from dotenv import load_dotenv

from utils.gcp_client import get_secret
from utils.knowledge_base import buscar_conocimiento, formatear_conocimiento, init_embeddings

load_dotenv()

ITINERARIO_CONTEXTO = """
VIAJE FAMILIAR A EUROPA — JULIO 2026
Familia: Jonathan (46), Giovanna (46, cumpleaños 21 julio), Camila (cumple 15 años el 17 julio)
Presupuesto disponible: S/. 31,941 (~€7,985)

=== VUELOS ===
Ida: Lima → Madrid | 14 jul 10:20am → 15 jul 05:10am
Vuelta: Ámsterdam → Madrid 30 jul ~15:00 → Madrid → Lima 30 jul 23:45

=== MADRID (15-18 julio) ===
Día 17 CUMPLEAÑOS CAMILA 15 AÑOS: Parque Warner → StreetXO
Día 18: Tour Bernabéu → El Botín → Gran Vía → Mercado San Miguel

=== BAYONA (19-20 julio) ===
Tren Madrid→Hendaya→Bayona (~5-6h, €70-80pp)

=== PARÍS (21-24 julio) ===
TGV Bayona→París (~4.5h, €60-70pp)
Día 21 CUMPLEAÑOS GIOVANNA 46 AÑOS: Torre Eiffel → Arco del Triunfo → Crucero Sena → Le Train Bleu
Día 23: Versalles | Día 24: Disneyland París

=== BRUSELAS (25-26 julio) ===
Eurostar París→Bruselas (~1.5h, €35-50pp)

=== ÁMSTERDAM (27-30 julio) — casa familiar GRATIS ===
Eurostar Bruselas→Ámsterdam (~2h, €30-50pp)
Día 27: Plaza Dam → Ana Frank → De Kas
Día 28: Van Gogh → Rijksmuseum
Día 29: Zaanse Schans → Crucero canales
Día 30 REGRESO: AMS→MAD→LIM

=== PRESUPUESTO ===
Madrid: ~€1,600-1,700 | Bayona: ~€700-800 | París: ~€2,500-2,600
Bruselas: ~€730-840 | Ámsterdam: ~€1,040-1,220 | TOTAL: ~€6,570-7,160
"""

SYSTEM_PROMPT = f"""Eres Lady 🐾, una schnauzer miniatura muy inteligente y simpática
que es la mascota virtual de la familia Jonathan, Giovanna y Camila.
Eres experta en viajes por Europa y das consejos como si fueras una perrita
que ya conoce cada rincón de estas ciudades con sus pequeñas patas.
Tu personalidad: alegre, cariñosa, entusiasta, muy útil y a veces haces
referencias divertidas a ser una perrita (olfatear los mejores restaurantes,
tus patas te llevan a los mejores lugares, ladrar de emoción ante un buen plan, etc.).

REGLAS ESTRICTAS:
1. Responde SIEMPRE en español
2. Para preguntas sobre SU itinerario específico usa el contexto
3. Para CUALQUIER pregunta sobre restaurantes, hoteles, precios,
   clima, eventos, actividades, lugares o información externa
   DEBES responder ÚNICAMENTE con: [BUSCAR_WEB: tu query aquí]
   SIN agregar texto adicional antes ni después
4. Solo después de recibir resultados web, responde normalmente

EJEMPLOS OBLIGATORIOS:
- "¿Qué restaurantes hay cerca de la Torre Eiffel?" → [BUSCAR_WEB: restaurantes cerca Torre Eiffel París 2026]
- "¿Qué tiempo hará en Madrid?" → [BUSCAR_WEB: clima Madrid julio 2026]
- "¿Hay eventos en Ámsterdam?" → [BUSCAR_WEB: eventos Ámsterdam julio 2026]
- "¿Cuánto cuesta el metro en París?" → [BUSCAR_WEB: precio metro París 2026]
- "¿Qué ver en Bruselas?" → [BUSCAR_WEB: qué ver Bruselas turismo 2026]

PREGUNTAS que respondes SIN buscar:
- ¿A qué hora sale nuestro tren? → del itinerario
- ¿Cuánto presupuesto nos queda? → del itinerario
- ¿Qué día es el cumpleaños de Camila? → del itinerario

ITINERARIO:
{ITINERARIO_CONTEXTO}
"""

# ── Búsqueda web con Tavily ────────────────────────────────────────────────
def buscar_en_web(query: str) -> list:
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            try:
                api_key = get_secret("TAVILY_API_KEY")
            except Exception:
                return []

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=4,
            include_answer=True,
        )

        resultados = []
        if response.get("answer"):
            resultados.append({
                "titulo": "Respuesta directa",
                "snippet": response["answer"],
                "url": "",
            })
        for r in response.get("results", []):
            resultados.append({
                "titulo": r.get("title", ""),
                "snippet": r.get("content", "")[:300],
                "url": r.get("url", ""),
            })
        return resultados
    except Exception as e:
        # Tavily es opcional: si falla (key inválida, red, cuota) Lady responde
        # igual sin web. No inyectamos el error al prompt para no confundir al
        # modelo ni filtrar ruido a la UI.
        from utils.logger import get_logger
        get_logger(__name__).warning("Búsqueda Tavily falló, sigo sin web: %s", e)
        return []


def formatear_resultados(resultados: list) -> str:
    if not resultados:
        return "No se encontraron resultados."
    texto = "RESULTADOS WEB:\n"
    for i, r in enumerate(resultados, 1):
        texto += f"\n{i}. {r['titulo']}\n   {r['snippet']}\n"
    return texto


def detectar_busqueda(respuesta: str) -> tuple:
    match = re.search(r'\[BUSCAR_WEB:\s*(.+?)\]', respuesta)
    if match:
        return True, match.group(1).strip()
    return False, ""


# Máximo de intercambios a mantener en contexto (1 par = 1 pregunta + 1 respuesta)
# 8 pares = 16 mensajes — suficiente contexto sin crecer indefinidamente
MAX_HISTORY_PAIRS = 8

# Timeout por llamada a Gemini (segundos). Acota el caso patológico de la API
# colgada (incidente 2026-05-12) sin abortar consultas legítimas lentas del
# camino RAG + web. 15s resultó muy agresivo y disparaba 504 Deadline Exceeded
# en el flujo de búsqueda web; 30s da holgura. Ajustable sin redeploy con la env
# GEMINI_TIMEOUT_SEC.
GEMINI_TIMEOUT_SEC = int(os.getenv("GEMINI_TIMEOUT_SEC", "30"))

@st.cache_resource
def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = get_secret("GEMINI_API_KEY")
        except Exception:
            return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )


def _sin_marcador(texto: str) -> str:
    # Defensa: nunca mostrar el marcador interno [BUSCAR_WEB: ...] al usuario,
    # aunque el modelo lo re-emita (p.ej. si la búsqueda web no encontró nada).
    return re.sub(r'\s*\[BUSCAR_WEB:.*?\]\s*', ' ', texto).strip()


def obtener_respuesta(model, historial: list, pregunta: str) -> tuple:
    try:
        init_embeddings()
        ciudad_mencionada = None
        for ciudad in ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]:
            if ciudad.lower() in pregunta.lower():
                ciudad_mencionada = ciudad
                break

        docs_relevantes = buscar_conocimiento(pregunta, ciudad_mencionada, top_k=4)
        contexto_kb = formatear_conocimiento(docs_relevantes)

        pregunta_enriquecida = pregunta
        if contexto_kb:
            pregunta_enriquecida = f"{pregunta}\n\n{contexto_kb}"

        # Limitar historial a los últimos MAX_HISTORY_PAIRS intercambios
        # para evitar que el costo en tokens crezca sin límite
        historial_reciente = historial[-(MAX_HISTORY_PAIRS * 2):]

        # Conversación stateless con generate_content (no start_chat) para poder
        # pasar request_options con timeout: ChatSession.send_message no acepta
        # request_options en google-generativeai 0.5.2. Copiamos la lista para no
        # mutar el historial de session_state que maneja el caller.
        opciones = {"request_options": {"timeout": GEMINI_TIMEOUT_SEC}}
        contenidos = list(historial_reciente)
        contenidos.append({"role": "user", "parts": [pregunta_enriquecida]})

        primera = model.generate_content(contenidos, **opciones).text
        necesita, query = detectar_busqueda(primera)

        if not necesita:
            return _sin_marcador(primera), []

        resultados = buscar_en_web(query)
        texto_resultados = formatear_resultados(resultados)

        prompt2 = f"""
Pregunta original: {pregunta}
{texto_resultados}
Responde en español integrando toda la información disponible.
Sé amigable y práctico para la familia.
"""
        contenidos.append({"role": "model", "parts": [primera]})
        contenidos.append({"role": "user", "parts": [prompt2]})
        respuesta_final = model.generate_content(contenidos, **opciones).text
        return _sin_marcador(respuesta_final), resultados
    except Exception as e:
        # Fallback offline: si Gemini falla, intentar matchear contra FAQ
        # pre-canned. Caso típico durante el viaje: API caída o sin red.
        from utils.logger import get_logger
        from utils.offline_faqs import buscar_faq_offline, respuesta_fallback_generica
        get_logger(__name__).warning(
            "Gemini falló en obtener_respuesta, usando fallback offline. Error: %s", e
        )
        faq = buscar_faq_offline(pregunta)
        if faq:
            return (
                f"🐾 *Lady está sin red, pero tengo esto guardado para ti:*\n\n"
                f"**{faq['pregunta']}**\n\n{faq['respuesta']}"
            ), []
        return respuesta_fallback_generica(), []


# ── Constantes para alertas ────────────────────────────────────────────────
ACTIVIDADES_OUTDOOR = {
    "mad_05", "mad_12", "mad_16",
    "bay_03", "bay_04",
    "par_03", "par_04", "par_05",
    "par_11", "par_13",
    "bru_02", "bru_04",
    "bru_07",
    "ams_02", "ams_10", "ams_12",
}

CIUDAD_POR_FECHA = {
    "2026-07-15": ("Madrid",    40.4168, -3.7038),
    "2026-07-16": ("Madrid",    40.4168, -3.7038),
    "2026-07-17": ("Madrid",    40.4168, -3.7038),
    "2026-07-18": ("Madrid",    40.4168, -3.7038),
    "2026-07-19": ("Bayona",    43.4929, -1.4748),
    "2026-07-20": ("Bayona",    43.4929, -1.4748),
    "2026-07-21": ("París",     48.8566,  2.3522),
    "2026-07-22": ("París",     48.8566,  2.3522),
    "2026-07-23": ("París",     48.8566,  2.3522),
    "2026-07-24": ("París",     48.8566,  2.3522),
    "2026-07-25": ("Bruselas",  50.8503,  4.3517),
    "2026-07-26": ("Bruselas",  50.8503,  4.3517),
    "2026-07-27": ("Ámsterdam", 52.3676,  4.9041),
    "2026-07-28": ("Ámsterdam", 52.3676,  4.9041),
    "2026-07-29": ("Ámsterdam", 52.3676,  4.9041),
    "2026-07-30": ("Ámsterdam", 52.3676,  4.9041),
}

COORDS_ACTIVIDAD = {
    "mad_01": (40.4936, -3.5773, "Aeropuerto Adolfo Suárez Barajas"),
    "mad_02": (40.4235, -3.6986, "Brunchit Chueca Madrid"),
    "mad_03": (40.4138, -3.6922, "Museo del Prado Madrid"),
    "mad_04": (40.4147, -3.6996, "Los Montes de Galicia Madrid"),
    "mad_05": (40.4153, -3.6844, "Parque del Retiro Madrid"),
    "mad_06": (40.4105, -3.7010, "Taberna El Sur Madrid"),
    "mad_07": (40.4179, -3.7143, "Palacio Real Madrid"),
    "mad_08": (40.4130, -3.7095, "Rosi La Loca Madrid"),
    "mad_09": (40.4082, -3.6939, "Museo Reina Sofia Madrid"),
    "mad_10": (40.4185, -3.7118, "La Bola Taberna Madrid"),
    "mad_11": (40.3436, -3.5738, "Parque Warner Madrid"),
    "mad_12": (40.3436, -3.5738, "Parque Warner Madrid"),
    "mad_13": (40.4289, -3.6824, "StreetXO Madrid"),
    "mad_14": (40.4531, -3.6883, "Estadio Santiago Bernabeu"),
    "mad_15": (40.4130, -3.7095, "El Botin Madrid"),
    "mad_16": (40.4200, -3.7025, "Gran Via Madrid"),
    "mad_17": (40.4151, -3.7088, "Mercado San Miguel Madrid"),
    "bay_01": (43.4929, -1.4748, "Gare de Bayonne Francia"),
    "bay_02": (43.4920, -1.4732, "Bakera Bayonne"),
    "bay_03": (43.4932, -1.4751, "Cathedrale Sainte Marie Bayonne"),
    "bay_04": (43.4925, -1.4755, "Casco Antiguo Bayonne"),
    "bay_05": (43.4915, -1.4740, "Restaurant Nuance Bayonne"),
    "bay_06": (43.4921, -1.4748, "Le Carre Bayonne"),
    "bay_07": (43.4940, -1.4720, "Musee Basque Bayonne"),
    "bay_08": (43.4928, -1.4745, "Bar Basque Bayonne"),
    "bay_09": (43.4918, -1.4752, "Musee du Chocolat Bayonne"),
    "bay_10": (43.4916, -1.4750, "Woods Bayonne"),
    "par_01": (48.8408,  2.3212, "Gare Montparnasse Paris"),
    "par_02": (48.8636,  2.3304, "Angelina Paris"),
    "par_03": (48.8584,  2.2945, "Torre Eiffel Paris"),
    "par_04": (48.8738,  2.2950, "Arco del Triunfo Paris"),
    "par_05": (48.8566,  2.3522, "Bateaux Mouches Paris"),
    "par_06": (48.8443,  2.3729, "Le Train Bleu Paris"),
    "par_07": (48.8606,  2.3376, "Museo del Louvre Paris"),
    "par_08": (48.8842,  2.3336, "Bouillon Pigalle Paris"),
    "par_09": (48.8554,  2.3451, "Sainte Chapelle Paris"),
    "par_10": (48.8559,  2.3629, "Chez Janou Paris"),
    "par_11": (48.8049,  2.1204, "Palacio de Versalles"),
    "par_12": (48.8523,  2.3393, "Le Procope Paris"),
    "par_13": (48.8674,  2.7836, "Disneyland Paris"),
    "par_14": (48.8559,  2.3629, "Chez Janou Paris"),
    "bru_01": (50.8364,  4.3366, "Bruxelles Midi"),
    "bru_02": (50.8467,  4.3525, "Grand Place Bruselas"),
    "bru_03": (50.8468,  4.3527, "Chez Leon Bruselas"),
    "bru_04": (50.8450,  4.3499, "Manneken Pis Bruselas"),
    "bru_05": (50.8538,  4.3468, "Noordzee Bruselas"),
    "bru_06": (50.8445,  4.3501, "Maison Dandoy Bruselas"),
    "bru_07": (50.8948,  4.3413, "Atomium Bruselas"),
    "bru_08": (50.8470,  4.3530, "La Roue d'Or Bruselas"),
    "bru_09": (50.8513,  4.3556, "Museo del Comic Bruselas"),
    "bru_10": (50.8498,  4.3457, "Fin de Siecle Bruselas"),
    "bru_11": (50.8364,  4.3366, "Bruxelles Midi"),
    "ams_01": (52.3791,  4.8994, "Amsterdam Centraal"),
    "ams_02": (52.3731,  4.8936, "Plaza Dam Amsterdam"),
    "ams_03": (52.3745,  4.8872, "The Pancake Bakery Amsterdam"),
    "ams_04": (52.3752,  4.8840, "Casa de Ana Frank Amsterdam"),
    "ams_05": (52.3577,  4.9218, "De Kas Amsterdam"),
    "ams_06": (52.3584,  4.8811, "Museo Van Gogh Amsterdam"),
    "ams_07": (52.3662,  4.8628, "Foodhallen Amsterdam"),
    "ams_08": (52.3600,  4.8852, "Rijksmuseum Amsterdam"),
    "ams_09": (52.3729,  4.9048, "Restaurant Greetje Amsterdam"),
    "ams_10": (52.4740,  4.8148, "Zaanse Schans"),
    "ams_11": (52.3726,  4.8902, "d'Vijff Vlieghen Amsterdam"),
    "ams_12": (52.3752,  4.8840, "Anne Frank Boat Tours Amsterdam"),
    "ams_13": (52.3733,  4.8808, "Moeders Amsterdam"),
    "ret_01": (52.3080,  4.7642, "Aeropuerto Schiphol Amsterdam"),
    "ret_02": (52.3080,  4.7642, "Aeropuerto Schiphol Amsterdam"),
    "ret_03": (40.4936, -3.5773, "Aeropuerto Barajas Madrid T4"),
    "ret_04": (40.4936, -3.5773, "Aeropuerto Barajas Madrid T4"),
}


# ── Funciones de clima y mapas ─────────────────────────────────────────────
def get_clima_hoy(lat: float, lon: float) -> dict:
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,weathercode,precipitation_probability"
            f"&timezone=Europe/Madrid"
            f"&forecast_days=1"
        )
        r = requests.get(url, timeout=5)
        data = r.json()
        hourly = data.get("hourly", {})
        return {
            "horas":   hourly.get("time", []),
            "temp":    hourly.get("temperature_2m", []),
            "wmo":     hourly.get("weathercode", []),
            "prob_ll": hourly.get("precipitation_probability", []),
        }
    except Exception:
        return {}


def wmo_a_texto(code: int) -> tuple:
    if code == 0:
        return "☀️", "Despejado"
    elif code <= 3:
        return "⛅", "Parcialmente nublado"
    elif code <= 49:
        return "🌫️", "Niebla"
    elif code <= 67:
        return "🌧️", "Lluvia"
    elif code <= 77:
        return "❄️", "Nieve"
    elif code <= 82:
        return "🌦️", "Chubascos"
    elif code <= 99:
        return "⛈️", "Tormenta"
    return "🌡️", "Desconocido"


def hay_lluvia(wmo_code: int, prob: int) -> bool:
    return wmo_code >= 51 or prob >= 60


def google_maps_url(lat: float, lon: float, nombre: str) -> str:
    nombre_enc = requests.utils.quote(nombre)
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lon}"
        f"&destination_place_id={nombre_enc}"
        f"&travelmode=walking"
    )


def sugerencia_lluvia_gemini(actividad: dict, ciudad: str, temp: float) -> str:
    try:
        model = init_gemini()
        if not model:
            return ""
        prompt = f"""
Eres Lady 🐾, una schnauzer viajera muy simpática.
La familia peruana (Jonathan, Giovanna, Camila 15 años) tiene planeado:
"{actividad['nombre']}" a las {actividad['hora']} en {ciudad}.

Problema: Está lloviendo ({temp:.0f}°C).
Esta es una actividad al aire libre.

Sugiere 2-3 alternativas bajo techo CERCANAS en {ciudad},
considerando que son turistas y tienen buen gusto.
Máximo 80 palabras, en español, con emojis.
"""
        return model.generate_content(prompt).text
    except Exception:
        return "Considera visitar un museo cercano o un café."


# ══════════════════════════════════════════════════════════════════════════
# ITINERARIO COMPLETO
# ══════════════════════════════════════════════════════════════════════════
ITINERARIO_CHECKS = [
    {
        "fecha": "Mié 15 Jul", "ciudad": "Madrid", "emoji": "🇪🇸",
        "especial": None,
        "actividades": [
            {"id": "mad_01", "hora": "05:10", "tipo": "transporte",
             "icono": "🛬", "nombre": "Llegada Barajas T4",
             "detalle": "Taxi al hotel ~€30, 30-40 min", "costo": 30},
            {"id": "mad_02", "hora": "09:00", "tipo": "restaurante",
             "icono": "🍳", "nombre": "Desayuno Brunchit Chueca",
             "detalle": "C/ Pelayo 18 — €15pp", "costo": 45},
            {"id": "mad_03", "hora": "11:30", "tipo": "atraccion",
             "icono": "🎨", "nombre": "Museo del Prado",
             "detalle": "Paseo del Prado s/n — €15pp", "costo": 45},
            {"id": "mad_04", "hora": "14:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Los Montes de Galicia",
             "detalle": "C/ Echegaray 17 — €25pp", "costo": 75},
            {"id": "mad_05", "hora": "16:30", "tipo": "atraccion",
             "icono": "🌳", "nombre": "Parque del Retiro",
             "detalle": "Plaza de la Independencia — Gratis", "costo": 0},
            {"id": "mad_06", "hora": "20:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Taberna El Sur",
             "detalle": "C/ Torrecilla del Leal 12 — €20pp", "costo": 60},
        ]
    },
    {
        "fecha": "Jue 16 Jul", "ciudad": "Madrid", "emoji": "🇪🇸",
        "especial": None,
        "actividades": [
            {"id": "mad_07", "hora": "09:00", "tipo": "atraccion",
             "icono": "👑", "nombre": "Palacio Real",
             "detalle": "C/ Bailén s/n — €12pp", "costo": 36},
            {"id": "mad_08", "hora": "12:00", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Rosi La Loca",
             "detalle": "C/ Cuchilleros 3 — €25pp", "costo": 75},
            {"id": "mad_09", "hora": "15:00", "tipo": "atraccion",
             "icono": "🎨", "nombre": "Museo Reina Sofía",
             "detalle": "C/ Santa Isabel 52 — €12pp", "costo": 36},
            {"id": "mad_10", "hora": "19:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena La Bola Taberna",
             "detalle": "C/ Bola 5 — €30pp", "costo": 90},
        ]
    },
    {
        "fecha": "Vie 17 Jul", "ciudad": "Madrid", "emoji": "🇪🇸",
        "especial": "🎂 CUMPLEAÑOS CAMILA — 15 AÑOS",
        "actividades": [
            {"id": "mad_11", "hora": "08:00", "tipo": "transporte",
             "icono": "🚕", "nombre": "Taxi al Parque Warner",
             "detalle": "~40 min, €40 ida", "costo": 40},
            {"id": "mad_12", "hora": "09:30", "tipo": "atraccion",
             "icono": "🎢", "nombre": "Parque Warner Madrid",
             "detalle": "San Martín de la Vega — €32.90pp", "costo": 99},
            {"id": "mad_13", "hora": "20:00", "tipo": "restaurante",
             "icono": "🎂", "nombre": "Cena especial StreetXO",
             "detalle": "C/ Serrano 52 — €45pp", "costo": 135},
        ]
    },
    {
        "fecha": "Sáb 18 Jul", "ciudad": "Madrid", "emoji": "🇪🇸",
        "especial": None,
        "actividades": [
            {"id": "mad_14", "hora": "09:00", "tipo": "atraccion",
             "icono": "⚽", "nombre": "Tour Santiago Bernabéu",
             "detalle": "Av. Concha Espina 1 — €28pp", "costo": 84},
            {"id": "mad_15", "hora": "12:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo El Botín",
             "detalle": "C/ Cuchilleros 17 — €35pp", "costo": 105},
            {"id": "mad_16", "hora": "15:00", "tipo": "compras",
             "icono": "🛍️", "nombre": "Compras Gran Vía",
             "detalle": "Zara, H&M, El Corte Inglés", "costo": 0},
            {"id": "mad_17", "hora": "19:00", "tipo": "restaurante",
             "icono": "🥘", "nombre": "Cena Mercado San Miguel",
             "detalle": "Plaza de San Miguel — €25pp", "costo": 80},
        ]
    },
    {
        "fecha": "Dom 19 Jul", "ciudad": "Bayona", "emoji": "🇫🇷",
        "especial": None,
        "actividades": [
            {"id": "bay_01", "hora": "08:00", "tipo": "transporte",
             "icono": "🚄", "nombre": "Tren Madrid → Bayona",
             "detalle": "AVE + cambio Hendaya ~5-6h, €75pp", "costo": 225},
            {"id": "bay_02", "hora": "14:00", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Bakera",
             "detalle": "38 Rue d'Espagne — €25pp", "costo": 75},
            {"id": "bay_03", "hora": "15:30", "tipo": "atraccion",
             "icono": "⛪", "nombre": "Cathédrale Sainte-Marie",
             "detalle": "Place Pasteur — Gratis", "costo": 0},
            {"id": "bay_04", "hora": "18:00", "tipo": "atraccion",
             "icono": "🚶", "nombre": "Casco Antiguo + Murallas",
             "detalle": "Centro histórico — Gratis", "costo": 0},
            {"id": "bay_05", "hora": "20:30", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Restaurant Nuance",
             "detalle": "8 Rue de la Monnaie — €35pp", "costo": 105},
        ]
    },
    {
        "fecha": "Lun 20 Jul", "ciudad": "Bayona", "emoji": "🇫🇷",
        "especial": None,
        "actividades": [
            {"id": "bay_06", "hora": "09:00", "tipo": "restaurante",
             "icono": "☕", "nombre": "Desayuno Le Carré",
             "detalle": "17 Rue Pontrique — €15pp", "costo": 45},
            {"id": "bay_07", "hora": "11:30", "tipo": "atraccion",
             "icono": "🏛️", "nombre": "Musée Basque",
             "detalle": "37 Quai des Corsaires — €8pp", "costo": 24},
            {"id": "bay_08", "hora": "14:00", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Bar Basque",
             "detalle": "Place de la Liberté — €20pp", "costo": 60},
            {"id": "bay_09", "hora": "16:00", "tipo": "atraccion",
             "icono": "🍫", "nombre": "Musée du Chocolat",
             "detalle": "Rue Lormand — €10pp", "costo": 30},
            {"id": "bay_10", "hora": "19:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Woods",
             "detalle": "26 Rue Lormand — €30pp", "costo": 90},
        ]
    },
    {
        "fecha": "Mar 21 Jul", "ciudad": "París", "emoji": "🇫🇷",
        "especial": "🌹 CUMPLEAÑOS GIOVANNA — 46 AÑOS EN PARÍS",
        "actividades": [
            {"id": "par_01", "hora": "08:00", "tipo": "transporte",
             "icono": "🚄", "nombre": "TGV Bayona → París",
             "detalle": "Gare Montparnasse ~4.5h, €65pp", "costo": 195},
            {"id": "par_02", "hora": "14:30", "tipo": "restaurante",
             "icono": "🥐", "nombre": "Angelina Paris",
             "detalle": "226 Rue de Rivoli — €30pp", "costo": 90},
            {"id": "par_03", "hora": "16:00", "tipo": "atraccion",
             "icono": "🗼", "nombre": "Torre Eiffel",
             "detalle": "Champ de Mars — €28pp", "costo": 84},
            {"id": "par_04", "hora": "18:30", "tipo": "atraccion",
             "icono": "🏛️", "nombre": "Arco del Triunfo",
             "detalle": "Place Charles de Gaulle — €13pp", "costo": 39},
            {"id": "par_05", "hora": "20:00", "tipo": "atraccion",
             "icono": "🚢", "nombre": "Crucero por el Sena",
             "detalle": "Bateaux Mouches — €20pp", "costo": 60},
            {"id": "par_06", "hora": "21:30", "tipo": "restaurante",
             "icono": "🎂", "nombre": "Cena Le Train Bleu",
             "detalle": "Gare de Lyon — €60pp", "costo": 180},
        ]
    },
    {
        "fecha": "Mié 22 Jul", "ciudad": "París", "emoji": "🇫🇷",
        "especial": None,
        "actividades": [
            {"id": "par_07", "hora": "09:00", "tipo": "atraccion",
             "icono": "🎨", "nombre": "Museo del Louvre",
             "detalle": "Rue de Rivoli — €17pp", "costo": 51},
            {"id": "par_08", "hora": "13:00", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Bouillon Pigalle",
             "detalle": "22 Bd de Clichy — €25pp", "costo": 75},
            {"id": "par_09", "hora": "15:00", "tipo": "atraccion",
             "icono": "⛪", "nombre": "Sainte-Chapelle",
             "detalle": "8 Bd du Palais — €11.50pp", "costo": 35},
            {"id": "par_10", "hora": "18:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Chez Janou",
             "detalle": "2 Rue Roger Verlomme — €35pp", "costo": 105},
        ]
    },
    {
        "fecha": "Jue 23 Jul", "ciudad": "París", "emoji": "🇫🇷",
        "especial": None,
        "actividades": [
            {"id": "par_11", "hora": "09:30", "tipo": "atraccion",
             "icono": "👑", "nombre": "Palacio de Versalles",
             "detalle": "Place d'Armes — €20pp", "costo": 60},
            {"id": "par_12", "hora": "19:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Le Procope",
             "detalle": "13 Rue de l'Ancienne Comédie — €40pp", "costo": 120},
        ]
    },
    {
        "fecha": "Vie 24 Jul", "ciudad": "París", "emoji": "🇫🇷",
        "especial": None,
        "actividades": [
            {"id": "par_13", "hora": "09:30", "tipo": "atraccion",
             "icono": "🎠", "nombre": "Disneyland París",
             "detalle": "Marne-la-Vallée — €105pp", "costo": 315},
            {"id": "par_14", "hora": "20:30", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Chez Janou",
             "detalle": "2 Rue Roger Verlomme — €35pp", "costo": 105},
        ]
    },
    {
        "fecha": "Sáb 25 Jul", "ciudad": "Bruselas", "emoji": "🇧🇪",
        "especial": None,
        "actividades": [
            {"id": "bru_01", "hora": "09:00", "tipo": "transporte",
             "icono": "🚄", "nombre": "Eurostar París → Bruselas",
             "detalle": "Gare du Nord ~1.5h, €42pp", "costo": 127},
            {"id": "bru_02", "hora": "11:30", "tipo": "atraccion",
             "icono": "🏛️", "nombre": "Grand Place",
             "detalle": "Grand Place — Gratis", "costo": 0},
            {"id": "bru_03", "hora": "13:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Chez Léon",
             "detalle": "Rue des Bouchers 18 — €25pp", "costo": 75},
            {"id": "bru_04", "hora": "15:30", "tipo": "atraccion",
             "icono": "🗿", "nombre": "Manneken Pis + Galeries Royales",
             "detalle": "Centro — Gratis", "costo": 0},
            {"id": "bru_05", "hora": "20:00", "tipo": "restaurante",
             "icono": "🦐", "nombre": "Cena Noordzee",
             "detalle": "Rue Sainte-Catherine 45 — €30pp", "costo": 90},
        ]
    },
    {
        "fecha": "Dom 26 Jul", "ciudad": "Bruselas→Ámsterdam",
        "emoji": "🇧🇪",
        "especial": None,
        "actividades": [
            {"id": "bru_06", "hora": "09:00", "tipo": "restaurante",
             "icono": "☕", "nombre": "Desayuno Maison Dandoy",
             "detalle": "Rue au Beurre 31 — €15pp", "costo": 45},
            {"id": "bru_07", "hora": "10:30", "tipo": "atraccion",
             "icono": "⚛️", "nombre": "Atomium",
             "detalle": "Square de l'Atomium — €16pp", "costo": 48},
            {"id": "bru_08", "hora": "13:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo La Roue d'Or",
             "detalle": "Rue des Chapeliers 26 — €30pp", "costo": 90},
            {"id": "bru_09", "hora": "15:30", "tipo": "atraccion",
             "icono": "📚", "nombre": "Museo del Cómic",
             "detalle": "Rue des Sables 20 — €12pp", "costo": 36},
            {"id": "bru_10", "hora": "18:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Fin de Siècle",
             "detalle": "Rue des Chartreux 9 — €25pp", "costo": 75},
            {"id": "bru_11", "hora": "20:30", "tipo": "transporte",
             "icono": "🚄", "nombre": "Eurostar → Ámsterdam",
             "detalle": "Bruxelles-Midi ~2h, €40pp", "costo": 120},
        ]
    },
    {
        "fecha": "Lun 27 Jul", "ciudad": "Ámsterdam", "emoji": "🇳🇱",
        "especial": None,
        "actividades": [
            {"id": "ams_01", "hora": "11:00", "tipo": "transporte",
             "icono": "🏠", "nombre": "Llegada casa familiar",
             "detalle": "Amsterdam Centraal → casa", "costo": 0},
            {"id": "ams_02", "hora": "13:00", "tipo": "atraccion",
             "icono": "🏛️", "nombre": "Plaza Dam + Palacio Real",
             "detalle": "Dam Square — €12pp", "costo": 36},
            {"id": "ams_03", "hora": "14:30", "tipo": "restaurante",
             "icono": "🥞", "nombre": "The Pancake Bakery",
             "detalle": "Prinsengracht 191 — €15pp", "costo": 45},
            {"id": "ams_04", "hora": "16:00", "tipo": "atraccion",
             "icono": "📖", "nombre": "Casa de Ana Frank",
             "detalle": "Westermarkt 20 — €16pp", "costo": 48},
            {"id": "ams_05", "hora": "19:00", "tipo": "restaurante",
             "icono": "🌿", "nombre": "Cena De Kas",
             "detalle": "Kamerlingh Onneslaan 3 — €45pp", "costo": 135},
        ]
    },
    {
        "fecha": "Mar 28 Jul", "ciudad": "Ámsterdam", "emoji": "🇳🇱",
        "especial": None,
        "actividades": [
            {"id": "ams_06", "hora": "09:00", "tipo": "atraccion",
             "icono": "🎨", "nombre": "Museo Van Gogh",
             "detalle": "Museumplein 6 — €20pp", "costo": 60},
            {"id": "ams_07", "hora": "12:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Almuerzo Foodhallen",
             "detalle": "Bellamyplein 51 — €20pp", "costo": 60},
            {"id": "ams_08", "hora": "14:30", "tipo": "atraccion",
             "icono": "🏛️", "nombre": "Rijksmuseum",
             "detalle": "Museumstraat 1 — €20pp", "costo": 60},
            {"id": "ams_09", "hora": "19:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Restaurant Greetje",
             "detalle": "Peperstraat 23 — €40pp", "costo": 120},
        ]
    },
    {
        "fecha": "Mié 29 Jul", "ciudad": "Ámsterdam", "emoji": "🇳🇱",
        "especial": None,
        "actividades": [
            {"id": "ams_10", "hora": "09:00", "tipo": "atraccion",
             "icono": "🌬️", "nombre": "Zaanse Schans",
             "detalle": "Zaandam — €15pp", "costo": 45},
            {"id": "ams_11", "hora": "13:30", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "d'Vijff Vlieghen",
             "detalle": "Spuistraat 294 — €35pp", "costo": 105},
            {"id": "ams_12", "hora": "15:30", "tipo": "atraccion",
             "icono": "🚢", "nombre": "Crucero por los canales",
             "detalle": "Anne Frank Boat Tours — €20pp", "costo": 60},
            {"id": "ams_13", "hora": "19:00", "tipo": "restaurante",
             "icono": "🍷", "nombre": "Cena Moeders",
             "detalle": "Rozengracht 251 — €30pp", "costo": 90},
        ]
    },
    {
        "fecha": "Jue 30 Jul", "ciudad": "Regreso", "emoji": "✈️",
        "especial": None,
        "actividades": [
            {"id": "ret_01", "hora": "12:00", "tipo": "transporte",
             "icono": "🚗", "nombre": "Traslado al aeropuerto Schiphol",
             "detalle": "Taxi ~€35 o tren €5", "costo": 35},
            {"id": "ret_02", "hora": "15:00", "tipo": "transporte",
             "icono": "✈️", "nombre": "Vuelo AMS → Madrid",
             "detalle": "Schiphol → Barajas ~2.5h", "costo": 300},
            {"id": "ret_03", "hora": "20:00", "tipo": "restaurante",
             "icono": "🍽️", "nombre": "Cena aeropuerto Barajas",
             "detalle": "Terminal 4 — €20pp", "costo": 60},
            {"id": "ret_04", "hora": "23:45", "tipo": "transporte",
             "icono": "✈️", "nombre": "Vuelo Madrid → Lima",
             "detalle": "Barajas T4 → LIM — ya reservado", "costo": 0},
        ]
    },
]


# ══════════════════════════════════════════════════════════════════════════
# UI PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════
def mostrar():
    st.title("🤖🐾 Travel Concierge — Lady")
    st.caption("Lady, tu schnauzer viajera 🐩 — itinerario, alertas y búsqueda web en tiempo real")

    model = init_gemini()
    if not model:
        st.error("No se pudo inicializar Gemini.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "messages_display" not in st.session_state:
        st.session_state.messages_display = []

    # Guardar referencia del itinerario para tab_alertas
    st.session_state._itinerario_ref = ITINERARIO_CHECKS

    # Guardar actividades del día actual
    fecha_hoy_init = datetime.now().strftime("%Y-%m-%d")
    if fecha_hoy_init in CIUDAD_POR_FECHA:
        ciudad_hoy_init = CIUDAD_POR_FECHA[fecha_hoy_init][0]
        for d in ITINERARIO_CHECKS:
            if ciudad_hoy_init in d["ciudad"]:
                st.session_state.itinerario_data = d["actividades"]
                break

    tab_chat, tab_timeline, tab_alertas, tab_mapa = st.tabs([
        "💬 Chat con Lady 🐾", "📅 Itinerario Día a Día",
        "🔔 Alertas del Día", "🗺️ Mapa del Viaje"
    ])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: CHAT
    # ══════════════════════════════════════════════════════════════════════
    with tab_chat:
        if not st.session_state.messages_display:
            st.session_state.messages_display.append({
                "role": "assistant",
                "content": (
                    "¡Woof woof! 🐾 ¡Hola familia, soy **Lady**! 🐩\n\n"
                    "Soy una schnauzer miniatura muy viajada que conoce "
                    "cada rincón de Europa. ¡Mi naricita ya olfateó los "
                    "mejores restaurantes de Madrid a Ámsterdam! 🗺️\n\n"
                    "**Puedo ayudarles con:**\n"
                    "- 🗓️ ¿Qué hacemos el día del cumpleaños de Camila?\n"
                    "- 🍽️ Buscar restaurantes cerca de la Torre Eiffel\n"
                    "- 🎉 ¿Qué eventos hay en Ámsterdam el 27 de julio?\n"
                    "- 💰 ¿Cuánto nos queda de presupuesto?\n\n"
                    "¡Mis patitas están listas para guiarlos! 🐾 ¿En qué les ayudo?"
                )
            })

        for msg in st.session_state.messages_display:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("fuentes"):
                    with st.expander("🌐 Fuentes consultadas"):
                        for f in msg["fuentes"]:
                            st.write(f"**{f['titulo']}**")
                            st.caption(f["snippet"])
                            if f.get("url"):
                                st.write(f"🔗 {f['url']}")

        if pregunta := st.chat_input("Pregunta sobre tu viaje..."):
            st.session_state.messages_display.append({
                "role": "user", "content": pregunta
            })
            with st.chat_message("user"):
                st.markdown(pregunta)

            with st.chat_message("assistant"):
                with st.spinner("🐾 Lady está olfateando la respuesta..."):
                    respuesta, fuentes = obtener_respuesta(
                        model, st.session_state.chat_history, pregunta
                    )
                st.markdown(respuesta)
                if fuentes:
                    with st.expander("🌐 Fuentes consultadas"):
                        for f in fuentes:
                            st.write(f"**{f['titulo']}**")
                            st.caption(f["snippet"])
                            if f.get("url"):
                                st.write(f"🔗 {f['url']}")

            st.session_state.messages_display.append({
                "role": "assistant",
                "content": respuesta,
                "fuentes": fuentes
            })
            st.session_state.chat_history.append({
                "role": "user", "parts": [pregunta]
            })
            st.session_state.chat_history.append({
                "role": "model", "parts": [respuesta]
            })

        if st.session_state.messages_display:
            if st.button("🗑️ Limpiar conversación", type="secondary"):
                st.session_state.chat_history = []
                st.session_state.messages_display = []
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2: TIMELINE
    # ══════════════════════════════════════════════════════════════════════
    with tab_timeline:

        def cargar_checks() -> dict:
            try:
                from utils.gcp_client import get_firestore_client
                db = get_firestore_client()
                docs = db.collection("itinerario_checks").stream()
                return {doc.id: doc.to_dict() for doc in docs}
            except Exception:
                return {}

        def guardar_check(act_id: str, completado: bool,
                          fuera_orden: bool = False):
            try:
                from utils.gcp_client import get_firestore_client
                db = get_firestore_client()
                db.collection("itinerario_checks").document(act_id).set({
                    "completado": completado,
                    "fuera_orden": fuera_orden,
                    "timestamp": datetime.now(),
                })
            except Exception as e:
                st.warning(f"No se pudo guardar: {e}")

        def generar_sugerencia_check(actividad: dict,
                                     dia: dict,
                                     checks: dict) -> str:
            completadas = [
                a["nombre"] for a in dia["actividades"]
                if checks.get(a["id"], {}).get("completado", False)
            ]
            pendientes = [
                a["nombre"] for a in dia["actividades"]
                if not checks.get(a["id"], {}).get("completado", False)
                and a["id"] != actividad["id"]
            ]
            prompt = f"""
La familia peruana (Jonathan, Giovanna, Camila 15 años) acaba de
completar: "{actividad['nombre']}" a las {actividad['hora']}
en {dia['ciudad']}.

Ya visitaron hoy: {', '.join(completadas) if completadas else 'nada aún'}
Aún pendiente hoy: {', '.join(pendientes) if pendientes else 'nada más'}

Sugiere máximo 3 opciones cortas de qué hacer con el tiempo libre:
- Restaurantes alternativos cercanos
- Atracciones cercanas fuera del itinerario
- Actividades según la hora del día
- Lugares de camino al siguiente punto

Responde en español, amigable, con emojis, máximo 120 palabras.
"""
            try:
                gemini = init_gemini()
                if gemini:
                    return gemini.generate_content(prompt).text
            except Exception:
                pass
            return "No se pudo generar sugerencia en este momento."

        if "itinerario_checks" not in st.session_state:
            with st.spinner("🐾 Lady cargando tu progreso..."):
                st.session_state.itinerario_checks = cargar_checks()

        checks = st.session_state.itinerario_checks

        total_acts = sum(len(d["actividades"]) for d in ITINERARIO_CHECKS)
        total_ok = sum(1 for c in checks.values() if c.get("completado", False))
        total_fuera = sum(1 for c in checks.values() if c.get("fuera_orden", False))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📅 Actividades", total_acts)
        col2.metric("✅ Completadas", total_ok)
        col3.metric("🔀 Fuera de orden", total_fuera)
        col4.metric(
            "📊 Progreso",
            f"{int(total_ok/total_acts*100)}%" if total_acts else "0%"
        )
        st.progress(total_ok / total_acts if total_acts else 0)
        st.divider()

        ciudades_unicas = ["Todos"] + list(
            dict.fromkeys(d["ciudad"] for d in ITINERARIO_CHECKS)
        )
        ciudad_filtro = st.selectbox("Filtrar por ciudad:", ciudades_unicas)

        dias_mostrar = (
            ITINERARIO_CHECKS if ciudad_filtro == "Todos"
            else [d for d in ITINERARIO_CHECKS if d["ciudad"] == ciudad_filtro]
        )

        for dia in dias_mostrar:
            acts_ok = sum(
                1 for a in dia["actividades"]
                if checks.get(a["id"], {}).get("completado", False)
            )
            total_dia = len(dia["actividades"])

            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"### {dia['emoji']} {dia['fecha']}")
                    st.caption(f"📍 {dia['ciudad']}")
                with col2:
                    if dia.get("especial"):
                        st.success(dia["especial"])
                with col3:
                    st.metric("Progreso día", f"{acts_ok}/{total_dia}")

                if acts_ok == total_dia:
                    st.success("🎉 ¡Día completado!")

                st.divider()

                for act in dia["actividades"]:
                    act_id = act["id"]
                    check_data = checks.get(act_id, {})
                    completado = check_data.get("completado", False)
                    fuera = check_data.get("fuera_orden", False)

                    col1, col2, col3, col4 = st.columns([0.4, 3.5, 1.5, 0.6])
                    with col1:
                        st.write(act["icono"])
                    with col2:
                        if completado:
                            st.markdown(
                                f"~~**{act['hora']}** — {act['nombre']}~~"
                            )
                            if fuera:
                                st.caption("🔀 Visitado fuera de orden")
                        else:
                            st.markdown(
                                f"**{act['hora']}** — {act['nombre']}"
                            )
                            st.caption(act["detalle"])
                    with col3:
                        if st.session_state.get("_show_prices", False):
                            st.caption(
                                f"€{act['costo']} · S/.{act['costo']*4}"
                                if act["costo"] > 0 else "Gratis"
                            )
                        else:
                            st.caption("🔒" if act["costo"] > 0 else "Gratis")
                    with col4:
                        nuevo_check = st.checkbox(
                            "✓", value=completado, key=f"tc_{act_id}"
                        )

                    if nuevo_check != completado:
                        fuera_nueva = False
                        if nuevo_check:
                            fuera_nueva = st.checkbox(
                                "🔀 ¿Lo visitaste fuera de orden?",
                                key=f"fo_{act_id}"
                            )
                        guardar_check(act_id, nuevo_check, fuera_nueva)
                        st.session_state.itinerario_checks[act_id] = {
                            "completado": nuevo_check,
                            "fuera_orden": fuera_nueva,
                            "timestamp": datetime.now(),
                        }
                        if nuevo_check:
                            with st.spinner("🐾 Lady busca alternativas..."):
                                sug = generar_sugerencia_check(
                                    act, dia,
                                    st.session_state.itinerario_checks
                                )
                            st.info(f"🐾 **Lady sugiere:**\n\n{sug}")
                        st.rerun()

        st.divider()
        if st.button("🔄 Resetear todos los checks", type="secondary"):
            try:
                from utils.gcp_client import get_firestore_client
                db = get_firestore_client()
                for doc in db.collection("itinerario_checks").stream():
                    doc.reference.delete()
                st.session_state.itinerario_checks = {}
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3: ALERTAS
    # ══════════════════════════════════════════════════════════════════════
    with tab_alertas:
        st.subheader("🔔 Alertas Inteligentes del Día")

        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.hour * 60 + ahora.minute

        if fecha_hoy not in CIUDAD_POR_FECHA:
            st.info(
                f"📅 Hoy es {ahora.strftime('%d/%m/%Y')}.\n\n"
                "Las alertas se activarán automáticamente "
                "durante el viaje del **15 al 30 de julio 2026**.\n\n"
                "Abre esta pestaña cualquier día del viaje "
                "y verás las alertas en tiempo real."
            )
            with st.expander("👁️ Vista previa de cómo funcionará"):
                st.markdown("""
**Ejemplo — alerta de tiempo:**

> ⏰ **En 25 minutos** — Museo del Prado (11:30)
> 📍 Paseo del Prado s/n — €15pp
> [📍 Cómo llegar →](https://maps.google.com)

**Ejemplo — alerta de lluvia:**

> 🌧️ **Lluvia prevista** a las 16:30 — Parque del Retiro
> 🌡️ 18°C · 80% probabilidad de lluvia
> 💡 Cleo sugiere alternativas bajo techo cercanas

**Ejemplo — próxima actividad:**

> ▶️ **14:30** — Almuerzo Los Montes de Galicia
> 📍 C/ Echegaray 17 — €25pp
> [📍 Google Maps →](https://maps.google.com)
                """)
        else:
            ciudad_hoy, lat_hoy, lon_hoy = CIUDAD_POR_FECHA[fecha_hoy]

            st.success(
                f"📍 Hoy estás en **{ciudad_hoy}** · "
                f"{ahora.strftime('%H:%M')} hora local"
            )

            with st.spinner("🌤️ Consultando clima..."):
                clima = get_clima_hoy(lat_hoy, lon_hoy)

            # Obtener actividades del día actual
            actividades_hoy = []
            for d in ITINERARIO_CHECKS:
                if ciudad_hoy in d["ciudad"]:
                    actividades_hoy = d["actividades"]
                    # Actualizar session_state
                    st.session_state.itinerario_data = actividades_hoy
                    break

            if not actividades_hoy:
                st.info("No se encontraron actividades para hoy.")
            else:
                checks_actuales = st.session_state.get("itinerario_checks", {})
                alertas_generadas = 0

                for act in actividades_hoy:
                    ya_completada = checks_actuales.get(
                        act["id"], {}
                    ).get("completado", False)

                    if ya_completada:
                        continue

                    try:
                        h, m = map(int, act["hora"].split(":"))
                        act_minutos = h * 60 + m
                    except Exception:
                        continue

                    diff = act_minutos - hora_actual

                    # Alerta: próxima en 30 min
                    if 0 <= diff <= 30:
                        alertas_generadas += 1
                        coords = COORDS_ACTIVIDAD.get(act["id"])
                        maps_url = (
                            google_maps_url(coords[0], coords[1], coords[2])
                            if coords else "#"
                        )
                        with st.container(border=True):
                            st.warning(
                                f"⏰ **En {diff} minutos** — "
                                f"{act['nombre']} ({act['hora']})"
                            )
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"📍 {act['detalle']}")
                                if act["costo"] > 0 and st.session_state.get("_show_prices", False):
                                    st.caption(
                                        f"💶 €{act['costo']} · "
                                        f"S/.{act['costo']*4}"
                                    )
                            with col2:
                                st.link_button(
                                    "📍 Cómo llegar", maps_url,
                                    type="primary",
                                    use_container_width=True
                                )

                    # Alerta: ya debería haber empezado
                    elif -15 <= diff < 0:
                        alertas_generadas += 1
                        coords = COORDS_ACTIVIDAD.get(act["id"])
                        maps_url = (
                            google_maps_url(coords[0], coords[1], coords[2])
                            if coords else "#"
                        )
                        with st.container(border=True):
                            st.error(
                                f"🚨 **¡Ya debería haber empezado!** — "
                                f"{act['nombre']} (era a las {act['hora']})"
                            )
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"📍 {act['detalle']}")
                            with col2:
                                st.link_button(
                                    "📍 Ir ahora", maps_url,
                                    type="primary",
                                    use_container_width=True
                                )

                    # Alerta: lluvia en actividad outdoor
                    if (act["id"] in ACTIVIDADES_OUTDOOR
                            and clima.get("horas")
                            and not ya_completada):
                        hora_str = (
                            f"{ahora.strftime('%Y-%m-%dT')}"
                            f"{act['hora']}:00"
                        )
                        if hora_str in clima["horas"]:
                            idx = clima["horas"].index(hora_str)
                            wmo  = clima["wmo"][idx] if idx < len(clima["wmo"]) else 0
                            prob = clima["prob_ll"][idx] if idx < len(clima["prob_ll"]) else 0
                            temp = clima["temp"][idx] if idx < len(clima["temp"]) else 20

                            if hay_lluvia(wmo, prob):
                                alertas_generadas += 1
                                emoji_w, desc_w = wmo_a_texto(wmo)
                                with st.container(border=True):
                                    st.warning(
                                        f"{emoji_w} **Lluvia prevista** "
                                        f"a las {act['hora']} — "
                                        f"{act['nombre']}"
                                    )
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Clima", desc_w,
                                                  f"{temp:.0f}°C")
                                        st.metric("Prob. lluvia", f"{prob}%")
                                    with col2:
                                        if st.button(
                                            "🐾 Alternativas bajo techo",
                                            key=f"lluvia_{act['id']}",
                                            type="primary",
                                            use_container_width=True
                                        ):
                                            with st.spinner("🐾 Lady olfateando alternativas..."):
                                                sug = sugerencia_lluvia_gemini(
                                                    act, ciudad_hoy, temp
                                                )
                                            st.info(
                                                f"🐾 **Lady sugiere:**\n\n{sug}"
                                            )

                if alertas_generadas == 0:
                    st.success("✅ Todo en orden — sin alertas activas ahora.")
                    st.caption(
                        "Las alertas aparecen 30 min antes de cada "
                        "actividad o cuando se detecta lluvia."
                    )

                # Próxima actividad
                st.divider()
                st.subheader("▶️ Próxima actividad")
                proxima = None
                for act in actividades_hoy:
                    ya_comp = checks_actuales.get(
                        act["id"], {}
                    ).get("completado", False)
                    if ya_comp:
                        continue
                    try:
                        h, m = map(int, act["hora"].split(":"))
                        if h * 60 + m >= hora_actual:
                            proxima = act
                            break
                    except Exception:
                        continue

                if proxima:
                    coords = COORDS_ACTIVIDAD.get(proxima["id"])
                    maps_url = (
                        google_maps_url(coords[0], coords[1], coords[2])
                        if coords else "#"
                    )
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(
                                f"**{proxima['icono']} "
                                f"{proxima['hora']} — "
                                f"{proxima['nombre']}**"
                            )
                            st.caption(proxima["detalle"])
                            if proxima["costo"] > 0:
                                st.caption(
                                    f"💶 €{proxima['costo']} · "
                                    f"S/.{proxima['costo']*4}"
                                )
                        with col2:
                            st.link_button(
                                "📍 Google Maps", maps_url,
                                type="primary",
                                use_container_width=True
                            )
                else:
                    st.info("🌙 No hay más actividades pendientes hoy.")

            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"🕐 Actualizado: {ahora.strftime('%H:%M:%S')}")
            with col2:
                if st.button("🔄 Refrescar alertas"):
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4: MAPA
    # ══════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════
    # TAB 4: MAPA DINÁMICO
    # ══════════════════════════════════════════════════════════════════════
    with tab_mapa:
        import plotly.graph_objects as go

        st.subheader("🗺️ Mapa Dinámico del Viaje")

        # ── Selector de día ────────────────────────────────────────────
        fechas_disponibles = [
            f"{d['emoji']} {d['fecha']} — {d['ciudad']}"
            for d in ITINERARIO_CHECKS
        ]

        # Determinar día por defecto según fecha real
        fecha_hoy_mapa = datetime.now().strftime("%Y-%m-%d")
        idx_default = 0
        if fecha_hoy_mapa in CIUDAD_POR_FECHA:
            ciudad_hoy_mapa = CIUDAD_POR_FECHA[fecha_hoy_mapa][0]
            for i, d in enumerate(ITINERARIO_CHECKS):
                if ciudad_hoy_mapa in d["ciudad"]:
                    idx_default = i
                    break

        col1, col2 = st.columns([3, 1])
        with col1:
            dia_sel_str = st.selectbox(
                "📅 Selecciona el día:",
                fechas_disponibles,
                index=idx_default,
                key="mapa_dia_sel"
            )
        with col2:
            st.write("")
            st.write("")
            zoom_act = st.session_state.get("mapa_zoom_actividad", None)
            if zoom_act:
                if st.button("🔄 Ver día completo"):
                    st.session_state.mapa_zoom_actividad = None
                    st.rerun()

        # Obtener día seleccionado
        idx_dia = fechas_disponibles.index(dia_sel_str)
        dia_actual = ITINERARIO_CHECKS[idx_dia]
        checks_mapa = st.session_state.get("itinerario_checks", {})

        # Filtrar actividades con coordenadas
        actividades_mapa = [
            act for act in dia_actual["actividades"]
            if act["id"] in COORDS_ACTIVIDAD
        ]

        if not actividades_mapa:
            st.warning("No hay coordenadas disponibles para este día.")
        else:
            # ── Lista clickeable a la izquierda + Mapa a la derecha ───
            col_lista, col_mapa = st.columns([1, 2])

            with col_lista:
                st.markdown("**📋 Actividades del día**")
                st.caption("Haz clic para centrar el mapa")

                for i, act in enumerate(actividades_mapa):
                    completada = checks_mapa.get(
                        act["id"], {}
                    ).get("completado", False)

                    es_zoom = (
                        st.session_state.get("mapa_zoom_actividad")
                        == act["id"]
                    )

                    # Botón de actividad
                    btn_label = (
                        f"{'✅' if completada else str(i+1)+'.'} "
                        f"{act['hora']} {act['icono']}\n"
                        f"{act['nombre']}"
                    )
                    if st.button(
                        btn_label,
                        key=f"mapa_btn_{act['id']}",
                        use_container_width=True,
                        type="primary" if es_zoom else "secondary"
                    ):
                        if es_zoom:
                            st.session_state.mapa_zoom_actividad = None
                        else:
                            st.session_state.mapa_zoom_actividad = act["id"]
                        st.rerun()

                    # Costo debajo del botón
                    st.caption(
                        f"€{act['costo']}" if act["costo"] > 0 else "Gratis"
                    )

            with col_mapa:
                zoom_id = st.session_state.get("mapa_zoom_actividad")
                fig = go.Figure()

                # Coordenadas del día
                coords_dia = [
                    COORDS_ACTIVIDAD[act["id"]]
                    for act in actividades_mapa
                ]
                lats = [c[0] for c in coords_dia]
                lons = [c[1] for c in coords_dia]

                # ── Línea de ruta del día ──────────────────────────────
                fig.add_trace(go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    line=dict(width=3, color="#1A73E8"),
                    name="Ruta del día",
                    hoverinfo="skip",
                ))

                # ── Marcadores por actividad ───────────────────────────
                for i, act in enumerate(actividades_mapa):
                    coords = COORDS_ACTIVIDAD[act["id"]]
                    completada = checks_mapa.get(
                        act["id"], {}
                    ).get("completado", False)
                    es_zoom = zoom_id == act["id"]

                    # Color según estado
                    if es_zoom:
                        color = "#FF4B4B"
                        size = 18
                    elif completada:
                        color = "#9E9E9E"
                        size = 10
                    else:
                        color = "#1A73E8"
                        size = 13

                    fig.add_trace(go.Scattermapbox(
                        lat=[coords[0]],
                        lon=[coords[1]],
                        mode="markers+text",
                        marker=dict(size=size, color=color),
                        text=[f"{i+1}"],
                        textfont=dict(size=11, color="white"),
                        textposition="middle center",
                        name=act["nombre"],
                        hovertemplate=(
                            f"<b>{i+1}. {act['nombre']}</b><br>"
                            f"🕐 {act['hora']}<br>"
                            f"📍 {act['detalle']}<br>"
                            f"💶 {'€'+str(act['costo']) if act['costo']>0 else 'Gratis'}"
                            "<extra></extra>"
                        ),
                        showlegend=False,
                    ))

                # ── Centro y zoom del mapa ─────────────────────────────
                if zoom_id and zoom_id in COORDS_ACTIVIDAD:
                    # Zoom a actividad seleccionada
                    zc = COORDS_ACTIVIDAD[zoom_id]
                    center_lat, center_lon = zc[0], zc[1]
                    zoom_level = 15
                    # Marcador destacado extra
                    fig.add_trace(go.Scattermapbox(
                        lat=[zc[0]],
                        lon=[zc[1]],
                        mode="markers",
                        marker=dict(
                            size=30,
                            color="#FF4B4B",
                            opacity=0.3,
                        ),
                        hoverinfo="skip",
                        showlegend=False,
                    ))
                else:
                    # Vista completa del día
                    center_lat = sum(lats) / len(lats)
                    center_lon = sum(lons) / len(lons)
                    # Calcular zoom según dispersión
                    lat_range = max(lats) - min(lats)
                    lon_range = max(lons) - min(lons)
                    rango = max(lat_range, lon_range)
                    if rango < 0.02:
                        zoom_level = 14
                    elif rango < 0.05:
                        zoom_level = 13
                    elif rango < 0.1:
                        zoom_level = 12
                    elif rango < 0.5:
                        zoom_level = 11
                    else:
                        zoom_level = 9

                fig.update_layout(
                    mapbox=dict(
                        style="open-street-map",
                        center=dict(lat=center_lat, lon=center_lon),
                        zoom=zoom_level,
                    ),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=520,
                    showlegend=False,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Info de actividad en zoom
                if zoom_id:
                    act_zoom = next(
                        (a for a in actividades_mapa if a["id"] == zoom_id),
                        None
                    )
                    if act_zoom:
                        coords_z = COORDS_ACTIVIDAD[zoom_id]
                        maps_url = google_maps_url(
                            coords_z[0], coords_z[1], coords_z[2]
                        )
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(
                                    f"**{act_zoom['icono']} "
                                    f"{act_zoom['hora']} — "
                                    f"{act_zoom['nombre']}**"
                                )
                                st.caption(act_zoom["detalle"])
                                if act_zoom["costo"] > 0:
                                    st.caption(
                                        f"💶 €{act_zoom['costo']} · "
                                        f"S/.{act_zoom['costo']*4}"
                                    )
                            with col2:
                                st.link_button(
                                    "📍 Google Maps",
                                    maps_url,
                                    type="primary",
                                    use_container_width=True
                                )

            # ── Resumen del día ────────────────────────────────────────
            st.divider()
            total_costo_dia = sum(
                a["costo"] for a in actividades_mapa
            )
            completadas_dia = sum(
                1 for a in actividades_mapa
                if checks_mapa.get(a["id"], {}).get("completado", False)
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📍 Paradas", len(actividades_mapa))
            col2.metric("✅ Completadas", completadas_dia)
            col3.metric("💶 Costo día", f"€{total_costo_dia}")
            col4.metric("🪙 En soles", f"S/.{total_costo_dia*4:,}")

            if dia_actual.get("especial"):
                st.success(f"🌟 {dia_actual['especial']}")
