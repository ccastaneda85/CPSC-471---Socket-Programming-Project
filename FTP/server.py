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
import threading
import logging
from datetime import datetime

#configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create log filename with timestamp
log_filename = os.path.join(LOG_DIR, f'ftp_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

SERVER_FILE_DIR = os.path.join(os.path.dirname(__file__), 'server_files')
IP = '127.0.0.1'
PORT = 5000

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
    logger.info(f"LS: Sent {len(file_list)} files")


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
        logger.warning(f"GET: File not found - {filename}")
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
    logger.info(f"GET: Sent file - {filename}")


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
        logger.info(f"PUT: Received file - {filename} ({result['bytes_received']} bytes)")
    else:
        logger.error(f"PUT: Failed to receive file - {filename}")

def handle_client(connection, address):
    """Handle a single client connection in a separate thread"""
    try:
        logger.info(f"New connection from {address}")

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
                logger.info(f"Client {address} disconnected")
                break

            # Parse command
            msg_type = msg.get("type")
            if msg_type != "command":
                logger.warning(f"Unknown message type from {address}: {msg_type}")
                continue

            client_command = msg.get("command", "").upper()
            filename = msg.get("filename")

            logger.info(f"{address} - Command: {client_command}" +
                       (f" {filename}" if filename else ""))

            # Validate command
            response_code, response_msg = validate_command(client_command)

            if response_code != 200:
                # Invalid command
                logger.warning(f"{address} - Invalid command: {client_command}")
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
                logger.info(f"Client {address} requested disconnect")
                break

    except Exception as e:
        logger.error(f"Error handling client {address}: {e}")
    finally:
        connection.close()
        logger.info(f"Connection closed for {address}")

def serve():
    """Main server loop - accepts connections and spawns threads"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
    server.bind((IP, PORT))
    server.listen(5)  # Increased from 1 to 5 for multiple connections

    logger.info(f"Multi-threaded FTP Server listening on {IP}:{PORT}")
    logger.info(f"Server directory: {SERVER_FILE_DIR}")
    logger.info(f"Logging to: {log_filename}")
    logger.info("Ready to accept multiple concurrent connections...")

    try:
        while True:
            # Wait for connection
            connection, address = server.accept()

            # Create and start a new thread for this client
            client_thread = threading.Thread(
                target=handle_client,
                args=(connection, address),
                name=f"Client-{address[0]}:{address[1]}"
            )
            client_thread.daemon = True  # Thread will close when main program exits
            client_thread.start()

            logger.info(f"Spawned thread {client_thread.name} for {address}")

    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    serve()
