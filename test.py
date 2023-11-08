from kafka import KafkaProducer
import pickle
import random

# Configura el servidor y el tema de Kafka
bootstrap_servers = 'localhost:9092'  # Cambia esto según la configuración de tu servidor Kafka
topic = 'mo1'

producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                             value_serializer=lambda v: str(v).encode('utf-8'))

mov = '1,SE'

# Enviar el movimiento al tópico 'movimientos-dron'
producer.send(topic, value=mov)
producer.flush()
