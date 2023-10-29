import socket
import sys
from kafka import KafkaProducer
from kafka import KafkaConsumer
import random
import sys
import json
import time

KAFKA_BOOTSTRAP_SERVERS = sys.argv[3]+':9092'  # La dirección de los brokers de Kafka
TOPIC = 'movimientos-dron'  # Nombre del tópico de Kafka
TOPIC_OK = 'espectaculo'

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
    print("\n-------- MOVIMIENTO DE DRON --------")
    movimientos = ['Norte', 'Sur', 'Este', 'Oeste']
    while True:
        movimiento = random.choice(movimientos)  # Selecciona un movimiento aleatorio
        envia_movimiento(movimiento)
        print(f"Movimiento '{movimiento}' enviado a Kafka.")
        time.sleep(3)

def main():
    if len(sys.argv[1:]) < 6:
        print("ARGUMENTOS INCORRECTOS: python3 AD_Drone.py <IP> <puerto> (Engine) <IP> <puerto> (Kafka) <IP> <puerto> (Registro)")
        return -1
    else:
        conectado = False
        while conectado == False:
            opc = menu_inicio()

            if opc == '2':
                token = input("Introduce tu token de dron: ")
                conectado = envia_token(token)
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
                    crea_dron(client)
                else:
                    print("OPCIÓN INCORRECTA")
            elif opc == '3':
                sys.exit()
            else:
                print()
                print("OPCIÓN INCORRECTA")

if __name__ == "__main__":
    main()


