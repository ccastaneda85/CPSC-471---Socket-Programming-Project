"""
FTP Client Implementation

Commands:
* LS        -> list files on server
* GET <file> -> download file from server
* PUT <file> -> upload file to server
* QUIT      -> disconnect from server
"""

import os
import socket
import protocol

CLIENT_FILE_DIR = os.path.join(os.path.dirname(__file__), 'client_files')
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5002

VALID_COMMANDS = ["LS", "GET", "PUT", "QUIT"]


def get_file_path(filename):
    """Get full path to file in client directory"""
    return os.path.join(CLIENT_FILE_DIR, filename)


def file_exists(filename):
    """Check if file exists in client directory"""
    filepath = get_file_path(filename)
    return os.path.exists(filepath)


def parse_input(user_input):
    """Parse user input into command and filename"""
    parts = user_input.strip().split(maxsplit=1)
    if not parts:
        return None, None

    command = parts[0].upper()
    filename = parts[1] if len(parts) > 1 else None
    return command, filename


def handle_ls(client):
    """Handle LS command - list files on server"""
    # Send command
    protocol.send_message(client, {
        "type": "command",
        "command": "LS"
    })

    # Receive response
    response = protocol.recv_message(client)
    if not response:
        print("Error: Connection lost")
        return False

    if response["code"] == 200:
        files = response.get("data", {}).get("files", [])
        print(f"\nServer files ({len(files)}):")
        for file in files:
            print(f"  - {file}")
    else:
        print(f"Error {response['code']}: {response['message']}")

    return True


def handle_get(client, filename):
    """Handle GET command - download file from server"""
    if not filename:
        print("Error: GET requires a filename")
        return True

    # Send command
    protocol.send_message(client, {
        "type": "command",
        "command": "GET",
        "filename": filename
    })

    # Receive response
    response = protocol.recv_message(client)
    if not response:
        print("Error: Connection lost")
        return False

    if response["code"] != 200:
        print(f"Error {response['code']}: {response['message']}")
        return True

    # Receive file
    filepath = get_file_path(filename)
    result = protocol.recv_file(client, filepath)

    if result:
        print(f"Downloaded: {filename} ({result['bytes_received']} bytes)")
    else:
        print(f"Error: Failed to download {filename}")

    return True


def handle_put(client, filename):
    """Handle PUT command - upload file to server"""
    if not filename:
        print("Error: PUT requires a filename")
        return True

    if not file_exists(filename):
        print(f"Error: File not found: {filename}")
        return True

    # Send command
    protocol.send_message(client, {
        "type": "command",
        "command": "PUT",
        "filename": filename
    })

    # Receive response
    response = protocol.recv_message(client)
    if not response:
        print("Error: Connection lost")
        return False

    if response["code"] != 200:
        print(f"Error {response['code']}: {response['message']}")
        return True

    # Send file
    filepath = get_file_path(filename)
    protocol.send_file(client, filename, filepath)
    print(f"Uploaded: {filename}")

    return True


def handle_quit(client):
    """Handle QUIT command - disconnect from server"""
    protocol.send_message(client, {
        "type": "command",
        "command": "QUIT"
    })

    # Receive response
    response = protocol.recv_message(client)
    if response:
        print(response.get("message", "Disconnected"))

    return False


def main():
    """Main client loop"""
    # Connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((SERVER_IP, SERVER_PORT))
        print(f"Connecting to {SERVER_IP}:{SERVER_PORT}...")

        # Receive connection acknowledgment
        ack = protocol.recv_message(client)
        if ack:
            print(f"{ack.get('message', 'Connected')}\n")

        # Command loop
        print("Available commands: LS, GET <file>, PUT <file>, QUIT")
        print("Client directory:", CLIENT_FILE_DIR)
        print()

        while True:
            try:
                user_input = input("ftp> ")
                if not user_input.strip():
                    continue

                command, filename = parse_input(user_input)

                if not command:
                    continue

                # Execute command
                if command == "LS":
                    if not handle_ls(client):
                        break

                elif command == "GET":
                    if not handle_get(client, filename):
                        break

                elif command == "PUT":
                    if not handle_put(client, filename):
                        break

                elif command == "QUIT":
                    handle_quit(client)
                    break

                else:
                    print(f"Unknown command: {command}")
                    print("Available commands: LS, GET <file>, PUT <file>, QUIT")

            except KeyboardInterrupt:
                print("\nInterrupted. Use QUIT to disconnect properly.")
                continue

    except ConnectionRefusedError:
        print(f"Error: Could not connect to server at {SERVER_IP}:{SERVER_PORT}")
        print("Make sure the server is running.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()
        print("Connection closed")


if __name__ == "__main__":
    main()
