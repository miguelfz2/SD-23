import re
import socket
import sqlite3
import threading
import time
import json
import sys
import pickle
import requests
import ssl
from kafka import KafkaConsumer
from kafka import KafkaProducer
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from io import StringIO
import datetime

app = Flask(__name__)
CORS(app)

CONEX_ACTIVAS = 0

FORMATO = 'utf-8'

def lee_topics():
    try:
        with open("../topics.txt", 'r') as archivo:
            # Leer la primera línea del archivo
            ciudad = archivo.readline().strip()
            return ciudad
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

TOPIC = 'mov'+lee_topics()  # Nombre del tópico de Kafka
TOPIC_OK = 'espec'+lee_topics()
TOPIC_PARES = 'par'+lee_topics()
TOPIC_MAPA = 'mapa'+lee_topics()

# Ruta de la base de datos
DB_FILE = r'/home/mfz/Escritorio/SD/SD-23/registry/drones.db'

# Dirección de los brokers de Kafka y nombre del tópico
KAFKA_BOOTSTRAP_SERVERS = sys.argv[3] + ":" + sys.argv[4] ##PARAMETRIZAR

# Maximo numero de drones
MAX_CONEXIONES = int(sys.argv[2]) ##PARAMETRIZAR

# Función para verificar el token y el alias en la base de datos
def verificar_registro(token):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dron WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def actualizar_bd(id_dron, pos):
    try:
        # Conectar a la base de datos
        conexion = sqlite3.connect(DB_FILE)
        cursor = conexion.cursor()

        # Actualizar la posición del dron en la base de datos
        cursor.execute('UPDATE dron SET posicion = ? WHERE id = ?', (pos, id_dron))
        conexion.commit()
        log = "localhost - ["+ str(hora()) +"] UPDATE POSITION drones.db /dron id = "+str(id_dron)
        logea(log)

    except Exception as e:
        log = "localhost - ["+ str(hora()) +"] UPDATE POSITION ERROR drones.db /dron id = "+str(id_dron)
        logea(log)
        print(f"Error al actualizar la base de datos: {e}")

    finally:
        # Cerrar la conexión
        conexion.close()

def obtener_temperatura(ciudad):
    api_key = "38f1ca83afe2c1e000674be068a20e1c"
    # URL de la API de OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}"

    try:
        # Realizar la solicitud a la API
        respuesta = requests.get(url)
        datos = respuesta.json()

        # Verificar si la solicitud fue exitosa
        if respuesta.status_code == 200:
            # Obtener la temperatura actual desde los datos
            temperatura = datos['main']['temp']
            
            # Convertir la temperatura de Kelvin a Celsius (restar 273.15)
            temperatura_celsius = temperatura - 273.15
            log = "37.139.1.159 - ["+ str(hora()) +"] GET temperatura: "+str(temperatura_celsius)+" HTTPS/1.1 "+str(respuesta.status_code)
            logea(log)
            return temperatura_celsius > 0
        else:
            print(f"Error al obtener datos. Código de estado: {respuesta.status_code}")
    except Exception as e:
        log = "37.139.1.159 - ["+ str(hora()) +"] GET temperatura ERROR HTTPS/1.1 "+str(respuesta.status_code)
        logea(log)
        print(f"No se pudo conectar con el servidor")
        return False


def obtener_ciudad():
    try:
        with open("./ciudades.txt", 'r') as archivo:
            # Leer la primera línea del archivo
            ciudad = archivo.readline().strip()
            return ciudad
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None


# Función que consulta al servidor de clima la temperatura de la zona
def consulta_clima(ciudad):
    try:
        ip_clima = sys.argv[3]
        port_clima = int(sys.argv[5])
        with socket.socket() as obj:
            obj.connect((ip_clima, port_clima))
            msg = ciudad.encode('utf-8')
            obj.send(msg)
            respuesta = obj.recv(4096)
            if int(respuesta.decode('utf-8')) > 0:
                return True
            else:
                return False
    except (ConnectionRefusedError, TimeoutError):
        print("No se pudo conectar con el servidor.")
        return False
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return False


def imprimir_mapa(mapa):
    for fila in mapa:
        for casilla in fila:
            if casilla == 0:
                print('-', end=' ')  
            else:
                print(casilla, end=' ')  
        print()  

def construir_mapa():
    mapa = [[0 for _ in range(20)] for _ in range(20)]
    return mapa

def son_mapas_iguales(mapa1, mapa2):
    filas = len(mapa1)
    columnas = len(mapa1[0])
    comp = True
    # Verificar las dimensiones de ambos mapas
    if len(mapa2) != filas or len(mapa2[0]) != columnas:
        comp = False
    
    # Comparar los valores en cada posición de los mapas
    for i in range(filas):
        for j in range(columnas):
            if mapa1[i][j] != mapa2[i][j]:
                comp = False
    
    # Si no se encontraron diferencias, los mapas son igualesç
    return comp

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
    data = client_socket.recv(2048).decode('utf-8')
    token = data
    print("TOKEN: "+token)
    
    try:
        # Verificar el registro en la base de datos
        if verificar_registro(token):
            # Cliente registrado, enviar mensaje de OK
            if client_socket.fileno() != -1:
                client_socket.send(msj.encode(FORMATO))
            else:
                print("El cliente ya ha cerrado la conexión.")
        else:
            # Cliente no registrado, enviar mensaje para registrarse
            msj = 'Por favor, regístrese.'
            client_socket.send(msj.encode(FORMATO))
    except BrokenPipeError as e:
        # Capturar la excepción específica de BrokenPipeError
        print(f"Error de Broken Pipe: {e}")
    except Exception as e:
        print(f"Error de SSL: {e}")

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
    log = str(KAFKA_BOOTSTRAP_SERVERS)+" - ["+ str(hora()) +"] SEND POSICIONES FINALES: "+str(pares)
    logea(log)
    producer.send(TOPIC_PARES, value=pares)
    producer.flush()

def envia_mapa(msg):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))
    time.sleep(1)
    log = str(KAFKA_BOOTSTRAP_SERVERS)+" - ["+ str(hora()) +"] SEND MAPA"
    logea(log)
    producer.send(TOPIC_MAPA, value=msg)
    producer.flush()

def envia_OK(ciudad):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))
    val = ''
    if consulta_clima(ciudad) == True:
        val = 'OK'
        log = str(KAFKA_BOOTSTRAP_SERVERS)+" - ["+ str(hora()) +"] SEND TEMPERATURA OK"
        logea(log)
        producer.send(TOPIC_OK, value=val)
        producer.flush()
    while True:
        if consulta_clima(ciudad) == False:
            val = 'Hace mucho frio.'
            log = str(KAFKA_BOOTSTRAP_SERVERS)+" - ["+ str(hora()) +"] SEND TEMPERATURA BAJA"
            logea(log)
            producer.send(TOPIC_OK, value=val)
            producer.flush()
        time.sleep(5)

def leer_kafka():
    consumer = KafkaConsumer(TOPIC,
                             bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             group_id='mov-group', auto_offset_reset='latest'
                             )

    start_time = time.time()
    mensaje_recibido = None

    while time.time() - start_time < 3:
        records = consumer.poll(timeout_ms=5000, max_records=1)
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


# Funcion para consumir mensajes de Kafka
def calcular_pos(mapa):
    
    print(f"Esperando movimientos del dron en el tópico '{TOPIC}'...")
    
    # Diccionario para mapear direcciones a cambios de posición
    movimientos = {
        'E': (0, 1),  # Mover hacia el este (aumentar la columna)
        'SE': (1, 1), # Mover hacia el sudeste (aumenta fila y columna)
        'NE': (-1, 1), # Mover hacia el noreste (disminuir fila aumentar columna)
        'O': (0, -1),  # Mover hacia el oeste (disminuir la columna)
        'NO': (-1, -1), #Mover hacia el noroeste (disiminuir fila y columna)
        'SO': (1, -1), #Mover hacia el sudoeste (aumentar fila disminuir columna)
        'N': (-1, 0),  # Mover hacia el norte (disminuir la fila)
        'S': (1, 0)   # Mover hacia el sur (aumentar la fila)
    }
    pos = (0, 0)
    respuesta = leer_kafka()
    if respuesta is None:
        return None, None
    res = respuesta.split(",")
    id_dron = res[0]
    movimiento = res[1]
    pos = leer_id_mapa(id_dron, mapa)
    print(f"Nuevo movimiento del dron: {movimiento}")
    cambiar_mapa(0, pos, mapa)
    # Verificar que el movimiento sea válido
    if movimiento in movimientos:
        # Obtener el cambio de posición para la dirección dada
        cambio_fila, cambio_columna = movimientos[movimiento]
            
        # Calcular la nueva posición del dron
        nueva_fila = pos[0] + cambio_fila
        nueva_columna = pos[1] + cambio_columna

        # Actualizar el mapa si la nueva posición está dentro de los límites
        if 0 <= nueva_fila < 20 and 0 <= nueva_columna <= 20:
            #mapa = cambiar_mapa(0, pos, mapa)
            pos = (nueva_fila, nueva_columna)
            #mapa = cambiar_mapa(id_dron, pos, mapa)
            #print("Posicion:" + str(pos))
            return id_dron, pos
        else:
            print("Movimiento fuera de los límites del mapa.")
    else:
        print("Movimiento no válido.")

def hora():
    return datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]

def logea(log):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (texto) VALUES (?)', (log,))
    conn.commit()
    conn.close()


@app.route('/logs', methods=['GET'])
def get_log_api():
    try:
        ##Consulta en base de datos de los logs
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT texto FROM logs')
        result = cursor.fetchall()
        conn.close()
        respuesta={
            ##Resultado de la consulta
            'logs': result
        }

        return jsonify(respuesta)
        
    except Exception as e:
        log = str(request.remote_addr)+" - ["+ str(hora()) +"] GET /logs HTTPS/1.1 500"
        logea(log)
        print("ERROR en endpoint GET /logs: "+e)

@app.route('/dron', methods=['GET'])
def get_dron_api():
    try:
        id_dron = request.args.get('data')
        ##Guardar log
        ip = request.remote_addr
        fecha = hora()
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] GET /dron id = "+str(id_dron)+" HTTPS/1.1 200"
        logea(log)

        ##Consulta en base de datos del mapa
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM dron WHERE id=?', (id_dron,))
        result = cursor.fetchone()
        conn.close()
        respuesta={
            ##Resultado de la consulta
            'alias': result[1],
            'pos': result[3]
        }

        return jsonify(respuesta)
        
    except Exception as e:        
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] GET /dron id = "+str(id_dron)+" HTTPS/1.1 500"
        logea(log)
        print("ERROR en endpoint GET /dron: "+str(e))

@app.route('/mapa', methods=['GET'])
def get_mapa_api():
    try:
        ##Guardar log
        ip = request.remote_addr
        fecha = hora()
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] GET /mapa HTTPS/1.1 200"
        logea(log)

        ##Consulta en base de datos del mapa
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT posicion FROM dron')
        result = cursor.fetchall()
        conn.close()
        respuesta={
            ##Resultado de la consulta
            'mapa': result
        }        

        return jsonify(respuesta)

    except Exception as e:
        print("ERROR en endpoint GET /mapa: "+str(e))
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] GET /mapa HTTPS/1.1 500"
        logea(log)


@app.route('/token', methods=['POST'])
def verificar_token_api():
    try:
        global CONEX_ACTIVAS
        token = request.args.get('data')
        #Guardar log
        ip = request.remote_addr
        fecha = hora()
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] POST /token HTTPS/1.1 200"
        logea(log)

        if verificar_registro(token):
            msj = 'OK'
            CONEX_ACTIVAS = CONEX_ACTIVAS + 1
        else:
            msj = 'Por favor, regístrese'

        respuesta = {
            'mensaje': msj,
            ##'clave: clave_publica'
        }

        return jsonify(respuesta)

    except Exception as e:
        print("ERROR en endpoint POST /token: "+str(e))
        log = str(request.remote_addr)+" - ["+ str(fecha) +"] POST /token HTTPS/1.1 500"
        logea(log)

def comprueba_drones(ids):
    mayor = 0
    idd = 0
    for id_d in ids:
        if id_d > mayor:
            mayor = id_d
    
    tam = len(ids)
    tam = tam * 2
    for id_d in ids:
        if id_d + tam < mayor:
            idd = id_d
    
    return idd

def menu():
    print()
    print("1. Iniciar espectaculo")
    print("2. Salir")
    print()
    return input('Elige una opción: ')

# Configurar el socket del servidor
HOST = '192.168.1.211'  # Dirección IP del servidor
PORT = int(sys.argv[1])        # Puerto del servidor PARAMETRIZAR

def handle_api():
    try:
        app.run(debug=False, port=PORT, host="0.0.0.0", ssl_context=('claves/certServ.pem','claves/certServ.pem'), threaded=True)
    except Exception as e:
        print(e)

def main():
    if len(sys.argv[1:]) < 5:
        sys.exit(1)
    mapa = construir_mapa()
    mapa_final = construir_mapa()
    limpiar_mapa(mapa)
    limpiar_mapa(mapa_final)
    pares = leer_json("./json/figura_simple.json")
    for id_dron, pos_f in pares:
        x = pos_f['x']
        y = pos_f['y']
        pos_final = (x, y)
        id_dron = str(id_dron)
        cambiar_mapa(id_dron, pos_final, mapa_final)
    drones_json = len(pares)
    if MAX_CONEXIONES < drones_json:
        print("ERROR: HAY MENOS CONEXCIONES QUE DRONES PARA EL ESPECTACULO")
        sys.exit(1)


    api_thread = threading.Thread(target=handle_api, args=[])
    api_thread.start()
    try:
        while True:            
            if MAX_CONEXIONES == CONEX_ACTIVAS or CONEX_ACTIVAS == drones_json:
                time.sleep(1)
                opc = '0'
                opc = menu()
                while opc != '1' and opc != '2':
                    opc = menu()
                if opc == '1':
                    ids = [tupla[0] for tupla in pares]
                    envia_pares(pares)
                    comp = False
                    while comp == False:
                        ciudad = obtener_ciudad()
                        if obtener_temperatura(ciudad) == True: 
                            contador = 0
                            drones_act = drones_json 
                            while contador < drones_act:        
                                id_dron, pos = calcular_pos(mapa)
                                if id_dron is not None and pos is not None:
                                    cambiar_mapa(id_dron, pos, mapa)
                                    pos_str=str(pos)
                                    actualizar_bd(id_dron, pos_str)
                                    msg = "ID: "+ id_dron + " ha actualizado su posicion a " + str(pos)
                                    print(msg)
                                    envia_mapa(msg)

                                else:
                                    print("UN DRON HA FINALIZADO")
                                    envia_mapa("UN DRON HA FINALIZADO")
                                contador = contador + 1
                            time.sleep(2)
                            imprimir_mapa(mapa)
                            comp = son_mapas_iguales(mapa, mapa_final)
                        else:
                            print("CONDICIONES ADVERSAS")
                            time.sleep(3)
                            mapa = construir_mapa()
                            envia_mapa("CONDICIONES ADVERSAS")
                    msg = "ESPECTACULO FINALIZADO"
                    envia_mapa(msg)
                    print("ESPECTACULO FINALIZADO")
                elif opc == '2':
                    sys.exit(1)
                else:
                    print("Opcion incorrecta")

    except Exception:
        sys.exit()

if __name__ == "__main__":
    main()


