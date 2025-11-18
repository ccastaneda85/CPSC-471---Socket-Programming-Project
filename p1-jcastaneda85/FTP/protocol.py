"""
Protocol Helper Functions for FTP Communication

Message Format:
- 4 bytes: message length (big-endian unsigned int)
- N bytes: JSON payload (UTF-8 encoded)

Message Types:
- command: Client sends command to server
- response: Server responds to command
- file_transfer_start: Metadata before file transfer
- file_transfer_complete: Signal file transfer is done
"""

import json
import struct
import os


def send_message(sock, message_dict):
    """
    Send a length-prefixed JSON message

    Args:
        sock: Socket connection
        message_dict: Dictionary to send as JSON
    """
    payload = json.dumps(message_dict).encode('utf-8')
    length = struct.pack('!I', len(payload))  # 4-byte big-endian unsigned int
    sock.sendall(length + payload)


def recv_message(sock):
    """
    Receive a length-prefixed JSON message

    Args:
        sock: Socket connection

    Returns:
        Dictionary parsed from JSON, or None if connection closed
    """
    # Read 4-byte length header
    length_data = recv_exact(sock, 4)
    if not length_data:
        return None

    length = struct.unpack('!I', length_data)[0]

    # Read the JSON payload
    payload = recv_exact(sock, length)
    if not payload:
        return None

    return json.loads(payload.decode('utf-8'))


def recv_exact(sock, n):
    """
    Helper to receive exactly n bytes from socket

    Args:
        sock: Socket connection
        n: Number of bytes to receive

    Returns:
        Bytes received, or None if connection closed
    """
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def send_file(sock, filename, filepath):
    """
    Send a file over the socket with metadata

    Args:
        sock: Socket connection
        filename: Name of the file
        filepath: Path to the file to send
    """
    # 1. Send file metadata
    file_size = os.path.getsize(filepath)
    send_message(sock, {
        "type": "file_transfer_start",
        "filename": filename,
        "size": file_size
    })

    # 2. Send file data in chunks
    bytes_sent = 0
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sock.sendall(chunk)
            bytes_sent += len(chunk)

    # 3. Send completion message
    send_message(sock, {
        "type": "file_transfer_complete",
        "bytes_sent": bytes_sent
    })


def recv_file(sock, filepath):
    """
    Receive a file over the socket

    Args:
        sock: Socket connection
        filepath: Path where to save the file

    Returns:
        Dictionary with file metadata, or None if failed
    """
    # 1. Receive file metadata
    metadata = recv_message(sock)
    if not metadata or metadata.get("type") != "file_transfer_start":
        return None

    file_size = metadata["size"]
    filename = metadata["filename"]

    # 2. Receive file data
    bytes_received = 0
    with open(filepath, 'wb') as f:
        while bytes_received < file_size:
            chunk_size = min(4096, file_size - bytes_received)
            chunk = recv_exact(sock, chunk_size)
            if not chunk:
                return None
            f.write(chunk)
            bytes_received += len(chunk)

    # 3. Receive completion message
    completion = recv_message(sock)

    return {
        "filename": filename,
        "size": file_size,
        "bytes_received": bytes_received
    }
