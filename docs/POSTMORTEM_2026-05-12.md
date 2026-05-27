# Post-mortem incidente 2026-05-12

## Resumen

Chat de Lady (módulo Travel Concierge) caído durante varias horas en producción por **`API_KEY_INVALID`** de Gemini. El fix de rotar la key reveló dos sub-incidentes encadenados: (1) la key se subió a Secret Manager con `\r\n` al final por usar PowerShell con pipe a `gcloud secrets versions add --data-file=-`, generando un header HTTP inválido y un timeout de 60s en la UI; (2) la API key de Gemini quedó expuesta brevemente en el chat con el asistente por un mal uso de `Read-Host`.

Mitigación: rotación de la API key (4 versiones intentadas hasta lograr una limpia), redeploy con pods frescos, deshabilitar todas las versiones malas del secret. Sin pérdida de datos. Tiempo total de Lady caída en prod: **~24h** (la key vieja `...DWDs` ya estaba siendo rechazada por Gemini desde antes, solo nadie lo había detectado).

## Línea de tiempo (UTC, 2026-05-13 en GMT)

- **00:58** Build de imagen `:latest` con código nuevo (packing en Firestore + FAQ offline + .env.example).
- **01:01** Deploy `00068-daf` con tag `offline-faqs`, sin tráfico. Healthcheck OK.
- **01:04** Usuario valida en la URL del tag → recibe `400 API_KEY_INVALID` desde Gemini.
- **01:05** Análisis: error preexistente en prod (`00065-hat`), no del deploy nuevo. Gemini está rechazando la key v5 del secret (creada el 2-abr).
- **01:08** Usuario sube primera key nueva con pipe → versión 6 (con CRLF colado).
- **01:13-01:15** Dos intentos más → versiones 7 y 8 (también con CRLF).
- **01:15** Tráfico movido a `00064-kjr` para forzar pods frescos.
- **01:16** Lady se cuelga 60s con `Illegal metadata` en logs → diagnosticado newline en el secret.
- **01:30** Usuario expone accidentalmente la key nueva pegándola como argumento de `Read-Host` (visible en pantalla y en chat con el asistente).
- **01:32** Key expuesta revocada en AI Studio por el usuario.
- **01:39** Versión 9 subida con archivo (todavía vacío, fallo).
- **01:40** Versión 10 subida correctamente con archivo de 39 bytes exactos.
- **01:42** Redeploy con tag `offline-faqs` → revisión `00073-tiz` con pods que leen v10.
- **01:46** Validación directa de la key contra Gemini con `curl` → `200 ok`.
- **01:48** Tráfico promovido al 100% a `00073-tiz`. Healthcheck canónico OK.
- **01:50** Versiones 5-9 del secret deshabilitadas.
- **01:52** Usuario confirma que Lady responde en URL canónica. Incidente cerrado.

## Causas raíz

### 1. Key original `...DWDs` (creada 2026-04-02) revocada por Google

No hay log explícito de cuándo Google la revocó. Hipótesis razonables:

- La key estuvo expuesta en algún punto del git history previo a este proyecto (no verificado).
- Google detectó uso anómalo o filtración indirecta.
- Una políticas de la cuenta "My Billing Account · Nivel 1 · Pospago" la marcó como sospechosa.

El error `API_KEY_INVALID` venía de `genai.embed_content` en `utils/knowledge_base.py:64`, llamado cada vez que Lady recibía una pregunta y necesitaba generar el embedding del query para el RAG.

### 2. Pipeline de PowerShell agrega `\r\n` al `--data-file=-`

```powershell
$plain | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

PowerShell pipea string al stdin de `gcloud` agregando CRLF al final (line ending Windows). El secret termina con `"AIza...\r\n"` (41 bytes para una key de 39 caracteres). Cuando el SDK de Gemini construye el header `x-goog-api-key`, el CRLF lo invalida → `INTERNAL:Illegal header value`. El cliente retry hasta el timeout de 60s en lugar de fallar rápido, por eso la UI quedaba "olfateando" sin recuperarse.

**Bytes esperados del secret**: exactamente **39** (longitud de una API key de Gemini). Cualquier valor distinto = corrupción.

### 3. Cache de la API key en los pods de Cloud Run

Cuando el secret monta con `key: latest`, los pods leen el valor solo al arrancar. Cambiar el secret no recicla pods en ejecución → la revisión vieja sigue usando la key vieja en memoria. Esto se ve agravado por:

- `gcloud run services update --update-secrets` crea revisiones nuevas pero no necesariamente mueve tráfico.
- El tag de prueba apuntaba a una revisión que arrancó ANTES del fix del secret, por lo que también tenía la key vieja cacheada hasta que hicimos un redeploy fresco.

### 4. Exposición accidental de la key en el chat

El usuario invocó `Read-Host` así:

```powershell
$key = Read-Host "AIzaSyBsDJUgydVUbsEq1ZolF-8JP0RdGZ5WVsc" -AsSecureString
```

`Read-Host` toma el primer argumento como el **texto del prompt**, no como la respuesta. La key terminó como label visible en pantalla (y en el log de la sesión compartida con el asistente). Adicionalmente, como el usuario solo presionó Enter sin pegar nada en el prompt, `$key` quedó vacío → archivo de 0 bytes → upload falló silenciosamente.

## Fix aplicado

### Subida correcta del secret a Secret Manager

```powershell
$key = Read-Host "Pega aqui la API key"  # SIN -AsSecureString
$key.Length                                # validar 39
[System.IO.File]::WriteAllText("$env:TEMP\gkey.txt", $key)
(Get-Item "$env:TEMP\gkey.txt").Length     # validar 39 (sin CRLF)
gcloud secrets versions add GEMINI_API_KEY --data-file="$env:TEMP\gkey.txt"
Remove-Item "$env:TEMP\gkey.txt" -Force
Clear-Variable key
Clear-History                               # limpia historial de PS
```

Claves:
- **Sin pipe a `--data-file=-`** porque PowerShell agrega CRLF.
- **`[System.IO.File]::WriteAllText`** no agrega newline final (a diferencia de `Out-File` o `>`).
- **Doble validación de length** (variable y archivo).
- **`Clear-Variable` + `Clear-History`** para no dejar la key en `Get-History`.

### Reciclar pods de Cloud Run para tomar el secret nuevo

```powershell
# Opción A: redeploy completo de la imagen (recomendado, asegura pods frescos)
gcloud run deploy europe-travel-app `
  --image=us-east1-docker.pkg.dev/europe-travel-app/europe-travel-app/app:latest `
  --region=us-east1 --platform=managed --allow-unauthenticated --quiet `
  --no-traffic --tag=<TAG>

# Opción B: trick más rápido, sin redeploy
# (alterna el binding del secret para forzar nueva revisión)
gcloud run services update europe-travel-app --region=us-east1 `
  --update-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### Validación de key contra Gemini sin pasar por Cloud Run

```powershell
$key = (gcloud secrets versions access latest --secret=GEMINI_API_KEY).Trim()
$body = @{ contents = @(@{ parts = @(@{text="ok"}) }) } | ConvertTo-Json -Depth 5
Invoke-WebRequest `
  -Uri "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" `
  -Method POST -UseBasicParsing `
  -Headers @{ "Content-Type"="application/json"; "x-goog-api-key"=$key } `
  -Body $body
```

Si retorna 200, la key es válida y el problema está en el secret o en el caché de Cloud Run, no en la key.

## Aprendizajes

- **No subir secrets binarios con pipe en PowerShell**. Siempre usar archivo temporal escrito con `WriteAllText`. Validar el length del archivo antes de subir.
- **`Read-Host` toma argumentos como prompt label, no como entrada**. El prompt debe ser una pregunta clara, nunca pegar la entrada como argumento.
- **OAuth redirige a la URL canónica**, no a la URL del tag. Imposible validar end-to-end un tag con login real sin tocar `OAUTH_REDIRECT_URI`. La validación pre-promoción cubre healthcheck + smoke tests + logs, pero el flow OAuth solo se valida post-promoción.
- **Pods de Cloud Run cachean secrets en memoria al arrancar**. Cambiar un secret no propaga automáticamente. Necesita redeploy o creación explícita de revisión nueva.
- **El fallback offline de Lady salvó la cara durante la rotación**. Las FAQ pre-canned en `utils/offline_faqs.py` no se activaron durante el incidente, pero no porque el `except` se quedara corto: `except Exception` ya captura `RetryError` y timeouts. El problema era que el SDK de Gemini reintenta internamente hasta ~60s antes de levantar la excepción, así que la UI quedaba colgada en vez de caer al fallback. Fix aplicado el 2026-05-27 vía `request_options={"timeout": ...}`. Ojo: en google-generativeai 0.5.2 `ChatSession.send_message` NO acepta `request_options` (y al llamar internamente a `generate_content` no lo reenvía), así que se reemplazó el patrón `start_chat`/`send_message` por dos llamadas stateless a `model.generate_content(contenidos, request_options=...)`, manejando el historial manualmente con el formato `{"role", "parts": [...]}`. **Lección de afinamiento**: el primer valor (15s) era demasiado agresivo y disparaba `504 Deadline Exceeded` en el flujo de búsqueda web (RAG + 2 llamadas a Gemini), detectado en validación post-promoción de la revisión 00075-gub. Subido a 30s y hecho configurable por env `GEMINI_TIMEOUT_SEC` para ajustar sin redeploy (commit 81f0ab3, revisión 00077-xow).
- **Una key revocada con Gemini sigue habilitada en Secret Manager**. AI Studio y Secret Manager no están sincronizados. Habilitar una versión del secret no garantiza que la API la acepte.

## Pendientes de seguimiento

- Verificar billing del proyecto: el dashboard de AI Studio muestra "Nivel 1 · Pospago", lo cual puede violar la restricción dura de free tier del CLAUDE.md. Revisar https://console.cloud.google.com/billing → Reports filtrado por `europe-travel-app` últimos 30 días. Si hay cargos, configurar budget alerts (gratuitos).
- ✅ Resuelto 2026-05-27: el fallback no se activaba por falta de timeout en las llamadas a Gemini (el SDK colgaba ~60s antes de levantar la excepción), no por el `except`. Se agregó timeout en `obtener_respuesta` migrando de `start_chat`/`send_message` a `generate_content` con `request_options` (send_message no soporta timeout en 0.5.2). El valor inicial de 15s resultó muy agresivo (504 Deadline Exceeded en el camino de búsqueda web); se subió a 30s configurable por env `GEMINI_TIMEOUT_SEC`. Validado en prod, revisión 00077-xow.
- Billing verificado 2026-05-27 por CLI: el proyecto tiene `billingEnabled: true`, vinculado a la cuenta `01CDEF-95CD77-E71C9B` ("My Billing Account", pospago). Tener billing activo es necesario para Cloud Run y NO implica salir del free tier por sí solo, pero confirma que hay una cuenta pospago detrás que puede generar cargos si se exceden las cuotas Always Free. Pendiente: configurar budget alert en $0–$1 (gratis) en la consola, ya que `vnathan2@gmail.com` no tiene permiso de billing por CLI. Revisar el reporte de costos de los últimos 30 días en https://console.cloud.google.com/billing.
- ✅ TAVILY_API_KEY rotada a versión 5 el 2026-05-27 (la anterior era un placeholder inválido de 23 chars que rompía la búsqueda web; la nueva es una key real `tvly-` de 58 chars, validada directo contra el API de Tavily antes de promover). Falta GOOGLE_CLIENT_SECRET: considerar rotación preventiva si se sospecha filtración.
