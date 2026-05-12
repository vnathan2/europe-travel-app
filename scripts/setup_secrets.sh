#!/bin/bash
# scripts/setup_secrets.sh
# Crea los secrets SENSIBLES en GCP Secret Manager (max 6 para capa gratuita)
# Los valores no sensibles van como --set-env-vars en el deploy (ver abajo)
# Uso: bash scripts/setup_secrets.sh

PROJECT="europe-travel-app"
REGION="us-east1"
IMAGE="us-east1-docker.pkg.dev/$PROJECT/$PROJECT/app:latest"

# ── Valores no sensibles — edítalos aquí directamente ─────────────────────────
OAUTH_REDIRECT_URI="https://europe-travel-app-565528729494.us-east1.run.app"
ADMIN_EMAIL="vnathan2@gmail.com"
FAMILIAR_EMAIL_1="giovannague07@gmail.com"
FAMILIAR_EMAIL_2="camilavrg17@gmail.com"
FALLBACK_EUR_PEN_RATE="3.85"
GCS_BUCKET_NAME="europe-travel-app-bucket"

echo "📦 Creando secrets sensibles en GCP Secret Manager (4 de 6 permitidos gratis)..."
echo "⚠️  Rellena los valores reales antes de ejecutar este script"
echo ""

# ── IMPORTANTE: Rellena con tus NUEVAS claves (las anteriores fueron expuestas) ──
GEMINI_API_KEY="TU_NUEVA_GEMINI_API_KEY"
TAVILY_API_KEY="TU_NUEVA_TAVILY_API_KEY"
GOOGLE_CLIENT_ID="TU_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET="TU_NUEVO_GOOGLE_CLIENT_SECRET"
# ─────────────────────────────────────────────────────────────────────────────────

create_or_update_secret() {
    local name=$1
    local value=$2
    if gcloud secrets describe "$name" --project="$PROJECT" &>/dev/null; then
        echo -n "$value" | gcloud secrets versions add "$name" \
            --project="$PROJECT" \
            --data-file=-
        echo "  ↺  $name (nueva versión añadida)"
    else
        echo -n "$value" | gcloud secrets create "$name" \
            --project="$PROJECT" \
            --replication-policy="automatic" \
            --data-file=-
        echo "  ✅ $name (creado)"
    fi
}

create_or_update_secret "GEMINI_API_KEY"       "$GEMINI_API_KEY"
create_or_update_secret "TAVILY_API_KEY"       "$TAVILY_API_KEY"
create_or_update_secret "GOOGLE_CLIENT_ID"     "$GOOGLE_CLIENT_ID"
create_or_update_secret "GOOGLE_CLIENT_SECRET" "$GOOGLE_CLIENT_SECRET"

echo ""
echo "🧹 Limpiando versiones antiguas (dejar solo la última de cada secret)..."

cleanup_old_versions() {
    local name=$1
    local versions
    versions=$(gcloud secrets versions list "$name" \
        --project="$PROJECT" \
        --filter="state=ENABLED" \
        --format="value(name)" | sort -t/ -k8 -n | head -n -1)
    for v in $versions; do
        gcloud secrets versions destroy "$v" --secret="$name" --project="$PROJECT" --quiet
        echo "  🗑  Versión antigua destruida: $v"
    done
}

cleanup_old_versions "GEMINI_API_KEY"
cleanup_old_versions "TAVILY_API_KEY"
cleanup_old_versions "GOOGLE_CLIENT_ID"
cleanup_old_versions "GOOGLE_CLIENT_SECRET"

echo ""
echo "🐳 Eliminando imágenes Docker antiguas en Artifact Registry (dejar solo latest)..."

gcloud artifacts docker tags list \
    "us-east1-docker.pkg.dev/$PROJECT/$PROJECT/app" \
    --project="$PROJECT" \
    --format="value(tag)" 2>/dev/null | grep -v "^latest$" | while read -r tag; do
    gcloud artifacts docker images delete \
        "us-east1-docker.pkg.dev/$PROJECT/$PROJECT/app:$tag" \
        --delete-tags --quiet 2>/dev/null && \
        echo "  🗑  Imagen eliminada: $tag"
done

echo ""
echo "🚀 Deploy en Cloud Run con valores no sensibles como env vars..."
echo ""

gcloud run deploy europe-travel-app \
    --image="$IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT,GCS_BUCKET_NAME=$GCS_BUCKET_NAME,FALLBACK_EUR_PEN_RATE=$FALLBACK_EUR_PEN_RATE,OAUTH_REDIRECT_URI=$OAUTH_REDIRECT_URI,ADMIN_EMAIL=$ADMIN_EMAIL,FAMILIAR_EMAIL_1=$FAMILIAR_EMAIL_1,FAMILIAR_EMAIL_2=$FAMILIAR_EMAIL_2" \
    --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,TAVILY_API_KEY=TAVILY_API_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest"

echo ""
echo "🎉 Listo. Secrets activos: 4/6 (dentro de la capa gratuita)"
