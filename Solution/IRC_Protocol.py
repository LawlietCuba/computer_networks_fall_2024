import socket
import ssl
import threading

class IRCClient:
    def __init__(self, host, port, nickname, use_ssl):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.connected = False
        self.use_ssl = use_ssl
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if self.use_ssl:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.check_hostname = False  # Permite conexiones sin verificación de hostname
            ssl_context.verify_mode = ssl.CERT_NONE  # Permite conexiones sin certificado
            self.socket = ssl_context.wrap_socket(self.socket, server_hostname=self.host)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.socket.sendall(f"NICK {self.nickname}\r\n".encode())
            self.socket.sendall(f"USER {self.nickname} 0 * :{self.nickname}\r\n".encode())
        except Exception as e:
            print(f"Error al conectar: {e}")
            self.connected = False
    
    def send_message(self, message):
        if self.connected:
            try:
                self.socket.sendall(f"{message}\r\n".encode())
            except Exception as e:
                print(f"Error al enviar mensaje: {e}")

    def receive_messages(self):
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    continue
                buffer += data.decode('utf-8', errors='replace')
                while "\r\n" in buffer:
                    message, buffer = buffer.split("\r\n", 1)
                    self.handle_message(message)
            except Exception as e:
                print(f"Error al recibir mensaje: {e}")
                self.connected = False
                break

    def handle_message(self, message):
        parts = message.split(" ")
        if parts[0] == "PING":
            self.send_message(f"PONG {parts[1]}")
        print(message)

    def process_command(self, command):
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        
        if cmd == "/join" and len(parts) > 1:
            self.send_message(f"JOIN {parts[1]}")
        elif cmd == "/msg" and len(parts) > 1:
            target_message = parts[1].split(' ', 1)
            if len(target_message) > 1:
                self.send_message(f"PRIVMSG {target_message[0]} msg:{target_message[1]}")
        elif cmd == "/nick" and len(parts) > 1:
            self.send_message(f"NICK {parts[1]}")
        elif cmd == "/list":
            self.send_message(f"LIST")
        else:
            print("Comando desconocido o faltan argumentos.")

def main():
    server_ip = input("Ingrese la dirección IP del servidor: ")
    port = int(input("Ingrese el puerto: "))
    nickname = input("Ingrese su apodo: ")
    usar_ssl = input("Ingrese 1 para usar conexión segura, 2 para conexión normal: ")
    use_ssl = usar_ssl == '1'
    
    irc_client = IRCClient(server_ip, port, nickname, use_ssl)
    irc_client.connect()
    
    if irc_client.connected:
        print(f"Conectado como {nickname}")
        threading.Thread(target=irc_client.receive_messages, daemon=True).start()
        
        while True:
            user_input = input()
            if user_input.startswith('/'):
                irc_client.process_command(user_input)
            else:
                irc_client.send_message(user_input)
    else:
        print("No se pudo conectar al servidor.")

if __name__ == "__main__":
    main()
