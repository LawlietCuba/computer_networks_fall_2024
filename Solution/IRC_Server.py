import socket
import threading

import sys

class IRCServer:
    def __init__(self, host, port, central_host, central_port):
        self.host = host
        self.port = port
        self.central_host = central_host
        self.central_port = central_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.channels = {"General": []}

    # Logic for handling the central server connection
    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"IRC Server started at {self.host}:{self.port}, connecting to central server at {self.central_host}:{self.central_port}")
        except Exception as e:
            print(f"Error starting IRC Server: {e}")
            sys.exit(1)

        while True:
            client_socket, client_address = self.socket.accept()
            print(f"New connection from {client_address}")
            self.connections.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def connect_to_central_server(self):
        try:
            self.central_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.central_socket.connect((self.central_server_host, self.central_server_port))
            print(f"Conectado al servidor central en {self.central_server_host}:{self.central_server_port}")
            
            # Enviar información al servidor central, como el host y el puerto de este servidor IRC
            self.central_socket.sendall(f"Servidor IRC {self.host}:{self.port} está activo.\r\n".encode())
        except Exception as e:
            print(f"No se pudo conectar al servidor central: {e}")

    def handle_client(self, client_socket):
        client_socket.sendall("¡Bienvenido al servidor IRC local!\r\n".encode())
        self.join_channel(client_socket, "General")

        while True:
            try:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break
                print(f"Mensaje recibido: {data}")
                self.process_command(client_socket, data)
            except Exception as e:
                print(f"Error al manejar cliente: {e}")
                break

        self.disconnect_client(client_socket)

    def process_command(self, client_socket, message):
        parts = message.split(" ", 2)
        command = parts[0].upper()
        
        if command == "JOIN" and len(parts) > 1:
            self.join_channel(client_socket, parts[1])
        elif command == "PART" and len(parts) > 1:
            self.leave_channel(client_socket, parts[1])
        elif command == "MSG" and len(parts) > 2:
            self.send_message(client_socket, parts[1], parts[2])
        elif command == "NOTICE" and len(parts) > 2:
            self.send_notice(client_socket, parts[1], parts[2])
        elif command == "LIST":
            self.list_channels(client_socket)
        elif command == "NAMES" and len(parts) > 1:
            self.list_users_in_channel(client_socket, parts[1])
        elif command == "NICK" and len(parts) > 1:
            self.change_nickname(client_socket, parts[1])
        else:
            client_socket.sendall("Comando no reconocido\r\n".encode())

    def join_channel(self, client_socket, channel):
        if channel not in self.channels:
            self.channels[channel] = []
        if client_socket not in self.channels[channel]:
            self.channels[channel].append(client_socket)
        client_socket.sendall(f"Te has unido al canal {channel}\r\n".encode())

    def leave_channel(self, client_socket, channel):
        if channel in self.channels and client_socket in self.channels[channel]:
            self.channels[channel].remove(client_socket)
            client_socket.sendall(f"Has dejado el canal {channel}\r\n".encode())

    def send_message(self, sender_socket, target, message):
        if target in self.channels:
            for client_socket in self.channels[target]:
                if client_socket != sender_socket:
                    client_socket.sendall(f"Mensaje en {target}: {message}\r\n".encode())
        else:
            sender_socket.sendall(f"Canal {target} no encontrado\r\n".encode())

    def send_notice(self, sender_socket, target, notice):
        if target in self.channels:
            for client_socket in self.channels[target]:
                if client_socket != sender_socket:
                    client_socket.sendall(f"Notificación en {target}: {notice}\r\n".encode())
        else:
            sender_socket.sendall(f"Canal {target} no encontrado\r\n".encode())

    def list_channels(self, client_socket):
        client_socket.sendall("Lista de canales:\r\n".encode())
        for channel in self.channels:
            client_socket.sendall(f"- {channel}\r\n".encode())

    def list_users_in_channel(self, client_socket, channel):
        if channel in self.channels:
            users = [str(user.getpeername()) for user in self.channels[channel]]
            client_socket.sendall(f"Usuarios en {channel}: {', '.join(users)}\r\n".encode())
        else:
            client_socket.sendall(f"Canal {channel} no encontrado\r\n".encode())

    def change_nickname(self, client_socket, new_nickname):
        client_socket.sendall(f"Tu apodo ha sido cambiado a {new_nickname}\r\n".encode())

    def disconnect_client(self, client_socket):
        for channel in self.channels.values():
            if client_socket in channel:
                channel.remove(client_socket)
        self.connections.remove(client_socket)
        client_socket.close()
        print("Cliente desconectado")


def main():
    server_ip = "127.0.0.1"
    server_port = 6667
    central_server_host = "127.0.0.1"  
    central_server_port = 8888 

    irc_server = IRCServer(server_ip, server_port, central_server_host, central_server_port)
    irc_server.start()

if __name__ == "__main__":
    main()
