# FTP Client-Server Implementation

A simple File Transfer Protocol (FTP) implementation using Python sockets for network programming.

## Features

- **LS**: List all files available on the server
- **GET**: Download a file from the server to the client
- **PUT**: Upload a file from the client to the server
- **QUIT**: Disconnect from the server

## Project Structure

```
FTP/
├── server.py          # FTP server implementation
├── client.py          # FTP client implementation
├── protocol.py        # Protocol helpers for message/file transfer
├── server_files/      # Server file directory
└── client_files/      # Client file directory
```

## Requirements

- Python 3.6+

## Usage

### Starting the Server

```bash
python FTP/server.py
```

The server will start listening on `127.0.0.1:5002` by default.

### Running the Client

In a separate terminal, run:

```bash
python FTP/client.py
```

### Available Commands

Once connected, you can use the following commands:

- `LS` - List all files on the server
- `GET <filename>` - Download a file from the server
- `PUT <filename>` - Upload a file to the server
- `QUIT` - Disconnect from the server

### Example Session

```
ftp> LS
Server files (2):
  - serverfile1.txt
  - serverfile2.txt

ftp> GET serverfile1.txt
Downloaded: serverfile1.txt (1234 bytes)

ftp> PUT clientfile1.txt
Uploaded: clientfile1.txt

ftp> QUIT
Goodbye
```

## Protocol

The implementation uses a custom JSON-based protocol over TCP sockets:
- Messages are JSON-encoded with type, code, and message fields
- Files are transferred with metadata headers followed by binary data
- All communication follows a request-response pattern

## Configuration

Default settings can be modified in the respective files:

- Server IP/Port: `server.py` (lines 21-22)
- Client connection: `client.py` (lines 16-17)
- File directories: Configured in both client and server files
