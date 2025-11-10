"""
FTP Server Implementation

Protocol:
1. Create TCP socket
2. Bind IP + Port
3. Listen for connections
4. Send confirmation to client that connection is accepted
5. Await commands from client
   * LS  -> list files in server directory
   * GET -> sends copy of file to client
   * PUT -> receives file from client and saves to server directory
   * QUIT -> closes connection
"""

import os
import socket
import protocol

SERVER_FILE_DIR = os.path.join(os.path.dirname(__file__), 'server_files')
IP = '127.0.0.1'
PORT = 5002

COMMANDS = ["LS", "GET", "PUT", "QUIT"]

def validate_command(command):
    response_code = 200
    response = "OK"

    if command not in COMMANDS:
        response = f"Invalid Command, command: \"{command}\" unknown. "
        response_code = 400

    return response_code, response

def get_file_list():
    """Get list of files in server directory"""
    return os.listdir(SERVER_FILE_DIR)


def file_exists(filename):
    """Check if file exists in server directory"""
    return filename in get_file_list()


def get_file_path(filename):
    """Get full path to file in server directory"""
    return os.path.join(SERVER_FILE_DIR, filename)


def handle_ls(connection):
    """Handle LS command - list all files"""
    file_list = get_file_list()
    protocol.send_message(connection, {
        "type": "response",
        "code": 200,
        "message": "OK",
        "data": {"files": file_list}
    })
    print(f"LS: Sent {len(file_list)} files")


def handle_get(connection, filename):
    """Handle GET command - send file to client"""
    if not filename:
        protocol.send_message(connection, {
            "type": "response",
            "code": 400,
            "message": "Bad Request: filename required"
        })
        return

    if not file_exists(filename):
        protocol.send_message(connection, {
            "type": "response",
            "code": 404,
            "message": f"File Not Found: {filename}"
        })
        print(f"GET: File not found - {filename}")
        return

    # Send success response
    protocol.send_message(connection, {
        "type": "response",
        "code": 200,
        "message": "OK"
    })

    # Send the file
    filepath = get_file_path(filename)
    protocol.send_file(connection, filename, filepath)
    print(f"GET: Sent file - {filename}")


def handle_put(connection, filename):
    """Handle PUT command - receive file from client"""
    if not filename:
        protocol.send_message(connection, {
            "type": "response",
            "code": 400,
            "message": "Bad Request: filename required"
        })
        return

    # Send ready response
    protocol.send_message(connection, {
        "type": "response",
        "code": 200,
        "message": "Ready to receive file"
    })

    # Receive the file
    filepath = get_file_path(filename)
    result = protocol.recv_file(connection, filepath)

    if result:
        print(f"PUT: Received file - {filename} ({result['bytes_received']} bytes)")
    else:
        print(f"PUT: Failed to receive file - {filename}")


def serve():
    """Main server loop"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(1)
    print(f"Server listening on {IP}:{PORT}")
    print(f"Server directory: {SERVER_FILE_DIR}\n")

    try:
        while True:
            # Wait for connection
            connection, address = server.accept()
            print(f"Connected by {address}")

            # Send connection acknowledgment
            protocol.send_message(connection, {
                "type": "connection",
                "code": 200,
                "message": "Connection established"
            })

            # Handle client commands
            while True:
                # Receive command message
                msg = protocol.recv_message(connection)
                if not msg:
                    print("Client disconnected")
                    break

                # Parse command
                msg_type = msg.get("type")
                if msg_type != "command":
                    print(f"Unknown message type: {msg_type}")
                    continue

                client_command = msg.get("command", "").upper()
                filename = msg.get("filename")

                print(f"Received command: {client_command}" + (f" {filename}" if filename else ""))

                # Validate command
                response_code, response_msg = validate_command(client_command)

                if response_code != 200:
                    # Invalid command
                    protocol.send_message(connection, {
                        "type": "response",
                        "code": response_code,
                        "message": response_msg
                    })
                    continue

                # Execute command
                if client_command == "LS":
                    handle_ls(connection)

                elif client_command == "GET":
                    handle_get(connection, filename)

                elif client_command == "PUT":
                    handle_put(connection, filename)

                elif client_command == "QUIT":
                    protocol.send_message(connection, {
                        "type": "response",
                        "code": 200,
                        "message": "Goodbye"
                    })
                    print("Client requested disconnect")
                    break

            connection.close()
            print("Connection closed\n")

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    serve()
