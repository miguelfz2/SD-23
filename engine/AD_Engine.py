import socket
import sqlite3
import threading
import time
import json
from kafka import KafkaConsumer
from kafka import KafkaProducer
TOPIC_OK = 'espectaculo'
TOPIC_MAPA = 'mapa'
TOPIC = 'movimientos-dron'
TOPIC_PARES = 'pares'

# Ruta de la base de datos
DB_FILE = r'/home/mfz/Escritorio/SD/SD-23/registry/drones.db'

# Dirección de los brokers de Kafka y nombre del tópico
KAFKA_BOOTSTRAP_SERVERS = '192.168.108.185:9092' ##PARAMETRIZAR

# Maximo numero de drones
MAX_CONEXIONES = 2 ##PARAMETRIZAR

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
    obj.connect((ip_clima,port_clima))
    msg = ciudad.encode('utf-8')
    obj.send(msg)
    respuesta = obj.recv(4096)
    if int(respuesta.decode('utf-8')) > 0:
        return True
    else:
        return False

def imprimir_mapa(mapa):
    for fila in mapa:
        for casilla in fila:
            if casilla == 0:
                print(' ', end=' ')  
            else:
                print(casilla, end=' ')  
        print()  

def construir_mapa():
    mapa = [[0 for _ in range(20)] for _ in range(20)]
    return mapa

#Devuelve el mapa con el cambio de posicion dado
def cambiar_mapa(dron, posicion, mapa):
    if 0 <= posicion[0] < 20 and 0 <= posicion[1] < 20:
        mapa[posicion[0]][posicion[1]] = dron
    else:
        print("La posición está fuera de los límites del mapa.")

    return mapa

# Función que maneja las conexiones de los clientes
def handle_client(client_socket, addr):
    print(f"Cliente conectado desde {addr}")
    
    # Recibir datos del cliente 
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


def leer_json(ruta):
    try:
        with open(ruta, 'r') as archivo:
            datos = json.load(archivo)
            elementos = datos.get("elementos", [])

            pares = []
            for elemento in elementos:
                id_elemento = elemento.get("id")
                posicion = elemento.get("posicion")
                if id_elemento is not None and posicion:
                    pares.append((id_elemento, posicion))

            return pares
    except FileNotFoundError:
        print(f"El archivo '{json}' no se encuentra.")

def envia_pares(pares):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    #mapa_dron = cambiar_mapa(dron, posicion, mapa)
    print("ENVIANDO PARES: "+str(pares))
    producer.send(TOPIC_PARES, value=pares)
    producer.flush()


def envia_OK(ciudad):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))
    val = ''
    while True:
        if consulta_clima(ciudad) == True:
            val = 'OK'
        else:
            val = 'NOOO'
        producer.send(TOPIC_OK, value=val)
        producer.flush()
        time.sleep(5)

# Función para consumir mensajes de Kafka
def consume_kafka():
    consumer = KafkaConsumer(TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='movimientos-group')
    print(f"Esperando movimientos del dron en el tópico '{TOPIC}'...")
    
    for message in consumer:
        movimiento = message.value.decode('utf-8')
        print(f"Nuevo movimiento del dron: {movimiento}")

# Configurar el socket del servidor
HOST = 'localhost'  # Dirección IP del servidor
PORT = 12346         # Puerto del servidor PARAMETRIZAR

def main():
    mapa = construir_mapa()
    pos = (2,3)
    cambiar_mapa(1,pos,mapa)
    imprimir_mapa(mapa)
    # Crear un socket de servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    CONEX_ACTIVAS = 0
    print(f"Servidor en el puerto {PORT} esperando conexiones...")
    ciudad = 'Minnesota'

    # Iniciar el hilo para consumir mensajes de movimientos del dron
    kafka_thread = threading.Thread(target=consume_kafka)
    kafka_thread.start()

    try:
        while True:
            # Esperar a que un cliente se conecte
            client_socket, addr = server_socket.accept()

            # Crear un nuevo subproceso para manejar la conexión del cliente
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
            # Iniciar el hilo para enviar mensajes "OK" periódicamente
            CONEX_ACTIVAS = CONEX_ACTIVAS + 1
            print("CONEX_ACTIVAS: " + str(CONEX_ACTIVAS))
            if MAX_CONEXIONES == CONEX_ACTIVAS:
                print("Entramos en if")
                ok_message_thread = threading.Thread(target=envia_OK, args=(ciudad,))
                ok_message_thread.start()
                #json = input("Introduce el archivo de espectaculo: ")
                pares = leer_json("./json/figura_simple.json")
                print("json leido")
                pares_thread = threading.Thread(target=envia_pares, args=(pares,))
                pares_thread.start()

    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        # Cerrar el socket del servidor al finalizar
        server_socket.close()

if __name__ == "__main__":
    main()

