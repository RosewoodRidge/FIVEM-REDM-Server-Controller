import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from config import COLORS, SERVER_FOLDER, SERVER_BACKUP_HOURS, SERVER_BACKUP_KEEP_COUNT
from app.common import ModernScrolledText
from server import backup_server_folder, restore_server_backup, delete_old_server_backups, get_server_backup_files
from discord_webhook import send_discord_webhook

class ServerBackupTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Server Backup")
        
        # Server backup files
        self.server_backup_files = []
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # Server backup info
        info_frame = ttk.LabelFrame(self.tab, text="Server Backup Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            info_frame,
            text=f"Backing up folder: {SERVER_FOLDER}",
            background=COLORS['panel'],
            foreground=COLORS['text_secondary'],
            wraplength=800
        ).pack(pady=(5, 5), padx=10, anchor=tk.W)
        
        ttk.Label(
            info_frame,
            text=f"Server backups run daily at {', '.join([f'{h} AM' for h in SERVER_BACKUP_HOURS])} and keep the {SERVER_BACKUP_KEEP_COUNT} most recent copies.",
            background=COLORS['panel'],
            wraplength=800
        ).pack(pady=(0, 10), padx=10, anchor=tk.W)
        
        # Manual server backup button
        server_backup_button = ttk.Button(
            self.tab, 
            text="Run Manual Server Backup Now", 
            command=self.run_manual_server_backup,
            style="Primary.TButton"
        )
        server_backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Server restore section
        server_restore_frame = ttk.LabelFrame(self.tab, text="Restore Server")
        server_restore_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Label with instructions
        ttk.Label(
            server_restore_frame, 
            text="Enter backup index to restore (1 = most recent):",
            background=COLORS['panel']
        ).pack(anchor=tk.W, pady=(10, 5), padx=10)
        
        # Entry for server backup number
        server_input_frame = ttk.Frame(server_restore_frame)
        server_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.server_restore_var = tk.StringVar(value="1")
        server_restore_entry = ttk.Entry(
            server_input_frame, 
            textvariable=self.server_restore_var, 
            width=5
        )
        server_restore_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Server restore button
        server_restore_button = ttk.Button(
            server_input_frame, 
            text="Restore Server Files", 
            command=self.restore_server
        )
        server_restore_button.pack(side=tk.LEFT)
        
        # Available server backups list
        ttk.Label(
            server_restore_frame, 
            text="Available Server Backups:",
            background=COLORS['panel']
        ).pack(anchor=tk.W, padx=10)
        
        # Scrolled text widget for server backup list
        self.server_backup_list = ModernScrolledText(
            server_restore_frame, 
            wrap=tk.WORD, 
            height=10
        )
        self.server_backup_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.server_backup_list.config(state=tk.DISABLED)
    
    def run_manual_server_backup(self):
        """Run a manual server backup"""
        self.app.log_message("Starting manual server backup...")
        self.app.status_label.config(text="Status: Server backup in progress...")
        
        # Broadcast that backup is starting
        if hasattr(self.app, 'broadcast_progress'):
            self.app.broadcast_progress("Starting manual server backup...", 0)
        
        # Run backup in a separate thread
        def do_backup():
            def progress_callback(msg):
                self.app.log_message(msg)
                # Broadcast progress updates
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress(msg, None)
            
            success, result = backup_server_folder(progress_callback)
            if success:
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress("Server backup completed, cleaning old backups...", 90)
                
                deleted = delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT)
                self.app.log_message(f"Server backup completed successfully")
                if deleted:
                    self.app.log_message(f"Deleted {deleted} old server backup(s)")
                
                # Send Discord webhook
                send_discord_webhook('server_backup')
                
                # Update local UI
                self.app.root.after(0, self.update_server_backup_list)
                
                # Broadcast to remote clients
                if hasattr(self.app, 'broadcast_server_backups'):
                    self.app.broadcast_server_backups()
                
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress("Server backup completed successfully", 100)
            else:
                self.app.log_message(f"Server backup failed: {result}")
                # Send Discord webhook for failure
                send_discord_webhook('backup_failed', custom_message=f"❌ **Server Backup Failed**\n{result}")
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress(f"Server backup failed: {result}", 0)
            
            self.app.root.after(0, lambda: self.app.status_label.config(text="Status: Running"))
        
        threading.Thread(target=do_backup, daemon=True).start()
    
    def restore_server(self):
        """Restore the server from a selected backup"""
        try:
            index = int(self.server_restore_var.get()) - 1
            if index < 0 or index >= len(self.server_backup_files):
                messagebox.showerror("Error", f"Invalid backup index. Please enter a value between 1 and {len(self.server_backup_files)}")
                return
            
            backup_path = self.server_backup_files[index][0]
            filename = self.server_backup_files[index][2]
            
            # Confirm restore operation
            if not messagebox.askyesno("Confirm Server Restore", 
                f"Are you sure you want to restore the server from backup:\n{filename}?\n\n"
                "WARNING: This will overwrite your current server files!",
                icon="warning"):
                return
            
            self.app.log_message(f"Starting server restore from backup {index+1}...")
            self.app.status_label.config(text="Status: Server restore in progress...")
            
            # Broadcast that restore is starting
            if hasattr(self.app, 'broadcast_progress'):
                self.app.broadcast_progress(f"Starting server restore from backup {index+1}...", 10)
            
            # Run restore in a separate thread
            def do_restore():
                def progress_callback(msg):
                    self.app.log_message(msg)
                    # Broadcast progress updates
                    if hasattr(self.app, 'broadcast_progress'):
                        self.app.broadcast_progress(msg, None)
                
                success, message = restore_server_backup(backup_path, progress_callback)
                if success:
                    self.app.log_message("Server restore completed successfully!")
                    if hasattr(self.app, 'broadcast_progress'):
                        self.app.broadcast_progress("Server restore completed successfully!", 100)
                else:
                    self.app.log_message(f"Server restore failed: {message}")
                    if hasattr(self.app, 'broadcast_progress'):
                        self.app.broadcast_progress(f"Server restore failed: {message}", 0)
                
                self.app.root.after(0, lambda: self.app.status_label.config(text="Status: Running"))
            
            threading.Thread(target=do_restore, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_server_backup_list(self):
        """Update the list of available server backups"""
        self.server_backup_files = get_server_backup_files()
        
        self.server_backup_list.config(state=tk.NORMAL)
        self.server_backup_list.delete(1.0, tk.END)
        
        if not self.server_backup_files:
            self.server_backup_list.insert(tk.END, "No server backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.server_backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.server_backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.server_backup_list.config(state=tk.DISABLED)
        
        # Update the app's reference to the backup files
        self.app.server_backup_files = self.server_backup_files
