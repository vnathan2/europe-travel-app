# Post-mortem deploy 2026-05-11

## Resumen

Deploy a Cloud Run (revisión `00054-569`) introdujo un bug que rompió la navegación entre módulos. La pantalla quedaba con el color del background y ningún módulo cargaba al hacer click en el menú lateral. Local con APP_MODE=DEVELOPMENT funcionaba correctamente.

Mitigación: rollback de tráfico a la revisión `00053-xr4`. Tiempo de impacto en producción: ~30 minutos. Sin pérdida de datos.

**✅ Causa raíz identificada (2026-05-11)**: `st.stop()` en la rama `elif code and oauth_code_processed` de `auth_gate()`. Ver sección "Causa raíz" más abajo.

## Línea de tiempo (UTC)

- **05:47** Revisión `00054-569` deployada (build + deploy desde sesión de mejoras).
- **05:55** Usuario reporta: al seleccionar opción del menú, pantalla queda en color de fondo.
- **05:58** Confirmado en producción. Local funciona.
- **06:02** Subida de memoria 512 MiB -> 1 GiB. No resuelve.
- **06:04** Rollback de tráfico a `00053-xr4`. Producción operativa.

## Lo que sabemos

- El bug afecta a todos los módulos por igual (no es uno específico).
- Logs HTTP de Cloud Run muestran responses 200/304/101 normales. Sin 500.
- No hay errores en jsonPayload de la app durante el bug.
- En local con APP_MODE=DEVELOPMENT el comportamiento es correcto.
- Subir memoria a 1 GiB no cambia el síntoma -> no es OOM.
- Auditado: el patrón `*.json` en `.gcloudignore` no excluye archivos críticos (todos los JSONs del repo viven en `.venv/` y `.claude/`, ya excluidos por separado).

## Diff entre 00053 y 00054 (lo que se deployó)

Archivos modificados:
- `modules/voice_translator.py` - typo `dokter`
- `modules/admin_panel.py` - fix nested function + invalidación cache RAG
- `utils/knowledge_base.py` - cache 10min + logger
- `utils/gcp_client.py` - logger en `get_secret`
- `utils/price_helper.py` - fallback rate 3.95 + logger + TTL 6h
- `utils/ui_theme.py` - 2 entradas extra en `MODULO_CIUDAD`
- `utils/logger.py` - **NUEVO** (logger central JSON/legible)
- `modules/emergency_card.py` - persistencia Firestore en tab Familia
- `auth/google_oauth.py` - rate limit + remove fallback URL hardcoded
- `modules/night_life.py` - disclaimer legal reforzado
- `scripts/ingest_knowledge.py` - env vars opcionales
- `requirements.txt` - removidas `scikit-learn`, `matplotlib`, `wikipedia-api`, `openpyxl`, `fpdf2`
- `patch_travel_concierge.py` - **ELIMINADO**
- `.gcloudignore` - **NUEVO**

## Causa raíz

**Archivo**: `auth/google_oauth.py`, función `auth_gate()`.

**El código culpable** (introducido en el diff de 00054):

```python
elif code and st.session_state.get("oauth_code_processed"):
    st.stop()   # ← bug
```

**Mecanismo exacto**:

1. Usuario se loguea → `auth_gate` procesa el `?code=`, llama `st.query_params.clear()` y luego `st.rerun()`.
2. Streamlit 1.32 en Cloud Run tarda un ciclo de rerun extra en reflejar `query_params.clear()` en el valor que lee `params.get("code")`. Durante ese ciclo: `code != None` pero `oauth_code_processed = True`.
3. El `elif` se activa → **`st.stop()`**.
4. En ese punto, `apply_theme()` ya había inyectado el CSS (fondo de color visible), pero el módulo nunca cargaba porque la ejecución se detenía antes del enrutamiento.
5. `st.stop()` lanza una `StopException` interna de Streamlit que no aparece en logs de Python → sin errores visibles.

**Por qué no pasa en local**: en `APP_MODE=DEVELOPMENT`, `auth_gate()` inyecta la sesión directamente y retorna antes del bloque OAuth. Nunca hay `?code=` → nunca entra al `elif` → nunca hace `st.stop()`.

**Por qué afecta a todos los módulos por igual**: el `st.stop()` ocurre en `app.py` antes del enrutamiento, independientemente del módulo seleccionado.

**Fix**: reemplazar `st.stop()` por `st.query_params.clear()` y dejar que el flujo continúe hacia `is_authenticated()`. El rate limit (deshabilitado en debug) también se restaura en la rama correcta (`if code and not processed`). Ver `auth/google_oauth_fixed.py`.

## Hipótesis descartadas

1. ~~`utils/logger.py` interactúa mal con Streamlit en Cloud Run~~ — `logger.py` está en no-op y el bug persiste/persistía igualmente. No es el logger.
2. ~~Módulo importado eagerly falla silenciosamente~~ — el `st.stop()` ocurre antes del `importlib.import_module`, no dentro.
3. ~~`requirements.txt` removió dependencia transitiva~~ — los síntomas son previos al enrutamiento, no en la ejecución de módulos.

## Plan de debug — completado ✅

1. ✅ **No re-deployar a prod** hasta identificar la causa. Mantenido.
2. ✅ **Causa raíz identificada** por análisis estático del código (no fue necesario el bisect Docker).
3. ✅ **Fix implementado** en `auth/google_oauth_fixed.py` — reemplazar `st.stop()` por `st.query_params.clear()` y restaurar el rate limit en la rama correcta.

## Próximos pasos para el re-deploy

```powershell
# 1. Aplicar el fix: reemplazar auth/google_oauth.py con la versión corregida
# 2. Restaurar logger.py completo (el no-op fue una medida de debug, ya no hace falta)
# 3. Build y deploy de prueba SIN TRÁFICO:
gcloud builds submit --tag us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest --quiet .
gcloud run deploy europe-travel-app `
  --image=us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest `
  --region=us-east1 --platform=managed --allow-unauthenticated --quiet `
  --no-traffic --tag=test-fix-oauth

# 4. Testear con la URL del tag: login completo + navegación entre 3+ módulos
# 5. Si pasa: promover a prod
gcloud run services update-traffic europe-travel-app --to-tags=test-fix-oauth=100 --region=us-east1
```

## Decisiones

- ~~Re-aplicar los cambios uno por uno cuando se identifique el culpable.~~ → Causa identificada; se re-aplican todos los cambios del diff junto con el fix.
- Considerar mantener `requirements-dev.txt` separado pero también versionar un `requirements.lock` (pip-compile) para evitar problemas de deps transitivas.

## Aprendizajes

- Los deploys grandes (10+ archivos cambiados) son difíciles de debuggear. Próxima sesión, deploys más chicos y atómicos.
- La validación local con `APP_MODE=DEVELOPMENT` no cubre el flujo OAuth ni la interacción con Cloud Run. **Un `st.stop()` en una rama OAuth nunca se puede detectar en local porque el modo dev no toca ese código.** Para cambios en `auth/`, validar siempre con un deploy `--no-traffic` real.
- `st.stop()` en Streamlit no lanza excepción de Python visible en logs — es una `StopException` interna. Cualquier `st.stop()` en rutas que pueden activarse post-login es un riesgo silencioso.