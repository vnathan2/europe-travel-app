# 1. Imagen base eficiente
FROM python:3.11-slim

# 2. Variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# 3. Instalación de dependencias del sistema (solo si son necesarias)
# Agregamos limpieza de caché de apt para reducir tamaño
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Aprovechar cache de capas para requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Crear un usuario de sistema para no correr como ROOT (Seguridad)
RUN useradd -m myuser
USER myuser

# 6. Copiar el código con los permisos del nuevo usuario
COPY --chown=myuser:myuser . .

EXPOSE 8080

# 7. Healthcheck (Opcional pero recomendado para monitoreo)
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py"]