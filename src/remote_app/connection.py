import tkinter as tk
from tkinter import ttk, messagebox
import threading

from config import COLORS
from app.common import ModernScrolledText

class RemoteConnectionTab:
    """Connection tab specific to remote client"""
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Connection", state="normal")
        
        self.create_tab_contents()
    
    def create_tab_contents(self):
        """Create the connection UI"""
        # Connection settings
        conn_frame = ttk.LabelFrame(self.tab, text="Server Connection")
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Server IP
        ip_frame = ttk.Frame(conn_frame)
        ip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ip_frame, text="Server IP:", width=15).pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(ip_frame, textvariable=self.app.server_ip_var, width=30)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        # Server Port
        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(port_frame, text="Port:", width=15).pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame, textvariable=self.app.server_port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # Auth Key
        auth_frame = ttk.Frame(conn_frame)
        auth_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(auth_frame, text="Auth Key:", width=15).pack(side=tk.LEFT)
        self.auth_entry = ttk.Entry(auth_frame, textvariable=self.app.auth_key_var, width=30, show="•")
        self.auth_entry.pack(side=tk.LEFT, padx=5)
        
        # Show/Hide button
        self.show_auth_btn = ttk.Button(auth_frame, text="👁", width=3, command=self.toggle_auth_visibility)
        self.show_auth_btn.pack(side=tk.LEFT, padx=2)
        
        # Connect/Disconnect buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connect_btn = ttk.Button(
            button_frame,
            text="Connect to Server",
            command=self.app.connect_to_server,
            style="Primary.TButton"
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.disconnect_btn = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self.app.disconnect_from_server,
            state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Connection Status
        status_frame = ttk.LabelFrame(self.tab, text="Connection Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.app.connection_status_var,
            font=('Segoe UI', 11, 'bold')
        )
        self.status_label.pack(pady=10, padx=10)
        
        # Connection Log
        log_frame = ttk.LabelFrame(self.tab, text="Connection Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.connection_log = ModernScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.connection_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.connection_log.config(state=tk.DISABLED)
    
    def toggle_auth_visibility(self):
        """Toggle visibility of auth key"""
        if self.auth_entry.cget('show') == '•':
            self.auth_entry.config(show='')
        else:
            self.auth_entry.config(show='•')
    
    def log_connection(self, message):
        """Add message to connection log"""
        from datetime import datetime
        
        self.connection_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.connection_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.connection_log.see(tk.END)
        self.connection_log.config(state=tk.DISABLED)
