import socket
import commands as command
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5002))  # Connect to the server
data = client.recv(1024)    
print("Received:", data.decode())

commands = ["LS", "GET", "PUT"]

def valid_command(command):
    if command in commands:
        return True
    else:
        return False


while True:
    
    message = input("Enter \"exit\" to disconnect \n")
    
    if message == "exit": break
    
    while True:
        #Parse Client Command
        client_command, filename = command.parse(message)

        #Validate Command
        if not valid_command(client_command):
            print(f"Error, command: {client_command} unknown")
            break
        else:
            if client_command == "LS":
                
                #send message
                client.sendall(message.encode())
                
                #get response code
                response_code = client.recv(1024).decode()
                
                response_payload = client.recv(4096).decode()
                

                #If request is acknowledged
                if response_code == "200":
                    file_list = json.loads(response_payload)
                    for file in file_list:
                        print(file)
                    break
                else: #bad request
                    print(f"{response_code}: {response_payload}")
                    break


client.close()

