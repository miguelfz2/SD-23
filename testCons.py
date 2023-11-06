from kafka import KafkaConsumer
import time

# Configura el servidor y el tema de Kafka
bootstrap_servers = 'localhost:9092'  # Cambia esto según la configuración de tu servidor Kafka
topic = 'mov'

def leer_mensaje_kafka():
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=bootstrap_servers,
                             group_id=None,
                             auto_offset_reset='latest')

    start_time = time.time()
    mensaje_recibido = None

    while time.time() - start_time < 20:
        records = consumer.poll(timeout_ms=1000, max_records=1)
        for record in records.values():
            for message in record:
                mensaje_recibido = message.value.decode('utf-8')
                break  
            if mensaje_recibido:
                break  
        if mensaje_recibido:
            break  

    # Cierra el consumidor
    consumer.close()

    return mensaje_recibido

msg = leer_mensaje_kafka()

if msg:
    print("Mensaje recibido:", msg)
else:
    print("No se recibió ningún mensaje durante 20 segundos.")
