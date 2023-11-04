from kafka import KafkaConsumer

# Configuración del servidor de Kafka y el tópico al que te quieres suscribir
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC_PARES = 'pares'

def consume_pares():
    # Configurar el consumidor de Kafka
    consumer = KafkaConsumer(TOPIC_PARES, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='pares-group')
    print(f"Esperando posiciones finales del dron en el tópico '{TOPIC_PARES}'...")

    # Consumir mensajes del tópico
    for message in consumer:
        pares = message.value.decode('utf-8')
        print(f"Pares recibidos: {pares}")

# Llamar a la función para iniciar la consumición
consume_pares()