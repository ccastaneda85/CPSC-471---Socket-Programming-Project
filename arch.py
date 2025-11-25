
"""The Archived serve() function prior multi-threading"""


# def serve():
#     """Main server loop"""
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind((IP, PORT))
#     server.listen(1)
#     logger.info(f"Multi-threaded FTP Server listening on {IP}: {PORT}")
#     logger.info(f"Server directory: {SERVER_FILE_DIR}")
    
#     try:
#         while True:
#             # Wait for connection
#             connection, address = server.accept()
#             print(f"Connected by {address}")

#             # Send connection acknowledgment
#             protocol.send_message(connection, {
#                 "type": "connection",
#                 "code": 200,
#                 "message": "Connection established"
#             })

#             # Handle client commands
#             while True:
#                 # Receive command message
#                 msg = protocol.recv_message(connection)
#                 if not msg:
#                     logger.info("Client disconnected")
#                     break

#                 # Parse command
#                 msg_type = msg.get("type")
#                 if msg_type != "command":
#                     logger.warning(f"Unknown message type: {msg_type}")
#                     continue

#                 client_command = msg.get("command", "").upper()
#                 filename = msg.get("filename")

#                 logger.info(f"Received command: {client_command}" + (f" {filename}" if filename else ""))

#                 # Validate command
#                 response_code, response_msg = validate_command(client_command)

#                 if response_code != 200:
#                     # Invalid command
#                     protocol.send_message(connection, {
#                         "type": "response",
#                         "code": response_code,
#                         "message": response_msg
#                     })
#                     continue

#                 # Execute command
#                 if client_command == "LS":
#                     handle_ls(connection)

#                 elif client_command == "GET":
#                     handle_get(connection, filename)

#                 elif client_command == "PUT":
#                     handle_put(connection, filename)

#                 elif client_command == "QUIT":
#                     protocol.send_message(connection, {
#                         "type": "response",
#                         "code": 200,
#                         "message": "Goodbye"
#                     })
#                     logger.info("Client requested disconnect")
#                     break

#             connection.close()
#             logger.info("Connection closed\n")

#     except KeyboardInterrupt:
#         logger.info("\nServer shutting down...")
#     finally:
#         server.close()
