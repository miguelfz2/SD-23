import sqlite3
import socket
import threading
import datetime
import sys

FORMATO = 'utf-8'



def obtener_conexion():
    return sqlite3.connect('drones.db')  # Base de datos

def obtener_cursor(conexion):
    return conexion.cursor()  # Cursor para instrucciones en DB

def borrar_db():
    conexion = sqlite3.connect("drones.db")

    # Crear un cursor para ejecutar comandos SQL
    cursor = conexion.cursor()

    # Comando SQL para borrar el contenido de la tabla dron
    sql_query = "DELETE FROM dron;"

    # Ejecutar el comando SQL
    cursor.execute(sql_query)

    # Confirmar los cambios y cerrar la conexión
    conexion.commit()
    conexion.close()


def obtener_ultimo_id(cursor):
    cursor.execute('SELECT MAX(id) FROM dron')
    resultado = cursor.fetchone()[0]
    return resultado if resultado is not None else 0

def generar_token(id):
    str_id = str(id)
    token = "token"+str_id  
    return token

def registrar_dron(alias, cursor):
    ultimo_id = obtener_ultimo_id(cursor)
    nuevo_id = ultimo_id + 1
    token_acceso = generar_token(nuevo_id)
    nuevo_dron = (nuevo_id, alias, token_acceso)
    cursor.execute('INSERT INTO dron (id, alias, token) VALUES (?, ?, ?)', nuevo_dron)
    return token_acceso

def obtener_id_por_alias(alias, cursor):
    cursor.execute('SELECT id FROM dron WHERE alias = ?', (alias,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else None

def editar_alias(alias, nuevo_alias, cursor):
    dron_id = obtener_id_por_alias(alias, cursor)
    if dron_id:
        cursor.execute('UPDATE dron SET alias = ? WHERE id = ?', (nuevo_alias, dron_id))
        return f"Alias del Dron ID '{dron_id}' editado a '{nuevo_alias}'"
    else:
        return "Dron no encontrado con el alias proporcionado."

def eliminar_dron(alias, cursor):
    dron_id = obtener_id_por_alias(alias, cursor)
    if dron_id:
        cursor.execute('DELETE FROM dron WHERE id = ?', (dron_id,))
        return f"Dron con Alias '{alias}' eliminado exitosamente."
    else:
        return "Dron no encontrado con el alias proporcionado."

def handle_client(client_socket):
    datos = client_socket.recv(2048).decode(FORMATO)
    opcion = datos.split(".")[0]
    alias = datos.split(".")[1]
    if len(datos.split("."))==3:
        nuevo_alias = datos.split(".")[2]  
    # Establecer una nueva conexión y cursor para cada hilo
    conexion = obtener_conexion()
    cursor = obtener_cursor(conexion)

    print(f"Conexión establecida con el dron {alias}")
    print(f"Opcion {opcion}")
    
    if opcion == "1":
        token_acceso = registrar_dron(alias, cursor)
        print(f"Dron registrado con ID '{obtener_ultimo_id(cursor)}', Alias '{alias}'.")
        respuesta = str(obtener_ultimo_id(cursor)) + "." + token_acceso
        client_socket.send(respuesta.encode(FORMATO))
    elif opcion == "2":
        msg = editar_alias(alias, nuevo_alias, cursor)
        client_socket.send(msg.encode(FORMATO))
    elif opcion == "3":
        msg = eliminar_dron(alias, cursor)
        client_socket.send(msg.encode(FORMATO))
    else:
        msg = "Opción no válida."
        client_socket.send(msg.encode(FORMATO))

    # Cerrar la conexión después de realizar la operación
    conexion.commit()
    conexion.close()
    client_socket.close()

if len(sys.argv) != 2:
    print("Error: formato: script.py <puerto>")
    sys.exit(1)

try:
    server_port = int(sys.argv[1])
except ValueError:
    print("Por favor, introduce un número de puerto válido.")
    sys.exit(1)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = 'localhost'  
server_socket.bind((server_host, server_port))
server_socket.listen(5)

borrar_db()
print(f"Esperando solicitudes de registro en {server_host}:{server_port}...")

while True:
    client_socket, client_address = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()
