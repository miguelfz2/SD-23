import sqlite3
import socket
import threading
#import jwt
import datetime
import sys

FORMATO = 'utf-8'
conn = sqlite3.connect('') #Base de datos
cursor = conn.cursor() #Cursor para instrucciones en DB

#Obtenemos el ultimo id para crear el nuevo
def obtener_ultimo_id():
    cursor.execute('SELECT MAX(id) FROM drones')
    max_id = cursor.fetchone()[0]
    if max_id is not None:
        return max_id
    else:
        max_id = 0
        return max_id

#Generamos un token de acceso que utilizará el dron
def generar_token(id):
    payload = {   #Cabeceras con el id y el tiempo de expiracion
        'dron_id': id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365)
    }
    secret = "mi_id_es_"+id
    token = jwt.encode(payload, secret, algorithm='HS256') #Algoritmo sencillo para el encode
    token = "t"
    return token

#Registramos el dron con su alias y generamos el nuevo id (id+1), devolvemos el token de acceso
def registrar_dron(alias):
    #ultimo_id = obtener_ultimo_id()
    nuevo_id = 1#ultimo_id + 1
    token_acceso = generar_token(nuevo_id)
    #nuevo_dron = (nuevo_id, alias, token_acceso)
    #cursor.execute('INSERT INTO drones (id, alias, token_acceso) VALUES (?, ?, ?)', nuevo_dron)
    #conn.commit()    
    return token_acceso

#Funcion que obtiene el primer id de un alias
def obtener_id_por_alias(alias):
    cursor.execute('SELECT id FROM drones WHERE alias = ?', (alias,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else None

#Funcion que edita un alias en la base de datos
def editar_alias(alias, nuevo_alias):
    dron_id = obtener_id_por_alias(alias)
    if dron_id:
        cursor.execute('UPDATE drones SET alias = ? WHERE id = ?', (nuevo_alias, dron_id))
        conn.commit()
        return f"Alias del Dron ID '{dron_id}' editado a '{nuevo_alias}'"
    else:
        return "Dron no encontrado con el alias proporcionado."

#Funcion que se le pasa un alias, calcula el id y lo elimina de la DB
def eliminar_dron(alias):
    dron_id = obtener_id_por_alias(alias)
    if dron_id:
        cursor.execute('DELETE FROM drones WHERE id = ?', (dron_id,))
        conn.commit()
        return f"Dron con Alias '{alias}' eliminado exitosamente."
    else:
        return "Dron no encontrado con el alias proporcionado."


#Funcion para que AD_Register funcione como un servidor concurrente
def handle_client(client_socket):
    alias = client_socket.recv(2048).decode(FORMATO)
    opcion = alias.split(".")[0]
    alias = alias.split(".")[1]
    if len(alias.split(".")==3):
        nuevo_alias = alias.split(".")[2]
    print(f"Conexión establecida con el dron {alias}")
    print(f"Opcion {opcion}")
    if opcion == "1": 
        msg = "Creando dron."
        msg = msg.encode(FORMATO)
        client_socket.send(msg)
        token_acceso = registrar_dron(alias)
        #print(f"Dron registrado con ID '{obtener_ultimo_id() + 1}', Alias '{alias}'.")
        client_socket.send(token_acceso.encode())
        client_socket.close()
    elif opcion == "2":
        #msg = editar_alias(alias, nuevo_alias)
        client_socket.send(msg.encode(FORMATO))
    elif opcion == "3":
        msg = eliminar_dron(alias)
    else:
        s="s"
    
if len(sys.argv) != 2:
    print("Error: formato: script.py <puerto>")
    sys.exit(1)

try:
    server_port = int(sys.argv[1])
except ValueError:
    print("Por favor, introduce un número de puerto válido.")
    sys.exit(1)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = '127.0.0.1'

server_socket.bind((server_host, server_port))
server_socket.listen(5)

print(f"Esperando solicitudes de registro en {server_host}:{server_port}...")

while True:
    client_socket, client_address = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()


