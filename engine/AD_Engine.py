import socket
import sqlite3
import threading
from kafka import KafkaConsumer
from kafka import KafkaProducer

# Ruta de la base de datos
DB_FILE = r'C:\Users\ayelo\OneDrive\Documentos\AAA\SD\Practica\registry\drones.db'

# Dirección de los brokers de Kafka y nombre del tópico
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC = 'movimientos-dron'
TOPIC_OK = #TOPIC PARA ENVIAR CONFIRMACION DE EMPEZAR ESPECTACULO(?)

# Maximo numero de drones
MAX_CONEXIONES = 2

# Función para verificar el token y el alias en la base de datos
def verificar_registro(token):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dron WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Función que consulta al servidor de clima la temperatura de la zona
def consulta_clima(ciudad):
    ip_clima = 'localhost'
    port_clima = 8010
    obj = socket.socket()
    obj.connect((HOST,PORT))
    msg = ciudad.encode('utf-8')
    obj.send(msg)
    respuesta = obj.recv(4096)
    if int(respuesta.decode('utf-8')) > 0:
        return True
    else:
        return False

# Función que maneja las conexiones de los clientes
def handle_client(client_socket, addr):
    print(f"Cliente conectado desde {addr}")
    
    # Recibir datos del cliente (token y alias)
    data = client_socket.recv(1024).decode('utf-8')
    token = data
    print(token)
    
    # Verificar el registro en la base de datos
    if verificar_registro(token):
        # Cliente registrado, enviar mensaje de OK
        client_socket.send('OK'.encode('utf-8'))
    else:
        # Cliente no registrado, enviar mensaje para registrarse
        client_socket.send('Por favor, regístrese.'.encode('utf-8'))
    
    # Cerrar la conexión con el cliente
    client_socket.close()
    print(f"Cliente {addr} desconectado.")

def envia_OK(ciudad):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    # Enviar la orden de empezar al tópico 'TOPIC_OK'
    if consulta_clima(ciudad) == True:
        producer.send(TOPIC_OK, value='OK')
    else:
        producer.send(TOPIC_OK, value='NOOK')
    producer.flush()

# Función para consumir mensajes de Kafka
def consume_kafka():
    consumer = KafkaConsumer(TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='movimientos-group')
    print(f"Esperando movimientos del dron en el tópico '{TOPIC}'...")
    
    for message in consumer:
        movimiento = message.value.decode('utf-8')
        print(f"Nuevo movimiento del dron: {movimiento}")

# Configurar el socket del servidor
HOST = 'localhost'  # Dirección IP del servidor
PORT = 12345         # Puerto del servidor

def main():
    # Crear un socket de servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Servidor en el puerto {PORT} esperando conexiones...")

    try:
        while True:
            # Esperar a que un cliente se conecte
            client_socket, addr = server_socket.accept()
            
            # Crear un nuevo subproceso para manejar la conexión del cliente
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
            CONEX_ACTIVAS = threading.active_count() - 1

            # Iniciar el consumidor de Kafka en un hilo separado
            if CONEX_ACTIVAS == MAX_CONEXIONES:
                ###MANDAR OK POR KAFKA
                ciudad = input('Elige la ciudad donde se desarrollara el espectaculo: ')
                envia_OK(ciudad)
                kafka_thread = threading.Thread(target=consume_kafka)
                kafka_thread.start()


    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        # Cerrar el socket del servidor al finalizar
        server_socket.close()

if __name__ == "__main__":
    main()
