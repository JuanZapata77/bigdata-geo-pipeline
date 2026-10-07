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
                withCredentials([string(credentialsId: 'kaggle-token', variable: 'KAGGLE_API_TOKEN')]) {
                    sh '''
                    echo "Descargando dataset de US Accidents desde Kaggle..."
                    mkdir -p data/raw
                    # Usamos el dataset de accidentes recomendado en la rúbrica
                    kaggle datasets download -d sobhanmoosavi/us-accidents -p data/raw --unzip
                    echo "¡Descarga exitosa!"
                    '''
                }
            }
        }
    }
}