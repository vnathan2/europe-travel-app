# scripts/ingest_knowledge.py
# Script de ingesta - corre manualmente para alimentar la KB.
#
# Uso por defecto (todas las ciudades, todas las fuentes):
#     python scripts/ingest_knowledge.py
#
# Acotar a una o varias ciudades (CSV, recomendado para pruebas):
#     $env:INGEST_CITIES = "Bayona"
#     python scripts/ingest_knowledge.py
#
# Saltarse Tavily (ahorra créditos en pruebas):
#     $env:INGEST_SKIP_TAVILY = "1"
#     python scripts/ingest_knowledge.py

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.knowledge_base import (
    fetch_opentripmap,
    fetch_tavily,
    fetch_wikipedia,
    guardar_documento,
    init_embeddings,
)

# ── Temas a buscar por ciudad ──────────────────────────────────────────────
TEMAS_POR_CIUDAD = {
    "Madrid": [
        "restaurantes recomendados turistas Madrid",
        "transporte metro Madrid turistas",
        "mejores barrios Madrid turismo",
        "museos Madrid entradas precios",
        "tips viajeros Madrid España",
        "gastronomía típica Madrid",
    ],
    "Bayona": [
        "qué ver Bayona País Vasco francés",
        "gastronomía vasca Bayona Francia",
        "tips turistas Bayona Biarritz",
    ],
    "París": [
        "restaurantes cerca Torre Eiffel París",
        "transporte metro París turistas",
        "mejores barrios París turismo",
        "museos París precios entradas 2026",
        "tips viajeros París Francia",
        "gastronomía francesa París restaurantes",
        "Disneyland París consejos familias",
        "Versalles visita tips",
        "mejores mercados París turistas",      # ← nuevo tema
        "París con adolescentes actividades",   # ← específico para Camila
        "cenas románticas París cumpleaños",    # ← específico para Giovanna,
    ],
    "Bruselas": [
        "qué ver Bruselas turismo",
        "gastronomía belga Bruselas cerveza chocolate",
        "transporte Bruselas turistas metro",
        "tips viajeros Bruselas Bélgica",
    ],
    "Ámsterdam": [
        "restaurantes Ámsterdam turistas",
        "transporte Ámsterdam tram bicicleta",
        "mejores museos Ámsterdam",
        "tips viajeros Ámsterdam Países Bajos",
        "canales Ámsterdam cruceros",
        "Zaanse Schans molinos visita",
    ],
}

TEMAS_WIKIPEDIA = {
    "Madrid": ["Madrid", "Museo del Prado", "Palacio Real de Madrid",
               "Parque del Retiro", "Gastronomía de Madrid"],
    "Bayona": ["Bayona (Francia)", "País Vasco francés",
               "Catedral de Bayona"],
    "París": ["París", "Torre Eiffel", "Museo del Louvre",
              "Palacio de Versalles", "Montmartre",
              "Gastronomía de Francia"],
    "Bruselas": ["Bruselas", "Grand Place de Bruselas",
                 "Atomium", "Gastronomía de Bélgica"],
    "Ámsterdam": ["Ámsterdam", "Rijksmuseum",
                  "Casa de Ana Frank",
                  "Museo Van Gogh", "Canales de Ámsterdam"],
}

def _ciudades_seleccionadas() -> list:
    """Permite acotar la ingesta via INGEST_CITIES=CSV (e.g. 'Bayona,París')."""
    todas = ["Madrid", "Bayona", "París", "Bruselas", "Ámsterdam"]
    raw = os.getenv("INGEST_CITIES", "").strip()
    if not raw:
        return todas
    pedidas = [c.strip() for c in raw.split(",") if c.strip()]
    invalidas = [c for c in pedidas if c not in todas]
    if invalidas:
        print(f"⚠️  Ciudades desconocidas ignoradas: {invalidas}")
    return [c for c in pedidas if c in todas]


def main():
    print("🚀 Iniciando ingesta de knowledge base...")
    print("=" * 60)

    skip_tavily = os.getenv("INGEST_SKIP_TAVILY", "").lower() in ("1", "true", "yes")
    ciudades = _ciudades_seleccionadas()
    print(f"📋 Ciudades a procesar: {ciudades}")
    print(f"📋 Tavily: {'OFF (ahorro de créditos)' if skip_tavily else 'ON'}")
    print("=" * 60)

    init_embeddings()

    total_docs = 0
    total_guardados = 0
    total_skip = 0

    for ciudad in ciudades:
        print(f"\n📍 Procesando {ciudad}...")
        docs_ciudad = []

        # 1. Wikipedia
        print("  📚 Wikipedia...")
        for tema in TEMAS_WIKIPEDIA.get(ciudad, []):
            docs = fetch_wikipedia(ciudad, tema)
            docs_ciudad.extend(docs)
            print(f"    ✓ {tema}: {len(docs)} docs")

        # 2. OpenTripMap
        print("  🗺️ OpenTripMap...")
        docs_otm = fetch_opentripmap(ciudad)
        docs_ciudad.extend(docs_otm)
        print(f"    ✓ {len(docs_otm)} atracciones")

        # 3. Tavily (opcional)
        if skip_tavily:
            print("  🌐 Tavily: omitido por INGEST_SKIP_TAVILY")
            docs_tavily = []
        else:
            print("  🌐 Tavily web search...")
            docs_tavily = fetch_tavily(
                ciudad, TEMAS_POR_CIUDAD.get(ciudad, [])
            )
            print(f"    ✓ {len(docs_tavily)} artículos web")
        docs_ciudad.extend(docs_tavily)

        # Guardar en Firestore con embeddings
        print(f"  💾 Guardando {len(docs_ciudad)} documentos...")
        for doc in docs_ciudad:
            total_docs += 1
            resultado = guardar_documento(doc)
            if resultado.startswith("OK"):
                total_guardados += 1
                print(f"    ✅ {resultado[4:50]}")
            elif resultado.startswith("SKIP"):
                total_skip += 1
            else:
                print(f"    ❌ {resultado}")

        print(f"  📊 {ciudad}: "
              f"{total_guardados} guardados, {total_skip} ya existían")

    print("\n" + "=" * 60)
    print("✅ Ingesta completada:")
    print(f"   Total procesados: {total_docs}")
    print(f"   Guardados nuevos: {total_guardados}")
    print(f"   Ya existían (skip): {total_skip}")

if __name__ == "__main__":
    main()
