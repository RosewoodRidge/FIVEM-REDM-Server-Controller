# Dependencies:
# Run this in your cmd terminal to install required packages:
# pip3 install requests
# pip3 install beautifulsoup4
# pip3 install psutil

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

# Import from other modules
from config import *
from ui import apply_styles, ModernScrolledText
from utils import restart_application, calculate_next_backup_time
from database import create_backup, restore_backup, delete_old_backups, get_backup_files
from server import backup_server_folder, restore_server_backup, delete_old_server_backups, get_server_backup_files
from txadmin import (
    get_latest_txadmin_url, backup_txadmin, download_txadmin, extract_txadmin,
    restore_txadmin_backup, delete_old_txadmin_backups, get_txadmin_backups,
    auto_update_txadmin, check_for_txadmin_updates, find_fxserver_processes,
    start_fxserver, stop_fxserver
)
from update import check_for_updates, CURRENT_VERSION

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FIVEM & REDM Server Controller and Backup App")
        self.root.geometry("850x800")
        self.root.configure(bg=COLORS['bg'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Apply modern styling
        apply_styles()
        
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # === Server Control Tab (Now first) ===
        self.server_control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.server_control_tab, text="Server Control")
        
        # Server control info
        control_info_frame = ttk.LabelFrame(self.server_control_tab, text="Server Information")
        control_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            control_info_frame,
            text=f"Server executable: {os.path.join(TXADMIN_SERVER_DIR, 'FXServer.exe')}",
            background=COLORS['panel'],
            foreground=COLORS['text_secondary'],
            wraplength=800
        ).pack(pady=(5, 5), padx=10, anchor=tk.W)
        
        # Server status section
        status_frame = ttk.LabelFrame(self.server_control_tab, text="Server Status")
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
        output_frame = ttk.LabelFrame(self.server_control_tab, text="Command Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.server_output = ModernScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            height=15
        )
        self.server_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.server_output.config(state=tk.DISABLED)
        
        # === Server Tab (Now second) ===
        self.server_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.server_tab, text="Server Backup")
        
        # Server backup info
        info_frame = ttk.LabelFrame(self.server_tab, text="Server Backup Information")
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
            self.server_tab, 
            text="Run Manual Server Backup Now", 
            command=self.run_manual_server_backup,
            style="Primary.TButton"
        )
        server_backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Server restore section
        server_restore_frame = ttk.LabelFrame(self.server_tab, text="Restore Server")
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
        
        # === Database Tab (Now third) ===
        self.db_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.db_tab, text="Database Backup")
        
        # Next backup timer
        timer_frame = ttk.LabelFrame(self.db_tab, text="Next Scheduled Backup")
        timer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.next_backup_label = ttk.Label(
            timer_frame, 
            text="Calculating...", 
            font=('Segoe UI', 12, 'bold'),
            foreground=COLORS['accent']
        )
        self.next_backup_label.pack(pady=10)
        
        self.countdown_label = ttk.Label(
            timer_frame, 
            text="", 
            font=('Segoe UI', 10)
        )
        self.countdown_label.pack(pady=(0, 10))
        
        # Manual backup button
        backup_button = ttk.Button(
            self.db_tab, 
            text="Run Manual Database Backup",
            command=self.run_manual_backup,
            style="Primary.TButton"
        )
        backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Restore section
        restore_frame = ttk.LabelFrame(self.db_tab, text="Restore Database")
        restore_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Label with instructions
        ttk.Label(
            restore_frame, 
            text="Enter backup index to restore (1 = most recent):",
            background=COLORS['panel']
        ).pack(anchor=tk.W, pady=(10, 5), padx=10)
        
        # Entry for backup number
        input_frame = ttk.Frame(restore_frame, style="TFrame")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.restore_var = tk.StringVar(value="1")
        restore_entry = ttk.Entry(
            input_frame, 
            textvariable=self.restore_var, 
            width=5
        )
        restore_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Restore button
        restore_button = ttk.Button(
            input_frame, 
            text="Restore Database", 
            command=self.restore_database
        )
        restore_button.pack(side=tk.LEFT)
        
        # Available backups list
        ttk.Label(
            restore_frame, 
            text="Available Database Backups:",
            background=COLORS['panel']
        ).pack(anchor=tk.W, padx=10)
        
        # Scrolled text widget for backup list
        self.backup_list = ModernScrolledText(
            restore_frame, 
            wrap=tk.WORD, 
            height=10
        )
        self.backup_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.backup_list.config(state=tk.DISABLED)
        
        # === TxAdmin Tab (Now fourth) ===
        self.txadmin_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.txadmin_tab, text="TxAdmin Update")
        
        # TxAdmin info
        info_frame = ttk.LabelFrame(self.txadmin_tab, text="TxAdmin Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            info_frame,
            text=f"Server folder: {TXADMIN_SERVER_DIR}",
            background=COLORS['panel'],
            foreground=COLORS['text_secondary'],
            wraplength=800
        ).pack(pady=(5, 5), padx=10, anchor=tk.W)
        
        ttk.Label(
            info_frame,
            text=f"Update will download to: {TXADMIN_DOWNLOAD_DIR}",
            background=COLORS['panel'],
            wraplength=800
        ).pack(pady=(0, 5), padx=10, anchor=tk.W)
        
        ttk.Label(
            info_frame,
            text=f"Using 7-Zip from: {SEVEN_ZIP_PATH}",
            background=COLORS['panel'],
            foreground=COLORS['text_secondary'],
            wraplength=800
        ).pack(pady=(0, 10), padx=10, anchor=tk.W)
        
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
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            length=100, 
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        self.txadmin_status = ttk.Label(
            progress_frame,
            text="Ready to update",
            background=COLORS['panel'],
            wraplength=800
        )
        self.txadmin_status.pack(pady=(0, 10), padx=10, anchor=tk.W)
        
        # Rollback section
        rollback_frame = ttk.LabelFrame(self.txadmin_tab, text="Restore Previous Version")
        rollback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Label with instructions
        ttk.Label(
            rollback_frame, 
            text="Select a backup to restore:",
            background=COLORS['panel']
        ).pack(anchor=tk.W, pady=(10, 5), padx=10)
        
        # Entry for backup number
        restore_frame = ttk.Frame(rollback_frame)
        restore_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.txadmin_restore_var = tk.StringVar(value="1")
        restore_entry = ttk.Entry(
            restore_frame, 
            textvariable=self.txadmin_restore_var, 
            width=5
        )
        restore_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Restore button
        restore_button = ttk.Button(
            restore_frame, 
            text="Restore TxAdmin", 
            command=self.restore_txadmin
        )
        restore_button.pack(side=tk.LEFT)
        
        # Available backups list
        ttk.Label(
            rollback_frame, 
            text="Available TxAdmin Backups:",
            background=COLORS['panel']
        ).pack(anchor=tk.W, padx=10)
        
        # Scrolled text widget for txadmin backup list
        self.txadmin_backup_list = ModernScrolledText(
            rollback_frame, 
            wrap=tk.WORD, 
            height=10
        )
        self.txadmin_backup_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.txadmin_backup_list.config(state=tk.DISABLED)
        
        # === Log Tab (Now fifth) ===
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
        
        # Status bar at the bottom of the window
        status_bar = ttk.Frame(root, style="TFrame")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
        
        self.status_label = ttk.Label(
            status_bar, 
            text="Status: Running", 
            foreground=COLORS['accent'],
            font=('Segoe UI', 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Version label (now with version from CURRENT_VERSION imported from update.py)
        version_label = ttk.Label(
            status_bar, 
            text=f"v{CURRENT_VERSION}", 
            foreground=COLORS['text_secondary'],
            font=('Segoe UI', 9)
        )
        version_label.pack(side=tk.RIGHT)
        
        # Check for updates button
        update_check_btn = ttk.Button(
            status_bar,
            text="Check for Updates",
            command=self.manual_update_check,
            style="Link.TButton"
        )
        update_check_btn.pack(side=tk.RIGHT, padx=10)
        
        # Initialize UI updates
        self.backup_files = []
        self.server_backup_files = []
        self.txadmin_backup_files = []
        self.update_backup_list()
        self.update_server_backup_list()
        self.update_txadmin_backup_list()
        self.update_next_backup_timer()
        
        # Start checking server status
        self.update_server_status()
        
        # Log app start
        self.log_message("Backup & Restore Tool started")
        
        # Initialize the scheduler thread
        self.scheduler_thread = threading.Thread(target=self.backup_scheduler, daemon=True)
        self.running = True
        self.scheduler_thread.start()
        
        # Check for updates on startup
        self.check_for_app_updates()
        
        # Schedule regular update checks
        self.schedule_update_check()
    
    def update_backup_list(self):
        """Update the list of available backups"""
        self.backup_files = get_backup_files()
        
        self.backup_list.config(state=tk.NORMAL)
        self.backup_list.delete(1.0, tk.END)
        
        if not self.backup_files:
            self.backup_list.insert(tk.END, "No backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.backup_list.config(state=tk.DISABLED)
    
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
    
    def update_txadmin_backup_list(self):
        """Update the list of available txAdmin backups"""
        self.txadmin_backup_files = get_txadmin_backups()
        
        self.txadmin_backup_list.config(state=tk.NORMAL)
        self.txadmin_backup_list.delete(1.0, tk.END)
        
        if not self.txadmin_backup_files:
            self.txadmin_backup_list.insert(tk.END, "No txAdmin backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.txadmin_backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.txadmin_backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.txadmin_backup_list.config(state=tk.DISABLED)
    
    def update_next_backup_timer(self):
        """Update the timer showing next backup time"""
        next_backup_time, backup_type = calculate_next_backup_time()
        time_str = next_backup_time.strftime('%Y-%m-%d %H:%M:%S')
        self.next_backup_label.config(text=f"{time_str} ({backup_type})")
        
        # Calculate countdown
        now = datetime.now()
        time_diff = next_backup_time - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.countdown_label.config(text=f"Time remaining: {time_diff.days} days, {hours:02}:{minutes:02}:{seconds:02}")
        
        # Schedule the next update in 1 second
        self.root.after(1000, self.update_next_backup_timer)
    
    def log_message(self, message):
        """Add a message to the log display"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Also log to file
        logging.info(message)
    
    def run_manual_backup(self):
        """Run a manual backup when button is pressed"""
        self.log_message("Starting manual database backup...")
        self.status_label.config(text="Status: Database backup in progress...")
        
        # Run backup in a separate thread to avoid freezing UI
        def do_backup():
            success, message = create_backup()
            if success:
                # Clean up old backups if we have too many
                deleted = delete_old_backups(keep_count=100)
                self.log_message(f"Database backup completed successfully")
                if deleted:
                    self.log_message(f"Deleted {deleted} old database backup(s)")
                # Update the backup list
                self.root.after(0, self.update_backup_list)
            else:
                self.log_message(f"Database backup failed: {message}")
            
            self.root.after(0, lambda: self.status_label.config(text="Status: Running"))
        
        threading.Thread(target=do_backup, daemon=True).start()
    
    def run_manual_server_backup(self):
        """Run a manual server backup"""
        self.log_message("Starting manual server backup...")
        self.status_label.config(text="Status: Server backup in progress...")
        
        # Run backup in a separate thread
        def do_backup():
            success, result = backup_server_folder(self.log_message)
            if success:
                # Clean up old backups if we have too many
                deleted = delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT)
                self.log_message(f"Server backup completed successfully")
                if deleted:
                    self.log_message(f"Deleted {deleted} old server backup(s)")
                # Update the backup list
                self.root.after(0, self.update_server_backup_list)
            else:
                self.log_message(f"Server backup failed: {result}")
            
            self.root.after(0, lambda: self.status_label.config(text="Status: Running"))
        
        threading.Thread(target=do_backup, daemon=True).start()
    
    def restore_database(self):
        """Restore the database from a selected backup"""
        try:
            index = int(self.restore_var.get()) - 1
            if index < 0 or index >= len(self.backup_files):
                messagebox.showerror("Error", f"Invalid backup index. Please enter a value between 1 and {len(self.backup_files)}")
                return
            
            backup_path = self.backup_files[index][0]
            filename = self.backup_files[index][2]
            
            # Confirm restore operation
            if not messagebox.askyesno("Confirm Restore", 
                f"Are you sure you want to restore from backup:\n{filename}?\n\n"
                "WARNING: This will overwrite your current database!"):
                return
            
            self.log_message(f"Starting database restore from backup {index+1}...")
            self.status_label.config(text="Status: Database restore in progress...")
            
            # Run restore in a separate thread
            def do_restore():
                success, message = restore_backup(backup_path)
                if success:
                    self.log_message("Database restore completed successfully!")
                else:
                    self.log_message(f"Database restore failed: {message}")
                
                self.root.after(0, lambda: self.status_label.config(text="Status: Running"))
            
            threading.Thread(target=do_restore, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
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
            
            self.log_message(f"Starting server restore from backup {index+1}...")
            self.status_label.config(text="Status: Server restore in progress...")
            
            # Run restore in a separate thread
            def do_restore():
                success, message = restore_server_backup(backup_path, self.log_message)
                if success:
                    self.log_message("Server restore completed successfully!")
                else:
                    self.log_message(f"Server restore failed: {message}")
                
                self.root.after(0, lambda: self.status_label.config(text="Status: Running"))
            
            threading.Thread(target=do_restore, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_txadmin_status(self, message, progress=None):
        """Update the txAdmin status message and progress bar"""
        self.txadmin_status.config(text=message)
        self.log_message(message)
        
        if progress is not None:
            self.progress_var.set(progress)
        
        # Make sure the UI updates
        self.root.update_idletasks()
    
    def update_txadmin(self):
        """Update TxAdmin to the latest recommended version"""
        # Check if 7-Zip is available
        if not os.path.exists(SEVEN_ZIP_PATH):
            messagebox.showerror("Error", f"7-Zip executable not found at {SEVEN_ZIP_PATH}. Please set the correct path in the configuration.")
            return
        
        self.update_txadmin_status("Starting TxAdmin update...", 0)
        self.progress_var.set(0)
        
        # Run in a separate thread to keep UI responsive
        def do_update():
            try:
                # Step 1: Get the latest URL
                self.update_txadmin_status("Getting latest recommended version...", 5)
                url = get_latest_txadmin_url(self.update_txadmin_status)
                if not url:
                    self.update_txadmin_status("Failed to get download URL.", 0)
                    return
                
                # Step 2: Backup the current server
                self.update_txadmin_status("Backing up current server...", 10)
                backup_success, backup_result = backup_txadmin(self.update_txadmin_status)
                if not backup_success:
                    self.update_txadmin_status(f"Backup failed: {backup_result}", 0)
                    return
                
                # Step 3: Download the update
                self.update_txadmin_status("Downloading update...", 20)
                download_success, download_path = download_txadmin(url, self.update_txadmin_status)
                if not download_success:
                    self.update_txadmin_status(f"Download failed: {download_path}", 0)
                    return
                
                # Step 4: Extract the update
                self.update_txadmin_status("Extracting update...", 80)
                extract_success, extract_message = extract_txadmin(download_path, self.update_txadmin_status)
                if not extract_success:
                    self.update_txadmin_status(f"Extraction failed: {extract_message}", 0)
                    return
                
                # Step 5: Clean up old backups
                self.update_txadmin_status("Cleaning up old backups...", 90)
                deleted = delete_old_txadmin_backups()
                if deleted > 0:
                    self.update_txadmin_status(f"Deleted {deleted} old backup(s)", 95)
                
                # Step 6: Done
                self.update_txadmin_status("TxAdmin update completed successfully!", 100)
                
                # Update the backup list
                self.root.after(0, self.update_txadmin_backup_list)
                
            except Exception as e:
                error_message = f"TxAdmin update failed with error: {str(e)}"
                self.update_txadmin_status(error_message, 0)
        
        threading.Thread(target=do_update, daemon=True).start()
    
    def restore_txadmin(self):
        """Restore TxAdmin from a selected backup"""
        try:
            # Check if backup files exist
            if not self.txadmin_backup_files:
                messagebox.showerror("Error", "No TxAdmin backups found.")
                return
            
            index = int(self.txadmin_restore_var.get()) - 1
            if index < 0 or index >= len(self.txadmin_backup_files):
                messagebox.showerror("Error", f"Invalid backup index. Please enter a value between 1 and {len(self.txadmin_backup_files)}")
                return
            
            backup_path = self.txadmin_backup_files[index][0]
            filename = self.txadmin_backup_files[index][2]
            
            # Confirm restore operation
            if not messagebox.askyesno("Confirm Restore", 
                f"Are you sure you want to restore TxAdmin from backup:\n{filename}?\n\n"
                "WARNING: This will overwrite your current server files!",
                icon="warning"):
                return
            
            self.log_message(f"Starting TxAdmin restore from backup {index+1}...")
            self.update_txadmin_status("Restoring TxAdmin...", 10)
            
            # Run restore in a separate thread
            def do_restore():
                try:
                    success, message = restore_txadmin_backup(backup_path, self.update_txadmin_status)
                    if success:
                        self.update_txadmin_status("TxAdmin restore completed successfully!", 100)
                    else:
                        self.update_txadmin_status(f"TxAdmin restore failed: {message}", 0)
                except Exception as e:
                    self.update_txadmin_status(f"TxAdmin restore failed: {str(e)}", 0)
            
            threading.Thread(target=do_restore, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def backup_scheduler(self):
        """Thread function that runs scheduled backups"""
        last_db_backup_datetime = None
        last_server_backup_date = None
        last_txadmin_check_datetime = None
        
        while self.running:
            now = datetime.now()
            current_datetime_rounded = now.replace(minute=0, second=0, microsecond=0)
            current_date = now.date()
            
            # Check for database backups (at configured hours)
            if now.hour in DB_BACKUP_HOURS and now.minute == BACKUP_MINUTE and last_db_backup_datetime != current_datetime_rounded:
                self.log_message("Starting scheduled database backup...")
                success, result = create_backup()
                if success:
                    # Clean up old backups
                    deleted = delete_old_backups(keep_count=100)
                    self.log_message(f"Scheduled database backup completed successfully")
                    if deleted:
                        self.log_message(f"Deleted {deleted} old database backup(s)")
                    # Update the backup list
                    self.root.after(0, self.update_backup_list)
                    
                    # Check for TxAdmin updates after database backup if enabled
                    if AUTO_UPDATE_TXADMIN:
                        self.log_message("Checking for TxAdmin updates...")
                        update_available, _, _ = check_for_txadmin_updates(self.log_message)
                        
                        if update_available:
                            self.log_message("TxAdmin update available. Starting update process...")
                            success, message = auto_update_txadmin(self.log_message)
                            if success:
                                self.log_message(f"TxAdmin automatic update completed: {message}")
                                # Update the backup list
                                self.root.after(0, self.update_txadmin_backup_list)
                            else:
                                self.log_message(f"TxAdmin automatic update failed: {message}")
                        else:
                            self.log_message("TxAdmin is already up to date.")
                else:
                    self.log_message(f"Scheduled database backup failed: {result}")
                
                last_db_backup_datetime = current_datetime_rounded
                last_txadmin_check_datetime = current_datetime_rounded
            
            # Check for server backups (at configured hours)
            if now.hour in SERVER_BACKUP_HOURS and now.minute == BACKUP_MINUTE and last_server_backup_date != current_date:
                self.log_message("Starting scheduled server backup...")
                success, result = backup_server_folder(self.log_message)
                if success:
                    # Clean up old backups
                    deleted = delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT)
                    self.log_message(f"Scheduled server backup completed successfully")
                    if deleted:
                        self.log_message(f"Deleted {deleted} old server backup(s)")
                    # Update the backup list
                    self.root.after(0, self.update_server_backup_list)
                else:
                    self.log_message(f"Scheduled server backup failed: {result}")
                
                last_server_backup_date = current_date
            
            # Check every 10 seconds
            time.sleep(10)
    
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
        except Exception as e:
            self.server_status_var.set("ERROR")
            self.server_status_label.config(foreground="orange")
            self.server_pid_var.set(f"Error checking status: {str(e)}")
        
        # Schedule the next update in 3 seconds
        self.root.after(3000, self.update_server_status)
    
    def server_log(self, message):
        """Add a message to the server control log display"""
        self.server_output.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.server_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.server_output.see(tk.END)
        self.server_output.config(state=tk.DISABLED)
        
        # Also add to the main log
        self.log_message(message)
    
    def start_server(self):
        """Start the FXServer.exe process"""
        self.server_log("Starting FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_start():
            success, message = start_fxserver(callback=self.server_log)
            if success:
                self.server_log("Server started successfully")
            else:
                self.server_log(f"Failed to start server: {message}")
        
        threading.Thread(target=do_start, daemon=True).start()
    
    def stop_server(self):
        """Stop the FXServer.exe process"""
        self.server_log("Stopping FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_stop():
            was_running, success, message = stop_fxserver(callback=self.server_log)
            if success:
                self.server_log("Server stopped successfully")
            else:
                self.server_log(f"Failed to stop server: {message}")
        
        threading.Thread(target=do_stop, daemon=True).start()
    
    def restart_server(self):
        """Restart the FXServer.exe process"""
        self.server_log("Restarting FXServer.exe...")
        
        # Run in a separate thread to avoid freezing UI
        def do_restart():
            # First stop the server
            was_running, stop_success, server_path = stop_fxserver(callback=self.server_log)
            
            if not stop_success:
                self.server_log("Failed to stop server during restart")
                return
            
            # Wait a moment
            time.sleep(2)
            
            # Then start it again
            start_success, start_message = start_fxserver(
                server_path=server_path if isinstance(server_path, str) else None, 
                callback=self.server_log
            )
            
            if start_success:
                self.server_log("Server restarted successfully")
            else:
                self.server_log(f"Failed to restart server: {start_message}")
        
        threading.Thread(target=do_restart, daemon=True).start()
    
    def manual_update_check(self):
        """Manually check for updates when button is clicked"""
        self.log_message("Checking for application updates...")
        result = check_for_updates(self.root, force=True)
        if result:
            # If update is ready to install, quit the app
            self.on_close()
    
    def check_for_app_updates(self):
        """Check for updates on startup"""
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(
            target=lambda: check_for_updates(self.root),
            daemon=True
        ).start()
    
    def schedule_update_check(self):
        """Schedule periodic update checks"""
        if self.running:
            # Check for updates every 24 hours
            check_for_updates(self.root)
            # Schedule next check
            self.root.after(24 * 60 * 60 * 1000, self.schedule_update_check)
    
    def on_close(self):
        """Clean up when the window is closed"""
        self.running = False
        self.root.destroy()

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
