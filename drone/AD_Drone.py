import socket
import sys
from kafka import KafkaProducer
import random
import sys

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'  # La dirección de los brokers de Kafka
TOPIC = 'movimientos-dron'  # Nombre del tópico de Kafka

FORMATO = 'utf-8'
CABECERA = 64

def send(code,client):
    msg = code.encode(FORMATO)
    client.send(msg)

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
    envia_token(respuesta)


def edita_dron(client):
    print("---------------------------------")
    print('--------CREACION DE DRON---------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron a editar: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("2."+alias,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print("Tu token es "+respuesta)
    envia_token(respuesta)

def envia_token(token):
    ipEngine = sys.argv[1]
    puertoEngine = int(sys.argv[2])
    ADDR_eng = (ipEngine,puertoEngine)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR_eng)
    send(token,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print(respuesta)
    



def elimina_dron(client):
    #send()
    print("")

def envia_movimiento(movimiento):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             value_serializer=lambda v: str(v).encode('utf-8'))

    # Enviar el movimiento al tópico 'movimientos-dron'
    producer.send(TOPIC, value=movimiento)
    producer.flush()

def mueve_dron():
    print("\n-------- MOVIMIENTO DE DRON --------")
    movimientos = ['Norte', 'Sur', 'Este', 'Oeste']
    movimiento = random.choice(movimientos)  # Selecciona un movimiento aleatorio
    envia_movimiento(movimiento)
    print(f"Movimiento '{movimiento}' enviado a Kafka.")

def main():
    if len(sys.argv[1:]) < 6:
        print("ARGUMENTOS INCORRECTOS: python3 cliente.py <IP> <puerto> (Engine) <IP> <puerto> (Kafka) <IP> <puerto> (Registro)")
        return -1
    else:
        ipRegistro = sys.argv[5]
        puertoRegistro = int(sys.argv[6])
        ADDR = (ipRegistro, puertoRegistro)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        while True:
            opc = menu()

            if opc == '1':
                crea_dron(client)
            elif opc == '2':
                edita_dron(client)
            elif opc == '3':
                elimina_dron(client)
            elif opc == '4':
                mueve_dron()
            else:
                print("OPCIÓN INCORRECTA")

if __name__ == "__main__":
    main()


