import socket
import sys
from kafka import KafkaProducer
from kafka import KafkaConsumer
import random
import sys
import time
import json

KAFKA_BOOTSTRAP_SERVERS = sys.argv[3]+':9092'  # La dirección de los brokers de Kafka
TOPIC = 'movimientos-dron'  # Nombre del tópico de Kafka
TOPIC_OK = 'espectaculo'
TOPIC_PARES = 'pares'
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
    print("Tu token es "+respuesta)
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
    print("Tu token es "+respuesta)
    return respuesta

def elimina_dron(client):
    print("---------------------------------")
    print('--------ELIMINAR DRON------------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron a eliminar: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("3."+alias,client)
    respuesta = client.recv(2048).decode(FORMATO)

def envia_token(token):
    ipEngine = sys.argv[1]
    puertoEngine = int(sys.argv[2])
    ADDR_eng = (ipEngine,puertoEngine)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR_eng)
    send(token,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print(respuesta)
    if respuesta == "OK":
        mueve_dron()
        return True
    else:
        return False

def consume_comienzo():
    consumer = KafkaConsumer(TOPIC_OK, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='espectaculo-group')
    print(f"Esperando confirmacion de inicio del espectaculo...")

    for message in consumer:
        ok = message.value.decode('utf-8')
        print(ok)
        if ok == 'OK':
            return True
        else:
            return False

def consume_pares():
    consumer = KafkaConsumer(TOPIC_PARES, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='pares-group')
    print(f"Esperando posiciones finales del dorn")
    for message in consumer:
        pares = message.value.decode('utf-8')
        print(pares)
        break

def imprimir_mapa(mapa):
    for fila in mapa:
        for casilla in fila:
            if casilla == 0:
                print(' ', end=' ')  
            else:
                print(casilla, end=' ')  
        print()  

def consume_mapa():
    consumer = KafkaConsumer(TOPIC_MAPA, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='mapa-group')
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

def mueve_dron():
    comienzo = False
    while comienzo == False:
        comienzo = consume_comienzo()
    consume_pares()
    print("\n-------- MOVIMIENTO DE DRON --------")
    movimientos = ['N', 'S', 'E', 'O']
    while True:
        movimiento = random.choice(movimientos)  # Selecciona un movimiento aleatorio
        envia_movimiento(movimiento)
        print(f"Movimiento '{movimiento}' enviado a Kafka.")
        consume_mapa()
        time.sleep(3)

def main():
    if len(sys.argv[1:]) < 6:
        print("ARGUMENTOS INCORRECTOS: python3 AD_Drone.py <IP> <puerto> (Engine) <IP> <puerto> (Kafka) <IP> <puerto> (Registro)")
        return -1
    else:
        id = 0
        token = ''
        conectado = False
        while conectado == False:
            opc = menu_inicio()

            if opc == '2':
                if token != '':
                    conectado = envia_token(token)
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
                    token = edita_dron(client)
                elif opc == '3':
                    elimina_dron(client)
                elif opc == '1':
                    token = crea_dron(client)
                else:
                    print("OPCIÓN INCORRECTA")
            elif opc == '3':
                sys.exit()
            else:
                print()
                print("OPCIÓN INCORRECTA")

if __name__ == "__main__":
    main()



