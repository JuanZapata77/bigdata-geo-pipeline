FROM jenkins/jenkins:lts

# Cambiamos a root para poder instalar paquetes
USER root

# Instalamos el cliente de Docker (CLI)
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

# Mantenemos el usuario root para evitar problemas de permisos con el socket de Docker