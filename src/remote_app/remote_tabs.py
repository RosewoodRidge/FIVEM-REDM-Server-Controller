"""
Remote-enabled tab wrappers that adapt main app tabs for remote use.
These tabs reuse the UI from the main app but send commands remotely.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from app.server_control import ServerControlTab as BaseServerControlTab
from app.server_backup import ServerBackupTab as BaseServerBackupTab
from app.database_backup import DatabaseBackupTab as BaseDatabaseBackupTab
from app.txadmin_update import TxAdminUpdateTab as BaseTxAdminUpdateTab

class RemoteServerControlTab(BaseServerControlTab):
    """Remote version of server control tab"""
    
    def __init__(self, notebook, app):
        super().__init__(notebook, app)
        
        # Remove server path info, not relevant for remote client
        for widget in self.tab.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and widget.winfo_children():
                if widget.winfo_children()[0].cget("text").startswith("Server executable:"):
                    widget.destroy()
                    break
    
    def start_server(self):
        """Send start server command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.server_log("Sending start server command...")
        self.app.send_command("START_SERVER")
        
        # Request updated status after a delay
        self.app.root.after(2000, lambda: self.app.send_command("GET_SERVER_STATUS"))
    
    def stop_server(self):
        """Send stop server command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.server_log("Sending stop server command...")
        self.app.send_command("STOP_SERVER")
        
        # Request updated status after a delay
        self.app.root.after(2000, lambda: self.app.send_command("GET_SERVER_STATUS"))
    
    def restart_server(self):
        """Send restart server command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.server_log("Sending restart server command...")
        self.app.send_command("RESTART_SERVER")
        
        # Request updated status after a delay
        self.app.root.after(5000, lambda: self.app.send_command("GET_SERVER_STATUS"))
    
    def update_server_status(self):
        """Override to prevent automatic polling - main.py handles this"""
        # Don't schedule automatic updates - main.py handles polling
        pass


class RemoteTxAdminUpdateTab(BaseTxAdminUpdateTab):
    """Remote version of TxAdmin update tab"""
    
    def __init__(self, notebook, app):
        super().__init__(notebook, app)
        
        # Remove server path info, not relevant for remote client
        for widget in self.tab.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and "TxAdmin Information" in widget.cget("text"):
                widget.destroy()
                break
    
    def update_txadmin(self):
        """Send TxAdmin update command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.update_txadmin_status("Requesting TxAdmin update...", 0)
        self.app.send_command("UPDATE_TXADMIN")
    
    def restore_txadmin(self):
        """Send TxAdmin restore command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        try:
            index = int(self.txadmin_restore_var.get()) - 1
            if index < 0 or index >= len(self.txadmin_backup_files):
                messagebox.showerror("Error", f"Invalid backup index")
                return
            
            filename = self.txadmin_backup_files[index][2]
            
            if not messagebox.askyesno("Confirm Restore",
                f"Restore TxAdmin from backup:\n{filename}?\n\n"
                "This will overwrite current server files on remote host!",
                icon="warning"):
                return
            
            self.app.log_message(f"Requesting TxAdmin restore from backup {index+1}...")
            self.app.send_command("RESTORE_TXADMIN", {"backup_index": index})
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_txadmin_backup_list(self):
        """Override to prevent automatic requests - data is pushed from server"""
        # Don't automatically request - just update the UI with existing data
        from datetime import datetime
        
        self.txadmin_backup_list.config(state=tk.NORMAL)
        self.txadmin_backup_list.delete(1.0, tk.END)
        
        if not self.txadmin_backup_files:
            self.txadmin_backup_list.insert(tk.END, "No TxAdmin backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.txadmin_backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.txadmin_backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.txadmin_backup_list.config(state=tk.DISABLED)


class RemoteServerBackupTab(BaseServerBackupTab):
    """Remote version of server backup tab"""
    
    def __init__(self, notebook, app):
        super().__init__(notebook, app)
        
        # Remove server path info, not relevant for remote client
        for widget in self.tab.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and "Server Backup Information" in widget.cget("text"):
                widget.destroy()
                break
    
    def run_manual_server_backup(self):
        """Send manual server backup command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.app.log_message("Requesting manual server backup...")
        self.app.send_command("BACKUP_SERVER")
    
    def restore_server(self):
        """Send server restore command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        try:
            index = int(self.server_restore_var.get()) - 1
            if index < 0 or index >= len(self.server_backup_files):
                messagebox.showerror("Error", f"Invalid backup index")
                return
            
            filename = self.server_backup_files[index][2]
            
            if not messagebox.askyesno("Confirm Server Restore",
                f"Restore server from backup:\n{filename}?\n\n"
                "This will overwrite current server files on remote host!",
                icon="warning"):
                return
            
            self.app.log_message(f"Requesting server restore from backup {index+1}...")
            self.app.send_command("RESTORE_SERVER", {"backup_index": index})
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_server_backup_list(self):
        """Override to prevent automatic requests - data is pushed from server"""
        # Don't automatically request - just update the UI with existing data
        from datetime import datetime
        
        self.server_backup_list.config(state=tk.NORMAL)
        self.server_backup_list.delete(1.0, tk.END)
        
        if not self.server_backup_files:
            self.server_backup_list.insert(tk.END, "No server backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.server_backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.server_backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.server_backup_list.config(state=tk.DISABLED)


class RemoteDatabaseBackupTab(BaseDatabaseBackupTab):
    """Remote version of database backup tab"""
    
    def __init__(self, notebook, app):
        super().__init__(notebook, app)
        # Store next backup timestamp for local countdown
        self.next_backup_timestamp = None
        self.backup_type = None
    
    def run_manual_backup(self):
        """Send manual database backup command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        self.app.log_message("Requesting manual database backup...")
        self.app.send_command("BACKUP_DATABASE")
    
    def restore_database(self):
        """Send database restore command to remote host"""
        if not self.app.is_connected():
            messagebox.showerror("Not Connected", "Please connect to a server first")
            return
        
        try:
            index = int(self.restore_var.get()) - 1
            if index < 0 or index >= len(self.backup_files):
                messagebox.showerror("Error", f"Invalid backup index")
                return
            
            filename = self.backup_files[index][2]
            
            if not messagebox.askyesno("Confirm Restore",
                f"Restore database from backup:\n{filename}?\n\n"
                "This will overwrite current database on remote host!"):
                return
            
            self.app.log_message(f"Requesting database restore from backup {index+1}...")
            self.app.send_command("RESTORE_DATABASE", {"backup_index": index})
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def update_backup_list(self):
        """Override to prevent automatic requests - data is pushed from server"""
        # Don't automatically request - just update the UI with existing data
        from datetime import datetime
        
        self.backup_list.config(state=tk.NORMAL)
        self.backup_list.delete(1.0, tk.END)
        
        if not self.backup_files:
            self.backup_list.insert(tk.END, "No backups found.")
        else:
            for i, (path, timestamp, filename) in enumerate(self.backup_files, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                self.backup_list.insert(tk.END, f"{i}. {filename} - {time_str}\n")
        
        self.backup_list.config(state=tk.DISABLED)
    
    def set_next_backup_time(self, next_backup_timestamp, backup_type, formatted_time):
        """Set the next backup time from server data"""
        self.next_backup_timestamp = next_backup_timestamp
        self.backup_type = backup_type
        self.next_backup_label.config(text=f"Next {backup_type} Backup: {formatted_time}")
        
        # Start the local countdown timer
        self.update_next_backup_timer()
    
    def update_next_backup_timer(self):
        """Update countdown based on stored timestamp - runs locally"""
        if not self.app.running:
            return
        
        if self.next_backup_timestamp is None:
            self.countdown_label.config(text="Waiting for server data...")
            self.app.root.after(1000, self.update_next_backup_timer)
            return
        
        # Calculate time remaining based on timestamp
        import time
        now = time.time()
        time_diff_seconds = self.next_backup_timestamp - now
        
        if time_diff_seconds <= 0:
            # Backup time has passed, request updated time
            self.countdown_label.config(text="Backup should be running...")
            # Request updated backup time after a short delay
            self.app.root.after(5000, lambda: self.app.send_command("GET_NEXT_BACKUP_TIME"))
            return
        
        # Calculate time components
        days = int(time_diff_seconds // 86400)
        hours = int((time_diff_seconds % 86400) // 3600)
        minutes = int((time_diff_seconds % 3600) // 60)
        seconds = int(time_diff_seconds % 60)
        
        # Display countdown
        if days > 0:
            countdown = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds remaining"
        else:
            countdown = f"{hours} hours, {minutes} minutes, {seconds} seconds remaining"
        
        self.countdown_label.config(text=countdown)
        
        # Update every second
        self.app.root.after(1000, self.update_next_backup_timer)
