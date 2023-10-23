import socket
import sqlite3
import threading
from kafka import KafkaProducer
import time

# Ruta de la base de datos
DB_FILE = r'C:\Users\ayelo\OneDrive\Documentos\GitHub\SD-23\registry\drones.db'

# Función para verificar el token y el alias en la base de datos
def verificar_registro(token):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dron WHERE token=?', (token,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def servir_mapa():
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    topic = 'SD'

    try:
        while True:
            # Simula la generación de un par de posiciones
            posiciones = [(1, 2), (3, 4), (5, 6)]

            for posicion in posiciones:
                # Envía el par de posiciones al topic 'posiciones'
                producer.send(topic, value=str(posicion))
                time.sleep(1)  # Pausa para simular la generación de posiciones cada 1 segundo

    except KeyboardInterrupt:
        pass
    finally:
        producer.close()

# Función que maneja las conexiones de los clientes
def handle_client(client_socket, addr):
    print(f"Cliente conectado desde {addr}")
    
    # Recibir datos del cliente (token y alias)
    data = client_socket.recv(1024).decode('utf-8')
    token = data
    print(token)
    
    # Verificar el registro en la base de datos
    if verificar_registro(token):
        # Cliente registrado, enviar mensaje de OK
        client_socket.send('OK'.encode('utf-8'))
        servir_mapa()
    else:
        # Cliente no registrado, enviar mensaje para registrarse
        client_socket.send('Por favor, regístrese.'.encode('utf-8'))
    
    # Cerrar la conexión con el cliente
    client_socket.close()
    print(f"Cliente {addr} desconectado.")

# Configurar el socket del servidor
HOST = 'localhost'  # Dirección IP del servidor
PORT = 12345         # Puerto del servidor

def main():
        # Crear un socket de servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Servidor en el puerto {PORT} esperando conexiones...")

    try:
        while True:
            # Esperar a que un cliente se conecte
            client_socket, addr = server_socket.accept()
            
            # Crear un nuevo subproceso para manejar la conexión del cliente
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()

    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        # Cerrar el socket del servidor al finalizar
        server_socket.close()

if __name__ == "__main__":
    main()
