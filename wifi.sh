#!/bin/bash

# Redes disponibles
echo "Redes Wi-Fi disponibles:"
nmcli device wifi list

# Elegir una red
read -p "Elegir red a la que conectarse: " network

# Contraseña de la red
read -p "Clave para $network: " password
echo

# Conectarse a la red seleccionada
nmcli device wifi connect $network password $password
