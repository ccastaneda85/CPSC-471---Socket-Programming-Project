"""
1. Create TCP socket
2. Bind IP + Port
3. Listen for connections
4. Send Confirmation to client that connection is accepted
5. await commands from client
    * First receive command from client
    * Confirm valid command, if not valid, respond and await another command
        * if Valid Command, call function, and await another command
    * ls -> list files 
    * get -> sends copy of file
    * put -> receives file and places in folder
    * quit/exit -> closes connection
"""

import os
import socket

SERVER_FILE_DIR = os.path.join(os.path.dirname(__file__), 'server_files')
FILE_LIST = os.listdir(SERVER_FILE_DIR)

def parse_command(message):
    message = message.strip()
    if not message:
        return None, None

    parts = message.split(maxsplit=1)
    command = parts[0].upper()

    filename = parts[1] if len(parts) > 1 else None
    return command, filename

def list_director():
    return FILE_LIST

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5002))   # Bind to IP + Port
server.listen(1)                   # Listen for connections
print("Server waiting for connection...")


try:
    while True:
        conn, addr = server.accept()       # Accept connection
        print("Connected by", addr)
        conn.sendall(b"200: OK, Connection established")
        while True:
            message = conn.recv(1024).decode()         # Receive up to 1024 bytes
            if not message:
                break
            command, filename = parse_command(message)
            print(f"command: {command}, filename: {filename}")
            conn.sendall(f"{command} request received".encode())
        conn.close()
finally:
    server.close()