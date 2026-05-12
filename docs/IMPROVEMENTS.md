# Puntos de mejora - Europe Travel App

> Backlog priorizado de oportunidades técnicas y funcionales detectadas en el review del 10 de mayo de 2026. Las prioridades usan la matriz ICE (Impact, Confidence, Ease) popularizada por Sean Ellis en GrowthHackers (2015), adaptada al contexto familiar/free-tier del proyecto.

## Resumen ejecutivo

- ~~3 bugs bloqueantes~~ **0 bugs bloqueantes** — los 3 P1 están resueltos (✅ 2026-05-11).
- 5 mejoras de seguridad o cumplimiento (URL hardcodeada, rate limit, disclaimer legal en Night Life, validación de inputs, manejo central de errores).
- 7 oportunidades de performance, costo o UX.
- 4 deudas de mantenimiento (tests, lint, CI, archivos huérfanos).

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

### 2.1 URL de producción hardcodeada en código

- **Archivo**: `auth/google_oauth.py:55, 59`.
- **Síntoma**: fallback contiene literal `"https://europe-travel-app-565528729494.us-east1.run.app"`. Si Cloud Run cambia el hash o se mueve la región, hay que recompilar. Y queda en git history.
- **Fix**: hacer obligatorio `OAUTH_REDIRECT_URI` en env vars. Si no está, fallar fast con mensaje claro.
- **Esfuerzo**: 15 minutos.

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

### 2.4 Inputs de emergencia no se persisten

- **Archivo**: `modules/emergency_card.py:255-291`.
- **Síntoma**: campos críticos (pasaporte, tipo de sangre, hotel, contacto Lima) se capturan via `st.text_input` pero no se guardan en sesión ni Firestore. Cada reload pierde el dato. Justo lo opuesto de lo que se necesita en una emergencia.
- **Fix**: persistir en `Firestore.collection("perfil_familia").document(<user_email>)` con cache lectura 10 min. O al menos guardar en session_state como mitigación inmediata.
- **Esfuerzo**: 1 hora.

### 2.5 ⚠️ PARCIAL - Logging estructurado (en investigación por postmortem)

- **Iniciado el**: 2026-05-11. **En pausa** hasta resolver la causa raíz del deploy 00054.
- **Archivo**: `utils/logger.py` — actualmente en **modo no-op** (devuelve `logging.getLogger` estándar sin handlers custom) para aislar si el formatter JSON/propagate fue la causa del bug de navegación en Cloud Run.
- **Migración completada en código**:
  - `utils/knowledge_base.py`: 6 `print(f"Error ...: {e}")` → `logger.exception(...)` con contexto.
  - `utils/gcp_client.py:get_secret`: el `except` ahora emite `logger.warning`.
- **Siguiente paso**: una vez identificada la causa raíz del deploy 00054, restaurar `logger.py` con los dos formatters (JSON en Cloud Run, legible en local) y re-deployar validando con `--no-traffic --tag=test` primero.
- **Sin dependencias nuevas**: Cloud Run captura stdout y parsea JSON con campos `severity`/`message`. Documentación: https://cloud.google.com/run/docs/logging

## Prioridad 3 - Performance, costo y UX

### 3.1 ✅ HECHO - Limpieza de `requirements.txt`

- **Resuelto el**: 2026-05-11.
- **Removidos**: `scikit-learn`, `matplotlib`, `wikipedia-api`, `openpyxl`, `fpdf2`. Ninguno importado en código (verificado con grep).
- **Mantenidos**: streamlit, python-dotenv, pandas, numpy, plotly, Pillow, requests, tavily-python, google-cloud-firestore, google-cloud-storage, google-cloud-secret-manager, google-generativeai.
- **Validado**: 17 smoke tests pasan, los 12 módulos importan correctamente.
- **Beneficio**: imagen Docker más liviana (sklearn solo ya pesa >100 MB) y build de Cloud Run más rápido.

### 3.2 `time.sleep(0.5)` en cada cambio de módulo

- **Archivo**: `app.py:74-76` (vía `show_loading_animation`).
- **Síntoma**: cada navegación entre módulos bloquea 0.5s artificiales. En móvil con red lenta el efecto es agravado.
- **Fix**: hacer la animación verdaderamente asíncrona (CSS only) o reducir a 0.2s. El loading visual no necesita sleep server-side.
- **Esfuerzo**: 30 minutos.

### 3.3 Galería del Trip Journal hace N descargas a GCS

- **Archivo**: `modules/trip_journal.py:160-173`.
- **Síntoma**: cada foto se descarga byte-a-byte desde GCS (cacheado 1h por foto). Con 50+ fotos el primer load es lento.
- **Fix**: usar signed URLs con expiración (`blob.generate_signed_url(expiration=timedelta(hours=1))`) y dejar que el browser pida directamente desde GCS. Reduce ancho de banda del Cloud Run y latencia.
- **Esfuerzo**: 1 hora.

### 3.4 ✅ HECHO - `MODULO_CIUDAD` completo

- **Resuelto el**: 2026-05-11.
- **Archivo**: `utils/ui_theme.py`.
- **Cambio**: agregadas las entradas `shopping_guide` y `admin_panel` al dict para que los 12 módulos tengan tema explícito.

### 3.5 Catálogo de tiendas en código Python

- **Archivo**: `modules/shopping_guide.py:127-859`.
- **Síntoma**: 700+ líneas de datos hardcoded. Cada ajuste de horario o tienda requiere redeploy.
- **Fix**: mover a `data/shopping.json` y cargar con cache. Editar es trivial sin tocar Python.
- **Esfuerzo**: 1.5 horas.

### 3.6 Persistencia de packing en session_state

- **Archivo**: `modules/packing_checker.py:238-247`.
- **Síntoma**: `items_marcados` vive solo en sesión. Si Giovanna marca items desde su celular y Camila desde el suyo, no se sincroniza.
- **Fix**: persistir en `Firestore.collection("packing").document("familia")` con escritura debounced.
- **Esfuerzo**: 1 hora.

### 3.7 ✅ HECHO - Tipo de cambio fallback

- **Resuelto el**: 2026-05-11.
- **Archivo**: `utils/price_helper.py`.
- **Cambios**:
  - TTL del cache subido de 1h a 6h (4 calls/día contra el límite gratuito de 1500/mes).
  - Default literal subido de 3.85 a 3.95 (cercano a la tasa observada según BCRP, https://www.bcrp.gob.pe/).
  - Logger warning estructurado cuando la API falla y se cae al fallback, para detectar caídas sostenidas en Cloud Logging.
  - El override por env var `FALLBACK_EUR_PEN_RATE` sigue disponible (ajustable sin redeploy).

## Prioridad 4 - Mantenimiento

### 4.1 Sin tests automatizados

- **Síntoma**: cero archivos `test_*.py`. El bug #1.1 estuvo merge-eado sin detección.
- **Fix mínimo**: agregar `pytest` y 5 smoke tests críticos:
  - Auth: `is_admin()` retorna True solo para email admin.
  - Price helper: `mostrar_precio` respeta el flag.
  - KB: `cosine_similarity` con vectores ortogonales = 0.
  - Conversor: `convertir(100, EUR, EUR, _) == 100`.
  - Travel concierge: `detectar_busqueda("[BUSCAR_WEB: foo]")` extrae query.
- **Esfuerzo**: 2 horas para los 5.

### 4.2 Sin linting ni formateo

- **Fix**: `ruff` (lint + format en un solo binario, rápido). Config mínima en `pyproject.toml`. Pre-commit hook opcional.
- **Esfuerzo**: 30 minutos.

### 4.3 ✅ HECHO - Eliminar `patch_travel_concierge.py`

- **Resuelto el**: 2026-05-11.
- **Acción**: archivo eliminado. La historia queda en git log para auditoría.

### 4.4 Falta `.env.example`

- **Síntoma**: nuevos colaboradores (o yo en 3 meses) no tienen idea qué variables necesita el setup local.
- **Fix**: agregar `.env.example` con todas las variables esperadas y comentarios.
- **Esfuerzo**: 10 minutos.

## Riesgos no técnicos

- **Crítico**: el viaje empieza en **65 días** (15 julio 2026, actualizado 2026-05-11). Cualquier mejora que toque rutas críticas (auth, ingesta, chat) debe terminar antes del 1 de julio para tener buffer.
- **Importante**: la app depende de 4 APIs externas (Gemini, Tavily, Open-Meteo, exchangerate-api). Si dos caen al mismo tiempo durante el viaje, los datos críticos quedan inaccesibles. Vale la pena precargar respuestas y guardarlas en Firestore como "offline cache" antes de salir de Lima.

## Framework de priorización aplicado

Se usó ICE (Impact × Confidence × Ease, escala 1-10) según Sean Ellis (https://growthhackers.com/articles/how-to-prioritize-your-tests-and-experiments-with-the-ice-score). Para un proyecto familiar y no monetizado, "Impact" se interpreta como impacto en la experiencia del viaje (datos accesibles, precisión, seguridad personal). Los items P1 tienen score > 200, P2 entre 100-200, P3 entre 50-100, P4 < 50.