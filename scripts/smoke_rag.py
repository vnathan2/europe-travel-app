"""
scripts/smoke_rag.py
Validación end-to-end del pipeline RAG: query -> embedding -> Firestore -> top_k.
No usa Streamlit ni Gemini chat; sólo busca y muestra los matches.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.knowledge_base import buscar_conocimiento, init_embeddings

QUERIES = [
    ("mejores restaurantes en París para una cena romántica", "París"),
    ("qué ver en Ámsterdam con adolescentes", "Ámsterdam"),
    ("cómo funciona el transporte público en Bruselas", "Bruselas"),
    ("Parque Warner Madrid consejos", "Madrid"),
    ("chocolate artesanal Bayona", "Bayona"),
]


def main():
    print("🔍 Smoke test del pipeline RAG\n" + "=" * 60)
    init_embeddings()

    for query, ciudad in QUERIES:
        print(f"\n📝 Query: {query!r}  (ciudad={ciudad})")
        resultados = buscar_conocimiento(query, ciudad=ciudad, top_k=3)
        if not resultados:
            print("   ⚠️  Sin resultados")
            continue
        for i, r in enumerate(resultados, 1):
            snippet = r["texto"][:120].replace("\n", " ")
            print(
                f"   {i}. [{r['similitud']:.3f}] "
                f"{r['fuente']:18s} | {r['titulo'][:50]}"
            )
            print(f"      ↪ {snippet}...")

    print("\n" + "=" * 60)
    print("✅ Si viste similitudes > 0.6 y textos relevantes, RAG funciona.")


if __name__ == "__main__":
    main()
