"""
Setup compartido para los smoke tests.

1. Agrega la raíz del proyecto al sys.path.
2. Stubs de dependencias externas pesadas (GCP, Gemini, Tavily) para que
   los smoke tests corran con instalación mínima: pytest + numpy + streamlit
   + requests + python-dotenv. Los tests son de lógica pura, no tocan
   servicios reales.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stubs antes de cualquier import del proyecto.
_STUB_MODULES = [
    "google.cloud",
    "google.cloud.firestore",
    "google.cloud.storage",
    "google.cloud.secretmanager",
    "google.generativeai",
    "tavily",
    "pandas",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
]
for _name in _STUB_MODULES:
    sys.modules.setdefault(_name, MagicMock())
