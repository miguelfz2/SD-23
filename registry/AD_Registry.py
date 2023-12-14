import sqlite3
import socket
import threading
import datetime
import sys
import ssl

from flask import Flask, jsonify, request, send_file
from modulefinder import Module

FORMATO = 'utf-8'

app = Flask(__name__)

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
    cursor.execute("DELETE FROM logs;")

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
    try:
        ultimo_id = obtener_ultimo_id(cursor)
        nuevo_id = ultimo_id + 1
        token_acceso = generar_token(nuevo_id)
        pos = "(1, 1)"
        nuevo_dron = (nuevo_id, alias, token_acceso, pos)
        cursor.execute('INSERT INTO dron (id, alias, token, posicion) VALUES (?, ?, ?, ?)', nuevo_dron)
        #cursor.connection.commit()
    except Exception as e:
        print(e)
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

@app.route('/registrar', methods=['POST'])
def insertar_dron_api():
    try:
        ip = request.remote_addr
        # Establecer una nueva conexión y cursor para cada hilo
        conexion = obtener_conexion()
        cursor = obtener_cursor(conexion)
        alias = request.args.get('data')
        token_acceso = registrar_dron(alias, cursor)
        id_dron = obtener_ultimo_id(cursor)

        # Enviar una respuesta al cliente
        respuesta = {
            'id_dron': id_dron,
            'token_acceso': token_acceso
        }
        conexion.commit()
        conexion.close()

        return jsonify(respuesta)

    except Exception as e:
        print(e)
        # Manejar errores y enviar una respuesta de error al cliente si es necesario
        return jsonify({'error': str(e)}), 500

@app.route('/editar', methods=['PUT'])
def editar_dron_api():
    try:
        ip = request.remote_addr
        # Establecer una nueva conexión y cursor para cada hilo
        conexion = obtener_conexion()
        cursor = obtener_cursor(conexion)
        alias = request.args.get('data')
        nuevo = request.args.get('nuevo')
        id_dron = obtener_ultimo_id(cursor)
        msg = editar_alias(alias, nuevo, cursor)

        # Enviar una respuesta al cliente
        respuesta = {
            'mensaje': msg,
        }
        conexion.commit()
        conexion.close()

        return jsonify(respuesta)

    except Exception as e:
        # Manejar errores y enviar una respuesta de error al cliente si es necesario
        return jsonify({'error': str(e)}), 500


@app.route('/eliminar', methods=['DELETE'])
def eliminar_dron_api():
    try:
        ip = request.remote_addr
        # Establecer una nueva conexión y cursor para cada hilo
        conexion = obtener_conexion()
        cursor = obtener_cursor(conexion)
        alias = request.args.get('data')
        msg = eliminar_dron(alias, cursor)

        # Enviar una respuesta al cliente
        respuesta = {
            'mensaje': msg,
        }
        conexion.commit()
        conexion.close()

        return jsonify(respuesta)

    except Exception as e:
        # Manejar errores y enviar una respuesta de error al cliente si es necesario
        return jsonify({'error': str(e)}), 500

def handle_api():
    try:
        app.run(debug=False, port=8234, host="0.0.0.0", ssl_context=('claves/certificado_registro.pem','claves/clave_registro.key'))
    except Exception as e:
        print(e)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='claves/certificado_registro.pem', keyfile="claves/clave_registro.key")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = '192.168.1.220'
server_socket.bind((server_host, server_port))
server_socket.listen(5)

borrar_db()
print(f"Esperando solicitudes de registro en {server_host}:{server_port}...")
api_thread = threading.Thread(target=handle_api, args=[])
api_thread.start()

while True:
    client_socket, client_address = server_socket.accept()
    ssl_socket = context.wrap_socket(client_socket, server_side=True)

    client_thread = threading.Thread(target=handle_client, args=(ssl_socket,))
    client_thread.start()
