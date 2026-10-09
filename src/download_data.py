import os
import glob
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

DATA_RAW_DIR = os.getenv("DATA_RAW_DIR", "/app/data/raw")
DATASET_NAME = os.getenv("KAGGLE_DATASET", "sobhanmoosavi/us-accidents")
# Límite de muestra: 1,200,000 registros para cumplir con la regla (> 1M) y no saturar disco/RAM
SAMPLE_LIMIT = int(os.getenv("SAMPLE_LIMIT", "1200000"))

def descargar_dataset():
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    
    # 1. Comprobar si ya existe un CSV válido
    archivos_csv = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))
    if archivos_csv and os.path.getsize(archivos_csv[0]) > 5000000:
        tam_mb = os.path.getsize(archivos_csv[0]) / (1024 * 1024)
        print(f"✅ Se encontró archivo CSV existente: {archivos_csv[0]} ({tam_mb:.2f} MB). Omitiendo descarga.", flush=True)
        return

    print(f"📥 Iniciando descarga automática desde Kaggle: {DATASET_NAME}...", flush=True)
    
    # 2. Autenticación con token
    token = os.getenv("KAGGLE_API_TOKEN") or os.getenv("KAGGLE_TOKEN") or os.getenv("KAGGLE_KEY")
    if token:
        os.environ["KAGGLE_API_TOKEN"] = token
        os.environ["KAGGLE_KEY"] = token
        
    try:
        api = KaggleApi()
        api.authenticate()
        print("🔐 Autenticación con Kaggle exitosa.", flush=True)
    except Exception as e:
        print(f"❌ Error al autenticar con la API de Kaggle: {e}", flush=True)
        print("Asegúrate de que la credencial kaggle-token esté configurada en Jenkins.", flush=True)
        raise e

    # 3. Descarga como ZIP (sin descomprimir en el filesystem raíz de Docker)
    print(f"📦 Descargando archivo comprimido en {DATA_RAW_DIR}...", flush=True)
    api.dataset_download_files(DATASET_NAME, path=DATA_RAW_DIR, unzip=False)
    
    archivos_zip = glob.glob(os.path.join(DATA_RAW_DIR, "*.zip"))
    if not archivos_zip:
        raise FileNotFoundError(f"❌ No se encontró el archivo .zip descargado en {DATA_RAW_DIR}")
        
    zip_path = archivos_zip[0]
    print(f"📂 Archivo ZIP descargado: {zip_path}. Extrayendo de forma optimizada...", flush=True)
    
    # 4. Extracción en streaming directo al CSV (cumpliendo con la muestra autorizada de > 1M registros)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_names = [f for f in zf.namelist() if f.endswith('.csv')]
        if not csv_names:
            raise FileNotFoundError("❌ No se encontró archivo CSV dentro del ZIP.")
            
        csv_file_name = csv_names[0]
        output_csv = os.path.join(DATA_RAW_DIR, "us_accidents.csv")
        
        print(f"🚀 Extrayendo {csv_file_name} -> {output_csv} (Límite: {SAMPLE_LIMIT:,} registros)...", flush=True)
        
        with zf.open(csv_file_name) as src, open(output_csv, 'wb') as dst:
            if SAMPLE_LIMIT > 0:
                count = 0
                for line in src:
                    dst.write(line)
                    count += 1
                    if count > SAMPLE_LIMIT:
                        break
                print(f"✨ Se extrajeron exitosamente {count:,} registros (> 1,000,000 requerido).", flush=True)
            else:
                import shutil
                shutil.copyfileobj(src, dst)
                print("✨ Archivo completo extraído exitosamente.", flush=True)
                
    # 5. Eliminamos el ZIP para recuperar espacio en disco inmediatamente
    try:
        os.remove(zip_path)
        print("🗑️ Archivo ZIP temporal eliminado para liberar espacio en disco.", flush=True)
    except Exception as e:
        print(f"Advertencia al borrar zip: {e}", flush=True)
        
    tam_final = os.path.getsize(output_csv) / (1024 * 1024)
    print(f"✅ Dataset listo para Dask en: {output_csv} ({tam_final:.2f} MB)", flush=True)

if __name__ == "__main__":
    descargar_dataset()
