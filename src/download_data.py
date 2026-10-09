import os
import glob
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

DATA_RAW_DIR = os.getenv("DATA_RAW_DIR", "/app/data/raw")
DATASET_NAME = os.getenv("KAGGLE_DATASET", "sobhanmoazemi/us-accidents")

def descargar_dataset():
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    
    # 1. Comprobar si ya existen archivos CSV para evitar descargas redundantes
    archivos_csv = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))
    if archivos_csv:
        print(f"✅ Se encontraron archivos CSV existentes en {DATA_RAW_DIR}: {archivos_csv}. Omitiendo descarga.", flush=True)
        return

    print(f"📥 Iniciando descarga automática desde Kaggle: {DATASET_NAME}...", flush=True)
    
    # 2. Autenticación con la API de Kaggle (usa KAGGLE_USERNAME y KAGGLE_KEY o ~/.kaggle/kaggle.json)
    try:
        api = KaggleApi()
        api.authenticate()
        print("🔐 Autenticación con Kaggle exitosa.", flush=True)
    except Exception as e:
        print(f"❌ Error al autenticar con la API de Kaggle: {e}", flush=True)
        print("Asegúrate de que las credenciales KAGGLE_USERNAME y KAGGLE_KEY estén configuradas en Jenkins.", flush=True)
        raise e

    # 3. Descarga y extracción automática
    print(f"📦 Descargando en {DATA_RAW_DIR}...", flush=True)
    api.dataset_download_files(DATASET_NAME, path=DATA_RAW_DIR, unzip=True)
    
    # 4. Verificación de archivos descargados
    archivos_descargados = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))
    if not archivos_descargados:
        # En caso de que se haya descargado un archivo .zip sin descomprimir automáticamente
        archivos_zip = glob.glob(os.path.join(DATA_RAW_DIR, "*.zip"))
        for zip_f in archivos_zip:
            print(f"Descomprimiendo {zip_f}...", flush=True)
            with zipfile.ZipFile(zip_f, 'r') as zip_ref:
                zip_ref.extractall(DATA_RAW_DIR)
            os.remove(zip_f)
            
        archivos_descargados = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))

    if archivos_descargados:
        print(f"✅ Descarga y extracción completada con éxito. Archivos disponibles: {archivos_descargados}", flush=True)
    else:
        raise FileNotFoundError(f"❌ No se encontraron archivos .csv en {DATA_RAW_DIR} tras la descarga.")

if __name__ == "__main__":
    descargar_dataset()

