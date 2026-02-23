# Imagen base ligera — python:3.11-slim (~150MB vs ~900MB de la full)
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Primero copiamos solo requirements para aprovechar el cache de Docker
# Si el código cambia pero requirements no, Docker no reinstala todo
COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Ahora copiamos el resto del código
COPY . .

# Exponemos el puerto de Streamlit
EXPOSE 8080

# Variable de entorno para que Streamlit no abra el browser
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Comando de inicio
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]