import os
import socket
import commands as command
import json

SERVER_FILE_DIR = os.path.join(os.path.dirname(__file__), 'server_files')
FILE_LIST = os.listdir(SERVER_FILE_DIR)
IP = '127.0.0.1'
PORT = 5002


def file_in_directory(filename):
    return True if filename in FILE_LIST else False

def get_file_path(file_name):
    return os.path.join(SERVER_FILE_DIR, file_name)

def send_file(file_path, connection):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break   
            connection.sendall(chunk)

def serve():
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))   # Bind to IP + Port
    server.listen(1)                   # Listen for connections
    print("Server waiting for connection...")

    try:
        while True:
            #Await connection
            connection, address = server.accept()
            print("Connected by", address)
            
            #Acknowledge Client Connection            
            connection.sendall(b"200: OK, Connection established")
            
            # Client Connected. Loop Begins:
            while True:
                message = connection.recv(1024).decode()
                if not message:
                    break
                
                #Parse client command
                client_command, filename = command.parse(message)

                #validate Command
                response_code, response = command.validate(client_command)
                
                #send response code
                connection.sendall(response_code.encode())

                #if good reqest
                if response_code == 200:
                    if client_command == "LS":
                        payload = json.dumps(FILE_LIST)
                        connection.sendall(payload.encode())
                    break
                    
            


            connection.close()
    finally:
        server.close()
    

if __name__ == "__main__":
    serve()