# CLAUDE.md - Guía para sesiones de Claude Code

Esta es una guía operativa para futuras sesiones trabajando en `europe-travel-app`. Léela completa antes de proponer cambios; el proyecto tiene restricciones específicas que no son obvias del código.

## Contexto del proyecto

- App Streamlit personal-familiar para gestionar un viaje a Europa del 15 al 30 de julio de 2026 (Jonathan, Giovanna, Camila).
- Desplegada en Cloud Run (us-east1). URL prod: `https://europe-travel-app-565528729494.us-east1.run.app`.
- 12 módulos funcionales. Documentación técnica completa en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Puntos de mejora priorizados en [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md).

## Restricciones invariables

1. **Free tier GCP**: este proyecto debe permanecer dentro de la capa gratuita de Google Cloud en todo momento. Antes de proponer un servicio nuevo, valida cuotas y costo. Está documentado en memoria como `project_gcp_free_tier`.
2. **No commits de secretos**: las claves (Gemini, Tavily, Google OAuth) viven en Secret Manager. `scripts/setup_secrets.sh` tiene placeholders deliberadamente; nunca los reemplaces y commitees con valores reales.
3. **Compatibilidad de la familia**: dos miembros (Giovanna, Camila) son rol `FAMILIAR` y no ven precios. `mostrar_precio()` debe respetarse en cualquier dato monetario.
4. **Idioma de UI**: todo en español. Mensajes y prompts a Gemini también.

## Comandos habituales

```powershell
# Setup local (desde la raíz)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Correr en local (modo desarrollo, sin OAuth)
$env:APP_MODE = "DEVELOPMENT"
streamlit run app.py

# Ingesta de knowledge base (offline desde script)
# En Windows: $env:PYTHONIOENCODING = "utf-8"  (necesario para emojis en consola)
python scripts/ingest_knowledge.py

# Ingesta acotada (útil para pruebas o cuando quieres ahorrar créditos)
$env:INGEST_CITIES = "Bayona"        # CSV; default: todas
$env:INGEST_SKIP_TAVILY = "1"        # default: Tavily activo
python scripts/ingest_knowledge.py

# Tests (suite mínima de smoke tests sobre lógica pura)
pip install -r requirements-dev.txt
pytest                          # 17 tests, corre en <1s
# Los tests no tocan Firestore/Gemini/Tavily; usan stubs en tests/conftest.py.

# Build y deploy (requiere gcloud)
# IMPORTANTE: leer el checklist pre-deploy más abajo antes de ejecutar.
gcloud builds submit --tag us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest --quiet .
gcloud run deploy europe-travel-app `
  --image=us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest `
  --region=us-east1 --platform=managed --allow-unauthenticated --quiet `
  --no-traffic --tag=test
# Testear con la URL del tag antes de promover:
gcloud run services update-traffic europe-travel-app --to-tags=test=100 --region=us-east1
```

## Checklist pre-deploy (obligatorio)

Aprendizaje del postmortem 2026-05-11: el modo DEVELOPMENT no cubre el flujo OAuth real ni el comportamiento de Streamlit en Cloud Run. Seguir estos pasos antes de cada deploy.

**1. Validación local**
- [ ] `pytest` pasa los 17 tests
- [ ] `streamlit run app.py` arranca sin errores en consola
- [ ] Navegar al menos 3 módulos distintos en local

**2. Reglas antes de hacer el build**
- [ ] El deploy toca ≤5 archivos. Si son más, dividir en deploys separados.
- [ ] Ningún cambio en `auth/google_oauth.py` introduce `st.stop()` en ramas que pueden activarse después del login (post-autenticación).
- [ ] `utils/logger.py` no tiene `propagate=False` en ningún logger.
- [ ] No hay secrets ni valores reales en ningún archivo commiteado.

**3. Deploy y validación en prod**
- [ ] Siempre usar `--no-traffic --tag=test` en el primer deploy.
- [ ] Con la URL del tag: hacer login completo con Google (no dev mode).
- [ ] Navegar al menos 4 módulos distintos y verificar que cargan.
- [ ] Revisar Cloud Logging por errores en los primeros 2 minutos.
- [ ] Solo entonces promover con `update-traffic --to-tags=test=100`.

## Convenciones de código

- **Estilo**: Python 3.11. Comentarios mayoritariamente en español, igual que la UI. No introducir docstrings extensos.
- **Imports**: imports dentro de funciones cuando son pesados (e.g. `tavily`, `google.generativeai`) para acelerar el arranque por módulo.
- **Caching**: usa `@st.cache_resource` para singletons (clientes GCP, modelos) y `@st.cache_data` con TTL para lecturas.
- **Logging**: importa `from utils.logger import get_logger` y usa `logger.exception(...)` o `logger.warning(...)`. Nunca uses `print()` en código de producción ni `except Exception: pass` sin loguear.
- **Persistencia**: Firestore para datos estructurados, Cloud Storage para binarios. Nunca subas archivos sin comprimir; usa la misma pipeline que `trip_journal.comprimir_imagen`.
- **Roles**: cualquier funcionalidad nueva con datos sensibles (precios, módulos restringidos) debe pasar por `is_admin()` y `mostrar_precio()`.
- **Lazy load**: módulos nuevos se agregan al dict `MODULOS` de `app.py:79` y se cargan con `importlib.import_module`. No importar al tope del archivo.

## Estructura del repo

```
europe-travel-app/
├── app.py                      # Router principal + auth gate + theme
├── Dockerfile                  # Cloud Run image (python:3.11-slim, no-root)
├── requirements.txt            # Streamlit, GCP SDKs, pandas, plotly, Gemini, Tavily
├── auth/
│   └── google_oauth.py         # OAuth2 manual + control de roles
├── modules/                    # 12 módulos funcionales
│   ├── euro_budgeter.py        # Gastos
│   ├── emergency_card.py       # Emergencia offline
│   ├── birthday_planner.py     # Cumpleaños Camila + Giovanna
│   ├── shopping_guide.py       # Tiendas hardcoded + Lady fallback
│   ├── packing_checker.py      # Equipaje + clima Open-Meteo
│   ├── voice_translator.py     # Web Speech + MyMemory
│   ├── train_optimizer.py      # 5 rutas hardcoded
│   ├── trip_journal.py         # Diario con fotos privadas en GCS
│   ├── phrase_pocket.py        # Conversor monedas + gráfico EUR/PEN
│   ├── travel_concierge.py     # Chat Lady (Gemini) + RAG + Web augmented
│   ├── night_life.py           # ADMIN: bares + coffee shops
│   └── admin_panel.py          # ADMIN: ingesta KB + stats + limpieza
├── utils/
│   ├── gcp_client.py           # Firestore/Storage/Secrets cacheados
│   ├── knowledge_base.py       # RAG engine (Wikipedia/OSM/Tavily + embeddings)
│   ├── ui_theme.py             # Temas por ciudad + menú + offline panel
│   ├── price_helper.py         # mostrar_precio + get_exchange_rate
│   ├── logger.py               # Logger central (JSON en Cloud Run, legible en local)
│   └── family_profiles.py      # Perfiles para personalización IA
├── scripts/
│   ├── ingest_knowledge.py     # Ingesta KB desde CLI
│   ├── setup_auth.sh           # Bootstrap inicial (deprecado tras primera vez)
│   └── setup_secrets.sh        # Deploy + secrets management
├── tests/
│   ├── conftest.py             # sys.path + stubs de deps externas
│   └── test_smoke.py           # 14 smoke tests sobre lógica pura
├── docs/
│   ├── ARCHITECTURE.md         # Doc técnica detallada por módulo
│   └── IMPROVEMENTS.md         # Backlog priorizado
├── pyproject.toml              # Config pytest (pythonpath, testpaths)
├── requirements.txt            # Runtime deps
└── requirements-dev.txt        # Runtime + pytest
```

## Cosas que NO hagas sin discutir

- Cambiar la persona "Lady" del bot por otra. El patch script `patch_travel_concierge.py` ya hizo la migración de "Cleo" a "Lady"; revertirlo sería confuso.
- Reemplazar las APIs gratuitas (Open-Meteo, exchangerate-api, MyMemory) por opciones pagas. El proyecto está diseñado para costo cero.
- Mover la knowledge base a Vertex AI Vector Search o similar. Sale del free tier.
- Hacer las fotos del journal públicas (`make_public`). Son personales y la familia confía en que son privadas.
- Aumentar `MAX_HISTORY_PAIRS` sin revisar el costo de Gemini.

## Bugs conocidos (priorizar antes de features nuevos)

Los 3 bugs P1 originales están resueltos (2026-05-11). Pendientes:

1. **Deploy roto en prod** — revisión `00054-569` rompía la navegación. **Causa raíz identificada y fix listo**: `st.stop()` en la rama `elif code and oauth_code_processed` de `auth_gate()`. Archivos corregidos: `auth/google_oauth.py` y `utils/logger.py`. Pendiente: hacer el re-deploy siguiendo el checklist pre-deploy. Ver `docs/POSTMORTEM_2026-05-11.md`.
2. `modules/emergency_card.py:255-291` — campos críticos (pasaporte, tipo de sangre, hotel, contacto Lima) se capturan via `st.text_input` pero no se persisten. Se pierden al recargar. Fix: guardar en Firestore `perfil_familia/<user_email>`.
3. `utils/knowledge_base.py` — `FutureWarning` de Firestore por `query.where(field, op, val)` deprecado. Conviene migrar a `filter=...` cuando se toque el archivo.

Detalle completo en [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md).

Detalle completo y prioridades en [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md).

## Hoja de ruta del viaje (relevante para fechas)

- 14 jul: LIM -> MAD
- 15-18 jul: Madrid (cumple Camila el 17, Parque Warner + StreetXO)
- 19-20 jul: Bayona
- 21-24 jul: París (cumple Giovanna el 21, Eiffel + Le Train Bleu; Versalles el 23; Disney el 24)
- 25-26 jul: Bruselas
- 27-30 jul: Ámsterdam (casa familiar, sin costo de hotel)
- 30 jul: AMS -> MAD -> LIM