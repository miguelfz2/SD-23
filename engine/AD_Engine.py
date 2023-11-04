import re
import socket
import sqlite3
import threading
import time
import json
import sys
from kafka import KafkaConsumer
from kafka import KafkaProducer
TOPIC_OK = 'espectaculo'
TOPIC_MAPA = 'mapa'
TOPIC = 'movimientos-dron'
TOPIC_PARES = 'pares'

# Ruta de la base de datos
DB_FILE = r'C:\Users\ayelo\OneDrive\Documentos\GitHub\SD-23\registry\drones.db'

# Dirección de los brokers de Kafka y nombre del tópico
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092' ##PARAMETRIZAR

# Maximo numero de drones
MAX_CONEXIONES = 10 ##PARAMETRIZAR

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

def limpiar_mapa(mapa):
    filas = len(mapa)
    columnas = len(mapa[0]) if filas > 0 else 0  

    nuevo_mapa = [[0 for _ in range(columnas)] for _ in range(filas)]
    return nuevo_mapa

def leer_id_mapa(id_dron, mapa):
    filas = len(mapa)
    for fila in range(filas):
        columnas = len(mapa[fila])
        for columna in range(columnas):
            if mapa[fila][columna] == id_dron:
                return fila, columna
    # Devuelve None si el ID no se encuentra en el mapa
    fila = 1
    columna = 1
    return fila, columna

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

    print("ENVIANDO PARES: "+str(pares))
    producer.send(TOPIC_PARES, value=pares)
    producer.flush()

def envia_mapa(mapa):
    mapa_json = json.dumps(mapa)
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    producer.send(TOPIC_MAPA, value=mapa_json)
    producer.flush()

def envia_OK(ciudad):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))
    val = ''
    while True:
        if consulta_clima(ciudad) == True:
            val = 'OK'
        else:
            val = 'Hace mucho frio.'
        producer.send(TOPIC_OK, value=val)
        producer.flush()
        time.sleep(5)

# Función para consumir mensajes de Kafka
def consume_kafka(mapa):
    consumer = KafkaConsumer(TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='movimientos-group')
    print(f"Esperando movimientos del dron en el tópico '{TOPIC}'...")
    
    # Diccionario para mapear direcciones a cambios de posición
    movimientos = {
        'E': (0, 1),  # Mover hacia el este (aumentar la columna)
        'SE': (1, 1), # Mover hacia el sudeste (aumenta fila y columna)
        'NE': (-1, 1) # Mover hacia el noreste (disminuir fila aumentar columna)
        'O': (0, -1),  # Mover hacia el oeste (disminuir la columna)
        'NO': (-1, -1), #Mover hacia el noroeste (disiminuir fila y columna)
        'SO': (1, -1), #Mover hacia el sudoeste (aumentar fila disminuir columna)
        'N': (-1, 0),  # Mover hacia el norte (disminuir la fila)
        'S': (1, 0)   # Mover hacia el sur (aumentar la fila)
    }
    pos = (0, 0)
    for message in consumer:
        respuesta = message.value.decode('utf-8')
        res = respuesta.split(",")
        id_dron = res[0]
        movimiento = res[1]
        print("El id es: "+id_dron)
        pos = leer_id_mapa(id_dron, mapa)
        print(f"Nuevo movimiento del dron: {movimiento}")

        # Verificar que el movimiento sea válido
        if movimiento in movimientos:
            # Obtener el cambio de posición para la dirección dada
            cambio_fila, cambio_columna = movimientos[movimiento]
            
            # Calcular la nueva posición del dron
            nueva_fila = pos[0] + cambio_fila
            nueva_columna = pos[1] + cambio_columna

            # Actualizar el mapa si la nueva posición está dentro de los límites
            if 0 <= nueva_fila < 20 and 0 <= nueva_columna < 20:
                mapa = cambiar_mapa('', pos, mapa)
                pos = (nueva_fila, nueva_columna)
                mapa = cambiar_mapa(id_dron, pos, mapa)
                print("Posicion:" + str(pos))
                return mapa
            else:
                print("Movimiento fuera de los límites del mapa.")
        else:
            print("Movimiento no válido.")


def menu():
    print()
    print("1. Iniciar espectaculo")
    print("2. Salir")
    print()
    return input('Elige una opción: ')

# Configurar el socket del servidor
HOST = 'localhost'  # Dirección IP del servidor
PORT = 12345         # Puerto del servidor PARAMETRIZAR

def main():
    mapa = construir_mapa()
    limpiar_mapa(mapa)
    pares = leer_json("./json/figura_simple.json")
    drones_json = len(pares)
    print("json leido")
    print(drones_json)
    # Crear un socket de servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    CONEX_ACTIVAS = 0
    print(f"Servidor en el puerto {PORT} esperando conexiones...")
    ciudad = 'Minnesota'


    try:
        while True:
            # Esperar a que un cliente se conecte
            client_socket, addr = server_socket.accept()

            # Crear un nuevo subproceso para manejar la conexión del cliente
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
            #Hilo para el servidor de clima
            clima_thread = threading.Thread(target=consulta_clima, args=(ciudad,))
            clima_thread.start()

            # Iniciar el hilo para enviar mensajes "OK" periódicamente
            CONEX_ACTIVAS = CONEX_ACTIVAS + 1
            print("CONEX_ACTIVAS: " + str(CONEX_ACTIVAS))
            if MAX_CONEXIONES == CONEX_ACTIVAS or CONEX_ACTIVAS == drones_json:
                time.sleep(1)
                opc = '0'
                while opc != '1' or opc != '2':
                    opc = menu()
                    if opc == '1':
                        ok_thread = threading.Thread(target=envia_OK, args=(ciudad,))
                        ok_thread.start()  
                        clima = consulta_clima(ciudad)  
                        envia_pares(pares)
                        while clima == True:            
                            mapa = consume_kafka(mapa)
                            imprimir_mapa(mapa)
                            envia_mapa(mapa)
                    elif opc == '2':
                        sys.exit()
                    else:
                        print("Opcion incorrecta")

    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        # Cerrar el socket del servidor al finalizar
        server_socket.close()

if __name__ == "__main__":
    main()

