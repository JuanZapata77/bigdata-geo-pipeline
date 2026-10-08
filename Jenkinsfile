pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

       stage('Construir e Iniciar Infraestructura') {
            steps {
                echo 'Limpiando contenedores de ejecuciones anteriores...'
                sh 'docker-compose down --remove-orphans'
                
                echo 'Levantando los contenedores con Docker Compose...'
                sh 'docker-compose up -d --build'
            }
        }

        stage('Pruebas Automatizadas (Pytest)') {
            steps {
                echo 'Esperando que la API levante...'
                sh 'sleep 10'
                
                echo 'Ejecutando pruebas con Pytest dentro del contenedor de la API...'
                // Si esta prueba falla, Jenkins cancelará el pipeline aquí mismo
                sh 'docker exec geo_api pytest /app/tests/'
            }
        }

        stage('Ingesta y Limpieza (Dask)') {
            steps {
                echo 'Ejecutando el pipeline ETL con el clúster de Dask...'
                sh 'docker exec geo_api python /app/src/etl.py'
            }
        }

        stage('Analítica Geoespacial (Spark)') {
            steps {
                echo 'Ejecutando agrupaciones analíticas con el clúster de Spark...'
                sh 'docker exec geo_api python /app/src/spark_agregaciones.py'
            }
        }
    }

    post {
        success {
            echo '✅ ¡Despliegue y procesamiento exitoso! Todo funciona perfecto.'
        }
        failure {
            echo '❌ Error en el pipeline. Revisa los logs de Jenkins.'
        }
    }
}