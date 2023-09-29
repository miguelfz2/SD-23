import socket
import sys

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


def edita_dron(client):
    print("---------------------------------")
    print('--------CREACION DE DRON---------')
    print("---------------------------------")
    alias = input('Introduce el alias del dron a editar: ')
    #ENVIAMOS EL ALIAS AL SOCKET
    send("2."+alias,client)
    respuesta = client.recv(2048).decode(FORMATO)
    print("Tu token es "+respuesta)

"""
def elimina_dron(client):
    send()
"""

def main():
    if len(sys.argv[1:]) < 2:
        print('ARGUMENTOS INCORRECTOS: python3 AD_Drone.py <IP> <puerto>')
        return -1
    else:
        opc = menu()
        print(opc)
       	ip = sys.argv[1]
        puerto =int(sys.argv[2])
        ADDR = (ip,puerto)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        if opc == '1':
            crea_dron(client)
        elif opc == '2':
            edita_dron(client)
        elif opc == '3':
            elimina_dron(client)
        else:
            print("OPCIÓN INCORRECTA")
        

if __name__ == "__main__":
    main()
