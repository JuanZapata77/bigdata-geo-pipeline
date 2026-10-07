pipeline {
    // Usamos un contenedor de Python dinámico para ejecutar este paso
    agent {
        docker { 
            image 'python:3.11-slim'
            args '-u root:root' 
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
                // Inyectamos el Secret Text en la variable de entorno exacta que exige Kaggle
                withCredentials([string(credentialsId: 'kaggle-token', variable: 'KAGGLE_API_TOKEN')]) {
                    sh '''
                    echo "Descargando dataset de bicicletas desde Kaggle..."
                    mkdir -p data/raw
                    kaggle datasets download -d residentmario/new-york-city-bike-share-dataset -p data/raw --unzip
                    echo "¡Descarga exitosa!"
                    '''
                }
            }
        }
    }
}