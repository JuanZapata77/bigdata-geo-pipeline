from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
import os

app = Flask(__name__, static_folder='static')

MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

cliente = MongoClient(MONGO_URI)
coleccion = cliente[DB_NAME][COLLECTION_NAME]

@app.route('/')
def home():
    # Renderizamos nuestro mapa de Leaflet
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/accidentes/cercanos', methods=['GET'])
def obtener_accidentes_cercanos():
    try:
        lat = float(request.args.get('lat', 40.7812))
        lng = float(request.args.get('lng', -73.9665))
        radio = int(request.args.get('radio_metros', 5000))
        limite = int(request.args.get('limite', 200))

        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radio
                }
            }
        }
        
        resultados = list(coleccion.find(query, {"_id": 0}).limit(limite))
        
        return jsonify({
            "total_encontrados": len(resultados),
            "datos": resultados
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/accidentes/poligono', methods=['POST'])
def obtener_accidentes_poligono():
    """Busca accidentes dentro de un polígono dado usando $geoWithin"""
    try:
        # El profe enviará las coordenadas del polígono en formato JSON
        datos = request.json
        coordenadas = datos.get("coordenadas") # Debe ser una lista de listas: [[[lng, lat], ...]]

        query = {
            "location": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": coordenadas
                    }
                }
            }
        }
        resultados = list(coleccion.find(query, {"_id": 0}).limit(200))
        return jsonify({"total_encontrados": len(resultados), "datos": resultados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/accidentes/cercanos_agrupados', methods=['GET'])
def accidentes_cercanos_agrupados():
    """Usa una agregación $geoNear para contar accidentes por severidad en un radio"""
    try:
        lat = float(request.args.get('lat', 40.7812))
        lng = float(request.args.get('lng', -73.9665))
        radio = int(request.args.get('radio_metros', 5000))

        # Pipeline de agregación exigido por la rúbrica
        pipeline = [
            {
                "$geoNear": {
                    "near": { "type": "Point", "coordinates": [lng, lat] },
                    "distanceField": "distancia_metros",
                    "maxDistance": radio,
                    "spherical": True
                }
            },
            {
                "$group": {
                    "_id": "$severidad",
                    "total_accidentes": { "$sum": 1 }
                }
            }
        ]
        resultados = list(coleccion.aggregate(pipeline))
        return jsonify({"agrupados_por_severidad": resultados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/estadisticas/spark', methods=['GET'])
def obtener_estadisticas_spark():
    """Devuelve los datos analíticos procesados por el clúster de Spark"""
    try:
        # Nos conectamos a la nueva colección donde Spark guardó los datos
        coleccion_resumen = cliente[DB_NAME]["resumen_estados"]
        resultados = list(coleccion_resumen.find({}, {"_id": 0}))
        return jsonify({"estadisticas_spark": resultados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)  