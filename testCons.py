from kafka import KafkaConsumer
import pickle

# Configura el servidor y el tema de Kafka
bootstrap_servers = 'localhost:9092'  # Cambia esto según la configuración de tu servidor Kafka
topic = 'mov'

# Crea un consumidor Kafka


consumer = KafkaConsumer(topic, bootstrap_servers=bootstrap_servers, group_id='movimientos-group')
print(f"Esperando movimientos del dron en el tópico ''...")

print("Esperando mensajes desde Kafka...")

# Se suscribe al tema y consume mensajes
for message in consumer:
    mov = message.value  # Obtiene el mapa del mensaje
    print("Mov recibido desde Kafka:")
    print(mov)

# Cierra el consumidor Kafka (esto no se ejecutará ya que el bucle anterior es infinito)
consumer.close()
