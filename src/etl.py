import dask.dataframe as dd
import pandas as pd
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

def procesar_y_cargar(df_partition):
    # Si la partición está vacía, saltamos
    if df_partition.empty:
        return pd.Series([0], dtype=int)
        
    # flush=True obliga a Jenkins a imprimir esto inmediatamente en la consola
    print(f"-> Procesando un bloque de {len(df_partition)} accidentes...", flush=True)
    
    cliente = MongoClient(MONGO_URI)
    coleccion = cliente[DB_NAME][COLLECTION_NAME]
    
    # 1. Limpieza vectorizada (mucho más rápida que un if por cada fila)
    df_clean = df_partition.dropna(subset=['Start_Lat', 'Start_Lng'])
    
    if df_clean.empty:
        cliente.close()
        return pd.Series([0], dtype=int)
        
    # 2. Función rápida para armar el GeoJSON
    def armar_doc(fila):
        return {
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
    
    # 3. apply procesa los datos de forma optimizada en C por debajo
    documentos = df_clean.apply(armar_doc, axis=1).tolist()
    
    # 4. Inserción masiva en Mongo
    if documentos:
        coleccion.insert_many(documentos)
        
    cliente.close()
    print(f"<- Bloque guardado exitosamente: {len(documentos)} documentos.", flush=True)
    
    # Retornamos una Serie de Pandas para evitar el FutureWarning de Dask
    return pd.Series([len(documentos)], dtype=int)

if __name__ == "__main__":
    print("1. Iniciando proceso ETL optimizado con Dask...", flush=True)
    
    ruta_archivo = "data/raw/*.csv"
    df = dd.read_csv(ruta_archivo, dtype=str, assume_missing=True)
    
    print("2. Transformando datos a GeoJSON y cargando a MongoDB...", flush=True)
    # Ejecutamos el procesamiento distribuido. Pasamos una Serie en meta para cumplir el estándar.
    resultados = df.map_partitions(procesar_y_cargar, meta=pd.Series(dtype=int)).compute()
    
    total = resultados.sum()
    print(f"\n3. ¡ETL Completado! Se insertaron {total} registros geoespaciales.", flush=True)
    
    print("4. Creando el índice '2dsphere'...", flush=True)
    cliente = MongoClient(MONGO_URI)
    cliente[DB_NAME][COLLECTION_NAME].create_index([("location", "2dsphere")])
    cliente.close()
    print("¡Base de datos lista para soportar consultas espaciales rápidas!", flush=True)