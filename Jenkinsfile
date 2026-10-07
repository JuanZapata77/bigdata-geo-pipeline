pipeline {
    agent {
        docker { 
            image 'python:3.11-slim'
            // Truco de DevOps: Conectamos este contenedor a la red de tus contenedores principales
            args '-u root:root --network bigdata-geo-pipeline_default' 
        }
    }
    
    stages {
        stage('Preparar Entorno') {
            steps {
                sh 'pip install kaggle'
            }
        }
        
        stage('Ingesta de Datos (Kaggle)') {
            steps {
                withCredentials([string(credentialsId: 'kaggle-token', variable: 'KAGGLE_API_TOKEN')]) {
                    sh '''
                    echo "Descargando dataset de US Accidents desde Kaggle..."
                    mkdir -p data/raw
                    kaggle datasets download -d sobhanmoosavi/us-accidents -p data/raw --unzip
                    echo "¡Descarga exitosa!"
                    '''
                }
            }
        }
        
        // ¡NUEVA ETAPA! Aquí corre la magia de Dask
        stage('Transformación y Carga (ETL)') {
            steps {
                sh '''
                echo "Instalando librerías de Big Data..."
                pip install -r requirements.txt
                
                echo "Ejecutando proceso ETL..."
                python src/etl.py
                '''
            }
        }
    }
}