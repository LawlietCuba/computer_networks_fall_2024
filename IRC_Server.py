# import argparse
import socket
import threading
import sys

class IRCServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []          # Lista de sockets conectados
        self.channels = {"#General": []}  # Diccionario de canales: canal -> lista de sockets
        self.nicknames = {}            # Diccionario: socket -> nickname
        self.running = False

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Servidor escuchando en {self.host}:{self.port}")
        except Exception as e:
            print(f"Error starting IRC Server: {e}")
            sys.exit(1)

        self.running = True
        while self.running:
            try:
                client_socket, client_address = self.socket.accept()
            except socket.timeout:
                # Timeout occurred, check if we should keep running.
                continue
            except OSError:
                # Socket has been closed, exit loop.
                break
            
            print(f"Nueva conexión desde {client_address}")
            self.connections.append(client_socket)
            # Asignamos un nombre por defecto (por ejemplo, la dirección) hasta que se envíe /NICK
            self.nicknames[client_socket] = f"{client_address}"
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        
    def handle_client(self, client_socket):
        # Enviar mensaje de bienvenida
        # client_socket.sendall("¡Bienvenido al servidor IRC local!\r\n".encode())
        # Unirse automáticamente al canal "General"
        self.join_channel(client_socket, "General")

        while True:
            try:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break
                print(data)
                self.process_command(client_socket, data)
            except Exception as e:
                print(f"Error al manejar cliente: {e}")
                break

        self.disconnect_client(client_socket)
        
    def process_command(self, client_socket, message):
        if not message.startswith("/"):
            client_socket.sendall("Comando no válido. Los comandos deben comenzar con '/'.\r\n".encode())
            return  
        
        # Se elimina la barra inicial y se separa el comando y sus argumentos
        message = message[1:]
        parts = message.split(" ", 2)
        command = parts[0].upper()
        
        # print(self.nicknames.get(client_socket, "Anonimo"), command)
        
        if command == "JOIN" and len(parts) > 1:
            self.join_channel(client_socket, parts[1])
        elif command == "PART" and len(parts) > 1:
            self.leave_channel(client_socket, parts[1])
        elif command == "PRIVMSG" and len(parts) > 2:
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
        if not channel.startswith("#"):
            client_socket.sendall("Comando no válido. Los canales deben comenzar con '#'.\r\n".encode())
            return  
        if channel not in self.channels:
            self.channels[channel] = []
        if client_socket not in self.channels[channel]:
            self.channels[channel].append(client_socket)
        client_socket.sendall(f"Te has unido al canal {channel}\r\n".encode())

    def leave_channel(self, client_socket, channel):
        if channel in self.channels and client_socket in self.channels[channel]:
            self.channels[channel].remove(client_socket)
            client_socket.sendall(f"Has salido del canal {channel}\r\n".encode())

    def send_message(self, sender_socket, target, message):
        sender_nick = self.nicknames.get(sender_socket, "Anónimo")
        for client_socket, nickname in self.nicknames.items():
                if nickname == target:
                    client_socket.sendall(f"Mensaje privado de {sender_nick}: {message}\r\n".encode())
                    return
            
        # Si no se encuentra ni canal ni usuario
        sender_socket.sendall(f"Destino {target} no encontrado\r\n".encode())

    def send_notice(self, sender_socket, target, notice):
        sender_nick = self.nicknames.get(sender_socket, "Anónimo")
        if target in self.channels:
            for client_socket in self.channels[target]:
                if client_socket != sender_socket:
                    # client_socket.sendall(f"Notificación de {sender_nick} en {target}: {notice}\r\n".encode())
                    client_socket.sendall(f"Notificacion de {sender_nick}: {notice} \r\n".encode())
        else:
            sender_socket.sendall(f"Canal {target} no encontrado\r\n".encode())

    def list_channels(self, client_socket):
        response = "Lista de canales:\r\n"
        for channel in self.channels:
            response += f"- {channel}\r\n"
        client_socket.sendall(response.encode())

    def list_users_in_channel(self, client_socket, channel):
        if channel in self.channels:
            # Se muestra el nick del usuario, o si no se ha establecido, se muestra la dirección
            users = [self.nicknames.get(user, str(user.getpeername())) for user in self.channels[channel]]
            client_socket.sendall(f"Usuarios en {channel}: {', '.join(users)}\r\n".encode())
        else:
            client_socket.sendall(f"Canal {channel} no encontrado\r\n".encode())

    def change_nickname(self, client_socket, new_nickname):
            self.nicknames[client_socket] = new_nickname
            client_socket.sendall(f"Tu nuevo apodo es {new_nickname}\r\n".encode())

    def disconnect_client(self, client_socket):
        # Remover el cliente de todos los canales
        for channel in self.channels.values():
            if client_socket in channel:
                channel.remove(client_socket)
        if client_socket in self.connections:
            self.connections.remove(client_socket)
        if client_socket in self.nicknames:
            del self.nicknames[client_socket]
        client_socket.close()
        print("Cliente desconectado")
        
    def shutdown(self):
        self.running = False
        self.socket.close()