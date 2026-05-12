#!/bin/bash
# scripts/setup_auth.sh
# Crea la estructura de carpetas y archivos nuevos para el sistema de auth
# Uso: bash scripts/setup_auth.sh (desde la raíz del proyecto)

echo "📁 Creando estructura de auth..."

# Crear carpeta auth
mkdir -p auth

# Crear __init__.py vacío
touch auth/__init__.py
echo "✅ auth/__init__.py"

# Verificar que google_oauth.py fue copiado
if [ -f "auth/google_oauth.py" ]; then
    echo "✅ auth/google_oauth.py — ya existe"
else
    echo "⚠️  auth/google_oauth.py — FALTA: copia el archivo descargado aquí"
fi

# Verificar night_life.py
if [ -f "modules/night_life.py" ]; then
    echo "✅ modules/night_life.py — ya existe"
else
    echo "⚠️  modules/night_life.py — FALTA: copia el archivo descargado aquí"
fi

# Crear utils/price_helper.py
cat > utils/price_helper.py << 'EOF'
# utils/price_helper.py
import streamlit as st

def mostrar_precio(precio_str: str, fallback: str = "🔒") -> str:
    """Retorna precio si admin, fallback si familiar."""
    if st.session_state.get("_show_prices", True):
        return precio_str
    return fallback
EOF
echo "✅ utils/price_helper.py"

echo ""
echo "🎉 Estructura creada. Recuerda:"
echo "   1. Copiar auth/google_oauth.py (descargado)"
echo "   2. Copiar modules/night_life.py (descargado)"
echo "   3. Reemplazar app.py (descargado)"
echo "   4. Editar .env con tus credenciales reales"
