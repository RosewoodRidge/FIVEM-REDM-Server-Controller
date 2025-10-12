import json
import socket
import secrets
import logging
import hashlib
import time
import base64
import threading
import os
from datetime import datetime
from collections import defaultdict
from config_manager import get_logs_dir

# Set up specific logger for remote operations
remote_logger = logging.getLogger('remote_control')
remote_logger.setLevel(logging.DEBUG)

# Add file handler if not already added
if not remote_logger.handlers:
    logs_dir = get_logs_dir()
    
    # Create file handler
    fh = logging.FileHandler(os.path.join(logs_dir, 'remote_control.log'))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    remote_logger.addHandler(fh)

# Remote protocol constants
DEFAULT_PORT = 40100
BUFFER_SIZE = 4096
TIMEOUT = 10  # socket timeout in seconds
HEARTBEAT_INTERVAL = 5  # seconds between heartbeat messages

# Command types
CMD_AUTH = "AUTH"  # Add explicit AUTH command type
CMD_HEARTBEAT = "HEARTBEAT"
CMD_SERVER_STATUS = "SERVER_STATUS"
CMD_START_SERVER = "START_SERVER"
CMD_STOP_SERVER = "STOP_SERVER"
CMD_RESTART_SERVER = "RESTART_SERVER"
CMD_BACKUP_DB = "BACKUP_DB"
CMD_RESTORE_DB = "RESTORE_DB"
CMD_GET_DB_BACKUPS = "GET_DB_BACKUPS"
CMD_BACKUP_SERVER = "BACKUP_SERVER"
CMD_RESTORE_SERVER = "RESTORE_SERVER"
CMD_GET_SERVER_BACKUPS = "GET_SERVER_BACKUPS"
CMD_UPDATE_TXADMIN = "UPDATE_TXADMIN"
CMD_RESTORE_TXADMIN = "RESTORE_TXADMIN"
CMD_GET_TXADMIN_BACKUPS = "GET_TXADMIN_BACKUPS"
CMD_LOG_MESSAGE = "LOG_MESSAGE"

# Response status codes
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
STATUS_AUTH_REQUIRED = "AUTH_REQUIRED"
STATUS_INVALID_AUTH = "INVALID_AUTH"
STATUS_AUTH_FAILED = "AUTH_FAILED"

class RemoteMessage:
    """Class to represent remote control messages"""
    
    def __init__(self, command, data=None, status=None, message=None):
        self.command = command
        self.data = data or {}
        self.status = status
        self.message = message
        self.timestamp = datetime.now().isoformat()
    
    def to_json(self):
        """Convert message to JSON string"""
        return json.dumps({
            "command": self.command,
            "data": self.data,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str):
        """Create a RemoteMessage from a JSON string"""
        try:
            data = json.loads(json_str)
            msg = cls(
                command=data.get("command"),
                data=data.get("data", {}),
                status=data.get("status"),
                message=data.get("message")
            )
            msg.timestamp = data.get("timestamp", datetime.now().isoformat())
            return msg
        except json.JSONDecodeError as e:
            remote_logger.error(f"Failed to decode message: {e}")
            return None

def generate_auth_key():
    """Generate a random authentication key"""
    # Generate a 24-character secure random string
    token = secrets.token_hex(12)  # 12 bytes = 24 hex characters
    
    # Format it with dashes for easier reading
    formatted_token = f"{token[:4]}-{token[4:8]}-{token[8:12]}-{token[12:16]}-{token[16:]}"
    return formatted_token

def hash_auth_key(key, salt=None):
    """Hash the authentication key for secure storage/comparison"""
    if salt is None:
        salt = secrets.token_bytes(16)
    
    # Use PBKDF2 with SHA-256 for secure hashing
    key_hash = hashlib.pbkdf2_hmac(
        'sha256',
        key.encode('utf-8'),
        salt,
        100000  # Number of iterations
    )
    
    # Return the salt and hash
    return salt, key_hash

def verify_auth_key(input_key, stored_salt, stored_hash):
    """Verify an authentication key against a stored hash"""
    _, input_hash = hash_auth_key(input_key, stored_salt)
    return input_hash == stored_hash

class RemoteServer:
    """TCP server to handle remote connections to the main app"""
    
    def __init__(self, port=DEFAULT_PORT, command_handler=None):
        self.port = port
        self.command_handler = command_handler
        self.server_socket = None
        self.running = False
        self.client_sockets = {}  # {socket: (address, auth_status)}
        self.auth_key = generate_auth_key()
        self.auth_salt, self.auth_hash = hash_auth_key(self.auth_key)
        self.debug_mode = True
        
        # Security enhancements
        self.whitelisted_ips = set()  # Set of allowed IP addresses
        self.ip_attempts = defaultdict(list)  # Track authentication attempts per IP
        self.max_attempts = 5  # Max failed attempts before temporary ban
        self.attempt_window = 300  # 5 minute window for attempts
        self.ban_duration = 600  # 10 minute ban after max attempts
        self.banned_ips = {}  # {ip: ban_expiry_timestamp}
        
        remote_logger.info(f"Generated authentication key: {self.auth_key}")
    
    def hash_auth_key(self, key, salt=None):
        """Hash the authentication key with a random salt"""
        return hash_auth_key(key, salt)  # Use the global function
    
    def start(self):
        """Start the server in a separate thread"""
        if self.running:
            return False
        
        try:
            # Check if port is already in use
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(('localhost', self.port))
            test_socket.close()
            
            if result == 0:
                logging.error(f"Port {self.port} is already in use")
                return False
            
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Critical fix: Bind to all network interfaces instead of just localhost
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            # Start thread to listen for connections
            self.listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            self.listen_thread.start()
            
            logging.info(f"Remote control server started on port {self.port}")
            logging.info(f"Make sure Windows Firewall allows connections on port {self.port}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start remote server: {str(e)}")
            self.server_socket = None
            return False
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Close all client connections
        for sock in list(self.client_sockets.keys()):
            try:
                sock.close()
            except:
                pass
        self.client_sockets.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        logging.info("Remote control server stopped")
    
    def _listen_for_connections(self):
        """Thread function to listen for incoming connections"""
        self.server_socket.settimeout(1)  # 1 second timeout for accept() to allow checking self.running
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logging.info(f"New connection from {address[0]}:{address[1]}")
                
                # Set up client socket
                client_socket.settimeout(30)  # 30 seconds timeout for client operations
                self.client_sockets[client_socket] = (address, False)  # Not authenticated yet
                
                # Start thread to handle this client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                # This is expected due to the timeout on accept()
                continue
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logging.error(f"Error accepting connection: {str(e)}")
                    time.sleep(1)  # Avoid tight loop if there's an error
    
    def add_whitelisted_ip(self, ip_address):
        """Add an IP address to the whitelist"""
        self.whitelisted_ips.add(ip_address)
        remote_logger.info(f"Added {ip_address} to whitelist")
    
    def remove_whitelisted_ip(self, ip_address):
        """Remove an IP address from the whitelist"""
        self.whitelisted_ips.discard(ip_address)
        remote_logger.info(f"Removed {ip_address} from whitelist")
    
    def is_ip_banned(self, ip_address):
        """Check if an IP is currently banned"""
        if ip_address in self.banned_ips:
            if time.time() < self.banned_ips[ip_address]:
                return True
            else:
                # Ban expired, remove it
                del self.banned_ips[ip_address]
                return False
        return False
    
    def record_failed_attempt(self, ip_address):
        """Record a failed authentication attempt"""
        current_time = time.time()
        
        # Clean old attempts outside the window
        self.ip_attempts[ip_address] = [
            t for t in self.ip_attempts[ip_address]
            if current_time - t < self.attempt_window
        ]
        
        # Add new attempt
        self.ip_attempts[ip_address].append(current_time)
        
        # Check if should be banned
        if len(self.ip_attempts[ip_address]) >= self.max_attempts:
            self.banned_ips[ip_address] = current_time + self.ban_duration
            remote_logger.warning(f"IP {ip_address} banned for {self.ban_duration}s after {self.max_attempts} failed attempts")
            return True
        
        return False
    
    def clear_failed_attempts(self, ip_address):
        """Clear failed attempts for an IP (after successful auth)"""
        if ip_address in self.ip_attempts:
            del self.ip_attempts[ip_address]
    
    def _handle_client(self, client_socket, address):
        """Handle communication with a client"""
        ip_address = address[0]
        logging.info(f"Handling connection from {ip_address}:{address[1]}")
        
        try:
            # Check if IP is banned
            if self.is_ip_banned(ip_address):
                remote_logger.warning(f"Rejected connection from banned IP: {ip_address}")
                ban_msg = RemoteMessage(
                    command="AUTH",
                    status=STATUS_ERROR,
                    message="IP temporarily banned due to too many failed attempts"
                )
                self._send_message(client_socket, ban_msg)
                client_socket.close()
                if client_socket in self.client_sockets:
                    del self.client_sockets[client_socket]
                return
            
            # Check whitelist if enabled
            if self.whitelisted_ips and ip_address not in self.whitelisted_ips:
                remote_logger.warning(f"Rejected connection from non-whitelisted IP: {ip_address}")
                whitelist_msg = RemoteMessage(
                    command="AUTH",
                    status=STATUS_ERROR,
                    message="IP not whitelisted"
                )
                self._send_message(client_socket, whitelist_msg)
                client_socket.close()
                if client_socket in self.client_sockets:
                    del self.client_sockets[client_socket]
                return
            
            # Set a longer timeout during authentication
            client_socket.settimeout(30)
            
            # Exchange authentication
            auth_required = RemoteMessage(
                command="AUTH",
                status=STATUS_AUTH_REQUIRED,
                message="Authentication required"
            )
            logging.info(f"Sending auth request to {ip_address}:{address[1]}")
            self._send_message(client_socket, auth_required)
            
            # Wait for auth response
            logging.info(f"Waiting for auth response from {ip_address}:{address[1]}")
            auth_response = self._receive_message(client_socket)
            if not auth_response or auth_response.command != "AUTH":
                logging.warning(f"Invalid authentication response from {ip_address}:{address[1]}")
                self.record_failed_attempt(ip_address)
                client_socket.close()
                if client_socket in self.client_sockets:
                    del self.client_sockets[client_socket]
                return
            
            # Verify auth key
            logging.info(f"Received auth response from {ip_address}:{address[1]}")
            provided_key = auth_response.data.get("auth_key", "")
            if self.verify_auth_key(provided_key):
                logging.info(f"Client authenticated: {ip_address}:{address[1]}")
                self.client_sockets[client_socket] = (address, True)  # Mark as authenticated
                
                # Clear any failed attempts
                self.clear_failed_attempts(ip_address)
                
                # Auto-whitelist successful connections
                if ip_address not in self.whitelisted_ips:
                    self.add_whitelisted_ip(ip_address)
                
                auth_success = RemoteMessage(
                    command="AUTH",
                    status=STATUS_OK,
                    message="Authentication successful"
                )
                self._send_message(client_socket, auth_success)
                
                # Set socket to blocking mode for command processing
                client_socket.settimeout(None)
                logging.info(f"Entering command loop for {ip_address}:{address[1]} (blocking mode)")
                
                # Process commands from this client
                self._process_client_commands(client_socket, address)
            else:
                logging.warning(f"Authentication failed for {ip_address}:{address[1]}")
                
                # Record failed attempt
                banned = self.record_failed_attempt(ip_address)
                
                auth_failed = RemoteMessage(
                    command="AUTH",
                    status=STATUS_AUTH_FAILED,
                    message="Authentication failed" + (" - IP temporarily banned" if banned else "")
                )
                self._send_message(client_socket, auth_failed)
                client_socket.close()
                if client_socket in self.client_sockets:
                    del self.client_sockets[client_socket]
        
        except Exception as e:
            logging.error(f"Error handling client {ip_address}:{address[1]}: {str(e)}")
            try:
                client_socket.close()
            except:
                pass
            if client_socket in self.client_sockets:
                del self.client_sockets[client_socket]
    
    def verify_auth_key(self, provided_key):
        """Verify the authentication key provided by a client"""
        try:
            # First check if keys match directly (for simpler testing)
            if provided_key == self.auth_key:
                return True
                
            # Then do the proper secure verification
            key_hash = hashlib.pbkdf2_hmac(
                'sha256',
                provided_key.encode('utf-8'),
                self.auth_salt,
                100000
            )
            return key_hash == self.auth_hash
        except Exception as e:
            logging.error(f"Auth verification error: {str(e)}")
            return False
            
    def _process_client_commands(self, client_socket, address):
        """Process commands from an authenticated client"""
        logging.info(f"Started command loop for {address[0]}:{address[1]}")
        while self.running:
            try:
                message = self._receive_message(client_socket)
                if not message:
                    logging.info(f"Client {address[0]}:{address[1]} connection closed or no message received")
                    break
                
                logging.info(f"Received command {message.command} from {address[0]}:{address[1]}")
                
                if self.command_handler:
                    response = self.command_handler(message)
                    if response:
                        self._send_message(client_socket, response)
                else:
                    response = RemoteMessage(
                        command=message.command,
                        status=STATUS_ERROR,
                        message="No command handler registered"
                    )
                    self._send_message(client_socket, response)
            
            except socket.timeout:
                # Timeout is fine - just means no message received
                # Don't send ping on timeout, just continue
                continue
            
            except Exception as e:
                if self.running:
                    logging.error(f"Error processing commands from {address[0]}:{address[1]}: {str(e)}")
                break
        
        # Clean up when done
        try:
            client_socket.close()
        except:
            pass
        if client_socket in self.client_sockets:
            del self.client_sockets[client_socket]
        logging.info(f"Client disconnected: {address[0]}:{address[1]}")
    
    def _send_message(self, client_socket, message):
        """Send a message to a client"""
        try:
            json_str = message.to_json()
            data = json_str.encode('utf-8')
            
            # Send message length as 4 bytes
            length = len(data)
            client_socket.sendall(length.to_bytes(4, byteorder='big'))
            
            # Send the actual message
            client_socket.sendall(data)
            return True
        
        except Exception as e:
            if self.debug_mode:
                logging.error(f"Error sending message: {str(e)}")
            return False
    
    def _receive_message(self, client_socket):
        """Receive a message from a client"""
        try:
            # Get message length (4 bytes)
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return None
            
            if len(length_bytes) != 4:
                remote_logger.error(f"Incomplete length header received: {len(length_bytes)} bytes")
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Sanity check on message length
            if length <= 0 or length > 10 * 1024 * 1024:  # Max 10MB message
                remote_logger.error(f"Invalid message length: {length}")
                return None
            
            # Get the message data
            data = b''
            while len(data) < length:
                remaining = length - len(data)
                chunk = client_socket.recv(min(4096, remaining))
                if not chunk:
                    remote_logger.error(f"Connection closed while receiving message. Got {len(data)}/{length} bytes")
                    return None
                data += chunk
            
            # Parse the message
            try:
                json_str = data.decode('utf-8')
                return RemoteMessage.from_json(json_str)
            except UnicodeDecodeError as e:
                remote_logger.error(f"Failed to decode message as UTF-8: {e}")
                remote_logger.error(f"First 100 bytes: {data[:100]}")
                return None
        
        except Exception as e:
            if self.debug_mode:
                logging.error(f"Error receiving message: {str(e)}")
            return None
    
    def broadcast_message(self, message):
        """Broadcast a message to all authenticated clients"""
        for client_socket, (address, is_authenticated) in list(self.client_sockets.items()):
            if is_authenticated:
                try:
                    self._send_message(client_socket, message)
                except:
                    # Client probably disconnected
                    try:
                        client_socket.close()
                    except:
                        pass
                    if client_socket in self.client_sockets:
                        del self.client_sockets[client_socket]

class RemoteClient:
    """Client for connecting to the remote control server"""
    
    def __init__(self, host=None, port=40100, auth_key=None, message_handler=None, server_ip=None):
        # Support both 'host' and 'server_ip' parameter names for backward compatibility
        self.host = host if host is not None else server_ip
        if not self.host:
            raise ValueError("Host or server_ip must be provided.")
        self.port = port
        self.auth_key = auth_key
        self.message_handler = message_handler
        
        self.client_socket = None
        self.connected = False
        self.authenticated = False
        self.listener_thread = None
        self.running = False
        
        # Add a lock for socket operations to prevent concurrent access
        self.socket_lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def connect(self):
        """Connect to the remote server and authenticate."""
        if self.connected:
            return True

        if not self.auth_key:
            logging.error("Authentication key is not set.")
            return False
            
        try:
            logging.info(f"Connecting to server at {self.host}:{self.port}")
            
            # Create socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.client_socket.settimeout(30)
            
            # Connect to server
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            
            # Authenticate
            if not self._authenticate():
                self.disconnect()
                return False
            
            # Set socket to non-blocking mode for listener
            self.client_socket.setblocking(False)
            
            # Start listener thread for broadcast messages
            self.running = True
            self.listener_thread = threading.Thread(target=self._listen_for_broadcasts, daemon=True)
            self.listener_thread.start()
            
            logging.info("Successfully connected and authenticated")
            return True
            
        except socket.timeout:
            logging.error("Failed to connect to server: timed out")
            self.disconnect()
            return False
        except Exception as e:
            logging.error(f"Failed to connect to server: {str(e)}")
            self.disconnect()
            return False
    
    def _authenticate(self):
        """Authenticate with the server"""
        try:
            # Wait for auth request
            auth_request = self._receive_message_blocking()
            if not auth_request or auth_request.command != "AUTH":
                logging.error("Invalid authentication request")
                return False
            
            # Send auth response
            auth_response = RemoteMessage(
                command="AUTH",
                data={"auth_key": self.auth_key}
            )
            self._send_message_blocking(auth_response)
            
            # Wait for auth result
            auth_result = self._receive_message_blocking()
            if not auth_result or auth_result.command != "AUTH" or auth_result.status != "OK":
                logging.error("Authentication failed")
                return False
            
            self.authenticated = True
            return True
            
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return False
    
    def _listen_for_broadcasts(self):
        """Background thread that listens for broadcast messages from server"""
        logging.info("Started listening for broadcast messages")
        
        while self.running and self.connected:
            try:
                # Use select to check if data is available (non-blocking)
                import select
                ready_to_read, _, _ = select.select([self.client_socket], [], [], 1.0)
                
                if ready_to_read:
                    with self.socket_lock:
                        message = self._receive_message_nonblocking()
                        if message:
                            # Handle the broadcast message
                            if self.message_handler:
                                self.message_handler(message)
                            else:
                                logging.info(f"Received broadcast: {message.command}")
                        else:
                            # No message could mean connection closed
                            if not self.connected:
                                break
                        
            except Exception as e:
                if self.running:
                    logging.error(f"Error in listener thread: {str(e)}")
                    self.disconnect()
                break
        
        logging.info("Stopped listening for broadcast messages")
    
    def send_command(self, command, data=None):
        """Send a command and wait for response"""
        if not self.connected or not self.authenticated:
            logging.error("Not connected or authenticated")
            return None
        
        with self.socket_lock:
            try:
                # Send command
                message = RemoteMessage(command=command, data=data or {})
                self._send_message_blocking(message)
                
                # Wait for response with timeout
                self.client_socket.settimeout(30)
                response = self._receive_message_blocking()
                
                # Restore non-blocking mode
                self.client_socket.setblocking(False)
                
                return response
                
            except socket.timeout:
                logging.error(f"Timeout waiting for response to {command}")
                self.client_socket.setblocking(False)
                return None
            except Exception as e:
                logging.error(f"Error in send_command: {str(e)}")
                self.disconnect()
                return None
    
    def _send_message_blocking(self, message):
        """Send a message (blocking mode - use with lock)"""
        if not self.client_socket:
            return False
            
        try:
            json_str = message.to_json()
            data = json_str.encode('utf-8')
            
            # Send message length as 4 bytes
            length = len(data)
            self.client_socket.sendall(length.to_bytes(4, byteorder='big'))
            
            # Send the actual message
            self.client_socket.sendall(data)
            return True
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            return False
    
    def _receive_message_blocking(self):
        """Receive a message (blocking mode - use during auth)"""
        if not self.client_socket:
            return None
            
        try:
            # Get message length (4 bytes)
            length_bytes = self._recv_exact(4)
            if not length_bytes or len(length_bytes) != 4:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Sanity check
            if length <= 0 or length > 10 * 1024 * 1024:
                logging.error(f"Invalid message length: {length}")
                return None
            
            # Get the message data
            data = self._recv_exact(length)
            if not data or len(data) != length:
                return None
            
            # Parse the message
            json_str = data.decode('utf-8')
            return RemoteMessage.from_json(json_str)
            
        except Exception as e:
            logging.error(f"Error receiving message: {str(e)}")
            return None
    
    def _receive_message_nonblocking(self):
        """Receive a message (non-blocking mode - for listener)"""
        if not self.client_socket:
            return None
            
        try:
            # Get message length (4 bytes)
            length_bytes = self._recv_exact_nonblocking(4)
            if not length_bytes or len(length_bytes) != 4:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Sanity check
            if length <= 0 or length > 10 * 1024 * 1024:
                logging.error(f"Invalid message length: {length}")
                return None
            
            # Get the message data
            data = self._recv_exact_nonblocking(length)
            if not data or len(data) != length:
                return None
            
            # Parse the message
            json_str = data.decode('utf-8')
            return RemoteMessage.from_json(json_str)
            
        except Exception as e:
            logging.error(f"Error receiving message: {str(e)}")
            return None
    
    def _recv_exact(self, num_bytes):
        """Receive exactly num_bytes (blocking)"""
        data = b''
        while len(data) < num_bytes:
            chunk = self.client_socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _recv_exact_nonblocking(self, num_bytes):
        """Receive exactly num_bytes (non-blocking with timeout)"""
        import select
        data = b''
        start_time = time.time()
        timeout = 5.0  # 5 second timeout for receiving
        
        while len(data) < num_bytes:
            if time.time() - start_time > timeout:
                logging.error(f"Timeout receiving {num_bytes} bytes, got {len(data)}")
                return None
            
            # Wait for data to be available
            ready, _, _ = select.select([self.client_socket], [], [], 0.1)
            if ready:
                try:
                    chunk = self.client_socket.recv(num_bytes - len(data))
                    if not chunk:
                        return None
                    data += chunk
                except socket.error:
                    pass  # Would block, continue waiting
        
        return data
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        self.connected = False
        self.authenticated = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        # Wait for listener thread to finish
        if self.listener_thread and threading.current_thread() != self.listener_thread:
            try:
                self.listener_thread.join(timeout=2)
            except:
                pass
            
        logging.info("Disconnected from server")
