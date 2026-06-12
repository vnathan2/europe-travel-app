## Postmortem 2026-06-08 — Deploys reusaban revisión vieja
- Síntoma: `gcloud run deploy` reportaba "revision 00099 serving 100%" en cada
  intento; la app servía código de mayo pese a builds nuevos exitosos.
- Causa raíz: la revisión viva estaba clavada a un digest viejo y los deploys
  por tag (`:latest`, `:$tag`) no forzaban revisión nueva. Cloud Run dedupea
  por digest y no rotaba tráfico a la imagen nueva.
- Fix: deploy por digest explícito (`app@sha256:...`) + `--revision-suffix`
  único, que obliga a crear una revisión con nombre nuevo y mover el 100%.
- Regla: nunca deployar `:latest`. Taggear cada build con el git short SHA y,
  si un deploy reusa revisión, forzar con `--revision-suffix=<algo-único>`.
  Verificar siempre `status.traffic` y revisar la URL canónica en incógnito.