import os
import sys
import time
import socket
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# Set up logging for the remote app
logging.basicConfig(
    filename='remote_client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import the remote protocol
from remote_protocol import RemoteClient, RemoteMessage, STATUS_OK, STATUS_ERROR, STATUS_AUTH_REQUIRED
from remote_protocol import CMD_AUTH, CMD_SERVER_STATUS, CMD_START_SERVER, CMD_STOP_SERVER, CMD_RESTART_SERVER
from remote_protocol import CMD_BACKUP_DB, CMD_RESTORE_DB, CMD_GET_DB_BACKUPS
from remote_protocol import CMD_BACKUP_SERVER, CMD_RESTORE_SERVER, CMD_GET_SERVER_BACKUPS
from remote_protocol import CMD_UPDATE_TXADMIN, CMD_RESTORE_TXADMIN, CMD_GET_TXADMIN_BACKUPS
from remote_protocol import CMD_LOG_MESSAGE

# Import settings manager for remote app
from remote_settings import load_settings, save_settings

# Import colors from config
from config import COLORS

# Version constant
REMOTE_VERSION = "2.1"  # Keep in sync with main app

class ModernScrolledText(scrolledtext.ScrolledText):
    """Custom ScrolledText widget with Web 3.0 styling"""
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        
        # Apply custom styling with improved contrast
        self.config(
            background=COLORS['panel'],
            foreground=COLORS['text'],
            insertbackground=COLORS['text'],  # cursor color
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['text'],
            borderwidth=0,
            font=('Consolas', 9)
        )

def apply_styles():
    """Apply Web 3.0 styling to ttk widgets with improved contrast"""
    style = ttk.Style()
    
    # Configure the main theme
    style.configure("TFrame", background=COLORS['bg'])
    style.configure("TLabel", 
                    background=COLORS['bg'], 
                    foreground=COLORS['text'],
                    font=('Segoe UI', 10))
    
    # LabelFrame styling
    style.configure("TLabelframe", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
    style.configure("TLabelframe.Label", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'],
                    font=('Segoe UI', 11, 'bold'))
    
    # Button styling with improved contrast
    style.configure("TButton", 
                    background=COLORS['accent'],
                    foreground=COLORS['button_text'],
                    padding=10,
                    font=('Segoe UI', 10, 'bold'))
    style.map("TButton",
              background=[('active', COLORS['accent_hover'])],
              foreground=[('active', COLORS['button_text'])])
    
    # Primary action button
    style.configure("Primary.TButton", 
                    background=COLORS['accent'],
                    foreground=COLORS['button_text'],
                    padding=12,
                    font=('Segoe UI', 11, 'bold'))
    style.map("Primary.TButton",
              background=[('active', COLORS['accent_hover'])],
              foreground=[('active', COLORS['button_text'])])
    
    # Link-style button
    style.configure("Link.TButton", 
                    background=COLORS['bg'],
                    foreground=COLORS['accent'],
                    padding=2,
                    font=('Segoe UI', 9, 'underline'),
                    borderwidth=0)
    style.map("Link.TButton",
              background=[('active', COLORS['bg'])],
              foreground=[('active', COLORS['accent_hover'])])
    
    # Entry styling with black text for better visibility on light backgrounds
    style.configure("TEntry", 
                    fieldbackground=COLORS['panel'],
                    foreground='#000000',  # Black text for visibility
                    borderwidth=1,
                    padding=8)
    
    # Tab styling with improved visibility
    style.configure("TNotebook", 
                    background=COLORS['bg'],
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab", 
                    background=COLORS['tab_bg'],
                    foreground=COLORS['tab_fg'],
                    padding=[15, 5],
                    font=('Segoe UI', 10))
    style.map("TNotebook.Tab",
              background=[('selected', COLORS['tab_selected_bg'])],
              foreground=[('selected', COLORS['tab_selected_fg'])])
              
    # Make sure text is visible inside panels
    style.configure("TFrame.Label", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
                    
    # Fix contrast for labels inside panels
    style.configure("Panel.TLabel", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
    
    # Success and error styles for status indicators
    style.configure("Success.TLabel",
                    background=COLORS['panel'],
                    foreground='green',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Error.TLabel",
                    background=COLORS['panel'],
                    foreground='red',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Warning.TLabel",
                    background=COLORS['panel'],
                    foreground='orange',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Disconnected.TLabel",
                    background=COLORS['bg'],
                    foreground='red',
                    font=('Segoe UI', 10, 'bold'))
    style.configure("Connected.TLabel",
                    background=COLORS['bg'],
                    foreground='green',
                    font=('Segoe UI', 10, 'bold'))

class RemoteClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FIVEM & REDM Server Controller - Remote Client")
        self.root.geometry("850x650")
        self.root.configure(bg=COLORS['bg'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Load settings
        self.settings = load_settings()
        
        # Apply modern styling
        apply_styles()
        
        # Remote client
        self.client = None
        self.connected = False
        self.authenticated = False
        
        # Data storage
        self.db_backups = []
        self.server_backups = []
        self.txadmin_backups = []
        
        # Create main content
        self.create_connection_panel()
        
        # Create a notebook for tabs (hidden until connected)
        self.notebook = ttk.Notebook(root)
        
        # Create the tab content (similar to the main app)
        self.create_server_control_tab()
        self.create_server_backup_tab()
        self.create_database_backup_tab()
        self.create_txadmin_tab()
        self.create_log_tab()
        
        # Status bar at the bottom of the window
        status_bar = ttk.Frame(root, style="TFrame")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
        
        self.status_label = ttk.Label(
            status_bar, 
            text="Status: Not connected", 
            style="Disconnected.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Version label
        version_label = ttk.Label(
            status_bar, 
            text=f"v{REMOTE_VERSION} Remote", 
            foreground=COLORS['text_secondary'],
            font=('Segoe UI', 9)
        )
        version_label.pack(side=tk.RIGHT)
    
    def create_connection_panel(self):
        """Create the connection panel for server details and auth"""
        self.connection_frame = ttk.LabelFrame(self.root, text="Connect to Server")
        self.connection_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Server address
        server_frame = ttk.Frame(self.connection_frame)
        server_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            server_frame, 
            text="Server IP:"
        ).pack(side=tk.LEFT)
        
        self.server_ip_var = tk.StringVar(value=self.settings['connection']['server_ip'])
        server_ip_entry = ttk.Entry(
            server_frame,
            textvariable=self.server_ip_var,
            width=20
        )
        server_ip_entry.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(
            server_frame, 
            text="Port:"
        ).pack(side=tk.LEFT)
        
        self.server_port_var = tk.StringVar(value=str(self.settings['connection']['port']))
        server_port_entry = ttk.Entry(
            server_frame,
            textvariable=self.server_port_var,
            width=10
        )
        server_port_entry.pack(side=tk.LEFT, padx=10)
        
        # Authentication key
        auth_frame = ttk.Frame(self.connection_frame)
        auth_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            auth_frame, 
            text="Authentication Key:"
        ).pack(side=tk.LEFT)
        
        self.auth_key_var = tk.StringVar(value=self.settings['connection']['auth_key'])
        auth_key_entry = ttk.Entry(
            auth_frame,
            textvariable=self.auth_key_var,
            width=40
        )
        auth_key_entry.pack(side=tk.LEFT, padx=10)
        
        # Connect button
        button_frame = ttk.Frame(self.connection_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connect_button = ttk.Button(
            button_frame,
            text="Connect",
            command=self.connect_to_server,
            style="Primary.TButton"
        )
        self.connect_button.pack(side=tk.RIGHT)
        
        # Connection status
        status_frame = ttk.Frame(self.connection_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(
            status_frame,
            text="Connection Status:"
        ).pack(side=tk.LEFT)
        
        self.connection_status_var = tk.StringVar(value="Not Connected")
        self.connection_status_label = ttk.Label(
            status_frame,
            textvariable=self.connection_status_var,
            style="Disconnected.TLabel"
        )
        self.connection_status_label.pack(side=tk.LEFT, padx=10)
    
    def create_server_control_tab(self):
        """Create the server control tab"""
        self.server_control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.server_control_tab, text="Server Control")
        
        # Server status section
        status_frame = ttk.LabelFrame(self.server_control_tab, text="Server Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.server_status_var = tk.StringVar(value="Unknown")
        
        status_container = ttk.Frame(status_frame, style="TFrame")
        status_container.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            status_container,
            text="Current Status:",
            background=COLORS['panel'],
            font=('Segoe UI', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.server_status_label = ttk.Label(
            status_container,
            textvariable=self.server_status_var,
            foreground="gray",
            background=COLORS['panel'],
            font=('Segoe UI', 11, 'bold')
        )
        self.server_status_label.pack(side=tk.LEFT)
        
        # PID info (if server is running)
        self.server_pid_var = tk.StringVar(value="")
        self.server_pid_label = ttk.Label(
            status_frame,
            textvariable=self.server_pid_var,
            background=COLORS['panel'],
            foreground=COLORS['text_secondary']
        )
        self.server_pid_label.pack(padx=10, pady=(0, 10), anchor=tk.W)
        
        # Refresh status button
        refresh_button = ttk.Button(
            status_frame,
            text="Refresh Status",
            command=self.refresh_server_status
        )
        refresh_button.pack(anchor=tk.E, padx=10, pady=(0, 10))
        
        # Button container for server control actions
        button_frame = ttk.Frame(self.server_control_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Start Server button
        self.start_server_button = ttk.Button(
            button_frame, 
            text="Start Server",
            command=self.start_server,
            style="Primary.TButton"
        )
        self.start_server_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Stop Server button
        self.stop_server_button = ttk.Button(
            button_frame, 
            text="Stop Server",
            command=self.stop_server,
            style="TButton"
        )
        self.stop_server_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Restart Server button
        self.restart_server_button = ttk.Button(
            button_frame, 
            text="Restart Server",
            command=self.restart_server,
            style="TButton"
        )
        self.restart_server_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Command output section
        output_frame = ttk.LabelFrame(self.server_control_tab, text="Server Log")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_output = ModernScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            height=15
        )
        self.server_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.server_output.config(state=tk.DISABLED)
    
    def create_server_backup_tab(self):
        """Create the server backup tab"""
        self.server_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.server_tab, text="Server Backup")
        
        # Manual server backup button
        server_backup_button = ttk.Button(
            self.server_tab, 
            text="Run Manual Server Backup Now", 
            command=self.run_manual_server_backup,
            style="Primary.TButton"
        )
        server_backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Server restore section
        server_restore_frame = ttk.LabelFrame(self.server_tab, text="Restore Server")
        server_restore_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backups list
        backups_frame = ttk.Frame(server_restore_frame)
        backups_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrolled text widget for server backup list
        self.server_backup_list = ModernScrolledText(
            backups_frame, 
            wrap=tk.WORD, 
            height=15
        )
        self.server_backup_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.server_backup_list.config(state=tk.DISABLED)
        
        # Controls for restore
        controls_frame = ttk.Frame(server_restore_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Refresh button
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh Backup List",
            command=self.refresh_server_backups
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Restore controls
        restore_controls = ttk.Frame(controls_frame)
        restore_controls.pack(side=tk.RIGHT)
        
        ttk.Label(
            restore_controls,
            text="Backup #:"
        ).pack(side=tk.LEFT, padx=5)
        
        self.server_restore_var = tk.StringVar(value="1")
        server_restore_entry = ttk.Entry(
            restore_controls,
            textvariable=self.server_restore_var,
            width=5
        )
        server_restore_entry.pack(side=tk.LEFT, padx=5)
        
        restore_button = ttk.Button(
            restore_controls,
            text="Restore",
            command=self.restore_server_backup
        )
        restore_button.pack(side=tk.LEFT, padx=5)
    
    def create_database_backup_tab(self):
        """Create the database backup tab"""
        self.db_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.db_tab, text="Database Backup")
        
        # Manual backup button
        backup_button = ttk.Button(
            self.db_tab, 
            text="Run Manual Database Backup",
            command=self.run_manual_db_backup,
            style="Primary.TButton"
        )
        backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Database restore section
        db_restore_frame = ttk.LabelFrame(self.db_tab, text="Restore Database")
        db_restore_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backups list
        backups_frame = ttk.Frame(db_restore_frame)
        backups_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrolled text widget for database backup list
        self.db_backup_list = ModernScrolledText(
            backups_frame, 
            wrap=tk.WORD, 
            height=15
        )
        self.db_backup_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.db_backup_list.config(state=tk.DISABLED)
        
        # Controls for restore
        controls_frame = ttk.Frame(db_restore_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Refresh button
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh Backup List",
            command=self.refresh_db_backups
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Restore controls
        restore_controls = ttk.Frame(controls_frame)
        restore_controls.pack(side=tk.RIGHT)
        
        ttk.Label(
            restore_controls,
            text="Backup #:"
        ).pack(side=tk.LEFT, padx=5)
        
        self.db_restore_var = tk.StringVar(value="1")
        db_restore_entry = ttk.Entry(
            restore_controls,
            textvariable=self.db_restore_var,
            width=5
        )
        db_restore_entry.pack(side=tk.LEFT, padx=5)
        
        restore_button = ttk.Button(
            restore_controls,
            text="Restore",
            command=self.restore_db_backup
        )
        restore_button.pack(side=tk.LEFT, padx=5)
    
    def create_txadmin_tab(self):
        """Create the txAdmin tab"""
        self.txadmin_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.txadmin_tab, text="TxAdmin Update")
        
        # Update button
        update_button = ttk.Button(
            self.txadmin_tab, 
            text="Update TxAdmin (Latest Recommended)",
            command=self.update_txadmin,
            style="Primary.TButton"
        )
        update_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.txadmin_tab, text="Update Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.txadmin_progress_var = tk.DoubleVar()
        self.txadmin_progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.txadmin_progress_var,
            length=100, 
            mode='determinate'
        )
        self.txadmin_progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        self.txadmin_status_var = tk.StringVar(value="Ready to update")
        self.txadmin_status = ttk.Label(
            progress_frame,
            textvariable=self.txadmin_status_var,
            background=COLORS['panel'],
            wraplength=800
        )
        self.txadmin_status.pack(pady=(0, 10), padx=10, anchor=tk.W)
        
        # TxAdmin restore section
        txadmin_restore_frame = ttk.LabelFrame(self.txadmin_tab, text="Restore TxAdmin")
        txadmin_restore_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backups list
        backups_frame = ttk.Frame(txadmin_restore_frame)
        backups_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrolled text widget for txadmin backup list
        self.txadmin_backup_list = ModernScrolledText(
            backups_frame, 
            wrap=tk.WORD, 
            height=10
        )
        self.txadmin_backup_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.txadmin_backup_list.config(state=tk.DISABLED)
        
        # Controls for restore
        controls_frame = ttk.Frame(txadmin_restore_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Refresh button
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh Backup List",
            command=self.refresh_txadmin_backups
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Restore controls
        restore_controls = ttk.Frame(controls_frame)
        restore_controls.pack(side=tk.RIGHT)
        
        ttk.Label(
            restore_controls,
            text="Backup #:"
        ).pack(side=tk.LEFT, padx=5)
        
        self.txadmin_restore_var = tk.StringVar(value="1")
        txadmin_restore_entry = ttk.Entry(
            restore_controls,
            textvariable=self.txadmin_restore_var,
            width=5
        )
        txadmin_restore_entry.pack(side=tk.LEFT, padx=5)
        
        restore_button = ttk.Button(
            restore_controls,
            text="Restore",
            command=self.restore_txadmin
        )
        restore_button.pack(side=tk.LEFT, padx=5)
    
    def create_log_tab(self):
        """Create the log tab"""
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Activity Log")
        
        # Log output
        self.log_text = ModernScrolledText(
            self.log_tab, 
            wrap=tk.WORD, 
            height=30
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Controls frame
        controls_frame = ttk.Frame(self.log_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Clear log button
        clear_button = ttk.Button(
            controls_frame,
            text="Clear Log",
            command=self.clear_log
        )
        clear_button.pack(side=tk.RIGHT)
        
        # Send message to log
        message_frame = ttk.Frame(controls_frame)
        message_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.log_message_var = tk.StringVar()
        log_entry = ttk.Entry(
            message_frame,
            textvariable=self.log_message_var,
            width=50
        )
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        send_button = ttk.Button(
            message_frame,
            text="Send Message",
            command=self.send_log_message
        )
        send_button.pack(side=tk.LEFT)
        
        # Bind Enter key to send message
        log_entry.bind("<Return>", lambda event: self.send_log_message())
    
    def connect_to_server(self):
        """Connect to the remote server"""
        server_ip = self.server_ip_var.get().strip()
        
        try:
            port = int(self.server_port_var.get().strip())
            if not 1024 <= port <= 65535:
                messagebox.showerror("Invalid Port", "Port must be between 1024 and 65535")
                return
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be a number")
            return
            
        auth_key = self.auth_key_var.get().strip()
        if not auth_key:
            messagebox.showerror("Authentication Required", "Please enter an authentication key")
            return
        
        # Save settings for next time
        self.settings['connection']['server_ip'] = server_ip
        self.settings['connection']['port'] = port
        self.settings['connection']['auth_key'] = auth_key
        save_settings(self.settings)
        
        # Update UI
        self.connect_button.config(text="Connecting...", state="disabled")
        self.connection_status_var.set("Connecting...")
        self.log_to_ui("Connecting to server at " + server_ip + ":" + str(port))
        
        # Connect in a separate thread
        threading.Thread(target=self._do_connect, 
                        args=(server_ip, port, auth_key),
                        daemon=True).start()
    
    def _do_connect(self, server_ip, port, auth_key):
        """Thread function to connect to server"""
        try:
            # Initialize the client with the auth key
            self.client = RemoteClient(
                host=server_ip,
                port=port,
                auth_key=auth_key,
                message_handler=self.handle_server_message
            )
            
            # The connect() method now handles authentication internally.
            if self.client.connect():
                # Connection and auth successful
                self.connected = True
                self.authenticated = True
                self.root.after(0, lambda: self._update_connection_status(True, "Connected and authenticated"))
                
                # Get initial data
                self.root.after(100, self.initialize_data)
            else:
                # Connection or authentication failed
                self.root.after(0, lambda: self._update_connection_status(False, "Failed to connect or authenticate."))
            
        except Exception as e:
            error_message = str(e)  # Capture the error message immediately
            self.root.after(0, lambda err=error_message: self._update_connection_status(False, f"Connection error: {err}"))
    
    def _update_connection_status(self, success, message):
        """Update the connection status UI"""
        if success:
            self.connection_status_var.set("Connected")
            self.connection_status_label.config(style="Connected.TLabel")
            self.status_label.config(text="Status: Connected", style="Connected.TLabel")
            self.connect_button.config(text="Disconnect", command=self.disconnect_from_server)
            self.connect_button.config(state="normal")
            
            # Show the notebook
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            # Log success
            self.log_to_ui("Connected to server successfully")
            
        else:
            self.connection_status_var.set("Not Connected")
            self.connection_status_label.config(style="Disconnected.TLabel")
            self.status_label.config(text="Status: Not connected", style="Disconnected.TLabel")
            self.connect_button.config(text="Connect", command=self.connect_to_server)
            self.connect_button.config(state="normal")
            
            # Hide the notebook if it was shown
            if self.notebook.winfo_ismapped():
                self.notebook.pack_forget()
                
            # Log failure
            self.log_to_ui(f"Connection failed: {message}")
            
            # Clean up client if needed
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
                self.client = None
                self.connected = False
                self.authenticated = False
    
    def disconnect_from_server(self):
        """Disconnect from the server"""
        if not self.client:
            return
        
        self.log_to_ui("Disconnecting from server...")
        
        # Disable the button during disconnect
        self.connect_button.config(text="Disconnecting...", state="disabled")
        
        # Disconnect in a thread
        threading.Thread(target=self._do_disconnect, daemon=True).start()
    
    def _do_disconnect(self):
        """Thread function to disconnect from server"""
        try:
            if self.client:
                self.client.disconnect()
            
            self.client = None
            self.connected = False
            self.authenticated = False
            
            # Update UI
            self.root.after(0, lambda: self._update_connection_status(False, "Disconnected by user"))
            
        except Exception as e:
            self.log_to_ui(f"Error during disconnect: {str(e)}")
            # Still update UI
            self.root.after(0, lambda: self._update_connection_status(False, "Disconnected with errors"))
    
    def initialize_data(self):
        """Get initial data from the server after connecting"""
        self.refresh_server_status()
        self.refresh_db_backups()
        self.refresh_server_backups()
        self.refresh_txadmin_backups()
    
    def handle_server_message(self, message):
        """Handle messages received from the server"""
        command = message.command
        
        # Handle authentication response
        if command == CMD_AUTH:
            self.authenticated = (message.status == STATUS_OK)
            return
        
        # Handle disconnect notification
        if command == "DISCONNECT":
            self.root.after(0, lambda: self._update_connection_status(False, message.message))
            return
        
        # Handle server status updates
        if command == CMD_SERVER_STATUS:
            self._update_server_status(message)
            return
            
        # Handle database backup listing
        if command == CMD_GET_DB_BACKUPS:
            self._update_db_backups(message)
            return
            
        # Handle server backup listing
        if command == CMD_GET_SERVER_BACKUPS:
            self._update_server_backups(message)
            return
            
        # Handle txadmin backup listing
        if command == CMD_GET_TXADMIN_BACKUPS:
            self._update_txadmin_backups(message)
            return
            
        # Handle log messages
        if command == CMD_LOG_MESSAGE:
            if message.data and "message" in message.data:
                self.log_to_ui(message.data["message"], from_server=True)
            return
            
        # Handle progress updates
        if command == "PROGRESS_UPDATE":
            if message.data and "progress" in message.data:
                self._update_progress(message.message, message.data["progress"])
            return
            
        # Handle backup/restore results
        if command in [CMD_BACKUP_DB, CMD_RESTORE_DB, CMD_BACKUP_SERVER, CMD_RESTORE_SERVER,
                       CMD_UPDATE_TXADMIN, CMD_RESTORE_TXADMIN]:
            if message.status == STATUS_OK:
                self.log_to_ui(f"Success: {message.message}")
            else:
                self.log_to_ui(f"Error: {message.message}")
            return
            
        # Log any unknown or unhandled messages
        self.log_to_ui(f"Received from server: {command} - {message.status}: {message.message}")
    
    def _update_server_status(self, message):
        """Update the server status UI based on received message"""
        if message.status != STATUS_OK or not message.data:
            self.server_status_var.set("Unknown")
            self.server_status_label.config(foreground="gray")
            self.server_pid_var.set("")
            return
        
        status = message.data.get("status", "Unknown")
        running = message.data.get("running", False)
        pid = message.data.get("pid")
        
        # Update status display
        self.server_status_var.set(status)
        if running:
            self.server_status_label.config(foreground="green")
            self.server_pid_var.set(f"Process ID: {pid}")
            
            # Update button states
            self.start_server_button.config(state=tk.DISABLED)
            self.stop_server_button.config(state=tk.NORMAL)
            self.restart_server_button.config(state=tk.NORMAL)
        else:
            self.server_status_label.config(foreground="red")
            self.server_pid_var.set("")
            
            # Update button states
            self.start_server_button.config(state=tk.NORMAL)
            self.stop_server_button.config(state=tk.DISABLED)
            self.restart_server_button.config(state=tk.DISABLED)
    
    def _update_db_backups(self, message):
        """Update the database backups list"""
        if message.status != STATUS_OK or not message.data or "backups" not in message.data:
            self.db_backup_list.config(state=tk.NORMAL)
            self.db_backup_list.delete(1.0, tk.END)
            self.db_backup_list.insert(tk.END, "No backups found or error retrieving list")
            self.db_backup_list.config(state=tk.DISABLED)
            return
            
        backups = message.data["backups"]
        self.db_backups = backups  # Store for later use
        
        self.db_backup_list.config(state=tk.NORMAL)
        self.db_backup_list.delete(1.0, tk.END)
        
        if not backups:
            self.db_backup_list.insert(tk.END, "No database backups found")
        else:
            for i, backup in enumerate(backups, 1):
                self.db_backup_list.insert(tk.END, f"{i}. {backup['filename']} - {backup['date']}\n")
                
        self.db_backup_list.config(state=tk.DISABLED)
    
    def _update_server_backups(self, message):
        """Update the server backups list"""
        if message.status != STATUS_OK or not message.data or "backups" not in message.data:
            self.server_backup_list.config(state=tk.NORMAL)
            self.server_backup_list.delete(1.0, tk.END)
            self.server_backup_list.insert(tk.END, "No backups found or error retrieving list")
            self.server_backup_list.config(state=tk.DISABLED)
            return
            
        backups = message.data["backups"]
        self.server_backups = backups  # Store for later use
        
        self.server_backup_list.config(state=tk.NORMAL)
        self.server_backup_list.delete(1.0, tk.END)
        
        if not backups:
            self.server_backup_list.insert(tk.END, "No server backups found")
        else:
            for i, backup in enumerate(backups, 1):
                self.server_backup_list.insert(tk.END, f"{i}. {backup['filename']} - {backup['date']}\n")
                
        self.server_backup_list.config(state=tk.DISABLED)
    
    def _update_txadmin_backups(self, message):
        """Update the txAdmin backups list"""
        if message.status != STATUS_OK or not message.data or "backups" not in message.data:
            self.txadmin_backup_list.config(state=tk.NORMAL)
            self.txadmin_backup_list.delete(1.0, tk.END)
            self.txadmin_backup_list.insert(tk.END, "No backups found or error retrieving list")
            self.txadmin_backup_list.config(state=tk.DISABLED)
            return
            
        backups = message.data["backups"]
        self.txadmin_backups = backups  # Store for later use
        
        self.txadmin_backup_list.config(state=tk.NORMAL)
        self.txadmin_backup_list.delete(1.0, tk.END)
        
        if not backups:
            self.txadmin_backup_list.insert(tk.END, "No TxAdmin backups found")
        else:
            for i, backup in enumerate(backups, 1):
                self.txadmin_backup_list.insert(tk.END, f"{i}. {backup['filename']} - {backup['date']}\n")
                
        self.txadmin_backup_list.config(state=tk.DISABLED)
    
    def _update_progress(self, message, progress):
        """Update the progress bar and message for operations"""
        # Update txAdmin progress if on that tab
        self.txadmin_status_var.set(message)
        if progress is not None:
            self.txadmin_progress_var.set(progress)
        
        # Also log the progress message
        self.log_to_ui(message)
    
    def refresh_server_status(self):
        """Request server status from the server"""
        if not self.check_connection():
            return
            
        self.log_to_ui("Refreshing server status...")
        self.client.send_command(CMD_SERVER_STATUS)
    
    def refresh_db_backups(self):
        """Request database backup list from the server"""
        if not self.check_connection():
            return
            
        self.log_to_ui("Refreshing database backups list...")
        self.client.send_command(CMD_GET_DB_BACKUPS)
    
    def refresh_server_backups(self):
        """Request server backup list from the server"""
        if not self.check_connection():
            return
            
        self.log_to_ui("Refreshing server backups list...")
        self.client.send_command(CMD_GET_SERVER_BACKUPS)
    
    def refresh_txadmin_backups(self):
        """Request txAdmin backup list from the server"""
        if not self.check_connection():
            return
            
        self.log_to_ui("Refreshing TxAdmin backups list...")
        self.client.send_command(CMD_GET_TXADMIN_BACKUPS)
    
    def run_manual_db_backup(self):
        """Request a manual database backup"""
        if not self.check_connection():
            return
            
        if not messagebox.askyesno("Confirm Backup", "Run a database backup on the server?"):
            return
            
        self.log_to_ui("Requesting manual database backup...")
        self.client.send_command(CMD_BACKUP_DB)
    
    def run_manual_server_backup(self):
        """Request a manual server backup"""
        if not self.check_connection():
            return
            
        if not messagebox.askyesno("Confirm Backup", "Run a server backup? This may take some time."):
            return
            
        self.log_to_ui("Requesting manual server backup...")
        self.client.send_command(CMD_BACKUP_SERVER)
    
    def restore_db_backup(self):
        """Restore a database backup"""
        if not self.check_connection():
            return
            
        try:
            backup_num = int(self.db_restore_var.get())
            if backup_num < 1 or backup_num > len(self.db_backups):
                messagebox.showerror("Invalid Backup", f"Please enter a number between 1 and {len(self.db_backups)}")
                return
                
            # Get the backup
            backup = self.db_backups[backup_num - 1]
            
            # Confirm restore
            if not messagebox.askyesno("Confirm Restore", 
                                      f"Restore database from backup:\n{backup['filename']}?\n\n"
                                      "WARNING: This will overwrite the current database!",
                                      icon="warning"):
                return
                
            # Send restore request
            self.log_to_ui(f"Requesting database restore from backup #{backup_num}...")
            self.client.send_command(
                CMD_RESTORE_DB,
                data={"backup_index": backup_num - 1}  # Server uses 0-based index
            )
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid backup number")
        except IndexError:
            messagebox.showerror("Invalid Backup", "Backup not found")
    
    def restore_server_backup(self):
        """Restore a server backup"""
        if not self.check_connection():
            return
            
        try:
            backup_num = int(self.server_restore_var.get())
            if backup_num < 1 or backup_num > len(self.server_backups):
                messagebox.showerror("Invalid Backup", f"Please enter a number between 1 and {len(self.server_backups)}")
                return
                
            # Get the backup
            backup = self.server_backups[backup_num - 1]
            
            # Confirm restore
            if not messagebox.askyesno("Confirm Restore", 
                                      f"Restore server from backup:\n{backup['filename']}?\n\n"
                                      "WARNING: This will overwrite the current server files!",
                                      icon="warning"):
                return
                
            # Send restore request
            self.log_to_ui(f"Requesting server restore from backup #{backup_num}...")
            self.client.send_command(
                CMD_RESTORE_SERVER,
                data={"backup_index": backup_num - 1}  # Server uses 0-based index
            )
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid backup number")
        except IndexError:
            messagebox.showerror("Invalid Backup", "Backup not found")
    
    def update_txadmin(self):
        """Request TxAdmin update"""
        if not self.check_connection():
            return
            
        if not messagebox.askyesno("Confirm Update", "Update TxAdmin to the latest recommended version?"):
            return
            
        self.log_to_ui("Requesting TxAdmin update...")
        self.client.send_command(CMD_UPDATE_TXADMIN)
    
    def restore_txadmin(self):
        """Restore a TxAdmin backup"""
        if not self.check_connection():
            return
            
        try:
            backup_num = int(self.txadmin_restore_var.get())
            if backup_num < 1 or backup_num > len(self.txadmin_backups):
                messagebox.showerror("Invalid Backup", f"Please enter a number between 1 and {len(self.txadmin_backups)}")
                return
                
            # Get the backup
            backup = self.txadmin_backups[backup_num - 1]
            
            # Confirm restore
            if not messagebox.askyesno("Confirm Restore", 
                                      f"Restore TxAdmin from backup:\n{backup['filename']}?\n\n"
                                      "WARNING: This will overwrite the current TxAdmin installation!",
                                      icon="warning"):
                return
                
            # Send restore request
            self.log_to_ui(f"Requesting TxAdmin restore from backup #{backup_num}...")
            self.client.send_command(
                CMD_RESTORE_TXADMIN,
                data={"backup_index": backup_num - 1}  # Server uses 0-based index
            )
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid backup number")
        except IndexError:
            messagebox.showerror("Invalid Backup", "Backup not found")
    
    def start_server(self):
        """Request to start the server"""
        if not self.check_connection():
            return
            
        self.log_to_ui("Requesting server start...")
        self.client.send_command(CMD_START_SERVER)
    
    def stop_server(self):
        """Request to stop the server"""
        if not self.check_connection():
            return
            
        if not messagebox.askyesno("Confirm Stop", "Stop the server?"):
            return
            
        self.log_to_ui("Requesting server stop...")
        self.client.send_command(CMD_STOP_SERVER)
    
    def restart_server(self):
        """Request to restart the server"""
        if not self.check_connection():
            return
            
        if not messagebox.askyesno("Confirm Restart", "Restart the server?"):
            return
            
        self.log_to_ui("Requesting server restart...")
        self.client.send_command(CMD_RESTART_SERVER)
    
    def send_log_message(self):
        """Send a message to be logged on the server"""
        if not self.check_connection():
            return
            
        message_text = self.log_message_var.get().strip()
        if not message_text:
            return
            
        # Send the message
        self.client.send_command(
            CMD_LOG_MESSAGE,
            data={"message": message_text}
        )
        
        # Log locally
        self.log_to_ui(f"Sent: {message_text}")
        
        # Clear the input
        self.log_message_var.set("")
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_to_ui(self, message, from_server=False):
        """Add a message to the log display"""
        self.log_text.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        if from_server:
            self.log_text.insert(tk.END, f"[{timestamp}] SERVER: {message}\n")
            
            # Also update server output if appropriate
            self.server_output.config(state=tk.NORMAL)
            self.server_output.insert(tk.END, f"[{timestamp}] {message}\n")
            self.server_output.see(tk.END)
            self.server_output.config(state=tk.DISABLED)
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Also log to file
        logging.info(message)
    
    def check_connection(self):
        """Check if we're connected and authenticated, show error if not"""
        if not self.connected or not self.authenticated:
            messagebox.showerror("Not Connected", "Please connect to the server first")
            return False
        return True
    
    def on_close(self):
        """Clean up and exit"""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = RemoteClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
