from kafka import KafkaProducer
import pickle
import random

# Configura el servidor y el tema de Kafka
bootstrap_servers = 'localhost:9092'  # Cambia esto según la configuración de tu servidor Kafka
topic = 'mov'

# Crea un productor Kafka
producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    # Enviar el movimiento al tópico 'movimientos-dron'
id_dron = 1
move = 'S'
movimiento = str(id_dron) + "," + move
producer.send(topic, value=movimiento)
producer.flush()

# Cierra el productor Kafka
producer.close()
