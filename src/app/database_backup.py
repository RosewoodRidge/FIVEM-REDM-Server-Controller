import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from config import COLORS, DB_BACKUP_HOURS, BACKUP_MINUTE
from app.common import ModernScrolledText
from database import create_backup, restore_backup, delete_old_backups, get_backup_files
from utils import calculate_next_backup_time
from discord_webhook import send_discord_webhook

class DatabaseBackupTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Database Backup")
        
        # Database backup files
        self.backup_files = []
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # Next backup timer
        timer_frame = ttk.LabelFrame(self.tab, text="Next Scheduled Backup")
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
            self.tab, 
            text="Run Manual Database Backup",
            command=self.run_manual_backup,
            style="Primary.TButton"
        )
        backup_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Restore section
        restore_frame = ttk.LabelFrame(self.tab, text="Restore Database")
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
    
    def run_manual_backup(self):
        """Run a manual backup when button is pressed"""
        self.app.log_message("Starting manual database backup...")
        self.app.status_label.config(text="Status: Database backup in progress...")
        
        # Broadcast that backup is starting
        if hasattr(self.app, 'broadcast_progress'):
            self.app.broadcast_progress("Starting manual database backup...", 0)
        
        # Run backup in a separate thread to avoid freezing UI
        def do_backup():
            success, message = create_backup()
            if success:
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress("Database backup completed, cleaning old backups...", 90)
                
                deleted = delete_old_backups(keep_count=100)
                self.app.log_message(f"Database backup completed successfully")
                if deleted:
                    self.app.log_message(f"Deleted {deleted} old database backup(s)")
                
                # Send Discord webhook
                send_discord_webhook('database_backup')
                
                # Update local UI
                self.app.root.after(0, self.update_backup_list)
                
                # Broadcast to remote clients
                if hasattr(self.app, 'broadcast_database_backups'):
                    self.app.broadcast_database_backups()
                
                # Broadcast next backup time
                if hasattr(self.app, 'broadcast_next_backup_time'):
                    self.app.broadcast_next_backup_time()
                
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress("Database backup completed successfully", 100)
            else:
                self.app.log_message(f"Database backup failed: {message}")
                # Send Discord webhook for failure
                send_discord_webhook('backup_failed', custom_message=f"❌ **Database Backup Failed**\n{message}")
                if hasattr(self.app, 'broadcast_progress'):
                    self.app.broadcast_progress(f"Database backup failed: {message}", 0)
            
            self.app.root.after(0, lambda: self.app.status_label.config(text="Status: Running"))
        
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
            
            self.app.log_message(f"Starting database restore from backup {index+1}...")
            self.app.status_label.config(text="Status: Database restore in progress...")
            
            # Broadcast that restore is starting
            if hasattr(self.app, 'broadcast_progress'):
                self.app.broadcast_progress(f"Starting database restore from backup {index+1}...", 10)
            
            # Run restore in a separate thread
            def do_restore():
                success, message = restore_backup(backup_path)
                if success:
                    self.app.log_message("Database restore completed successfully!")
                    if hasattr(self.app, 'broadcast_progress'):
                        self.app.broadcast_progress("Database restore completed successfully!", 100)
                else:
                    self.app.log_message(f"Database restore failed: {message}")
                    if hasattr(self.app, 'broadcast_progress'):
                        self.app.broadcast_progress(f"Database restore failed: {message}", 0)
                
                self.app.root.after(0, lambda: self.app.status_label.config(text="Status: Running"))
            
            threading.Thread(target=do_restore, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
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
        
        # Update the app's reference to the backup files
        self.app.backup_files = self.backup_files
    
    def update_next_backup_timer(self):
        """Update the next scheduled backup time and countdown display"""
        if not self.app.running:
            return
            
        # Calculate the next backup time
        next_backup_time, backup_type = calculate_next_backup_time()
        
        # Format the date for display
        formatted_time = next_backup_time.strftime('%Y-%m-%d %H:%M:%S')
        self.next_backup_label.config(text=f"Next {backup_type} Backup: {formatted_time}")
        
        # Calculate time remaining
        now = datetime.now()
        time_diff = next_backup_time - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        days = time_diff.days
        
        # Display countdown
        if days > 0:
            countdown = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds remaining"
        else:
            countdown = f"{hours} hours, {minutes} minutes, {seconds} seconds remaining"
            
        self.countdown_label.config(text=countdown)
        
        # Update every second for real-time countdown
        self.app.root.after(1000, self.update_next_backup_timer)
