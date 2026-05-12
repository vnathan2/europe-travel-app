# Europe Travel 2026 - Documentación Técnica

> App familiar (Jonathan, Giovanna, Camila) para gestionar el viaje a Europa del 15 al 30 de julio de 2026. Stack: Streamlit + Google Cloud (Firestore, Cloud Storage, Secret Manager, Cloud Run) + Gemini 2.5 Flash + Tavily.

## Resumen ejecutivo

- App web monolítica en Python construida sobre Streamlit, desplegada en Cloud Run (us-east1) detrás de OAuth2 con Google.
- 12 módulos funcionales orquestados por un router dinámico (`app.py`) con lazy import.
- Persistencia en Firestore (gastos, diario, conversiones, knowledge base, embeddings) y Cloud Storage (fotos privadas comprimidas).
- IA generativa: Gemini 2.5 Flash para chat, recomendaciones y sugerencias contextuales; `gemini-embedding-001` para RAG.
- Búsqueda web vía Tavily; clima vía Open-Meteo; tipo de cambio vía exchangerate-api; traducción vía MyMemory.
- Control de roles (ADMIN vs FAMILIAR) basado en email autorizado; ADMIN ve precios y módulos restringidos (Night Life, Admin Panel).
- Toda la arquitectura está optimizada para mantenerse dentro del free tier de GCP (caching agresivo, secrets mínimos, compresión de imágenes).

## 1. Topología y flujo

```
                 ┌──────────────────────────────────────────────┐
   Browser   ──► │  Cloud Run (Streamlit 1.32, Python 3.11)    │
                 │  app.py (router + theme + auth gate)         │
                 └───┬───────────────┬───────────────┬──────────┘
                     │               │               │
       ┌─────────────▼───┐   ┌───────▼──────┐   ┌────▼───────────┐
       │ Google OAuth2   │   │  Modules     │   │  Utils         │
       │  (login + role) │   │  (12 vistas) │   │  (gcp, theme,  │
       └─────────────────┘   └──┬───┬───┬───┘   │   price, KB)   │
                                │   │   │       └──┬─────────────┘
              ┌─────────────────┘   │   └─────────┐│
              ▼                     ▼             ▼▼
       ┌──────────────┐  ┌──────────────────┐ ┌──────────────────┐
       │  Gemini      │  │   APIs externas  │ │  GCP Firestore   │
       │  + Tavily    │  │  Open-Meteo,     │ │  + Cloud Storage │
       │  (chat, RAG) │  │  ExchangeRate,   │ │  + Secret Mgr    │
       │              │  │  MyMemory, etc.  │ │                  │
       └──────────────┘  └──────────────────┘ └──────────────────┘
```

### Ciclo de request

1. `app.py` setea config de página, modo (DEV/PROD) y dispara `auth_gate()`.
2. `auth_gate()` procesa el `?code=` de OAuth si aplica, intercambia por token y resuelve el rol contra la lista blanca (`ADMIN_EMAIL`, `FAMILIAR_EMAIL_1/2`).
3. Una vez autenticado, se inyecta el tema CSS por ciudad (`utils.ui_theme.apply_theme`) y se renderiza el menú lateral.
4. El usuario selecciona un módulo; `app.py` hace `importlib.import_module(MODULOS[id])` y llama `mostrar()`. Lazy import = arranque liviano.
5. Cada módulo lee/escribe Firestore o Storage via `utils.gcp_client` (clientes cacheados con `@st.cache_resource`).

## 2. Stack y dependencias clave

| Capa | Componente | Notas |
|---|---|---|
| Runtime | Python 3.11-slim (Docker) | Usuario no-root `myuser`, healthcheck Streamlit |
| UI | Streamlit 1.32 | Layout wide, sidebar expandido |
| Auth | OAuth2 Google (manual con `requests`) | Lista blanca por email, 2 roles |
| DB | Firestore (Native mode) | Colecciones: `gastos_viaje`, `journal_entries`, `conversiones_historial`, `knowledge_base`, `embeddings_cache` |
| Storage | Cloud Storage | Bucket `europe-travel-app-bucket`, fotos privadas (sin make_public) |
| Secrets | Secret Manager (4 secrets) | `GEMINI_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| Env vars | `--set-env-vars` Cloud Run | `OAUTH_REDIRECT_URI`, emails autorizados, bucket, tipo cambio fallback |
| IA | google-generativeai 0.5.2 | Modelos `gemini-2.5-flash` y `gemini-embedding-001` |
| Web search | tavily-python 0.3.3 | Búsqueda web con presupuesto controlado |
| Datos | pandas, plotly, Pillow | Visualizaciones y compresión de imágenes |

## 3. Autenticación y autorización (`auth/google_oauth.py`)

- Flujo OAuth2 manual (sin librería específica): construye URL, intercambia code por token, fetch `userinfo`.
- Detección automática de `redirect_uri`:
  1. Variable `OAUTH_REDIRECT_URI`.
  2. `st.context.headers["host"]` con heurística para `run.app` / `localhost`.
  3. Si no hay configuración ni host detectable, falla fast con `st.error` + `st.stop()` indicando configurar la variable (ya no hay URLs hardcodeadas).
- Modo `APP_MODE=DEVELOPMENT` saltea OAuth e inyecta `dev@local.com` como ADMIN (línea 22-29 de `app.py`).
- Roles: `ADMIN` (ve precios, accede a Night Life y Admin Panel) y `FAMILIAR`.
- Gate de seguridad: `RESTRICCIONES = ["night_life", "admin_panel"]` se valida en `app.py:95-99`.
- **Rate limit del login**: `MAX_LOGIN_ATTEMPTS=5` intentos en una ventana de `LOGIN_WINDOW_SEC=300` segundos por sesión de navegador. Implementado en `auth_gate` antes de procesar el `code`. Resetea al login exitoso. Mitigación OWASP A07. La granularidad por sesión no detiene ataques distribuidos pero sí frena rebotes de un mismo cliente.

## 4. Módulos funcionales

### 4.1 `euro_budgeter.py` - Euro-Budgeter

- Registro de gastos en Firestore (`gastos_viaje`) con campos: fecha, ciudad, categoría, descripción, monto en EUR y PEN, tipo cambio, usuario, timestamp.
- Conversión automática EUR↔PEN usando `utils.price_helper.get_exchange_rate` (cache 1h, fallback 3.85).
- Dashboard con métricas (gastado, disponible vs presupuesto base 7985 EUR) y `st.bar_chart` por categoría.
- Caching de lecturas con `@st.cache_data(ttl=600)` para reducir reads en Firestore. Invalida con `.clear()` tras cada inserción.
- Tab "Exportar" declarada en el código pero no implementada en cuerpo (`tab_exportar` queda vacío).

### 4.2 `emergency_card.py` - Emergency Card

- Datos 100% hardcodeados, sin dependencias de red. Sirve incluso sin internet.
- Estructura: por país (España, Francia, Bélgica, Países Bajos) con números, embajada Perú, hospitales, consejos.
- Tab seguro de viaje (datos de la póliza), datos de la familia (form sin persistir), consejos generales.
- Risk: campos de pasaporte y tipo de sangre se capturan via `st.text_input` pero no se guardan en sesión ni Firestore.

### 4.3 `birthday_planner.py` - Birthday Planner

- Planes confirmados para los cumpleaños de Camila (17 jul, Madrid, Warner + StreetXO) y Giovanna (21 jul, París, TGV + Eiffel + Le Train Bleu).
- Tab "Sugerencias IA": Gemini 2.5 Flash genera mensaje de cumpleaños + sugerencias personalizadas a partir del perfil hardcodeado.
- Presupuesto y precios condicionados por rol (`mostrar_precio`).

### 4.4 `shopping_guide.py` - Shopping Guide

- Base de tiendas hardcodeada por ciudad (>50 tiendas) con categoría, dirección, horario, precio (€/€€/€€€), rating, productos, tip de ahorro, comentario, audiencia.
- Filtros: ciudad, categoría, persona (Jonathan/Camila/Giovanna), texto libre.
- Fallback inteligente "Lady": si el buscador local no devuelve resultados, llama a Tavily + Gemini para generar sugerencias en línea con tono de schnauzer viajera.
- Sección Tax Free y tips de aduana para regreso a Perú.

### 4.5 `packing_checker.py` - Packing Checker

- Lista de equipaje categorizada (documentos, ropa adultos, ropa hija, salud, tecnología, higiene, accesorios) con flag `critico` y cantidad sugerida.
- Pronóstico de clima por las 5 ciudades vía Open-Meteo (gratuito, sin API key). Si falla, fallback histórico hardcodeado por ciudad.
- Genera recomendaciones automáticas según temperatura máxima, días de lluvia y temperatura mínima.
- Persistencia: `st.session_state.items_marcados` (volátil, se pierde al cerrar sesión).

### 4.6 `voice_translator.py` - Traductor de Voz

- 3 tabs: Voz (Web Speech API en JS embebido), Texto (input + MyMemory API), Frases prearmadas con TTS.
- Reconocimiento de voz con `webkitSpeechRecognition`, traducción con MyMemory (gratis, con límite de cuota), TTS con `SpeechSynthesisUtterance`.
- Soporta inglés (en-GB), francés (fr-FR), neerlandés (nl-NL).
- Bug menor: frase "Necesito un médico" en NL escribe `docker` en vez de `dokter` (línea 57).

### 4.7 `train_optimizer.py` - Train-Route Optimizer

- 5 rutas hardcodeadas: MAD→Bayona (Renfe+SNCF), Bayona→París (TGV), París→Bruselas (Eurostar), Bruselas→Ámsterdam (Eurostar), Ámsterdam→Madrid (vuelo low-cost).
- Cada ruta con operador, salida, llegada, duración, cambio, precio por persona y familia, link de reserva y alternativa.
- Estado de reserva con checkbox + localizador (volátil, session_state).
- Tab "Resumen de Costos" calcula totales min/max/promedio familia.

### 4.8 `trip_journal.py` - Trip Journal

- Entradas en Firestore (`journal_entries`) con fecha, ciudad, título, texto, highlight, autor, ánimo (slider emoji), rating, fotos (paths GCS).
- Compresión de imagen: Pillow redimensiona a max 1200 px y guarda JPEG calidad 75. Reduce drásticamente el storage.
- Fotos privadas (sin `make_public`). Se descargan on-demand con `descargar_foto()` cacheado 1h.
- Eliminación cascade: al borrar entrada, elimina blobs en GCS.

### 4.9 `phrase_pocket.py` - Conversor de Moneda

- 5 tabs: convertir simple, multi-moneda, calculadora del viaje, historial (Firestore), gráfico EUR/PEN últimos 30 días.
- API: `exchangerate-api.com/v4` (gratis, 1500 req/mes). Cache 1h.
- Gráfico histórico con Plotly. Líneas de referencia para "hoy" y "presupuesto base 4.0".
- Análisis comparativo: si euro está 1%+ sobre/bajo promedio, muestra alerta.

### 4.10 `travel_concierge.py` - Travel Concierge (Lady)

Es el módulo más complejo. Tiene 4 tabs:

**Tab Chat con Lady**
- Persona: "Lady", schnauzer miniatura viajera (tono cariñoso, emojis 🐾).
- Modelo: `gemini-2.5-flash` con `system_instruction` que incluye contexto del itinerario completo.
- Patrón RAG: para cada pregunta genera embedding con `gemini-embedding-001`, busca docs relevantes en Firestore por similitud coseno (umbral 0.5, top 4) y los inyecta en el prompt.
- Patrón Web Augmented: si el LLM responde `[BUSCAR_WEB: query]`, dispara Tavily y manda los resultados de vuelta al chat para una segunda pasada.
- Limita historial a `MAX_HISTORY_PAIRS=8` (16 mensajes) para acotar costo de tokens.

**Tab Itinerario Día a Día**
- 16 días (15 al 30 jul 2026) con actividades hora a hora: id, hora, tipo, ícono, nombre, detalle, costo.
- IDs como `mad_01`, `par_03`, `bru_07`. Soporta marcado de "completado" en session_state.

**Tab Alertas del Día**
- Para la fecha actual, obtiene clima vía Open-Meteo y revisa actividades outdoor (set `ACTIVIDADES_OUTDOOR`).
- Si detecta lluvia, ofrece "alternativas bajo techo" generadas por Gemini con prompt específico.

**Tab Mapa del Viaje**
- Genera Google Maps URLs `dir/?api=1&destination=lat,lon&travelmode=walking` por actividad.

### 4.11 `night_life.py` - Night Life (ADMIN only)

- Datos hardcodeados de bares/discotecas por ciudad y coffee shops de Ámsterdam.
- Coffee shops incluyen producto, precio, THC aproximado y comentario.
- **Disclaimer legal reforzado** (2026-05-11): `st.error` con prohibición explícita de importación al Perú (Decreto Legislativo 1126, Ley 28305, Código Penal Art. 296), `st.warning` con marco legal neerlandés (gedoogbeleid + restricciones turísticas recientes) y `st.info` aclarando que el contenido es solo educativo.

### 4.12 `admin_panel.py` - Admin Panel (ADMIN only)

- Tab 1 Ingesta: orquesta `utils.knowledge_base` para alimentar la KB desde Wikipedia, OpenStreetMap (Overpass) y Tavily con queries específicas por ciudad y categoría (TripAdvisor, blogs latinos, transporte, gastronomía, tips familia).
- Presupuesta créditos Tavily (`TAVILY_BUDGET_INGESTA=80`) y advierte si la selección excede.
- Tab 2 Stats: lee `knowledge_base` desde Firestore y muestra distribución por ciudad y fuente.
- Tab 3 Limpiar: elimina docs por ciudad con doble confirmación.
- **Bug crítico**: la función `run_ingesta_ciudad` define `contar_queries_tavily` dentro de su cuerpo y el loop `for fuente in fuentes` queda como código inalcanzable después del `return` de la nested function. La ingesta nunca corre. Ver `modules/admin_panel.py:172-254` en IMPROVEMENTS.

## 5. Capas utilitarias

### 5.1 `utils/gcp_client.py`
- Clientes Firestore, Storage y Secret Manager cacheados con `@st.cache_resource` (única conexión por proceso, ahorra latencia).
- `get_secret(name)`: leer de Secret Manager con fallback a `os.getenv`. Lista `_ENV_VARS_ONLY` decide qué se debe leer solo desde env (ahorra cuota de Secret Manager).
- `upload_to_bucket`: subida simple, sin signed URLs.

### 5.2 `utils/knowledge_base.py` - Motor RAG
- Fuentes: Wikipedia REST + MediaWiki API, OpenTripMap (con fallback Overpass de OSM), Tavily.
- Embeddings: `gemini-embedding-001` con `task_type` distinto para `retrieval_document` vs `retrieval_query`.
- `buscar_conocimiento(query, ciudad, top_k)` con cache 10 min en `_cargar_docs_kb` para mantenerse en free tier de Firestore (50k reads/día).
- `invalidar_cache_kb()` se llama desde Admin Panel tras una ingesta exitosa.
- IDs únicos derivados de `ciudad_fuente_titulo[:30]` para evitar duplicados.
- Función `formatear_conocimiento(resultados)` produce el bloque de contexto que se inyecta en el prompt.
- Logging estructurado vía `utils.logger` para todos los errores de fetch (Wikipedia, OpenTripMap, Overpass, Tavily).

### 5.3 `utils/ui_theme.py`
- 5 paletas por ciudad (Madrid, Bayona, París, Bruselas, Ámsterdam) + default. Cada una con primary, secondary, accent, bg_dark, bg_card, gradient, sidebar_bg.
- `apply_theme()` inyecta CSS global (incluye fuente Inter desde Google Fonts).
- Toggle modo claro/oscuro en sidebar (session_state.modo_oscuro).
- `show_loading_animation` con mensajes contextuales por módulo (Lady, trenes, cumpleaños, night life).
- Panel offline con números de emergencia, frases, itinerario rápido, hoteles, vuelos.
- Menú estructurado en `MENU_SECTIONS` (Finanzas, Planificación, Especiales, Utilidades) y `MENU_ADMIN`.

### 5.4 `utils/price_helper.py`
- `mostrar_precio(str, fallback="🔒")`: devuelve precio si es admin, fallback en otro caso. Default seguro (False).
- `get_exchange_rate()`: cachea 6h, fallback env var `FALLBACK_EUR_PEN_RATE` con default 3.95. Si la API falla, registra warning estructurado (visible en Cloud Logging).

### 5.5 `utils/logger.py`
- Logger compartido. Detecta Cloud Run vía `K_SERVICE` y emite JSON estructurado a stdout. Cloud Logging parsea automáticamente los campos `severity`, `message`, `module`, `function`, `line`, `exception`.
- En local, formato legible con timestamp.
- Sin dependencias externas; usa solo `logging` y `json` de stdlib.
- Uso típico: `from utils.logger import get_logger; logger = get_logger(__name__); logger.exception("contexto")`.

### 5.6 `utils/family_profiles.py`
- Perfiles hardcodeados con gustos y recomendaciones específicas por persona y por ciudad.
- `get_contexto_perfiles()` produce un bloque inyectable al prompt de Gemini (no se ve referenciado activamente en travel_concierge.py).

## 6. Despliegue (Cloud Run)

- Build: Dockerfile multi-stage simple, python 3.11-slim. Usuario no-root.
- Build se sube con `gcloud builds submit` ignorando archivos del `.gcloudignore` (tests, docs, .venv, .env, etc.).
- Deploy con `gcloud run deploy` reusa env vars y secrets configurados previamente en el servicio:
  - Memoria: 512 MiB
  - Puerto: 8080
  - 4 secrets montados desde Secret Manager
  - 7 env vars (project id, bucket, fallback rate, redirect URI, 3 emails)
- `scripts/setup_secrets.sh` se mantiene para rotación de claves o setup inicial, **no** para deploys regulares.
- Tag de imagen: `us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest`.
- Healthcheck nativo de Streamlit: `/_stcore/health`.
- **APIs habilitadas** en el proyecto: `cloudbuild.googleapis.com`, `run.googleapis.com`, `artifactregistry.googleapis.com`, `firestore.googleapis.com`, `secretmanager.googleapis.com`, `storage.googleapis.com`.
- **Service account de Cloud Build** (`565528729494@cloudbuild.gserviceaccount.com`) tiene `roles/cloudbuild.builds.builder` para que el build se autorice.

## 7. Modelo de datos (Firestore)

| Colección | Documento | Campos clave |
|---|---|---|
| `gastos_viaje` | auto-id | fecha, ciudad, categoria, descripcion, monto_eur, monto_pen, tipo_cambio, usuario, timestamp |
| `journal_entries` | auto-id | fecha, ciudad, titulo, texto, highlight, autor, animo, rating, fotos[], timestamp |
| `conversiones_historial` | auto-id | monto_origen, moneda_origen, monto_resultado, moneda_destino, tasa, fecha, timestamp |
| `knowledge_base` | `{ciudad}_{fuente}_{titulo[:30]}` | ciudad, fuente, titulo, texto, url, categoria, fecha_ingesta, embedding[768], timestamp |
| `embeddings_cache` | (declarada, sin uso activo) | - |

## 8. Variables de entorno

Sensibles (Secret Manager): `GEMINI_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

No sensibles (env vars): `GCP_PROJECT_ID`, `GCS_BUCKET_NAME`, `OAUTH_REDIRECT_URI`, `ADMIN_EMAIL`, `FAMILIAR_EMAIL_1`, `FAMILIAR_EMAIL_2`, `FALLBACK_EUR_PEN_RATE`, `APP_MODE` (DEV o PROD), `DEBUG_AUTH` (true para mostrar URI activa en login), `OPENTRIPMAP_API_KEY` (opcional).

## 9. Performance y costo

- Caching agresivo: `@st.cache_resource` (clientes GCP, modelo Gemini), `@st.cache_data` (lecturas Firestore TTL 10 min, tipo de cambio TTL 1h, fotos TTL 1h, historial tasas TTL 24h).
- Lazy import por módulo (sólo el activo se carga).
- Imágenes comprimidas a 1200 px / quality 75 antes de subir a GCS.
- Tope manual de queries Tavily en Admin Panel (`TAVILY_BUDGET_INGESTA=80` con margen para chat).
- Truncado de historial de chat a 8 pares (16 mensajes) en travel_concierge.

## 10. Frameworks aplicables al review

- **OWASP Top 10 (2021)**: A01 control de acceso (lista blanca por email correcto, pero sin rate limit en login); A02 cryptographic failures (secrets en Secret Manager ✓); A05 misconfiguration (URL hardcodeada en código). Fuente: https://owasp.org/Top10/
- **Twelve-Factor App** (Heroku, 2011-2017): config en env vars ✓, dependencias declaradas en requirements.txt ✓, build/release/run separados ✓, logs como streams (parcial, varios `print`). Fuente: https://12factor.net
- **Google SRE Workbook** (Beyer et al., 2018): el caching deliberado para mantenerse en free tier es buen ejemplo de "trade-off explícito entre costo y latencia". Sin embargo, faltan SLI/SLO y observabilidad (no hay logging estructurado ni métricas).
- **Streamlit best practices**: `@st.cache_resource` para clientes singletons y `@st.cache_data` para datos, aplicado correctamente.
