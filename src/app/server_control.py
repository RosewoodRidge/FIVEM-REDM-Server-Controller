import tkinter as tk
from tkinter import ttk
import threading
import time

from config import COLORS, TXADMIN_SERVER_DIR
from app.common import ModernScrolledText
from txadmin import find_fxserver_processes, start_fxserver, stop_fxserver

class ServerControlTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Server Control")
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # Server control info
        control_info_frame = ttk.LabelFrame(self.tab, text="Server Information")
        control_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            control_info_frame,
            text=f"Server executable: {TXADMIN_SERVER_DIR}\\FXServer.exe",
            background=COLORS['panel'],
            foreground=COLORS['text_secondary'],
            wraplength=800
        ).pack(pady=(5, 5), padx=10, anchor=tk.W)
        
        # Server status section
        status_frame = ttk.LabelFrame(self.tab, text="Server Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.server_status_var = tk.StringVar(value="Checking...")
        self.server_status_color_var = tk.StringVar(value=COLORS['text_secondary'])
        
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
            foreground=COLORS['accent'],
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
        
        # Button container for server control actions
        button_frame = ttk.Frame(self.tab)
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
        output_frame = ttk.LabelFrame(self.tab, text="Command Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_output = ModernScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            height=15
        )
        self.server_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.server_output.config(state=tk.DISABLED)
    
    def update_server_status(self):
        """Update the server status display"""
        try:
            processes = find_fxserver_processes()
            if processes:
                # Server is running
                self.server_status_var.set("RUNNING")
                self.server_status_label.config(foreground="green")
                pid = processes[0].pid
                self.server_pid_var.set(f"Process ID: {pid}")
                
                # Update button states
                self.start_server_button.config(state=tk.DISABLED)
                self.stop_server_button.config(state=tk.NORMAL)
                self.restart_server_button.config(state=tk.NORMAL)
            else:
                # Server is not running
                self.server_status_var.set("STOPPED")
                self.server_status_label.config(foreground="red")
                self.server_pid_var.set("")
                
                # Update button states
                self.start_server_button.config(state=tk.NORMAL)
                self.stop_server_button.config(state=tk.DISABLED)
                self.restart_server_button.config(state=tk.DISABLED)
                
            # Broadcast server status to remote clients if available
            if hasattr(self.app, 'broadcast_server_status'):
                self.app.broadcast_server_status()
        except Exception as e:
            self.server_status_var.set("ERROR")
            self.server_status_label.config(foreground="orange")
            self.server_pid_var.set(f"Error checking status: {str(e)}")
        
        # Schedule the next update in 3 seconds
        self.app.root.after(3000, self.update_server_status)
    
    def server_log(self, message):
        """Add a message to the server control log display"""
        from datetime import datetime
        
        self.server_output.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.server_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.server_output.see(tk.END)
        self.server_output.config(state=tk.DISABLED)
        
        # Also add to the main log (which will broadcast to remote)
        self.app.log_message(message)
    
    def start_server(self):
        """Start the FXServer.exe process"""
        self.server_log("Starting FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_start():
            def callback(msg):
                self.server_log(msg)
            
            success, message = start_fxserver(callback=callback)
            if success:
                self.server_log("Server started successfully")
            else:
                self.server_log(f"Failed to start server: {message}")
            
            # Broadcast status change to remote clients
            if hasattr(self.app, 'broadcast_server_status'):
                self.app.broadcast_server_status()
        
        threading.Thread(target=do_start, daemon=True).start()
    
    def stop_server(self):
        """Stop the FXServer.exe process"""
        self.server_log("Stopping FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_stop():
            def callback(msg):
                self.server_log(msg)
            
            was_running, success, message = stop_fxserver(callback=callback)
            if success:
                self.server_log("Server stopped successfully")
            else:
                self.server_log(f"Failed to stop server: {message}")
            
            # Broadcast status change to remote clients
            if hasattr(self.app, 'broadcast_server_status'):
                self.app.broadcast_server_status()
        
        threading.Thread(target=do_stop, daemon=True).start()
    
    def restart_server(self):
        """Restart the FXServer.exe process"""
        self.server_log("Restarting FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_restart():
            def callback(msg):
                self.server_log(msg)
            
            # First stop the server
            was_running, stop_success, server_path = stop_fxserver(callback=callback)
            
            if not stop_success:
                self.server_log("Failed to stop server during restart")
                return
            
            # Wait a moment
            time.sleep(2)
            
            # Then start it again
            start_success, start_message = start_fxserver(
                server_path=server_path if isinstance(server_path, str) else None, 
                callback=callback
            )
            
            if start_success:
                self.server_log("Server restarted successfully")
            else:
                self.server_log(f"Failed to restart server: {start_message}")
            
            # Broadcast status change to remote clients
            if hasattr(self.app, 'broadcast_server_status'):
                self.app.broadcast_server_status()
        
        threading.Thread(target=do_restart, daemon=True).start()
