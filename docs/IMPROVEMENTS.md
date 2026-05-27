# Puntos de mejora - Europe Travel App

> Backlog priorizado de oportunidades técnicas y funcionales detectadas en el review del 10 de mayo de 2026. Las prioridades usan la matriz ICE (Impact, Confidence, Ease) popularizada por Sean Ellis en GrowthHackers (2015), adaptada al contexto familiar/free-tier del proyecto.

## Resumen ejecutivo

> Última sincronización con el código: **2026-05-12** (sesión de trabajo de la tarde). Verificado contra el repo.

- **0 bugs bloqueantes** — los 3 P1 están resueltos (✅ 2026-05-11).
- **P2 seguridad y cumplimiento**: 5/5 resueltos.
- **P3 performance, costo y UX**: 7/7 resueltos. Catálogo a JSON (3.5), galería con signed URLs (3.3) y `time.sleep(0.5)` (3.2) cerrados el 2026-05-27.
- **P4 mantenimiento**: 4/4 resueltos. Lint con ruff cerrado el 2026-05-27, `.env.example` el 2026-05-12, tests cubiertos con 23 smoke tests.
- **Riesgo operativo**: fallback de Gemini con 10 FAQ pre-canned offline (`utils/offline_faqs.py`), cerrado el 2026-05-12. Open-Meteo y exchangerate-api ya tenían fallbacks.

## Prioridad 1 - Bloqueantes (resolver antes del viaje)

### 1.0 ✅ HECHO - Validación end-to-end del pipeline RAG

- **Validado el**: 2026-05-11.
- **Cómo**: ingesta completa de las 5 ciudades vía `python scripts/ingest_knowledge.py` (74 docs procesados, 23 nuevos en Firestore con embeddings de Gemini). Validación programática vía `scripts/smoke_rag.py` (5 queries con similitud > 0.69) y validación interactiva en Streamlit local con chat de Lady.
- **Resultado**: Firestore, Gemini embeddings, Wikipedia, OpenStreetMap (Overpass) y Tavily funcionando. ~51 créditos Tavily consumidos del bucket mensual.
- **Observaciones menores**:
  - El script de ingesta reporta totales por ciudad acumulados (cosmetic bug, no afecta lo guardado).
  - OpenTripMap devuelve 0 atracciones porque no hay API key; sin embargo el fallback Overpass sí guarda docs (visible en queries RAG).
  - Firestore lanza `FutureWarning` por `query.where(field, op, val)` deprecado; conviene migrar a `filter=...` cuando se toque `utils/knowledge_base.py`.

### 1.1 ✅ HECHO - Ingesta de KB desde Admin Panel

- **Resuelto el**: 2026-05-11.
- **Archivo**: `modules/admin_panel.py`.
- **Fix aplicado**: `contar_queries_tavily` movida fuera del cuerpo de `run_ingesta_ciudad` — ahora es función top-level. El `for fuente in fuentes` es alcanzable y la ingesta desde la UI funciona correctamente. El workaround de la terminal sigue disponible pero ya no es necesario.

### 1.2 ✅ HECHO - Typo en traducción de emergencia (Neerlandés)

- **Resuelto el**: 2026-05-11.
- **Archivo**: `modules/voice_translator.py`.
- **Fix aplicado**: "Necesito un médico" en NL ahora dice correctamente `"Ik heb een dokter nodig"`. Era una frase de emergencia crítica.

### 1.3 ✅ HECHO - RAG: cache por ciudad para mantenerse en free tier

- **Resuelto el**: 2026-05-11.
- **Archivo**: `utils/knowledge_base.py`.
- **Fix aplicado**: función `_cargar_docs_kb(ciudad)` con `@st.cache_data(ttl=600)` pre-filtra por ciudad antes de stream. Los docs se cachean 10 min en memoria — el free tier de Firestore (50k reads/día) aguanta perfectamente el uso del chat. `invalidar_cache_kb()` se llama desde Admin Panel tras cada ingesta exitosa.
- **Pendiente a largo plazo**: si la KB supera los ~1000 docs por ciudad, evaluar índice Firestore por `ciudad + categoria` o migrar a Firestore vector search (en preview, free hasta cierto volumen).

## Prioridad 2 - Seguridad y cumplimiento

### 2.1 ✅ HECHO - URL de producción hardcodeada en código

- **Resuelto el**: 2026-05-11.
- **Archivo**: `auth/google_oauth.py:40-69` (función `get_redirect_uri`).
- **Fix aplicado**: orden de resolución 1) variable `OAUTH_REDIRECT_URI` (canonical para prod), 2) detección automática por `st.context.headers.host` (run.app o localhost), 3) si nada matchea, falla fast con `st.error` + `st.stop` y mensaje claro. Sin URLs hardcodeadas en código.

### 2.2 ✅ HECHO - Rate limit en el login

- **Resuelto el**: 2026-05-10.
- **Archivo**: `auth/google_oauth.py` (constantes `MAX_LOGIN_ATTEMPTS=5`, `LOGIN_WINDOW_SEC=300`; helpers `_login_bloqueado`, `_registrar_intento_login`, `_resetear_throttle`).
- **Cobertura**: 3 tests nuevos en `tests/test_smoke.py` (no bloqueado, bloqueado al superar, libera al expirar ventana).
- **Limitación**: el throttle es por sesión de navegador, no por IP. Mitiga rebotes de un mismo browser pero no un ataque distribuido. Para eso haría falta Cloud Armor (sale del free tier) o un middleware adicional.
- **Referencia**: OWASP A07:2021 - Identification and Authentication Failures.

### 2.3 ✅ HECHO - Disclaimer legal en Night Life

- **Resuelto el**: 2026-05-11.
- **Archivo**: `modules/night_life.py` tab de coffee shops.
- **Cambios**:
  - `st.error` con prohibición explícita de importación a Perú, citando Decreto Legislativo 1126, Ley 28305 y Código Penal Art. 296 (pena 8-15 años).
  - `st.warning` actualizado con el marco legal neerlandés (gedoogbeleid) y mención a las restricciones recientes de acceso a turistas en algunos barrios.
  - `st.info` aclara que el contenido es solo educativo, no recomendación de adquisición ni transporte.
- **Verificado**: `modules/shopping_guide.py` tab "Tips para llevar compras a Lima" no menciona cannabis ni productos ambiguos; sólo bienes legales con sus respectivos certificados (tulipanes).

### 2.4 ✅ HECHO - Inputs de emergencia no se persisten

- **Resuelto el**: 2026-05-11.
- **Archivo**: `modules/emergency_card.py:11` (`COLECCION_PERFIL = "perfil_familia"`), `:163` (`cargar_perfil_familia`), `:176` (`guardar_perfil_familia`).
- **Fix aplicado**: pasaporte, tipo de sangre, hoteles por ciudad y contacto Lima se persisten en `Firestore.collection("perfil_familia")`. Cache de lectura con `@st.cache_data`, invalidado tras cada escritura. El formulario sigue mostrando los datos guardados en el siguiente reload.

### 2.5 ✅ HECHO - Logging estructurado

- **Resuelto el**: 2026-05-12.
- **Archivo**: `utils/logger.py`.
- **Fix aplicado**: tras descartar al logger como causa raíz del deploy 00054 (la causa real fue el `st.stop()` en `auth_gate`), se restauraron los dos formatters: `_JsonFormatter` para Cloud Run (detectado por `K_SERVICE` env var, emite payload con `severity`/`message`/`module`/`function`/`line`/`exception`) y `_ReadableFormatter` para local. Se mantiene `propagate=True` por precaución para no interferir con la captura de logs de Streamlit.
- **Migración en código**: `utils/knowledge_base.py`, `utils/gcp_client.py`, `utils/price_helper.py` y módulos sensibles usan `logger.exception` / `logger.warning` en lugar de `print`.
- **Validado en prod**: revisión `00065-hat` corriendo desde 2026-05-12 sin errores ni regresiones en logs.

## Prioridad 3 - Performance, costo y UX

### 3.1 ✅ HECHO - Limpieza de `requirements.txt`

- **Resuelto el**: 2026-05-11.
- **Removidos**: `scikit-learn`, `matplotlib`, `wikipedia-api`, `openpyxl`, `fpdf2`. Ninguno importado en código (verificado con grep).
- **Mantenidos**: streamlit, python-dotenv, pandas, numpy, plotly, Pillow, requests, tavily-python, google-cloud-firestore, google-cloud-storage, google-cloud-secret-manager, google-generativeai.
- **Validado**: 17 smoke tests pasan, los 12 módulos importan correctamente.
- **Beneficio**: imagen Docker más liviana (sklearn solo ya pesa >100 MB) y build de Cloud Run más rápido.

### 3.2 ✅ HECHO - `time.sleep(0.5)` en cada cambio de módulo

- **Resuelto el**: 2026-05-27.
- **Archivo**: `utils/ui_theme.py` (`show_loading_animation`), `app.py` (enrutamiento).
- **Fix aplicado**: se eliminó el `time.sleep(duration)` que bloqueaba el thread del servidor 0.5s en cada navegación. Ahora `show_loading_animation` solo renderiza el spinner temático y devuelve el placeholder; el caller (app.py) lo limpia **después** del `importlib.import_module`, así el spinner es visible exactamente durante la carga real del módulo (feedback honesto) en vez de un delay artificial. Se quitó también `import time` (ya sin uso) y el parámetro `duration`.
- **Validado**: ruff limpio, 23 tests, ui_theme importa.

### 3.3 ✅ HECHO - Galería del Trip Journal hace N descargas a GCS

- **Resuelto el**: 2026-05-27.
- **Archivo**: `utils/gcp_client.py` (`get_signed_url`), `modules/trip_journal.py` (`foto_src` + render de galería y entradas).
- **Fix aplicado**: `get_signed_url` genera signed URLs v4 (expiración 1h, cacheadas 50 min) para que el navegador baje las fotos directo de GCS, sin pasar los bytes por Cloud Run. Las fotos siguen **privadas** (acceso temporal, sin `make_public`). `foto_src` usa la URL firmada y, si la firma falla, cae a `descargar_foto` (bytes) — sin riesgo de regresión.
- **Infra (gotcha de Cloud Run)**: las credenciales por defecto no tienen private key, así que se firma vía IAM `signBlob`. Requirió grant de `roles/iam.serviceAccountTokenCreator` a la SA `565528729494-compute@developer.gserviceaccount.com` sobre sí misma (la API `iamcredentials` ya estaba habilitada). signBlob es gratis (free tier OK).
- **Validado**: ruff limpio, 23 tests, fallback verificado. Validación end-to-end de la firma real: post-deploy en prod.

### 3.4 ✅ HECHO - `MODULO_CIUDAD` completo

- **Resuelto el**: 2026-05-11.
- **Archivo**: `utils/ui_theme.py`.
- **Cambio**: agregadas las entradas `shopping_guide` y `admin_panel` al dict para que los 12 módulos tengan tema explícito.

### 3.5 ✅ HECHO - Catálogo de tiendas en código Python

- **Resuelto el**: 2026-05-27.
- **Archivo**: `data/shopping.json` (54 tiendas en 5 ciudades), `modules/shopping_guide.py` (`_cargar_tiendas` lee el JSON al importar; `TIENDAS = _cargar_tiendas()`).
- **Fix aplicado**: las ~730 líneas del dict `TIENDAS` salieron del .py a `data/shopping.json`. El JSON se generó desde el dict original (round-trip verificado `==`), así que la data es idéntica. Ahora editar tiendas/horarios es JSON plano, sin tocar Python ni arriesgar sintaxis.
- **Gotcha resuelto**: tanto `.gitignore` como `.gcloudignore` tenían `*.json` (para no filtrar credenciales), lo que excluía el catálogo. Se agregó la excepción `!data/shopping.json` en ambos. Verificado: git lo trackea y Cloud Build lo sube.
- **Matiz honesto**: el JSON viaja **dentro de la imagen Docker**, así que publicar un cambio del catálogo **sigue requiriendo build + deploy**. Lo que se ganó es separar data de código (edición trivial, sin riesgo de Python). Para edición sin redeploy habría que mover el catálogo a Firestore/GCS (no se hizo: agrega latencia/lecturas; queda como posible paso futuro).
- **Validado**: ruff limpio, 23 tests, TIENDAS carga idéntico (54 tiendas), import OK.

### 3.6 ✅ HECHO - Persistencia de packing en Firestore compartida

- **Resuelto el**: 2026-05-12.
- **Archivo**: `modules/packing_checker.py:11` (constantes Firestore), `:43-78` (cargar/guardar).
- **Fix aplicado**: nuevas funciones `cargar_packing()` (cacheada 10 min con `@st.cache_data`) y `guardar_packing(items)` (last-write-wins). Documento único `packing/familia` compartido entre Jonathan, Giovanna y Camila. Cada escritura guarda `actualizado_por` con el email del usuario. La persistencia es debounced naturalmente: solo escribe a Firestore cuando el snapshot inicial difiere del estado actual al final del render. El botón "Reiniciar lista" también limpia Firestore.
- **Cobertura**: 2 smoke tests nuevos en `tests/test_smoke.py` (cargar desde Firestore, guardar payload completo con `actualizado_por`).
- **Limitación conocida**: las tabs "Lista completa" y "Solo críticos" usan keys de widget distintas para evitar `DuplicateWidgetID` de Streamlit, por lo que la sincronización entre tabs solo ocurre en el primer render de cada widget. La persistencia entre sesiones y entre usuarios funciona correctamente.

### 3.7 ✅ HECHO - Tipo de cambio fallback

- **Resuelto el**: 2026-05-11.
- **Archivo**: `utils/price_helper.py`.
- **Cambios**:
  - TTL del cache subido de 1h a 6h (4 calls/día contra el límite gratuito de 1500/mes).
  - Default literal subido de 3.85 a 3.95 (cercano a la tasa observada según BCRP, https://www.bcrp.gob.pe/).
  - Logger warning estructurado cuando la API falla y se cae al fallback, para detectar caídas sostenidas en Cloud Logging.
  - El override por env var `FALLBACK_EUR_PEN_RATE` sigue disponible (ajustable sin redeploy).

## Prioridad 4 - Mantenimiento

### 4.1 ✅ HECHO - Sin tests automatizados

- **Resuelto el**: 2026-05-11.
- **Archivo**: `tests/test_smoke.py` (17 tests), `tests/conftest.py` (stubs de Firestore/Gemini/Tavily para no tocar servicios reales), `pyproject.toml` (config pytest).
- **Cobertura**:
  - Auth: `is_admin()` por rol, `get_user_role()` por email, rate limit (3 tests: bajo límite, sobrepaso, expiración de ventana).
  - Price helper: `mostrar_precio` respeta `show_prices()`, conversión a soles con tasa fallback.
  - KB: `cosine_similarity` con ortogonales/idénticos, dedupe de docs.
  - Voice translator: traducciones críticas (médico, ambulancia, alergia) en 4 idiomas.
  - Phrase pocket: `convertir(100, EUR, EUR, _) == 100`, lookup de tasa cacheada.
- **Tiempo de ejecución**: <1s. Sin dependencia de red ni APIs externas.

### 4.2 ✅ HECHO - Linting con ruff

- **Resuelto el**: 2026-05-27.
- **Archivo**: `pyproject.toml` (`[tool.ruff]`), `requirements-dev.txt` (`ruff==0.15.14`).
- **Config**: `select = ["E","F","I","W","UP"]`, `line-length=100`, `ignore=["E501"]` (comentarios en español y datos hardcoded). Per-file ignore de `E402` en `app.py` (imports después de `st.set_page_config`/auth gate, patrón Streamlit intencional).
- **Limpieza aplicada**: 86 hallazgos → 0. Se quitaron imports sin usar (F401), se ordenaron imports (I001, preservando los perezosos dentro de funciones), newlines finales, f-strings sin placeholders y código muerto (`border`/`bg` en el mapa de `travel_concierge`, `is_admin` no usado en `shopping_guide`, `if not gastos: return` en una línea en `euro_budgeter`).
- **Decisión sobre format**: `ruff format` NO se aplica en masa (cambiaría ~5.600 líneas y destruiría la alineación intencional de los dicts de datos). Queda disponible on-demand por archivo.
- **Validado**: `ruff check .` pasa limpio, 23 tests pasan, los 12 módulos importan.

### 4.3 ✅ HECHO - Eliminar `patch_travel_concierge.py`

- **Resuelto el**: 2026-05-11.
- **Acción**: archivo eliminado. La historia queda en git log para auditoría.

### 4.4 ✅ HECHO - Falta `.env.example`

- **Resuelto el**: 2026-05-12.
- **Archivo**: `.env.example` en la raíz.
- **Cobertura**: 17 variables documentadas agrupadas en 7 secciones (modo, OAuth, GCP, APIs externas, helpers de fallback, scripts de ingesta). Cada bloque explica de dónde sacar el valor y si va a Secret Manager en prod o como env var directa.

## Riesgos no técnicos

- **Crítico**: el viaje empieza en **64 días** (15 julio 2026, actualizado 2026-05-12). Cualquier mejora que toque rutas críticas (auth, ingesta, chat) debe terminar antes del 1 de julio para tener buffer de validación.
- **Mitigado parcialmente**: la app depende de 4 APIs externas (Gemini, Tavily, Open-Meteo, exchangerate-api). Mitigaciones actuales: (1) Open-Meteo tiene fallback hardcodeado de julio histórico en `packing_checker.get_clima`; (2) exchangerate-api tiene `FALLBACK_EUR_PEN_RATE` configurable en `price_helper`; (3) Tavily es opcional, Lady responde sin búsqueda web si falla; (4) Gemini ahora tiene fallback de 10 FAQ pre-canned (`utils/offline_faqs.py`) que matchean por keywords y cubren los casos críticos del viaje (robo pasaporte, teléfonos de emergencia 112, embajada peruana, bloqueo de tarjeta, vuelo perdido, asaltos, atención médica, transporte público). Implementado el 2026-05-12. Si quieres ampliar el cache offline (modo emergencia completo o PWA), está en backlog como item futuro.

## Framework de priorización aplicado

Se usó ICE (Impact × Confidence × Ease, escala 1-10) según Sean Ellis (https://growthhackers.com/articles/how-to-prioritize-your-tests-and-experiments-with-the-ice-score). Para un proyecto familiar y no monetizado, "Impact" se interpreta como impacto en la experiencia del viaje (datos accesibles, precisión, seguridad personal). Los items P1 tienen score > 200, P2 entre 100-200, P3 entre 50-100, P4 < 50.