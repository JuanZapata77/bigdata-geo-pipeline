import os
import glob
import json
import shutil
import zipfile

DATA_RAW_DIR = os.getenv("DATA_RAW_DIR", "/app/data/raw")
TEMP_DOWNLOAD_DIR = os.getenv("TEMP_DOWNLOAD_DIR", "/tmp/kaggle_download")
DATASET_NAME = os.getenv("KAGGLE_DATASET", "sobhanmoosavi/us-accidents")
SAMPLE_LIMIT = int(os.getenv("SAMPLE_LIMIT", "1200000"))

def descargar_dataset():
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    
    # 1. Comprobar si ya existe un CSV válido en /app/data/raw
    archivos_csv = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))
    if archivos_csv:
        for csv_f in archivos_csv:
            size_mb = os.path.getsize(csv_f) / (1024 * 1024)
            if size_mb > 10:  # Archivo mayor a 10 MB
                print(f"✅ Se encontró archivo CSV existente: {csv_f} ({size_mb:.2f} MB). Omitiendo descarga.", flush=True)
                return

    print(f"📥 Iniciando descarga automática desde Kaggle: {DATASET_NAME}...", flush=True)
    
    # 2. Configuración de credenciales Kaggle
    token = os.getenv("KAGGLE_API_TOKEN") or os.getenv("KAGGLE_TOKEN") or os.getenv("KAGGLE_KEY")
    username = os.getenv("KAGGLE_USERNAME", "kaggle_user")
    
    if token:
        os.environ["KAGGLE_KEY"] = token
        os.environ["KAGGLE_USERNAME"] = username
        
        for cfg_dir in ["/root/.kaggle", "/root/.config/kaggle", os.path.expanduser("~/.kaggle"), os.path.expanduser("~/.config/kaggle")]:
            try:
                os.makedirs(cfg_dir, exist_ok=True)
                cfg_file = os.path.join(cfg_dir, "kaggle.json")
                with open(cfg_file, "w") as f:
                    json.dump({"username": username, "key": token}, f)
                os.chmod(cfg_file, 0o600)
            except Exception:
                pass

    # 3. Importación y autenticación con Kaggle
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("🔐 Autenticación con Kaggle exitosa.", flush=True)
    except Exception as e:
        print(f"❌ Error al autenticar con la API de Kaggle: {e}", flush=True)
        raise e

    # 4. Descargar en el disco raíz (/tmp/kaggle_download con >900 GB libres) para evitar desbordar el volumen
    print(f"📦 Descargando archivo ZIP en {TEMP_DOWNLOAD_DIR}...", flush=True)
    api.dataset_download_files(DATASET_NAME, path=TEMP_DOWNLOAD_DIR, unzip=False)
    
    archivos_zip = glob.glob(os.path.join(TEMP_DOWNLOAD_DIR, "*.zip"))
    if not archivos_zip:
        raise FileNotFoundError(f"❌ No se encontró el archivo .zip descargado en {TEMP_DOWNLOAD_DIR}")
        
    zip_path = archivos_zip[0]
    print(f"📂 Archivo ZIP descargado en {zip_path}. Extrayendo en streaming hacia {DATA_RAW_DIR}...", flush=True)
    
    # 5. Extracción en streaming directo a /app/data/raw/us_accidents.csv
    output_csv = os.path.join(DATA_RAW_DIR, "us_accidents.csv")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_names = [f for f in zf.namelist() if f.endswith('.csv')]
        if not csv_names:
            raise FileNotFoundError("❌ No se encontró archivo CSV dentro del ZIP.")
            
        csv_file_name = csv_names[0]
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
                shutil.copyfileobj(src, dst)
                print("✨ Archivo completo extraído exitosamente.", flush=True)

    # 6. Limpieza del directorio temporal de descarga
    try:
        shutil.rmtree(TEMP_DOWNLOAD_DIR, ignore_errors=True)
        print("🗑️ Archivos temporales de /tmp eliminados con éxito.", flush=True)
    except Exception as e:
        print(f"Advertencia al limpiar temp: {e}", flush=True)
        
    tam_final = os.path.getsize(output_csv) / (1024 * 1024)
    print(f"✅ Dataset listo para Dask en: {output_csv} ({tam_final:.2f} MB)", flush=True)

if __name__ == "__main__":
    descargar_dataset()
