FROM python:3.10-slim

# Instalamos Java (requisito obligatorio para que PySpark funcione)
RUN apt-get update && \
    apt-get install -y default-jre && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos los requerimientos e instalamos todo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente y las pruebas
COPY src/ /app/src/
COPY tests/ /app/tests/

# Le decimos al contenedor que arranque la API
CMD ["python", "src/api.py"]