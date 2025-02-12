import argparse
import socket
import sys
import threading
import time

from IRC_Server import IRCServer

def main():
    test_input = sys.argv[1:]
    server_ip, port, nickname, command, argument = test_input[1],int(test_input[3]),test_input[5],'/'+test_input[7].split('/').pop(),test_input[9:]
    argument = ' '.join(argument)
    
    irc_server = IRCServer(server_ip, port)
    server_thread = threading.Thread(target=irc_server.start, daemon=False)
    server_thread.start()
    
    time.sleep(1)

    # Crear el socket y conectar con el servidor IRC.
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
    except Exception as e:
        print(f"Error al conectar al servidor: {e}")
        sys.exit(1)

    try:
        # # Si el comando principal NO es NICK, primero se envía el comando NICK para identificarse.
        # if nickname not in irc_server.nicknames and command.upper() != "NICK":
        #     nick_message = f"/NICK {nickname}\r\n"
            irc_server.process_command(client_socket, nick_message)
            irc_server.process_command(client_socket, "/JOIN #General\r\n")
            
        time.sleep(1)

        # El formato esperado por el servidor es: /<COMMAND> <ARGUMENT>
        command_message = f"{command} {argument}\r\n"
        
        irc_server.process_command(client_socket, command_message)

    except Exception as e:
        print(f"Error al enviar/recibir datos: {e}")
        
    finally:
        irc_server.shutdown()

if __name__ == "__main__":
    main()
