import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
import socket
import subprocess
import traceback

# Import app modules
from app.common import log_message, ModernScrolledText, apply_styles, update_setting
from app.server_control import ServerControlTab
from app.server_backup import ServerBackupTab
from app.database_backup import DatabaseBackupTab
from app.txadmin_update import TxAdminUpdateTab
from app.activity_log import ActivityLogTab
from app.remote_control import RemoteControlTab
from app.configuration import ConfigurationTab

# Import from other modules
from config import *
from utils import restart_application, calculate_next_backup_time, add_firewall_rule
from database import create_backup, delete_old_backups, get_backup_files
from server import backup_server_folder, delete_old_server_backups, get_server_backup_files
from txadmin import get_txadmin_backups, check_for_txadmin_updates, find_fxserver_processes, auto_update_txadmin, start_fxserver, stop_fxserver
from update import check_for_updates, CURRENT_VERSION
from remote_protocol import RemoteServer, RemoteMessage, STATUS_OK, STATUS_ERROR
from settings import load_settings

class BackupApp:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("FIVEM & REDM Server Controller and Backup App")
            self.root.geometry("850x800")
            self.root.configure(bg=COLORS['bg'])
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            
            # Set running and remote flags early to avoid AttributeError
            self.running = True
            self.remote_server = None
            self.remote_enabled = False
            
            # Load settings early before they're needed
            logging.info("Loading settings...")
            self.settings = load_settings()
            
            # Apply modern styling
            logging.info("Applying styles...")
            apply_styles()
            
            # Create a notebook for tabs
            logging.info("Creating notebook...")
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
            logging.info("Creating tabs...")
            self.tabs = {}
            self.tabs['server_control'] = ServerControlTab(self.notebook, self)
            self.tabs['server_backup'] = ServerBackupTab(self.notebook, self)
            self.tabs['database_backup'] = DatabaseBackupTab(self.notebook, self)
            self.tabs['txadmin_update'] = TxAdminUpdateTab(self.notebook, self)
            self.tabs['activity_log'] = ActivityLogTab(self.notebook, self)
            self.tabs['remote_control'] = RemoteControlTab(self.notebook, self)
            self.tabs['configuration'] = ConfigurationTab(self.notebook, self)
            
            # Add the activity log's text widget as the app-wide log text
            self.log_text = self.tabs['activity_log'].log_text
            
            # Status bar at the bottom of the window
            logging.info("Creating status bar...")
            status_bar = ttk.Frame(root, style="TFrame")
            status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
            
            self.status_label = ttk.Label(
                status_bar, 
                text="Status: Running", 
                foreground=COLORS['accent'],
                font=('Segoe UI', 9)
            )
            self.status_label.pack(side=tk.LEFT)
            
            # Version label
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
            self.tabs['server_backup'].update_server_backup_list()
            self.tabs['database_backup'].update_backup_list()
            self.tabs['txadmin_update'].update_txadmin_backup_list()
            self.tabs['database_backup'].update_next_backup_timer()
            
            # Start checking server status
            self.tabs['server_control'].update_server_status()
            
            # Log app start
            self.log_message("Backup & Restore Tool started")
            
            # Initialize the scheduler thread
            self.scheduler_thread = threading.Thread(target=self.backup_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            # Check for updates on startup
            self.check_for_app_updates()
            
            # Schedule regular update checks
            self.schedule_update_check()
            
            # If remote control was previously enabled, start it
            if self.settings["remote_control"]["enabled"]:
                self.tabs['remote_control'].remote_enabled_var.set(True)
                self.root.after(1000, self.tabs['remote_control'].toggle_remote_control)
        
            logging.info("Application initialized successfully")
            
        except Exception as e:
            logging.error(f"Error during BackupApp initialization: {e}")
            logging.error(traceback.format_exc())
            raise
    
    def handle_remote_command(self, message):
        """Handle commands received from remote clients"""
        try:
            command = message.command
            data = message.data or {}
            
            self.log_message(f"[Remote] Received command: {command}")
            
            if command == "GET_SERVER_STATUS":
                processes = find_fxserver_processes()
                if processes:
                    return RemoteMessage(
                        command="SERVER_STATUS",
                        status=STATUS_OK,
                        data={"status": "RUNNING", "pid": processes[0].pid}
                    )
                else:
                    return RemoteMessage(
                        command="SERVER_STATUS",
                        status=STATUS_OK,
                        data={"status": "STOPPED"}
                    )
            
            elif command == "START_SERVER":
                success, msg = start_fxserver(callback=self.log_message)
                
                # Broadcast status change to all clients
                if self.remote_server:
                    self.broadcast_server_status()
                
                return RemoteMessage(
                    command="START_SERVER",
                    status=STATUS_OK if success else STATUS_ERROR,
                    message=msg
                )
            
            elif command == "STOP_SERVER":
                was_running, success, msg = stop_fxserver(callback=self.log_message)
                
                # Broadcast status change to all clients
                if self.remote_server:
                    self.broadcast_server_status()
                
                return RemoteMessage(
                    command="STOP_SERVER",
                    status=STATUS_OK if success else STATUS_ERROR,
                    message=msg
                )
            
            elif command == "RESTART_SERVER":
                # Stop then start
                was_running, stop_success, server_path = stop_fxserver(callback=self.log_message)
                if stop_success:
                    time.sleep(2)
                    start_success, start_msg = start_fxserver(
                        server_path=server_path if isinstance(server_path, str) else None,
                        callback=self.log_message
                    )
                    
                    # Broadcast status change to all clients
                    if self.remote_server:
                        self.broadcast_server_status()
                    
                    return RemoteMessage(
                        command="RESTART_SERVER",
                        status=STATUS_OK if start_success else STATUS_ERROR,
                        message=start_msg
                    )
                else:
                    return RemoteMessage(
                        command="RESTART_SERVER",
                        status=STATUS_ERROR,
                        message=server_path
                    )
            
            elif command == "GET_DATABASE_BACKUPS":
                backups = get_backup_files()
                # Convert tuples to serializable dictionaries
                backup_list = []
                for path, timestamp, filename in backups:
                    backup_list.append({
                        "path": path,
                        "timestamp": timestamp,
                        "filename": filename
                    })
                return RemoteMessage(
                    command="DATABASE_BACKUPS",
                    status=STATUS_OK,
                    data={"backups": backup_list}
                )
            
            elif command == "GET_SERVER_BACKUPS":
                backups = get_server_backup_files()
                # Convert tuples to serializable dictionaries
                backup_list = []
                for path, timestamp, filename in backups:
                    backup_list.append({
                        "path": path,
                        "timestamp": timestamp,
                        "filename": filename
                    })
                return RemoteMessage(
                    command="SERVER_BACKUPS",
                    status=STATUS_OK,
                    data={"backups": backup_list}
                )
            
            elif command == "GET_TXADMIN_BACKUPS":
                backups = get_txadmin_backups()
                # Convert tuples to serializable dictionaries
                backup_list = []
                for path, timestamp, filename in backups:
                    backup_list.append({
                        "path": path,
                        "timestamp": timestamp,
                        "filename": filename
                    })
                return RemoteMessage(
                    command="TXADMIN_BACKUPS",
                    status=STATUS_OK,
                    data={"backups": backup_list}
                )
            
            elif command == "GET_NEXT_BACKUP_TIME":
                next_time, backup_type = calculate_next_backup_time()
                return RemoteMessage(
                    command="NEXT_BACKUP_TIME",
                    status=STATUS_OK,
                    data={
                        "next_backup_time": next_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "next_backup_timestamp": next_time.timestamp(),  # Unix timestamp for accurate sync
                        "server_time": datetime.now().timestamp(),  # Current server time
                        "backup_type": backup_type
                    }
                )
            
            elif command == "BACKUP_DATABASE":
                def do_backup():
                    success, result = create_backup()
                    if success:
                        delete_old_backups(keep_count=100)
                        # Broadcast updated backup list to ALL clients
                        if self.remote_server:
                            backups = get_backup_files()
                            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
                            self.remote_server.broadcast_message(RemoteMessage(
                                command="DATABASE_BACKUPS",
                                status=STATUS_OK,
                                data={"backups": backup_list}
                            ))
                        self.root.after(0, self.tabs['database_backup'].update_backup_list)
                
                threading.Thread(target=do_backup, daemon=True).start()
                return RemoteMessage(
                    command="BACKUP_DATABASE",
                    status=STATUS_OK,
                    message="Database backup started"
                )
            
            elif command == "BACKUP_SERVER":
                def do_backup():
                    success, result = backup_server_folder(lambda msg: self.broadcast_log(msg))
                    if success:
                        delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT)
                        # Broadcast updated backup list to ALL clients
                        if self.remote_server:
                            backups = get_server_backup_files()
                            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
                            self.remote_server.broadcast_message(RemoteMessage(
                                command="SERVER_BACKUPS",
                                status=STATUS_OK,
                                data={"backups": backup_list}
                            ))
                        self.root.after(0, self.tabs['server_backup'].update_server_backup_list)
                
                threading.Thread(target=do_backup, daemon=True).start()
                return RemoteMessage(
                    command="BACKUP_SERVER",
                    status=STATUS_OK,
                    message="Server backup started"
                )
            
            elif command == "UPDATE_TXADMIN":
                def do_update():
                    def progress_callback(msg, progress=None):
                        self.log_message(msg)
                        # Broadcast progress to all clients
                        if self.remote_server:
                            self.remote_server.broadcast_message(RemoteMessage(
                                command="PROGRESS_UPDATE",
                                status=STATUS_OK,
                                data={"message": msg, "progress": progress or 0}
                            ))
                    
                    success, result = auto_update_txadmin(progress_callback)
                    if success:
                        # Broadcast updated backup list
                        if self.remote_server:
                            backups = get_txadmin_backups()
                            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
                            self.remote_server.broadcast_message(RemoteMessage(
                                command="TXADMIN_BACKUPS",
                                status=STATUS_OK,
                                data={"backups": backup_list}
                            ))
                        self.root.after(0, self.tabs['txadmin_update'].update_txadmin_backup_list)
                
                threading.Thread(target=do_update, daemon=True).start()
                return RemoteMessage(
                    command="UPDATE_TXADMIN",
                    status=STATUS_OK,
                    message="TxAdmin update started"
                )
            
            else:
                return RemoteMessage(
                    command=command,
                    status=STATUS_ERROR,
                    message=f"Unknown command: {command}"
                )
        
        except Exception as e:
            error_msg = f"Error handling remote command {command}: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg, exc_info=True)
            return RemoteMessage(
                command=message.command,
                status=STATUS_ERROR,
                message=str(e)
            )
    
    def broadcast_server_status(self):
        """Broadcast current server status to all connected remote clients"""
        if not self.remote_server:
            return
        
        try:
            processes = find_fxserver_processes()
            status_msg = RemoteMessage(
                command="SERVER_STATUS",
                status=STATUS_OK,
                data={
                    "status": "RUNNING" if processes else "STOPPED",
                    "pid": processes[0].pid if processes else None
                }
            )
            self.remote_server.broadcast_message(status_msg)
        except Exception as e:
            logging.error(f"Error broadcasting server status: {e}")
    
    def log_message(self, message):
        """Add a message to the log display"""
        log_message(self.log_text, message)
        
        # Also log to file
        logging.info(message)
    
        # Also broadcast to remote clients if enabled
        if self.remote_enabled and self.remote_server:
            log_msg = RemoteMessage(
                command="LOG_MESSAGE",
                data={"message": message, "timestamp": datetime.now().isoformat()}
            )
            self.remote_server.broadcast_message(log_msg)
    
    def broadcast_log(self, message):
        """Log and broadcast message to all remote clients"""
        self.log_message(message)
        if self.remote_server:
            self.remote_server.broadcast_message(RemoteMessage(
                command="LOG_MESSAGE",
                data={"message": message}
            ))
    
    def broadcast_database_backups(self):
        """Broadcast updated database backup list to all clients"""
        if self.remote_server:
            backups = get_backup_files()
            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
            self.remote_server.broadcast_message(RemoteMessage(
                command="DATABASE_BACKUPS",
                status=STATUS_OK,
                data={"backups": backup_list}
            ))
    
    def broadcast_server_backups(self):
        """Broadcast updated server backup list to all clients"""
        if self.remote_server:
            backups = get_server_backup_files()
            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
            self.remote_server.broadcast_message(RemoteMessage(
                command="SERVER_BACKUPS",
                status=STATUS_OK,
                data={"backups": backup_list}
            ))
    
    def broadcast_txadmin_backups(self):
        """Broadcast updated TxAdmin backup list to all clients"""
        if self.remote_server:
            backups = get_txadmin_backups()
            backup_list = [{"path": p, "timestamp": t, "filename": f} for p, t, f in backups]
            self.remote_server.broadcast_message(RemoteMessage(
                command="TXADMIN_BACKUPS",
                status=STATUS_OK,
                data={"backups": backup_list}
            ))
    
    def broadcast_next_backup_time(self):
        """Broadcast next backup time to all clients"""
        if self.remote_server:
            try:
                next_time, backup_type = calculate_next_backup_time()
                self.remote_server.broadcast_message(RemoteMessage(
                    command="NEXT_BACKUP_TIME",
                    status=STATUS_OK,
                    data={
                        "next_backup_time": next_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "next_backup_timestamp": next_time.timestamp(),  # Unix timestamp
                        "server_time": datetime.now().timestamp(),  # Current server time
                        "backup_type": backup_type
                    }
                ))
            except Exception as e:
                logging.error(f"Error broadcasting next backup time: {e}")
    
    def broadcast_progress(self, message, progress=None):
        """Broadcast progress updates to all clients"""
        if self.remote_server:
            self.remote_server.broadcast_message(RemoteMessage(
                command="PROGRESS_UPDATE",
                status=STATUS_OK,
                data={"message": message, "progress": progress or 0}
            ))
    
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
                    deleted = delete_old_backups(keep_count=100)
                    self.log_message(f"Scheduled database backup completed successfully")
                    if deleted:
                        self.log_message(f"Deleted {deleted} old database backup(s)")
                    
                    # Update local UI
                    self.root.after(0, self.tabs['database_backup'].update_backup_list)
                    
                    # Broadcast to all remote clients
                    self.broadcast_database_backups()
                    
                    # Check for TxAdmin updates after database backup if enabled
                    if AUTO_UPDATE_TXADMIN:
                        self.log_message("Checking for TxAdmin updates...")
                        update_available, _, _ = check_for_txadmin_updates(self.log_message)
                        
                        if update_available:
                            self.log_message("TxAdmin update available. Starting update process...")
                            success, message = auto_update_txadmin(self.log_message)
                            if success:
                                self.log_message(f"TxAdmin automatic update completed: {message}")
                                self.root.after(0, self.tabs['txadmin_update'].update_txadmin_backup_list)
                                self.broadcast_txadmin_backups()
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
                    deleted = delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT)
                    self.log_message(f"Scheduled server backup completed successfully")
                    if deleted:
                        self.log_message(f"Deleted {deleted} old server backup(s)")
                    
                    # Update local UI
                    self.root.after(0, self.tabs['server_backup'].update_server_backup_list)
                    
                    # Broadcast to all remote clients
                    self.broadcast_server_backups()
                else:
                    self.log_message(f"Scheduled server backup failed: {result}")
                
                last_server_backup_date = current_date
            
            # Check every 10 seconds
            time.sleep(10)
    
    def manual_update_check(self):
        """Manually check for updates when button is clicked"""
        self.log_message("Checking for application updates...")
        result = check_for_updates(self.root, force=True)
        if result:
            # If update is ready to install, completely exit the app
            self.log_message("Update available, application will restart after update...")
            self.on_close()
            # Force exit to ensure the app fully closes
            self.root.after(500, lambda: os._exit(0))

    def check_for_app_updates(self):
        """Check for updates on startup"""
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(
            target=self._check_updates_thread,
            daemon=True
        ).start()
        
    def _check_updates_thread(self):
        """Thread function to check for updates"""
        result = check_for_updates(self.root)
        if result:
            # Schedule app exit for update
            self.root.after(0, lambda: self.log_message("Update available, application will restart after update..."))
            self.root.after(1000, self.on_close)
            self.root.after(1500, lambda: os._exit(0))

    def schedule_update_check(self):
        """Schedule periodic update checks"""
        if self.running:
            # Run update check in thread to avoid UI freezing
            threading.Thread(
                target=self._scheduled_update_check,
                daemon=True
            ).start()
            # Schedule next check
            self.root.after(24 * 60 * 60 * 1000, self.schedule_update_check)
        
    def _scheduled_update_check(self):
        """Run a scheduled update check"""
        result = check_for_updates(self.root)
        if result and self.running:
            # Schedule app exit for update
            self.root.after(0, lambda: self.log_message("Update available, application will restart after update..."))
            self.root.after(1000, self.on_close)
            self.root.after(1500, lambda: os._exit(0))

    def on_close(self):
        """Clean up when the window is closed"""
        # Stop remote server if running
        if hasattr(self, 'remote_server') and self.remote_server:
            self.remote_server.stop()
            self.remote_server = None
        
        self.running = False
        self.root.destroy()
