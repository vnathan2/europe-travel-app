# Imagen base ligera — Python 3.11 slim (~150MB vs ~900MB full)
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements primero (optimización de capas Docker:
# si el código cambia pero requirements no, Docker reutiliza
# esta capa cacheada y no reinstala todo desde cero)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que usa Streamlit
EXPOSE 8080

# Variables de entorno para Streamlit
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Comando para arrancar la app
CMD ["streamlit", "run", "app.py"]