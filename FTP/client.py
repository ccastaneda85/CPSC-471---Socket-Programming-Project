import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5002))  # Connect to the server
data = client.recv(1024)    
print("Received:", data.decode())

while True:
    message = input("Begin Message: ")
    if message == "exit": break
    client.sendall(message.encode())   
    response = client.recv(1024).decode()
    print(f"Server Response: {response}")


client.close()