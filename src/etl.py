import dask.dataframe as dd
import pandas as pd
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

def procesar_y_cargar(df_partition):
    if df_partition.empty:
        return pd.Series([0], dtype=int)
        
    print(f"-> Procesando un bloque de {len(df_partition)} accidentes...", flush=True)
    
    cliente = MongoClient(MONGO_URI)
    coleccion = cliente[DB_NAME][COLLECTION_NAME]
    
    # 1. Filtramos las coordenadas vacías (obligatorias para el mapa)
    df_clean = df_partition.dropna(subset=['Start_Lat', 'Start_Lng'])
    
    if df_clean.empty:
        cliente.close()
        return pd.Series([0], dtype=int)
        
    # Función auxiliar para convertir el <NA> de Pandas a None (null de MongoDB)
    def get_val(val):
        return None if pd.isna(val) else val
        
    # 2. Función para armar el GeoJSON limpiando los nulos en otros campos
    def armar_doc(fila):
        return {
            "id_accidente": get_val(fila.get('ID')),
            "severidad": get_val(fila.get('Severity')),
            "ciudad": get_val(fila.get('City')),
            "estado": get_val(fila.get('State')),
            "fecha_inicio": get_val(fila.get('Start_Time')),
            "location": {
                "type": "Point",
                "coordinates": [float(fila['Start_Lng']), float(fila['Start_Lat'])]
            }
        }
    
    # 3. apply procesa los datos
    documentos = df_clean.apply(armar_doc, axis=1).tolist()
    
    # 4. Inserción masiva en Mongo
    if documentos:
        coleccion.insert_many(documentos)
        
    cliente.close()
    print(f"<- Bloque guardado exitosamente: {len(documentos)} documentos.", flush=True)
    return pd.Series([len(documentos)], dtype=int)

if __name__ == "__main__":
    print("1. Iniciando proceso ETL optimizado con Dask...", flush=True)
    
    ruta_archivo = "data/raw/*.csv"
    df = dd.read_csv(ruta_archivo, dtype=str, assume_missing=True)
    
    print("2. Transformando datos a GeoJSON y cargando a MongoDB...", flush=True)
    resultados = df.map_partitions(procesar_y_cargar, meta=pd.Series(dtype=int)).compute()
    
    total = resultados.sum()
    print(f"\n3. ¡ETL Completado! Se insertaron {total} registros geoespaciales.", flush=True)
    
    print("4. Creando el índice '2dsphere'...", flush=True)
    cliente = MongoClient(MONGO_URI)
    cliente[DB_NAME][COLLECTION_NAME].create_index([("location", "2dsphere")])
    cliente.close()
    print("¡Base de datos lista para soportar consultas espaciales rápidas!", flush=True)