FROM python:3.11-slim
WORKDIR /app
# Cambiamos fastapi por flask
RUN pip install flask pymongo
COPY src/ /app/src/
EXPOSE 8000
# Comando para iniciar Flask
CMD ["python", "src/api.py"]