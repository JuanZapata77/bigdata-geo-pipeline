import dask.dataframe as dd
import pandas as pd
from pymongo import MongoClient
import os

# Jenkins levantará un contenedor de Python en la misma red de nuestro docker-compose.
# Gracias a esto, Mongo es accesible simplemente usando el nombre del contenedor "geo_mongo".
MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

def procesar_y_cargar(df_partition):
    # Nos conectamos a Mongo dentro de cada "worker" (pedazo de memoria) de Dask
    cliente = MongoClient(MONGO_URI)
    coleccion = cliente[DB_NAME][COLLECTION_NAME]
    
    documentos = []
    # Iteramos sobre esta porción de datos
    for _, fila in df_partition.iterrows():
        # Limpieza: Si no hay coordenadas, la búsqueda espacial fallaría, así que los descartamos
        if pd.isna(fila.get('Start_Lat')) or pd.isna(fila.get('Start_Lng')):
            continue
            
        try:
            # Transformación: Construimos el estándar GeoJSON que exige MongoDB
            # Nota: El estándar oficial exige que sea [Longitud, Latitud] (X, Y)
            doc = {
                "id_accidente": fila.get('ID'),
                "severidad": fila.get('Severity'),
                "ciudad": fila.get('City'),
                "estado": fila.get('State'),
                "fecha_inicio": fila.get('Start_Time'),
                "location": {
                    "type": "Point",
                    "coordinates": [float(fila['Start_Lng']), float(fila['Start_Lat'])]
                }
            }
            documentos.append(doc)
        except Exception:
            continue # Si hay datos sucios o erróneos en las coordenadas, los saltamos
            
    # Carga (Load): Insertamos miles de documentos de golpe para mayor velocidad
    if documentos:
        coleccion.insert_many(documentos)
        
    cliente.close()
    return len(documentos)

if __name__ == "__main__":
    print("1. Iniciando proceso ETL con Dask...")
    
    # Leemos cualquier archivo CSV que haya descomprimido Kaggle en la carpeta
    ruta_archivo = "data/raw/*.csv"
    
    # Lectura diferida (lazy): Usamos dtype=str para evitar problemas de tipos de datos mezclados
    df = dd.read_csv(ruta_archivo, dtype=str, assume_missing=True)
    
    print("2. Transformando datos a GeoJSON y cargando a MongoDB...")
    # map_partitions distribuye nuestra función por todos los bloques de datos
    resultados = df.map_partitions(procesar_y_cargar, meta=('int')).compute()
    
    total = sum(resultados)
    print(f"3. ¡ETL Completado! Se insertaron {total} registros de accidentes.")
    
    print("4. Creando el índice '2dsphere'...")
    # Esto es OBLIGATORIO para que Mongo entienda que 'location' es un mapa real
    cliente = MongoClient(MONGO_URI)
    cliente[DB_NAME][COLLECTION_NAME].create_index([("location", "2dsphere")])
    cliente.close()
    print("¡Base de datos lista para soportar consultas geoespaciales!")