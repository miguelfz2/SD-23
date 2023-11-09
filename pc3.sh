#!/bin/bash

# Verificar si se proporcionó exactamente 7 argumentos (6 + el número de veces)
##IP y puerto del AD_Engine IP y puerto del Broker/Bootstrap-server del gestor de colas IP y puerto del AD_Registry
if [ "$#" -ne 6 ]; then
  echo "Uso: $0 <número de drones> <IP Engine/Registry 1> <Puerto Engine 2> <Puerto Registry 3> <IP Kafka 4> <Puerto Kafka 5>"
  exit 1
fi

# Obtener el número de veces a ejecutar el script
veces_a_ejecutar="$1"

# Shift para eliminar el primer argumento (el número de veces)
shift

# Bucle para ejecutar el script Python
for ((i = 0; i < veces_a_ejecutar; i++)); do
  echo "Ejecución número $((i+1))"
  python AD_Drone.py "$@"
done

