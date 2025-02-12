import argparse
import socket
import sys
import threading
import time

from IRC_Server import IRCServer

def main():
    parser = argparse.ArgumentParser(description="Cliente IRC")
    parser.add_argument("-H", "--host", required=True, help="Dirección IP del servidor")
    parser.add_argument("-p", "--port", type=int, required=True, help="Puerto del servidor")
    parser.add_argument("-n", "--nick", required=True, help="Nickname del usuario")
    parser.add_argument("-c", "--command", required=True, help="Comando a ejecutar (NICK, JOIN, PART, MSG, NOTICE, LIST, NAMES)")
    parser.add_argument("-a", "--argument", required=True, help="Argumento del comando")
    args = parser.parse_args()
    
    irc_server = IRCServer(args.host, args.port)
    server_thread = threading.Thread(target=irc_server.start, daemon=True)
    server_thread.start()
    
    time.sleep(1)

    # Crear el socket y conectar con el servidor IRC.
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.host, args.port))
    except Exception as e:
        print(f"Error al conectar al servidor: {e}")
        sys.exit(1)

    try:
        # Si el comando principal NO es NICK, primero se envía el comando NICK para identificarse.
        if args.command.upper() != "NICK":
            nick_message = f"/NICK {args.nick}\r\n"
            irc_server.process_command(client_socket, nick_message)

        # El formato esperado por el servidor es: /<COMMAND> <ARGUMENT>
        command_message = f"{args.command} {args.argument}\r\n"
        
        print(command_message)
        
        irc_server.process_command(client_socket, command_message)

    except Exception as e:
        print(f"Error al enviar/recibir datos: {e}")
    finally:
        # server_thread.join()
        irc_server.shutdown()

if __name__ == "__main__":
    main()
