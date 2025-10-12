import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import json
import logging
from datetime import datetime

from config import COLORS
from app.common import ModernScrolledText, apply_styles
from app.activity_log import ActivityLogTab
from remote_app.connection import RemoteConnectionTab
from remote_app.remote_tabs import (
    RemoteServerControlTab,
    RemoteServerBackupTab,
    RemoteDatabaseBackupTab,
    RemoteTxAdminUpdateTab
)
from remote_app.resource_monitor_tab import ResourceMonitorTab
from remote_protocol import RemoteClient, RemoteMessage, STATUS_OK, STATUS_ERROR
from remote_settings import load_settings, save_settings
from update import check_for_updates, CURRENT_VERSION

class RemoteBackupApp:
    """Remote client application for controlling the backup server"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("FIVEM & REDM Remote Controller")
        self.root.geometry("925x800")  # Increased from 850x800 to 925x800
        self.root.configure(bg=COLORS['bg'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Connection state
        self.client = None
        self.connected = False
        self.running = True
        
        # Load settings
        self.settings = load_settings()
        
        # Connection variables - load from settings
        self.server_ip_var = tk.StringVar(value=self.settings["connection"]["server_ip"])
        self.server_port_var = tk.StringVar(value=str(self.settings["connection"]["port"]))
        self.auth_key_var = tk.StringVar(value=self.settings["connection"]["auth_key"])
        self.connection_status_var = tk.StringVar(value="Disconnected")
        
        # Apply modern styling
        apply_styles()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Initialize data lists
        self.backup_files = []
        self.server_backup_files = []
        self.txadmin_backup_files = []
        
        # Create log for app-wide use
        self.log_text = ModernScrolledText(root, wrap=tk.WORD, height=1)
        self.log_text.config(state=tk.DISABLED)
        
        # Create tabs
        self.tabs = {}
        self.tabs['connection'] = RemoteConnectionTab(self.notebook, self)
        self.tabs['server_control'] = RemoteServerControlTab(self.notebook, self)
        self.tabs['server_backup'] = RemoteServerBackupTab(self.notebook, self)
        self.tabs['database_backup'] = RemoteDatabaseBackupTab(self.notebook, self)
        self.tabs['txadmin_update'] = RemoteTxAdminUpdateTab(self.notebook, self)
        self.tabs['resource_monitor'] = ResourceMonitorTab(self.notebook, self)
        self.tabs['activity_log'] = ActivityLogTab(self.notebook, self)
        
        # Manually add resource monitor tab (it doesn't add itself)
        self.notebook.add(self.tabs['resource_monitor'].tab, text="Resources")
        self.tabs['resource_monitor'].tab_index = 5  # Index in notebook
        
        # Use activity log's text widget
        self.log_text = self.tabs['activity_log'].log_text
        
        # Disable tabs until connected
        self.set_tabs_state(tk.DISABLED)
        self.notebook.tab(0, state="normal")  # Keep connection tab enabled
        self.notebook.tab(6, state="normal")  # Keep activity log enabled (now index 6)
        
        # Status bar
        status_bar = ttk.Frame(root, style="TFrame")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
        
        self.status_label = ttk.Label(
            status_bar,
            text="Status: Not Connected",
            foreground='red',
            font=('Segoe UI', 9, 'bold')
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Version label
        version_label = ttk.Label(
            status_bar,
            text=f"Remote Client v{CURRENT_VERSION}",
            foreground=COLORS['text_secondary'],
            font=('Segoe UI', 9)
        )
        version_label.pack(side=tk.RIGHT)
        
        # Log app start
        self.log_message("Remote Control Client started")
        
        # Check for updates
        self.check_for_app_updates()
    
    def set_tabs_state(self, state):
        """Enable or disable all tabs except connection and log"""
        for i in range(1, 6):  # Server control through Resource Monitor
            self.notebook.tab(i, state=state)
    
    def is_connected(self):
        """Check if connected to server"""
        return self.connected and self.client and self.client.connected
    
    def connect_to_server(self):
        """Connect to the remote server"""
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        auth_key = self.auth_key_var.get().strip()
        
        if not ip or not port or not auth_key:
            messagebox.showerror("Error", "Please fill in all connection fields")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return
        
        # Disable connect button
        self.tabs['connection'].connect_btn.config(state=tk.DISABLED)
        self.log_message(f"Connecting to {ip}:{port}...")
        
        # Connect in separate thread
        def do_connect():
            try:
                # Pass message handler that will process broadcasts
                self.client = RemoteClient(
                    ip, 
                    port, 
                    auth_key, 
                    message_handler=self.handle_broadcast_message
                )
                if self.client.connect():
                    self.connected = True
                    self.root.after(0, self.on_connected)
                else:
                    self.root.after(0, lambda: self.on_connection_failed("Connection refused"))
            except Exception as exc:
                error_msg = str(exc)
                self.root.after(0, lambda msg=error_msg: self.on_connection_failed(msg))
        
        threading.Thread(target=do_connect, daemon=True).start()
    
    def handle_broadcast_message(self, message):
        """Handle broadcast messages from server (called by listener thread)"""
        if message:
            # Schedule handling on main thread to avoid threading issues
            self.root.after(0, lambda m=message: self.handle_response(m))
    
    def handle_message(self, message):
        """Handle incoming messages from server"""
        if message:
            self.root.after(0, lambda m=message: self.handle_response(m))
    
    def on_connected(self):
        """Called when successfully connected"""
        self.log_message("Connected successfully!")
        self.connection_status_var.set("Connected")
        self.status_label.config(text="Status: Connected", foreground='green')
        
        # Save connection settings
        self.save_connection_settings()
        
        # Update UI
        self.tabs['connection'].connect_btn.config(state=tk.DISABLED)
        self.tabs['connection'].disconnect_btn.config(state=tk.NORMAL)
        self.tabs['connection'].status_label.config(style="Connected.TLabel")
        
        # Enable tabs
        self.set_tabs_state(tk.NORMAL)
        
        # Request initial data ONCE - after that, server will broadcast ALL changes
        self.root.after(500, self.request_initial_data)
        
        # NO POLLING - server broadcasts everything when it changes
    
    def save_connection_settings(self):
        """Save connection settings for next time"""
        try:
            self.settings["connection"]["server_ip"] = self.server_ip_var.get().strip()
            self.settings["connection"]["port"] = int(self.server_port_var.get().strip())
            self.settings["connection"]["auth_key"] = self.auth_key_var.get().strip()
            save_settings(self.settings)
            self.log_message("Connection settings saved")
        except Exception as e:
            logging.error(f"Failed to save connection settings: {e}")
    
    def on_connection_failed(self, error):
        """Called when connection fails"""
        self.log_message(f"Connection failed: {error}")
        messagebox.showerror("Connection Failed", f"Could not connect to server:\n{error}")
        self.tabs['connection'].connect_btn.config(state=tk.NORMAL)
        self.connected = False
        self.client = None
    
    def disconnect_from_server(self):
        """Disconnect from the remote server"""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.connected = False
        self.connection_status_var.set("Disconnected")
        self.status_label.config(text="Status: Not Connected", foreground='red')
        
        # Update UI
        self.tabs['connection'].connect_btn.config(state=tk.NORMAL)
        self.tabs['connection'].disconnect_btn.config(state=tk.DISABLED)
        self.tabs['connection'].status_label.config(style="Disconnected.TLabel")
        
        # Disable tabs
        self.set_tabs_state(tk.DISABLED)
        
        self.log_message("Disconnected from server")
    
    def request_initial_data(self):
        """Request initial data from server"""
        def fetch_data():
            try:
                # Get server status
                response = self.client.send_command("GET_SERVER_STATUS")
                if response:
                    self.root.after(0, lambda r=response: self.handle_response(r))
                
                # Get database backups
                response = self.client.send_command("GET_DATABASE_BACKUPS")
                if response:
                    self.root.after(0, lambda r=response: self.handle_response(r))
                
                # Get server backups
                response = self.client.send_command("GET_SERVER_BACKUPS")
                if response:
                    self.root.after(0, lambda r=response: self.handle_response(r))
                
                # Get TxAdmin backups
                response = self.client.send_command("GET_TXADMIN_BACKUPS")
                if response:
                    self.root.after(0, lambda r=response: self.handle_response(r))
                
                # Get next backup time
                response = self.client.send_command("GET_NEXT_BACKUP_TIME")
                if response:
                    self.root.after(0, lambda r=response: self.handle_response(r))
                    
            except Exception as e:
                self.log_message(f"Error fetching initial data: {e}")
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=fetch_data, daemon=True).start()
    
    def send_command(self, command, data=None):
        """Send a command to the remote server and get response"""
        if not self.is_connected():
            self.log_message("Not connected - cannot send command")
            return
        
        def do_send():
            try:
                response = self.client.send_command(command, data)
                if response:
                    # Handle command response
                    self.root.after(0, lambda r=response: self.handle_response(r))
                else:
                    self.log_message(f"No response for command: {command}")
                    # Check if we're still connected
                    if not self.client.connected:
                        self.root.after(0, self.disconnect_from_server)
            except Exception as e:
                self.log_message(f"Error sending command {command}: {e}")
                self.root.after(0, self.disconnect_from_server)
        
        # Run in background thread
        threading.Thread(target=do_send, daemon=True).start()
    
    def receive_messages(self):
        """Receive messages from server in background thread"""
        # This is no longer needed since RemoteClient handles receiving in its own thread
        pass
    
    def handle_response(self, message):
        """Handle a response from the server"""
        if not message:
            return
        
        # Log for debugging
        logging.info(f"Handling response: {message.command}")
        
        # Handle disconnect message
        if message.command == "DISCONNECT":
            self.log_message("Server connection lost")
            self.root.after(0, self.disconnect_from_server)
            return
        
        # Handle PING (keepalive) messages
        if message.command == "PING":
            return
        
        if message.command == "LOG_MESSAGE":
            # Remote log message - DO NOT add [Remote] prefix since it's already in the message
            msg = message.data.get('message', '')
            # Only log to activity log, not to connection log
            from app.common import log_message
            log_message(self.log_text, msg)
        
        elif message.command == "SERVER_STATUS":
            # Update server status
            status = message.data.get('status', 'UNKNOWN')
            pid = message.data.get('pid')
            
            self.tabs['server_control'].server_status_var.set(status)
            
            if status == "RUNNING":
                self.tabs['server_control'].server_status_label.config(foreground="green")
                self.tabs['server_control'].start_server_button.config(state=tk.DISABLED)
                self.tabs['server_control'].stop_server_button.config(state=tk.NORMAL)
                self.tabs['server_control'].restart_server_button.config(state=tk.NORMAL)
                if pid:
                    self.tabs['server_control'].server_pid_var.set(f"Process ID: {pid}")
            else:
                self.tabs['server_control'].server_status_label.config(foreground="red")
                self.tabs['server_control'].start_server_button.config(state=tk.NORMAL)
                self.tabs['server_control'].stop_server_button.config(state=tk.DISABLED)
                self.tabs['server_control'].restart_server_button.config(state=tk.DISABLED)
                self.tabs['server_control'].server_pid_var.set("")
            
            logging.info(f"Updated server status to: {status}")
        
        elif message.command == "DATABASE_BACKUPS":
            # Update database backup list - convert dict back to tuple
            backups_data = message.data.get('backups', [])
            self.backup_files = [(b['path'], b['timestamp'], b['filename']) for b in backups_data]
            self.tabs['database_backup'].backup_files = self.backup_files
            self.tabs['database_backup'].update_backup_list()
            logging.info(f"Updated database backups: {len(self.backup_files)} backups")
        
        elif message.command == "SERVER_BACKUPS":
            # Update server backup list - convert dict back to tuple
            backups_data = message.data.get('backups', [])
            self.server_backup_files = [(b['path'], b['timestamp'], b['filename']) for b in backups_data]
            self.tabs['server_backup'].server_backup_files = self.server_backup_files
            self.tabs['server_backup'].update_server_backup_list()
            logging.info(f"Updated server backups: {len(self.server_backup_files)} backups")
        
        elif message.command == "TXADMIN_BACKUPS":
            # Update TxAdmin backup list - convert dict back to tuple
            backups_data = message.data.get('backups', [])
            self.txadmin_backup_files = [(b['path'], b['timestamp'], b['filename']) for b in backups_data]
            self.tabs['txadmin_update'].txadmin_backup_files = self.txadmin_backup_files
            self.tabs['txadmin_update'].update_txadmin_backup_list()
            logging.info(f"Updated TxAdmin backups: {len(self.txadmin_backup_files)} backups")
        
        elif message.command == "NEXT_BACKUP_TIME":
            # Update next backup time using timestamp for accurate sync
            next_time = message.data.get('next_backup_time')
            next_backup_timestamp = message.data.get('next_backup_timestamp')
            backup_type = message.data.get('backup_type')
            
            if next_time and next_backup_timestamp and backup_type:
                # Pass timestamp to the tab so it can calculate countdown locally
                self.tabs['database_backup'].set_next_backup_time(
                    next_backup_timestamp,
                    backup_type,
                    next_time
                )
                logging.info(f"Updated next backup time: {next_time} (timestamp: {next_backup_timestamp})")
        
        elif message.command == "PROGRESS_UPDATE":
            # Update progress (for TxAdmin updates, server backups, etc.)
            progress = message.data.get('progress', 0)
            msg = message.data.get('message', '')
            
            # Update TxAdmin progress if applicable
            if hasattr(self.tabs['txadmin_update'], 'update_txadmin_status'):
                self.tabs['txadmin_update'].update_txadmin_status(msg, progress)
            
            logging.info(f"Progress update: {msg} ({progress}%)")
        
        elif message.command == "RESOURCE_STATS":
            # Update resource monitor with new stats
            stats = message.data
            if hasattr(self.tabs.get('resource_monitor'), 'update_stats'):
                self.tabs['resource_monitor'].update_stats(stats)
            logging.debug("Updated resource stats")
    
    def log_message(self, message):
        """Add a message to the log display"""
        from app.common import log_message
        log_message(self.log_text, message)
        
        # Also log connection messages to connection tab
        if hasattr(self.tabs.get('connection'), 'log_connection'):
            self.tabs['connection'].log_connection(message)
    
    def check_for_app_updates(self):
        """Check for application updates"""
        threading.Thread(
            target=lambda: check_for_updates(self.root),
            daemon=True
        ).start()
    
    def on_close(self):
        """Clean up when window is closed"""
        # Save settings before closing
        try:
            self.save_connection_settings()
        except:
            pass  # Don't fail on close if settings can't be saved
        
        self.running = False
        if self.client:
            self.client.disconnect()
        self.root.destroy()