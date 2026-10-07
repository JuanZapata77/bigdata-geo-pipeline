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
                // Aquí extraemos tus credenciales ocultas con el ID exacto que creaste
                withCredentials([usernamePassword(credentialsId: 'kaggle-credentials', passwordVariable: 'KAGGLE_KEY', usernameVariable: 'KAGGLE_USERNAME')]) {
                    sh '''
                    echo "Descargando dataset de bicicletas desde Kaggle..."
                    mkdir -p data/raw
                    # Usamos un dataset popular de Citi Bike de NYC (puedes cambiar este ID luego)
                    kaggle datasets download -d residentmario/new-york-city-bike-share-dataset -p data/raw --unzip
                    echo "¡Descarga exitosa!"
                    '''
                }
            }
        }
    }
}