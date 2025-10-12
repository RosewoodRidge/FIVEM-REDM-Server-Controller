import os
import socket
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from config import COLORS
from app.common import ModernScrolledText, update_setting
from remote_protocol import RemoteServer, RemoteMessage, STATUS_OK, STATUS_ERROR
from utils import add_firewall_rule

class RemoteControlTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Remote Control")
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # Remote control settings
        remote_control_frame = ttk.LabelFrame(self.tab, text="Remote Control Settings")
        remote_control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Enable/disable remote control
        self.remote_enabled_var = tk.BooleanVar(value=self.app.settings["remote_control"]["enabled"])
        ttk.Checkbutton(
            remote_control_frame,
            text="Enable Remote Control",
            variable=self.remote_enabled_var,
            command=self.toggle_remote_control
        ).pack(anchor=tk.W, pady=10, padx=10)
        
        # Connection info section
        connection_frame = ttk.LabelFrame(self.tab, text="Connection Information")
        connection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # IP address info
        ip_frame = ttk.Frame(connection_frame)
        ip_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(
            ip_frame,
            text="Server IP:",
            width=15
        ).pack(side=tk.LEFT)
        
        self.ip_var = tk.StringVar(value="Detecting...")
        ttk.Label(
            ip_frame,
            textvariable=self.ip_var,
            font=('Segoe UI', 10, 'bold')
        ).pack(side=tk.LEFT)
        
        # Port info
        port_frame = ttk.Frame(connection_frame)
        port_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(
            port_frame,
            text="Port:",
            width=15
        ).pack(side=tk.LEFT)
        
        self.port_var = tk.StringVar(value=str(self.app.settings["remote_control"]["port"]))
        port_entry = ttk.Entry(
            port_frame,
            textvariable=self.port_var,
            width=10
        )
        port_entry.pack(side=tk.LEFT)
        
        # Auth key section
        auth_frame = ttk.LabelFrame(self.tab, text="Authentication Key")
        auth_frame.pack(fill=tk.X, padx=10, pady=10)
        
        saved_auth_key = self.app.settings["remote_control"]["auth_key"] or "Not generated"
        self.auth_key_var = tk.StringVar(value=saved_auth_key)
        
        ttk.Label(
            auth_frame,
            text="Connect using this authentication key:"
        ).pack(anchor=tk.W, pady=(10, 5), padx=10)
        
        # Container for auth key entry and buttons
        auth_entry_frame = ttk.Frame(auth_frame)
        auth_entry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Show auth key in a readonly entry (password style by default)
        self.auth_key_entry = ttk.Entry(
            auth_entry_frame,
            textvariable=self.auth_key_var,
            width=40,
            state="readonly",
            show="•"
        )
        self.auth_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Eye icon button to show/hide
        self.auth_key_visible = False
        self.show_auth_button = ttk.Button(
            auth_entry_frame,
            text="👁",
            width=3,
            command=self.toggle_auth_key_visibility
        )
        self.show_auth_button.pack(side=tk.LEFT, padx=2)
        
        # Copy button
        copy_button = ttk.Button(
            auth_entry_frame,
            text="📋 Copy",
            width=8,
            command=self.copy_auth_key
        )
        copy_button.pack(side=tk.LEFT, padx=2)
        
        # Button to regenerate key
        ttk.Button(
            auth_frame,
            text="Generate New Key",
            command=self.generate_new_auth_key
        ).pack(pady=10)
        
        # IP Whitelist section
        whitelist_frame = ttk.LabelFrame(self.tab, text="IP Whitelist (Optional)")
        whitelist_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Enable whitelist checkbox
        self.whitelist_enabled_var = tk.BooleanVar(value=self.app.settings["remote_control"].get("whitelist_enabled", False))
        ttk.Checkbutton(
            whitelist_frame,
            text="Enable IP Whitelist (Only allow specific IPs to connect)",
            variable=self.whitelist_enabled_var,
            command=self.toggle_whitelist
        ).pack(anchor=tk.W, pady=10, padx=10)
        
        # Whitelisted IPs list
        ttk.Label(
            whitelist_frame,
            text="Whitelisted IP Addresses:"
        ).pack(anchor=tk.W, pady=(0, 5), padx=10)
        
        self.whitelist_text = ModernScrolledText(
            whitelist_frame, 
            wrap=tk.WORD, 
            height=5
        )
        self.whitelist_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Add IP controls
        add_ip_frame = ttk.Frame(whitelist_frame)
        add_ip_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(
            add_ip_frame,
            text="Add IP:"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_ip_var = tk.StringVar()
        ttk.Entry(
            add_ip_frame,
            textvariable=self.add_ip_var,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            add_ip_frame,
            text="Add",
            command=self.add_ip_to_whitelist
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            add_ip_frame,
            text="Remove Selected",
            command=self.remove_ip_from_whitelist
        ).pack(side=tk.LEFT, padx=5)
        
        # Connected clients section
        clients_frame = ttk.LabelFrame(self.tab, text="Connected Clients")
        clients_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrolled text widget for connected clients list
        self.clients_list = ModernScrolledText(
            clients_frame, 
            wrap=tk.WORD, 
            height=10
        )
        self.clients_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.clients_list.config(state=tk.DISABLED)
        self.clients_list.insert(tk.END, "No clients connected")
        
        # Get and display local IP address
        self.detect_ip_address()
        
        # Update whitelist display
        self.update_whitelist_display()

    def detect_ip_address(self):
        """Detect and display the local IP address"""
        try:
            # Get the hostname
            hostname = socket.gethostname()
            # Get the local IP address using the hostname
            ip_address = socket.gethostbyname(hostname)
            
            self.ip_var.set(ip_address)
        except Exception as e:
            self.ip_var.set(f"Error: {str(e)}")

    def toggle_remote_control(self):
        """Enable or disable remote control"""
        if self.remote_enabled_var.get():
            # Enable remote control
            try:
                port = int(self.port_var.get())
                if not (1024 <= port <= 65535):
                    raise ValueError("Port must be between 1024 and 65535")
                
                # Save port to settings
                update_setting("remote_control", "port", port)
                
                # Use saved auth key if one exists
                saved_auth_key = self.app.settings["remote_control"]["auth_key"]
                
                self.app.remote_server = RemoteServer(port=port, command_handler=self.app.handle_remote_command)
                
                # If we have a saved key, use it instead of generating a new one
                if saved_auth_key:
                    self.app.remote_server.auth_key = saved_auth_key
                    self.app.remote_server.auth_salt, self.app.remote_server.auth_hash = self.app.remote_server.hash_auth_key(saved_auth_key)
                    self.app.log_message(f"Using saved authentication key")
                
                if self.app.remote_server.start():
                    self.app.remote_enabled = True
                    self.auth_key_var.set(self.app.remote_server.auth_key)
                    
                    # Save the auth key and enabled state
                    update_setting("remote_control", "auth_key", self.app.remote_server.auth_key)
                    update_setting("remote_control", "enabled", True)
                    
                    self.app.log_message(f"Remote control server started on port {port}")
                    
                    # Automatically add firewall rule
                    self.ensure_firewall_rule(port)
                    
                    self.update_clients_list()
                else:
                    self.remote_enabled_var.set(False)
                    update_setting("remote_control", "enabled", False)
                    self.app.log_message("Failed to start remote control server")
            except Exception as e:
                self.remote_enabled_var.set(False)
                update_setting("remote_control", "enabled", False)
                self.app.log_message(f"Failed to start remote control server: {e}")
        else:
            # Disable remote control
            if self.app.remote_server:
                self.app.remote_server.stop()
                self.app.remote_server = None
                self.app.remote_enabled = False
                
                # Save disabled state
                update_setting("remote_control", "enabled", False)
                
                self.app.log_message("Remote control server stopped")
                
                # Clear clients list
                self.clients_list.config(state=tk.NORMAL)
                self.clients_list.delete(1.0, tk.END)
                self.clients_list.insert(tk.END, "No clients connected")
                self.clients_list.config(state=tk.DISABLED)
    
    def ensure_firewall_rule(self, port):
        """Check for and add a firewall rule for the given port."""
        rule_name = "FIVEM-REDM-Controller-Remote"
        success, message = add_firewall_rule(rule_name, port)
        self.app.log_message(message)
        if not success:
            # If it fails, inform the user they may need to add it manually
            messagebox.showwarning("Firewall Rule", 
                               "Could not automatically add a Windows Firewall rule. "
                               "You may need to run this application as an Administrator or "
                               f"manually allow TCP traffic on port {port}.")

    def update_clients_list(self):
        """Update the list of connected clients"""
        if not self.app.remote_server:
            return
            
        self.clients_list.config(state=tk.NORMAL)
        self.clients_list.delete(1.0, tk.END)
        
        if not self.app.remote_server.client_sockets:
            self.clients_list.insert(tk.END, "No clients connected")
        else:
            for sock, (address, is_authenticated) in self.app.remote_server.client_sockets.items():
                status = "Authenticated" if is_authenticated else "Not authenticated"
                self.clients_list.insert(tk.END, f"{address[0]}:{address[1]} - {status}\n")
        
        self.clients_list.config(state=tk.DISABLED)
        
        # Schedule next update
        self.app.root.after(5000, self.update_clients_list)

    def toggle_auth_key_visibility(self):
        """Toggle visibility of the authentication key"""
        if self.auth_key_visible:
            self.auth_key_entry.config(show="•")
            self.auth_key_visible = False
        else:
            self.auth_key_entry.config(show="")
            self.auth_key_visible = True
    
    def copy_auth_key(self):
        """Copy the authentication key to clipboard"""
        auth_key = self.auth_key_var.get()
        if auth_key and auth_key != "Not generated":
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(auth_key)
            self.app.log_message("Authentication key copied to clipboard")
            
            # Visual feedback
            original_text = self.show_auth_button.cget("text")
            self.show_auth_button.config(text="✓")
            self.app.root.after(1000, lambda: self.show_auth_button.config(text=original_text))
        else:
            messagebox.showinfo("No Key", "No authentication key available to copy. Enable remote control first.")
    
    def generate_new_auth_key(self):
        """Generate a new authentication key"""
        if not self.app.remote_enabled or not self.app.remote_server:
            messagebox.showinfo("Remote Control", "Enable remote control first to generate a key.")
            return
        
        # Generate new key in the server
        self.app.remote_server.auth_key = self.app.remote_server.generate_auth_key()
        self.app.remote_server.auth_salt, self.app.remote_server.auth_hash = self.app.remote_server.hash_auth_key(self.app.remote_server.auth_key)
        
        # Update UI
        self.auth_key_var.set(self.app.remote_server.auth_key)
        
        # Save the new key
        update_setting("remote_control", "auth_key", self.app.remote_server.auth_key)
        
        self.app.log_message("Generated new remote control authentication key")
    
    def toggle_whitelist(self):
        """Enable or disable IP whitelist"""
        enabled = self.whitelist_enabled_var.get()
        update_setting("remote_control", "whitelist_enabled", enabled)
        
        if enabled:
            self.app.log_message("IP whitelist enabled")
        else:
            self.app.log_message("IP whitelist disabled - all IPs can attempt to connect")
        
        # Apply to running server
        if self.app.remote_server:
            if not enabled:
                self.app.remote_server.whitelisted_ips.clear()
            else:
                # Reload whitelist
                for ip in self.app.settings["remote_control"].get("whitelisted_ips", []):
                    self.app.remote_server.add_whitelisted_ip(ip)
    
    def add_ip_to_whitelist(self):
        """Add an IP address to the whitelist"""
        ip = self.add_ip_var.get().strip()
        
        # Basic IP validation
        if not ip:
            return
        
        parts = ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            messagebox.showerror("Invalid IP", "Please enter a valid IP address (e.g., 192.168.1.100)")
            return
        
        # Add to settings
        whitelisted = self.app.settings["remote_control"].get("whitelisted_ips", [])
        if ip not in whitelisted:
            whitelisted.append(ip)
            update_setting("remote_control", "whitelisted_ips", whitelisted)
            
            # Add to running server
            if self.app.remote_server and self.whitelist_enabled_var.get():
                self.app.remote_server.add_whitelisted_ip(ip)
            
            self.app.log_message(f"Added {ip} to whitelist")
            self.update_whitelist_display()
            self.add_ip_var.set("")
        else:
            messagebox.showinfo("Already Whitelisted", f"{ip} is already in the whitelist")
    
    def remove_ip_from_whitelist(self):
        """Remove selected IP from whitelist"""
        try:
            # Get selected text
            selection = self.whitelist_text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            
            # Extract IP (format: "• 192.168.1.1")
            if '•' in selection:
                ip = selection.split('•')[1].strip()
            else:
                ip = selection
            
            # Remove from settings
            whitelisted = self.app.settings["remote_control"].get("whitelisted_ips", [])
            if ip in whitelisted:
                whitelisted.remove(ip)
                update_setting("remote_control", "whitelisted_ips", whitelisted)
                
                # Remove from running server
                if self.app.remote_server:
                    self.app.remote_server.remove_whitelisted_ip(ip)
                
                self.app.log_message(f"Removed {ip} from whitelist")
                self.update_whitelist_display()
            
        except tk.TclError:
            messagebox.showinfo("No Selection", "Please select an IP address to remove")
    
    def update_whitelist_display(self):
        """Update the whitelist display"""
        self.whitelist_text.config(state=tk.NORMAL)
        self.whitelist_text.delete(1.0, tk.END)
        
        whitelisted = self.app.settings["remote_control"].get("whitelisted_ips", [])
        if not whitelisted:
            self.whitelist_text.insert(tk.END, "No IPs whitelisted (all IPs can connect if whitelist is disabled)")
        else:
            for ip in whitelisted:
                self.whitelist_text.insert(tk.END, f"• {ip}\n")
        
        self.whitelist_text.config(state=tk.DISABLED)
