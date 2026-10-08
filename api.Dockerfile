FROM python:3.11-slim

WORKDIR /app

# Instalamos las librerías exclusivas para la API
RUN pip install fastapi uvicorn pymongo

# Copiamos la carpeta src hacia el contenedor
COPY src/ /app/src/

# Exponemos el puerto de la API
EXPOSE 8000

# Arrancamos el servidor de FastAPI
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]