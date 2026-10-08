from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os

app = FastAPI(
    title="Geo-Pipeline API",
    description="API de consultas geoespaciales para el dataset de US Accidents",
    version="1.0.0"
)

# Conexión a Mongo (utilizando el nombre del contenedor de la base de datos)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

cliente = MongoClient(MONGO_URI)
coleccion = cliente[DB_NAME][COLLECTION_NAME]

@app.get("/")
def home():
    return {"mensaje": "Geo-API funcionando. Visita /docs para probar los endpoints."}

@app.get("/accidentes/cercanos")
def obtener_accidentes_cercanos(lat: float, lng: float, radio_metros: int = 5000, limite: int = 50):
    """
    Busca los accidentes más cercanos a una coordenada dada.
    Ejemplo de Central Park, NY: lat=40.7812, lng=-73.9665
    """
    try:
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat] # Mongo siempre requiere [Longitud, Latitud]
                    },
                    "$maxDistance": radio_metros
                }
            }
        }
        
        # Ocultamos el campo _id porque no es serializable en JSON por defecto
        cursor = coleccion.find(query, {"_id": 0}).limit(limite)
        resultados = list(cursor)
        
        return {
            "total_encontrados": len(resultados),
            "parametros_busqueda": {"lat": lat, "lng": lng, "radio_metros": radio_metros},
            "datos": resultados
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))