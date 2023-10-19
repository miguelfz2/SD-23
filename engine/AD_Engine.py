import socket
import sys
import threading

HEADER = 64
PORT = int(sys.argv[1])
SERVER = 'localhost'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def recibe_token(conn,addr):
    print(f"[NUEVA CONEXION] {addr} connected.")

    connected = True
    while connected:
        token = conn.recv(HEADER).decode(FORMAT)
        #print(f"El token es {token}".encode(FORMAT))
        #connected = False
        ###COMPROBAR TOKEN EN BBDD
        #if valida_token(token) == True:
            #connected = False
            #conn.send(f"HOLA DRON: token correcto!!!: {token} ".encode(FORMAT))
        #else:
        #   connected = False
        #   conn.send(f"ERROR: TOKEN NO EXISTENTE!!!".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()


#def valida_token(token):
    ##BUSCAR EN LA BD EL TOKEN Y DEVOLVER TRUE SI SE ENCUENTRA, FALSE EN CASO CONTRARIO

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count()-1
    MAX_CONEXIONES = int(sys.argv[2])
    print(CONEX_ACTIVAS)
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES):
            thread = threading.Thread(target=recibe_token, args=(conn, addr))
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")
            print("DRONES RESTANTES PARA EMPEZAR EL ESPECTÁCULO: ", MAX_CONEXIONES-CONEX_ACTIVAS)
        else:
            print("FLOTA DE DRONES COMPLETA. A LA ESPERA DE ALGUNA BAJA PARA RETOMAR CONEXIONES.")
            conn.send("OOppsss... DEMASIADAS CONEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
            conn.close()
            CONEX_ACTUALES = threading.active_count()-1


def main():
    server.bind(ADDR)
    print("[STARTING] Servidor inicializándose...")
    start()


if __name__ == "__main__":
    main()
