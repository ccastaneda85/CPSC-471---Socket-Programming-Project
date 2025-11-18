# Part 2: Multi-Client FTP Server Implementation Plan

## Objective
Upgrade the FTP server to handle multiple concurrent clients using multithreading for EC2 deployment.

## Current State
- Server handles one client at a time (blocking)
- Server listens on localhost (127.0.0.1)
- Connection limit: 1 (`server.listen(1)`)

## Target State
- Server handles multiple clients simultaneously
- Server listens on all interfaces (0.0.0.0) for EC2
- Each client connection runs in its own thread
- Thread-safe logging and file operations
- Comprehensive logging to both file and console

---

## Implementation Steps

### Step 1: Add Required Imports
**File:** `FTP/server.py`

**Action:** Add threading and logging modules to imports
```python
import os
import socket
import protocol
import threading
import logging
from datetime import datetime
```

**Why:**
- `threading`: Spawn threads for each client connection
- `logging`: Professional logging system (thread-safe by default)
- `datetime`: Timestamp log files

---

### Step 2: Configure Logging System
**File:** `FTP/server.py`

**Action:** Add logging configuration after the imports and before constants
```python
# Configure logging
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
        logging.FileHandler(log_filename),  # Log to file
        logging.StreamHandler()              # Also log to console
    ]
)

logger = logging.getLogger(__name__)

# Constants
SERVER_FILE_DIR = os.path.join(os.path.dirname(__file__), 'server_files')
IP = '0.0.0.0'  # Changed from 127.0.0.1 to listen on all interfaces
PORT = 5002

COMMANDS = ["LS", "GET", "PUT", "QUIT"]
```

**Why:**
- **Automatic thread-safety**: Python's logging module is thread-safe by default
- **Dual output**: Logs to both file (persistent) and console (real-time monitoring)
- **Timestamped logs**: Each log entry has a timestamp
- **Thread identification**: `%(threadName)s` shows which thread logged the message
- **Log levels**: INFO, WARNING, ERROR for categorizing messages
- **Persistent records**: All activity saved to `logs/` directory
- **0.0.0.0 binding**: Allows connections from any network interface (required for EC2)

---

### Step 3: Update All Print Statements to Use Logger
**File:** `FTP/server.py`

**Action:** Replace all `print()` calls with appropriate `logger` calls

**Logging Levels to Use:**
- `logger.info()` - Normal operations (connections, commands, file transfers)
- `logger.warning()` - Unusual but handled situations (file not found, invalid commands)
- `logger.error()` - Errors that prevent operations

**Examples:**
```python
# Before:
print(f"LS: Sent {len(file_list)} files")

# After:
logger.info(f"LS: Sent {len(file_list)} files")

# Before:
print(f"GET: File not found - {filename}")

# After:
logger.warning(f"GET: File not found - {filename}")
```

**Locations to update:**
- Line 60 in `handle_ls()`:
  ```python
  logger.info(f"LS: Sent {len(file_list)} files to client")
  ```

- Line 79 in `handle_get()`:
  ```python
  logger.warning(f"GET: File not found - {filename}")
  ```

- Line 92 in `handle_get()`:
  ```python
  logger.info(f"GET: Sent file - {filename}")
  ```

- Line 117 in `handle_put()`:
  ```python
  logger.info(f"PUT: Received file - {filename} ({result['bytes_received']} bytes)")
  ```

- Line 119 in `handle_put()`:
  ```python
  logger.error(f"PUT: Failed to receive file - {filename}")
  ```

- Line 127-128 in `serve()`:
  ```python
  logger.info(f"Multi-threaded FTP Server listening on {IP}:{PORT}")
  logger.info(f"Server directory: {SERVER_FILE_DIR}")
  logger.info(f"Logging to: {log_filename}")
  ```

- Line 148 in main loop:
  ```python
  logger.info("Client disconnected")
  ```

- Line 154 in main loop:
  ```python
  logger.warning(f"Unknown message type: {msg_type}")
  ```

- Line 160 in main loop:
  ```python
  logger.info(f"Received command: {client_command}" + (f" {filename}" if filename else ""))
  ```

- Line 190 in QUIT handler:
  ```python
  logger.info("Client requested disconnect")
  ```

- Line 194 after connection close:
  ```python
  logger.info("Connection closed")
  ```

- Line 197 in KeyboardInterrupt:
  ```python
  logger.info("Server shutting down...")
  ```

---

### Step 5: Extract Client Handler Function
**File:** `FTP/server.py`

**Action:** Create a new function `handle_client()` that contains all the client interaction logic. Add this function before the `serve()` function:

```python
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
```

**Why:** Extracting this logic into a separate function allows us to run it in a thread for each client.

---

### Step 6: Simplify Main Server Loop
**File:** `FTP/server.py`

**Action:** Replace the `serve()` function with a simplified version that spawns threads:

```python
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
```

**Why:**
- `server.listen(5)`: Allows up to 5 pending connections in the queue
- `SO_REUSEADDR`: Prevents "Address already in use" errors when restarting
- `daemon=True`: Threads automatically terminate when the main program exits
- Each connection gets its own thread, allowing concurrent client handling

---

### Step 7: Update Client Configuration (Optional)
**File:** `FTP/client.py`

**Action:** Update the server IP if testing locally, or leave as-is for EC2

```python
# For local testing with the new server:
SERVER_IP = '127.0.0.1'  # or 'localhost'
SERVER_PORT = 5002

# For connecting to EC2 (replace with your EC2 public IP):
# SERVER_IP = 'your-ec2-public-ip'
# SERVER_PORT = 5002
```

**Why:** Client needs to know where to connect. Localhost for testing, EC2 public IP for deployment.

---

## Testing Plan

### Test 1: Single Client (Sanity Check)
1. Start the server: `python FTP/server.py`
2. In another terminal, run client: `python FTP/client.py`
3. Test all commands: `LS`, `GET`, `PUT`, `QUIT`
4. Verify everything works as before

### Test 2: Multiple Clients Simultaneously
1. Start the server: `python FTP/server.py`
2. Open 3+ terminal windows
3. Run `python FTP/client.py` in each
4. Execute commands in different clients simultaneously
5. Verify:
   - All clients can connect at once
   - Each client gets responses
   - File transfers work for all clients
   - No garbled output in server logs

### Test 3: Stress Test
1. Start the server
2. Create a simple script to launch multiple clients:
```python
# test_multi_client.py
import subprocess
import time

for i in range(10):
    subprocess.Popen(['python', 'FTP/client.py'])
    time.sleep(0.5)
```
3. Monitor server behavior and resource usage

---

## Logging System Overview

### What Gets Logged

The server logs all connection and activity information with the following detail levels:

**INFO Level (Normal Operations):**
- Server startup and configuration
- New client connections with IP address
- All client commands (LS, GET, PUT, QUIT)
- Successful file transfers with sizes
- Client disconnections
- Thread spawning
- Server shutdown

**WARNING Level (Unusual Events):**
- Invalid commands from clients
- File not found errors (GET requests)
- Unknown message types
- Malformed requests

**ERROR Level (Failures):**
- File transfer failures
- Client handler exceptions
- Connection errors

### Log Output Locations

Logs are written to **two locations simultaneously**:

1. **Console/Terminal** - Real-time monitoring while server runs
2. **Log File** - Persistent storage in `FTP/logs/` directory
   - Format: `ftp_server_YYYYMMDD_HHMMSS.log`
   - Example: `ftp_server_20241117_143022.log`

### Log Entry Format

Each log entry follows this format:
```
YYYY-MM-DD HH:MM:SS,mmm - [ThreadName] - LEVEL - Message
```

**Example log entries:**
```
2024-11-17 14:30:22,145 - [MainThread] - INFO - Multi-threaded FTP Server listening on 0.0.0.0:5002
2024-11-17 14:30:22,146 - [MainThread] - INFO - Server directory: /path/to/FTP/server_files
2024-11-17 14:30:22,147 - [MainThread] - INFO - Logging to: /path/to/FTP/logs/ftp_server_20241117_143022.log
2024-11-17 14:30:22,148 - [MainThread] - INFO - Ready to accept multiple concurrent connections...
2024-11-17 14:30:35,234 - [MainThread] - INFO - Spawned thread Client-192.168.1.100:52431 for ('192.168.1.100', 52431)
2024-11-17 14:30:35,235 - [Client-192.168.1.100:52431] - INFO - New connection from ('192.168.1.100', 52431)
2024-11-17 14:30:38,567 - [Client-192.168.1.100:52431] - INFO - ('192.168.1.100', 52431) - Command: LS
2024-11-17 14:30:38,569 - [Client-192.168.1.100:52431] - INFO - LS: Sent 5 files to client
2024-11-17 14:30:45,123 - [Client-192.168.1.100:52431] - INFO - ('192.168.1.100', 52431) - Command: GET testfile.txt
2024-11-17 14:30:45,234 - [Client-192.168.1.100:52431] - INFO - GET: Sent file - testfile.txt
2024-11-17 14:31:02,456 - [MainThread] - INFO - Spawned thread Client-192.168.1.101:52432 for ('192.168.1.101', 52432)
2024-11-17 14:31:02,457 - [Client-192.168.1.101:52432] - INFO - New connection from ('192.168.1.101', 52432)
2024-11-17 14:31:10,789 - [Client-192.168.1.100:52431] - INFO - Client ('192.168.1.100', 52431) requested disconnect
2024-11-17 14:31:10,790 - [Client-192.168.1.100:52431] - INFO - Connection closed for ('192.168.1.100', 52431)
```

### Monitoring Logs in Real-Time

**On your local machine:**
```bash
# View live server output
python FTP/server.py

# Or run in background and tail the log
python FTP/server.py &
tail -f FTP/logs/ftp_server_*.log
```

**On EC2:**
```bash
# Run server in background with nohup
nohup python3 FTP/server.py &

# Monitor the latest log file
tail -f FTP/logs/ftp_server_*.log

# Or grep for specific events
grep "ERROR" FTP/logs/ftp_server_*.log
grep "192.168.1.100" FTP/logs/ftp_server_*.log  # Track specific client
grep "GET:" FTP/logs/ftp_server_*.log           # All GET requests
```

### Analyzing Logs

**Find all connections in a session:**
```bash
grep "New connection" FTP/logs/ftp_server_20241117_143022.log
```

**Track a specific client:**
```bash
grep "192.168.1.100:52431" FTP/logs/ftp_server_20241117_143022.log
```

**Count file transfers:**
```bash
grep -c "GET: Sent file" FTP/logs/ftp_server_20241117_143022.log
grep -c "PUT: Received file" FTP/logs/ftp_server_20241117_143022.log
```

**Find errors:**
```bash
grep "ERROR\|WARNING" FTP/logs/ftp_server_20241117_143022.log
```

**View most active times:**
```bash
awk '{print $1, $2}' FTP/logs/ftp_server_20241117_143022.log | cut -d',' -f1 | uniq -c
```

### Log File Management

**Disk Space Considerations:**
- Each connection generates ~5-10 log entries
- File transfers add 2-3 entries per transfer
- A log file from 100 connections might be 50-100 KB
- Monitor disk usage on EC2: `du -h FTP/logs/`

**Cleaning Old Logs:**
```bash
# Delete logs older than 7 days
find FTP/logs/ -name "ftp_server_*.log" -mtime +7 -delete

# Keep only the 10 most recent logs
ls -t FTP/logs/ftp_server_*.log | tail -n +11 | xargs rm -f
```

**Optional: Log Rotation (Advanced)**

For production deployment, consider using Python's `RotatingFileHandler`:

```python
from logging.handlers import RotatingFileHandler

# Replace the FileHandler in Step 2 with:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10 MB per file
            backupCount=5            # Keep 5 backup files
        ),
        logging.StreamHandler()
    ]
)
```

This automatically rotates logs when they reach 10 MB, keeping 5 backup files.

---

## EC2 Deployment Checklist

### Security Group Configuration
- [ ] Allow inbound TCP on port 5002 from your IP or 0.0.0.0/0
- [ ] Allow outbound traffic

### Server Setup
- [ ] Install Python 3.6+ on EC2 instance
- [ ] Upload FTP directory to EC2
- [ ] Ensure `server_files/` directory exists
- [ ] The `logs/` directory will be created automatically on first run
- [ ] Run server: `python3 FTP/server.py`
- [ ] For persistent background running:
  ```bash
  # Using nohup (server logs to FTP/logs/ automatically)
  nohup python3 FTP/server.py &

  # Or using screen (allows reattaching)
  screen -S ftp-server
  python3 FTP/server.py
  # Press Ctrl+A then D to detach
  # Reattach with: screen -r ftp-server
  ```
- [ ] Monitor logs: `tail -f FTP/logs/ftp_server_*.log`

### Client Configuration
- [ ] Update `SERVER_IP` in `client.py` to EC2 public IP
- [ ] Test connection from local machine

---

## File Operation Considerations

### Thread Safety Notes
- **File reads (GET)**: Safe - Python file reads are atomic
- **File writes (PUT)**: Potential race condition if same filename
- **Directory listing (LS)**: Safe - `os.listdir()` is thread-safe

### Potential Issues
1. **Same file upload simultaneously**: Two clients uploading the same filename
   - Current implementation: Last write wins
   - Improvement (optional): Add file locking or unique filenames

2. **File system limits**: Many concurrent file operations
   - Monitor disk I/O on EC2
   - Consider adding rate limiting if needed

---

## Performance Optimization (Optional Enhancements)

### 1. Thread Pool
Instead of creating unlimited threads, use a thread pool:
```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)
# In serve(): executor.submit(handle_client, connection, address)
```

### 2. Active Connection Counter
Track how many clients are currently connected:
```python
# Add to globals
active_connections = 0
connection_lock = threading.Lock()

# Update handle_client function
def handle_client(connection, address):
    global active_connections

    with connection_lock:
        active_connections += 1

    logger.info(f"New connection from {address} - Active connections: {active_connections}")

    try:
        # ... existing code ...
    finally:
        with connection_lock:
            active_connections -= 1

        connection.close()
        logger.info(f"Connection closed for {address} - Active connections: {active_connections}")
```

### 3. Connection Rate Limiting
Prevent DoS attacks by limiting connections per IP:
```python
from collections import defaultdict
from time import time

# Add to globals
connection_attempts = defaultdict(list)
MAX_CONNECTIONS_PER_IP = 5
TIME_WINDOW = 60  # seconds

# In serve() before spawning thread
def check_rate_limit(ip):
    now = time()
    # Remove old attempts
    connection_attempts[ip] = [t for t in connection_attempts[ip] if now - t < TIME_WINDOW]

    if len(connection_attempts[ip]) >= MAX_CONNECTIONS_PER_IP:
        return False

    connection_attempts[ip].append(now)
    return True

# Usage in serve():
ip = address[0]
if not check_rate_limit(ip):
    logger.warning(f"Rate limit exceeded for {ip}")
    connection.close()
    continue
```

---

## Troubleshooting

### Issue: "Address already in use"
**Solution:**
- Wait 30-60 seconds for socket to release
- Or add `SO_REUSEADDR` option (already in Step 6)

### Issue: Client can't connect to EC2
**Solution:**
- Check EC2 security group allows port 5002
- Verify server is running: `ps aux | grep server.py`
- Check server is listening: `netstat -tuln | grep 5002`

### Issue: Garbled server output
**Solution:**
- Ensure all `print()` changed to `thread_safe_print()`
- Verify `print_lock` is being used

### Issue: File transfer errors with multiple clients
**Solution:**
- Check file permissions in `server_files/` and `client_files/`
- Monitor disk space on EC2

---

## Summary of Changes

| Component | Change | Reason |
|-----------|--------|--------|
| IP Address | `127.0.0.1` → `0.0.0.0` | Accept connections from any interface (EC2) |
| Listen Backlog | `1` → `5` | Allow multiple pending connections |
| Client Handling | Inline → Separate function | Enable threading per client |
| Thread Creation | None → Per connection | Handle multiple clients concurrently |
| Logging System | `print()` → `logging` module | Thread-safe, persistent file logs + console |
| Log Storage | None → `logs/` directory | Persistent activity records with timestamps |
| Socket Options | None → `SO_REUSEADDR` | Easier server restart without wait time |
| Imports | Added `threading`, `logging`, `datetime` | Support for multithreading and logging |

---

## Next Steps After Implementation

### 1. Update .gitignore
Add the logs directory to `.gitignore` to prevent committing log files:

```bash
echo "FTP/logs/" >> .gitignore
```

Or manually add this line to `.gitignore`:
```
FTP/logs/
```

### 2. Test Locally
- Test with single client first
- Test with multiple concurrent clients
- Verify logging works (check console and `FTP/logs/` directory)

### 3. Commit Changes
```bash
git add .
git commit -m "Add multithreading and logging support for Part 2

- Implemented threading for concurrent client handling
- Added comprehensive logging system with file and console output
- Changed server IP to 0.0.0.0 for EC2 deployment
- Increased connection backlog to 5
- Added SO_REUSEADDR socket option

📝 See PART2_IMPLEMENTATION_PLAN.md for details"

git push -u origin Part-2
```

### 4. Deploy to EC2
- Follow EC2 Deployment Checklist above
- Monitor logs in real-time during testing

### 5. Update Documentation
- Update main README.md with Part 2 features
- Include information about logging and multithreading

### 6. Create Submission Package
```bash
# Similar to Part 1
mkdir -p p2-jcastaneda85
cp -r FTP p2-jcastaneda85/
cp README.md p2-jcastaneda85/
cp PART2_IMPLEMENTATION_PLAN.md p2-jcastaneda85/
tar cvf p2-jcastaneda85.tar p2-jcastaneda85
```

---

Good luck with your implementation!
