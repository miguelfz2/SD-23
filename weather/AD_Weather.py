import socket

HOST = 'localhost'
PORT = 8010

my_socket=socket.socket()
my_socket.bind((HOST, PORT))
my_socket.listen(5)

def buscar_bd(ciudad):
    resultado = ""
    try:
        with open("./bd_weather.txt", 'r') as file:
            for linea in file:
                if ciudad in linea:
                    partes = linea.split(" ")
                    if len(partes) > 1:
                        resultado = partes[-1].strip()
                    break
    except FileNotFoundError:
        print("ERROR: NO EXISTE LA BD")

    return resultado

print ("Servidor clima creado y a la escucha en ", HOST, " ", PORT )

while True:
    conexion, addr = my_socket.accept()

    print ("Nueva conexion")
    print (addr)

    pet=conexion.recv(4096)
    ciudad = pet.decode()
    print ("Recibido: ", ciudad)
    resultado = buscar_bd(ciudad)
    if resultado != "":
        conexion.send(resultado.encode('utf-8')
    else:
        conexion.send("CIUDAD NO ENCONTRADA".encode('utf-8'))

