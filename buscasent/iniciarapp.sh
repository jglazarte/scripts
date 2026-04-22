#!/bin/bash
# Navegar a la carpeta del proyecto
cd ~/Proyectos/Sentencias

# Iniciar el servidor de Flask en segundo plano
python3 app.py &

# Esperar 2 segundos para que el servidor arranque
sleep 2

# Abrir el navegador en la dirección local
xdg-open http://localhost:5000
