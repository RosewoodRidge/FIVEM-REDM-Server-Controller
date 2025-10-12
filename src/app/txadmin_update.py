import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from config import COLORS, TXADMIN_SERVER_DIR, TXADMIN_DOWNLOAD_DIR, SEVEN_ZIP_PATH
from app.common import ModernScrolledText
from txadmin import (
    get_latest_txadmin_url, backup_txadmin, download_txadmin, extract_txadmin,
    restore_txadmin_backup, delete_old_txadmin_backups, get_txadmin_backups
)

class TxAdminUpdateTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="TxAdmin Update")
        
        # TxAdmin backup files
        self.txadmin_backup_files = []
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # TxAdmin info
        info_frame = ttk.LabelFrame(self.tab, text="TxAdmin Information")
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
            self.tab, 
            text="Update TxAdmin (Latest Recommended)",
            command=self.update_txadmin,
            style="Primary.TButton"
        )
        update_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.tab, text="Update Progress")
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
        rollback_frame = ttk.LabelFrame(self.tab, text="Restore Previous Version")
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
    
    def update_txadmin_status(self, message, progress=None):
        """Update the txAdmin status message and progress bar"""
        self.txadmin_status.config(text=message)
        self.app.log_message(message)
        
        if progress is not None:
            self.progress_var.set(progress)
        
        # Broadcast progress to remote clients
        if hasattr(self.app, 'broadcast_progress'):
            self.app.broadcast_progress(message, progress)
        
        # Make sure the UI updates
        self.app.root.update_idletasks()
    
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
                
                # Update the local backup list
                self.app.root.after(0, self.update_txadmin_backup_list)
                
                # Broadcast to remote clients
                if hasattr(self.app, 'broadcast_txadmin_backups'):
                    self.app.broadcast_txadmin_backups()
                
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
            
            self.app.log_message(f"Starting TxAdmin restore from backup {index+1}...")
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
    
    def update_txadmin_backup_list(self):
        """Update the list of available TxAdmin backups"""
        self.txadmin_backup_files = get_txadmin_backups()
        
        self.txadmin_backup_list.config(state=tk.NORMAL)
        self.txadmin_backup_list.delete(1.0, tk.END)
        
        if not self.txadmin_backup_files:
            self.txadmin_backup_list.insert(tk.END, "No TxAdmin backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.txadmin_backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.txadmin_backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.txadmin_backup_list.config(state=tk.DISABLED)
        
        # Update the app's reference to the backup files
        self.app.txadmin_backup_files = self.txadmin_backup_files
