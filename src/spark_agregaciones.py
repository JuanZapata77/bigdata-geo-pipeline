from pyspark.sql import SparkSession
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://geo_mongo:27017/")

print("1. Conectando al clúster de Spark...")
spark = SparkSession.builder \
    .appName("AgregacionesGeoespaciales") \
    .master("spark://spark-master:7077") \
    .config("spark.mongodb.input.uri", f"{MONGO_URI}geo_db.accidents") \
    .config("spark.mongodb.output.uri", f"{MONGO_URI}geo_db.resumen_estados") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
    .getOrCreate()

print("2. Leyendo datos limpios desde MongoDB...")
df = spark.read.format("mongo").load()

print("3. Calculando agregaciones (Accidentes por Estado y Severidad)...")
# Agrupamos por estado y severidad, y contamos cuántos hay
resumen_df = df.groupBy("estado", "severidad").count()

print("4. Guardando resultados en la nueva colección 'resumen_estados'...")
resumen_df.write.format("mongo").mode("overwrite").save()

print("✅ ¡Procesamiento analítico con Spark terminado con éxito!")
spark.stop()