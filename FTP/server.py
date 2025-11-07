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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5001))   # Bind to IP + Port
server.listen(1)                   # Listen for connections
print("Server waiting for connection...")


try:
    while True:
        conn, addr = server.accept()       # Accept connection
        print("Connected by", addr)
        conn.sendall(b"You Are Connected!")
        while True:
            data = conn.recv(1024).decode()         # Receive up to 1024 bytes
            if not data:
                break
            response = f"received {data}"
            conn.sendall(response.encode())
        conn.close()
finally:
    server.close()