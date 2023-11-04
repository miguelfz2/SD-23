import socket
import sys
from kafka import KafkaProducer
from kafka import KafkaConsumer
import random
import sys
import time
import json
import ast

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'  # La dirección de los brokers de Kafka
TOPIC = 'movimiento'  # Nombre del tópico de Kafka
TOPIC_OK = 'espectaculo'
TOPIC_PARES = 'par'
TOPIC_MAPA = 'mapa'

FORMATO = 'utf-8'
CABECERA = 64

def send(code,client):
    msg = code.encode(FORMATO)
    client.send(msg)


def menu_inicio():
    print()
    print("---------------------------------")
    print('--------Art With Drones----------')
    print("---------------------------------")
    print('1. Gestor de drones')
    print('2. Unirse a espectáculo')
    print('3. Salir')

    return input('Elige una opción: ')

def menu():
    print()
    print("---------------------------------")
    print('--------GESTOR DE DRONES---------')
    print("---------------------------------")
    print('1. Crear dron')
    print('2. Editar dron')
    print('3. Eliminar dron')

    return input('Elige una opción: ')   

print("******* MENÚ DE DRON ************")

def crea_dron(client):
    print("---------------------------------")
    print('--------CREACION DE DRON---------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("1."+alias,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print("Tu token es "+respuesta.split(".")[1])
    return respuesta


def edita_dron(client):
    print("---------------------------------")
    print('--------CREACION DE DRON---------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron a editar: ')
    nuevo_alias = input('Introduce el nuevo alias: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("2."+alias+"."+nuevo_alias,client)
    respuesta = client.recv(2048).decode(FORMATO)

def elimina_dron(client):
    print("---------------------------------")
    print('--------ELIMINAR DRON------------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron a eliminar: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("3."+alias,client)
    respuesta = client.recv(2048).decode(FORMATO)

def envia_token(id_dron,token):
    ipEngine = sys.argv[1]
    puertoEngine = int(sys.argv[2])
    ADDR_eng = (ipEngine,puertoEngine)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR_eng)
    send(token,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print(respuesta)
    if respuesta == "OK":
        mueve_dron(id_dron)
        return True
    else:
        return False

def consume_comienzo(id_dron):
    consumer = KafkaConsumer(TOPIC_OK, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='espectaculo-group-'+id_dron)
    print(f"Esperando confirmacion de inicio del espectaculo...")
    ok=""
    for message in consumer:
        ok = message.value.decode('utf-8')
        print(ok)
        break
    return ok

def consume_pares(id_dron):
    # Configurar el consumidor de Kafka
    consumer = KafkaConsumer(TOPIC_PARES, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='pares-group-'+id_dron)
    print(f"Esperando posiciones finales del dron en el tópico '{TOPIC_PARES}'...")
    pares = ""
    # Consumir mensajes del tópico
    for message in consumer:
        pares = message.value.decode('utf-8')
        print(f"Pares recibidos: {pares}")
        break
    return pares

def imprimir_mapa(mapa):
    for fila in mapa:
        for casilla in fila:
            if casilla == 0:
                print(' ', end=' ')  
            else:
                print(casilla, end=' ')  
        print()  

def calcula_path(id_dron, pares):
    final = ()
    lista_pares = ast.literal_eval(pares)

    for pos in lista_pares:
        if pos[0] == id_dron:
            final = (pos[1]["x"],pos[1]["y"])

    x, y = 1, 1
    camino = []
    while x!=final[0] or y!= final[1]:
        if x < final[0] and y < final[1]:
            camino.append('SE')
            x += 1
            y += 1
        elif x < final[0]:
            camino.append('E')
            x += 1
        elif y < final[1]:
            camino.append('S')
            y += 1
        elif x > final[0] and y > final[1]:
            camino.append('NO')
            x -= 1
            y -= 1
        elif x > final[0]:
            camino.append('O')
            x -= 1
        elif y > final[1]:
            camino.append('N')
            y -= 1
        elif x < final[0] and y > final[1]:
            camino.append('SO')
            x += 1
            y -= 1
        elif x > final[0] and y < final[1]:
            camino.append('NE')
            x -= 1
            y += 1

    return camino

def consume_mapa(id_dron):
    consumer = KafkaConsumer(TOPIC_MAPA, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='mapa-group-'+id_dron)
    print("CONSUMIENDO MAPA")
    for message in consumer:
        mapa = message.value.decode('utf-8')
        mapa = json.loads(mapa)
        #imprimir_mapa(mapa)
        break

def envia_movimiento(movimiento):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    # Enviar el movimiento al tópico 'movimientos-dron'
    producer.send(TOPIC, value=movimiento)
    producer.flush()

def mueve_dron(id_dron):
    comienzo = ""
    #while comienzo != "OK":
    #    comienzo = consume_comienzo(id_dron)
    pares = consume_pares(id_dron)
    print("\n-------- MOVIMIENTO DE DRON --------")
    path = calcula_path(id_dron, pares)
    while True:
        move = path.pop(0)  # Selecciona el siguiente movimiento de la lista calculada
        id_dron = str(id_dron)
        mov = "" + id_dron + "," + move
        envia_movimiento(mov)
        print(f"Movimiento '{move}' enviado a Kafka.")
        consume_mapa(id_dron)
        time.sleep(3)

def main():
    if len(sys.argv[1:]) < 6:
        print("ARGUMENTOS INCORRECTOS: python3 AD_Drone.py <IP> <puerto> (Engine) <IP> <puerto> (Kafka) <IP> <puerto> (Registro)")
        return -1
    else:
        id_dron = 0
        token = ''
        conectado = False
        while conectado == False:
            opc = menu_inicio()

            if opc == '2':
                if token != '':
                    conectado = envia_token(id_dron,token)
                else:
                    print("Por favor, registrese!")
            elif opc == '1':
                ipRegistro = sys.argv[5]
                puertoRegistro = int(sys.argv[6])
                ADDR = (ipRegistro, puertoRegistro)
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDR)
                opc = menu()
                if opc == '2':
                    edita_dron(client)
                elif opc == '3':
                    elimina_dron(client)
                elif opc == '1':
                    respuesta = crea_dron(client)
                    id_dron = respuesta.split(".")[0]
                    token = respuesta.split(".")[1]
                    print("Dron creado con id: "+id_dron+" y token: "+token)
                else:
                    print("OPCIÓN INCORRECTA")
            elif opc == '3':
                sys.exit()
            else:
                print()
                print("OPCIÓN INCORRECTA")

if __name__ == "__main__":
    main()



