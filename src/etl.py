import dask.dataframe as dd
import pandas as pd
from pymongo import MongoClient
import os
from dask.distributed import Client

MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")
DB_NAME = "geo_db"
COLLECTION_NAME = "accidents"

def procesar_y_cargar(df_partition):
    if df_partition.empty:
        return pd.Series([0], dtype=int)
        
    print(f"-> Procesando partición de {len(df_partition):,} accidentes...", flush=True)
    
    # 1. Filtramos coordenadas vacías
    df_clean = df_partition.dropna(subset=['Start_Lat', 'Start_Lng']).copy()
    
    if df_clean.empty:
        return pd.Series([0], dtype=int)
        
    try:
        # Conversión rápida y vectorizada a float
        lngs = df_clean['Start_Lng'].astype(float).values
        lats = df_clean['Start_Lat'].astype(float).values
        
        # 2. Selección y renombramiento de columnas
        cols = ['ID', 'Severity', 'City', 'State', 'Start_Time']
        for col in cols:
            if col not in df_clean.columns:
                df_clean[col] = None
                
        subset = df_clean[cols].rename(columns={
            'ID': 'id_accidente',
            'Severity': 'severidad',
            'City': 'ciudad',
            'State': 'estado',
            'Start_Time': 'fecha_inicio'
        })
        
        # Reemplazar NaN por None para compatibilidad BSON / MongoDB
        subset = subset.where(pd.notnull(subset), None)
        documentos = subset.to_dict(orient='records')
        
        # 3. Asignación rápida de GeoJSON Point
        for i, doc in enumerate(documentos):
            doc['location'] = {
                "type": "Point",
                "coordinates": [lngs[i], lats[i]]
            }
            
        # 4. Inserción masiva en MongoDB
        cliente = MongoClient(MONGO_URI)
        coleccion = cliente[DB_NAME][COLLECTION_NAME]
        
        if documentos:
            coleccion.insert_many(documentos, ordered=False)
            
        cliente.close()
        print(f"<- Bloque guardado: {len(documentos):,} documentos en MongoDB.", flush=True)
        return pd.Series([len(documentos)], dtype=int)
    except Exception as e:
        print(f"Error procesando partición: {e}", flush=True)
        return pd.Series([0], dtype=int)


if __name__ == "__main__":
    print("1. Conectando al clúster distribuido de Dask...", flush=True)
    client = Client("tcp://dask_scheduler:8786")
    
    print("Esperando a que los workers de Dask estén listos...", flush=True)
    client.wait_for_workers(n_workers=1, timeout=60)
    
    workers = len(client.scheduler_info()['workers'])
    print(f"¡Conectado exitosamente! Workers disponibles: {workers}", flush=True)
    print("Monitorea el procesamiento en vivo en: http://localhost:8787", flush=True)
    
    print("2. Iniciando proceso ETL optimizado con Dask...", flush=True)
    ruta_archivo = "/app/data/raw/*.csv"
    df = dd.read_csv(ruta_archivo, dtype=str, assume_missing=True, blocksize="64MB")
    
    print("3. Transformando datos a GeoJSON y cargando a MongoDB...", flush=True)
    resultados = df.map_partitions(procesar_y_cargar, meta=pd.Series(dtype=int)).compute()
    
    total = resultados.sum()
    print(f"\n4. ¡ETL Completado! Se insertaron {total:,} registros geoespaciales.", flush=True)
    
    print("5. Creando el índice '2dsphere'...", flush=True)
    cliente = MongoClient(MONGO_URI)
    cliente[DB_NAME][COLLECTION_NAME].create_index([("location", "2dsphere")])
    cliente.close()
    print("✅ ¡Base de datos lista con índice 2dsphere para consultas espaciales rápidas!", flush=True)
    
    client.close()