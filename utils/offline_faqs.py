"""
utils/offline_faqs.py

FAQ universales pre-generadas como fallback cuando Gemini falla durante el viaje.
Son respuestas a preguntas frecuentes de emergencia/operación básica que no
requieren la creatividad de Lady (la persona del bot), solo información correcta
y accesible cuando no hay conexión a la API.

Diseño:
- Lista plana ordenada por prioridad. La búsqueda hace un matching por keywords
  contra el dict `keywords`.
- Si nada matchea, retornar `None` y el caller muestra un mensaje genérico.
- No depende de Firestore ni de ninguna API externa: vive como código.

Para agregar/editar: solo editar este archivo y redeployar.
"""
from __future__ import annotations

OFFLINE_FAQS: list[dict] = [
    {
        "id":       "robo_pasaporte",
        "keywords": ["robaron", "robo", "perdí", "perdi", "extravió", "extravio",
                     "pasaporte", "documento"],
        "pregunta": "¿Qué hago si pierdo o me roban el pasaporte?",
        "respuesta": (
            "**Pasos inmediatos si pierdes el pasaporte en Europa:**\n\n"
            "1. **Denuncia en la policía local** (necesaria para reposición). "
            "Pide una copia del informe.\n"
            "2. **Contacta el consulado peruano**:\n"
            "   - Madrid: +34 91 431 4242 — Calle Cristóbal Bordiú 49\n"
            "   - París: +33 1 53 64 03 04 — 25 Rue de l'Arcade\n"
            "   - Bruselas: +32 2 733 33 19 — Av. de Tervueren 179\n"
            "   - La Haya (cubre Ámsterdam): +31 70 365 3500\n"
            "3. Lleva fotocopia del pasaporte, 2 fotos carnet y comprobante de "
            "denuncia. Tu emergency_card en la app tiene el número.\n"
            "4. Te emiten **salvoconducto** para volver a Perú. No puedes "
            "viajar a otro país Schengen con eso, solo retornar."
        ),
    },
    {
        "id":       "telefonos_emergencia",
        "keywords": ["emergencia", "policía", "policia", "ambulancia", "bomberos",
                     "112", "número", "numero"],
        "pregunta": "¿Cuáles son los teléfonos de emergencia en Europa?",
        "respuesta": (
            "**112** funciona en TODA la Unión Europea para policía, "
            "ambulancia y bomberos. Es gratuito desde cualquier móvil, "
            "incluso sin saldo o sin SIM.\n\n"
            "Específicos por país (todos atienden en inglés):\n"
            "- **España**: 091 (policía nacional), 092 (policía local)\n"
            "- **Francia**: 17 (policía), 15 (urgencias médicas)\n"
            "- **Bélgica**: 101 (policía), 100 (ambulancia)\n"
            "- **Países Bajos**: 0900-8844 (policía no urgente)\n\n"
            "Para temas consulares peruanos, ver la FAQ de 'consulado'."
        ),
    },
    {
        "id":       "embajada_consulado",
        "keywords": ["embajada", "consulado", "perú", "peru", "peruano", "consular"],
        "pregunta": "¿Cómo contacto a la embajada o consulado peruano?",
        "respuesta": (
            "**Embajadas y consulados de Perú en Europa:**\n\n"
            "- **Madrid (España)**: Embajada y Consulado General.\n"
            "  Tel: +34 91 431 4242. Dir: Calle Cristóbal Bordiú 49.\n"
            "- **París (Francia)**: Embajada.\n"
            "  Tel: +33 1 53 64 03 04. Dir: 25 Rue de l'Arcade.\n"
            "- **Bruselas (Bélgica)**: Embajada y Consulado.\n"
            "  Tel: +32 2 733 33 19. Dir: Av. de Tervueren 179.\n"
            "- **La Haya (Países Bajos)**: Embajada (cubre Ámsterdam).\n"
            "  Tel: +31 70 365 3500.\n\n"
            "Horarios consulares suelen ser 9:00-13:00 lunes a viernes. "
            "Para emergencias fuera de horario, llamar igual: tienen línea 24h."
        ),
    },
    {
        "id":       "tarjeta_robada",
        "keywords": ["tarjeta", "credito", "crédito", "débito", "debito",
                     "bloquear", "robaron", "fraude"],
        "pregunta": "¿Cómo bloqueo una tarjeta robada o perdida?",
        "respuesta": (
            "**Bloqueo inmediato:**\n\n"
            "1. Llama al banco emisor desde el reverso de tu otra tarjeta "
            "(o la app móvil del banco si tienes red).\n"
            "2. Visa: +1 303-967-1090 (cobro revertido).\n"
            "3. Mastercard: +1 636-722-7111 (cobro revertido).\n"
            "4. Denuncia el robo en la policía local para tener el informe.\n"
            "5. Pide a tu banco una **tarjeta emergencia** que envían al "
            "consulado peruano más cercano (suele tomar 24-72h).\n\n"
            "Mientras tanto, usa tu tarjeta de respaldo. Por eso la "
            "emergency_card recomienda llevar 2 tarjetas en bolsillos "
            "separados."
        ),
    },
    {
        "id":       "perdi_vuelo",
        "keywords": ["perdí", "perdi", "vuelo", "aerolínea", "aerolinea",
                     "rebooking", "conexión", "conexion"],
        "pregunta": "¿Qué hago si pierdo un vuelo?",
        "respuesta": (
            "**Pasos si pierdes un vuelo:**\n\n"
            "1. Ve al **mostrador de la aerolínea** en el aeropuerto. "
            "No esperes a llegar a casa o al hotel.\n"
            "2. Si fue por causa de la aerolínea (retraso de conexión, "
            "cancelación), tienen obligación de re-embarcarte sin costo + "
            "compensación bajo el **Reglamento UE 261/2004**.\n"
            "3. Si fue por causa tuya, pide tarifa de 'no show' o vuelo "
            "siguiente; suele costar entre €100-€300 según ruta.\n"
            "4. Guarda **todos** los recibos (taxi, hotel) si la espera "
            "supera 2-3h: pueden reembolsarte gastos.\n"
            "5. Si tu seguro de viaje cubre missed connection, llámalo. "
            "El número está en tu emergency_card."
        ),
    },
    {
        "id":       "moneda_pago",
        "keywords": ["euro", "moneda", "cambio", "efectivo", "cajero",
                     "pago", "tasa", "soles"],
        "pregunta": "¿Cómo pago en Europa? ¿Llevo efectivo o tarjeta?",
        "respuesta": (
            "**Pagos en Europa (2026):**\n\n"
            "- **Tarjeta (90% de los casos)**: aceptada en restaurantes, "
            "hoteles, museos, supermercados. Usa contactless cuando puedas "
            "(menos exposición de la tarjeta).\n"
            "- **Efectivo en euros**: solo para mercados, taxis pequeños, "
            "propinas, y emergencias. €200 por persona alcanza para 16 días.\n"
            "- **Cajeros (ATM)**: usa los del banco oficial dentro de bancos "
            "abiertos. Evita los 'Euronet' azules en zonas turísticas: "
            "cobran 10-15% extra.\n"
            "- **Comisión de tu banco peruano**: típicamente 3-5% por retiro "
            "ATM + 2-3% por compra. Revisa tu app antes de salir.\n"
            "- **Tasa referencial EUR/PEN**: ~3.95 (jul 2026). El módulo "
            "Phrase Pocket en la app tiene el conversor con tasa actual."
        ),
    },
    {
        "id":       "lady_caida",
        "keywords": ["lady", "no responde", "error", "caída", "caida", "down",
                     "no funciona", "qué hago", "que hago"],
        "pregunta": "Lady no responde o el chat está caído. ¿Qué hago?",
        "respuesta": (
            "Si **Lady (el chat principal)** no responde, probablemente la "
            "API de Gemini está fuera. Mientras tanto:\n\n"
            "1. **Tarjeta de emergencia** (módulo 🆘): tiene datos críticos "
            "ya guardados — pasaporte, tipo de sangre, hoteles, contacto Lima.\n"
            "2. **Packing checker** (🧳): lista compartida con Giovanna y "
            "Camila.\n"
            "3. **Phrase Pocket** (💬): traductor offline para frases básicas "
            "y conversor de monedas con tasa cacheada.\n"
            "4. **Voice Translator** (🎤): frases de emergencia hardcoded en "
            "ES/EN/FR/NL.\n"
            "5. **Train Optimizer** (🚆): rutas Madrid-Bayona-París-Bruselas-"
            "Ámsterdam ya guardadas, no necesitan red.\n\n"
            "Para info actualizada de la ciudad, intenta refrescar la página "
            "en 5-10 min. Las APIs gratuitas suelen recuperarse rápido."
        ),
    },
    {
        "id":       "robo_general",
        "keywords": ["robaron", "robo", "asalto", "carterista", "pickpocket",
                     "qué hacer", "que hacer"],
        "pregunta": "Me robaron pertenencias. ¿Qué hago?",
        "respuesta": (
            "**Si te roban en la calle o transporte público:**\n\n"
            "1. **No persigas** al ladrón ni te resistas: prioridad es tu "
            "seguridad y la de la familia.\n"
            "2. **Denuncia en policía local** en las próximas 24h. "
            "Necesitas el informe para reclamar al seguro de viaje y "
            "para reponer documentos.\n"
            "3. **Bloquea tarjetas** robadas (ver FAQ 'tarjeta').\n"
            "4. **Reporta al seguro** con el número de tu emergency_card. "
            "Pídeles instrucciones específicas; la mayoría cubre objetos "
            "robados con denuncia.\n"
            "5. Si robaron pasaporte → contacta consulado peruano "
            "(ver FAQ 'consulado').\n\n"
            "**Prevención (París y Madrid en particular):**\n"
            "- Riñonera antirrobo por delante en metro.\n"
            "- No saques el celular en zonas concurridas.\n"
            "- Mochila al frente del cuerpo en multitudes."
        ),
    },
    {
        "id":       "frase_medica",
        "keywords": ["médico", "medico", "hospital", "ambulancia", "dolor",
                     "enfermo", "enferma"],
        "pregunta": "Necesito atención médica. ¿Cómo pido ayuda?",
        "respuesta": (
            "**Frases de emergencia médica:**\n\n"
            "- **Español** (Madrid/Bayona): 'Necesito un médico, por favor.'\n"
            "- **Inglés**: 'I need a doctor, please.'\n"
            "- **Francés** (Bayona/París): 'J'ai besoin d'un médecin, s'il "
            "vous plaît.'\n"
            "- **Neerlandés** (Bruselas/Ámsterdam): 'Ik heb een dokter "
            "nodig, alstublieft.'\n\n"
            "**Sistema de salud (Europa, 2026):**\n"
            "- **Llama al 112**: ambulancia gratuita en toda la UE.\n"
            "- Si tienes seguro de viaje, presenta la **tarjeta del seguro** "
            "en urgencias. La mayoría cubre directo o reembolso posterior.\n"
            "- En España y Francia las urgencias públicas atienden a "
            "extranjeros sin cargo inicial. Te facturan al seguro después.\n"
            "- Lleva la lista de **medicamentos personales** y alergias en "
            "tu emergency_card."
        ),
    },
    {
        "id":       "transporte_publico",
        "keywords": ["metro", "tren", "transporte", "bus", "boleto", "billete",
                     "ticket", "precio"],
        "pregunta": "¿Cuánto cuesta el transporte público?",
        "respuesta": (
            "**Precios referenciales jul 2026 (verifica en cada ciudad):**\n\n"
            "- **Madrid Metro**: €1.50-€2.00 por viaje. Bono 10 viajes ~€12.20.\n"
            "- **París Metro/RER**: €2.15 por ticket. **Pase Navigo Easy** "
            "recargable más conveniente. 1 día ilimitado ~€8.65.\n"
            "- **Bruselas STIB**: €2.60 por viaje sencillo. 1 día ilimitado "
            "~€7.50.\n"
            "- **Ámsterdam GVB**: €3.40 por hora. Pase 24h ~€8.50. Considera "
            "**OV-chipkaart anónima** si vas más de 3 días.\n"
            "- **Eurostar/Thalys** entre ciudades: ver módulo Train Optimizer "
            "en la app. Reservar con 1-2 meses de anticipación ahorra "
            "30-50%.\n\n"
            "Tip: muchos museos y atracciones tienen descuentos comprando "
            "el ticket combinado con transporte (ej. París Museum Pass + "
            "Navigo)."
        ),
    },
]


def buscar_faq_offline(pregunta: str) -> dict | None:
    """
    Busca la FAQ más relevante para `pregunta` usando matching simple de
    keywords. No depende de Firestore ni de Gemini.

    Retorna el dict completo de la FAQ matcheada (incluye `respuesta`,
    `pregunta`, `id`), o `None` si nada matchea con score > 0.

    Algoritmo: cuenta cuántas keywords de cada FAQ están presentes en la
    pregunta del usuario (case-insensitive). Devuelve la de mayor count.
    Empate: la primera en orden de declaración (FAQs ordenadas por prioridad).
    """
    if not pregunta:
        return None

    pregunta_lower = pregunta.lower()
    mejor_match: dict | None = None
    mejor_score = 0

    for faq in OFFLINE_FAQS:
        score = sum(1 for kw in faq["keywords"] if kw in pregunta_lower)
        if score > mejor_score:
            mejor_score = score
            mejor_match = faq

    return mejor_match


def respuesta_fallback_generica() -> str:
    """
    Mensaje genérico cuando Gemini falló y ninguna FAQ matchea.
    Lista los módulos offline disponibles como guía rápida.
    """
    return (
        "🐾 *Lady tuvo un problema técnico para responderte esta vez.*\n\n"
        "Mientras se recupera, puedes usar estos módulos que no dependen "
        "de su servicio:\n\n"
        "- **🆘 Emergency Card**: pasaporte, hoteles, contactos críticos.\n"
        "- **🧳 Packing Checker**: lista compartida con tasas histórias "
        "de clima.\n"
        "- **💬 Phrase Pocket**: traductor + conversor EUR/PEN.\n"
        "- **🎤 Voice Translator**: frases de emergencia en 4 idiomas.\n"
        "- **🚆 Train Optimizer**: rutas entre ciudades pre-cargadas.\n\n"
        "Si tu pregunta es urgente y necesitas un teléfono concreto "
        "(emergencia, embajada, banco), revisa la Emergency Card del menú "
        "principal."
    )
