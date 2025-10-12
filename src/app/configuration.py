import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import shutil
import sys
import traceback

from config import COLORS
from app.common import ModernScrolledText
from config_manager import get_config_file, save_config, load_config

class ConfigurationTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="⚙️")
        
        # Use JSON config file
        self.config_file = get_config_file()
        
        # Log the config file path for debugging
        logging.info(f"ConfigurationTab using config file: {self.config_file}")
        
        # Dictionary to store configuration values
        self.config_vars = {}
        
        # Create tab contents
        self.create_tab_contents()
        
        # Load current configuration
        self.load_config()

    def create_tab_contents(self):
        # Create main frame with scrollbar
        main_container = ttk.Frame(self.tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create configuration sections
        self.create_database_section()
        self.create_backup_section()
        self.create_server_section()
        self.create_txadmin_section()
        self.create_schedule_section()
        
        # Buttons at the bottom
        button_frame = ttk.Frame(self.tab)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            button_frame,
            text="Ready",
            foreground=COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_dict = load_config()
            
            # Populate config_vars with values from JSON
            for key, value in config_dict.items():
                if isinstance(value, list):
                    # Convert list to comma-separated string for display
                    self.config_vars[key] = ', '.join(map(str, value))
                else:
                    self.config_vars[key] = str(value)
            
            # NOW update all the UI fields with the loaded values
            self.update_ui_from_config()
            
            self.app.log_message("Configuration loaded successfully")
        
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def update_ui_from_config(self):
        """Update all UI fields with loaded config values"""
        # Update all StringVar fields
        for key, value in self.config_vars.items():
            if key.endswith('_VAR') or key.endswith('_ENTRY'):
                # This is a UI variable
                var_obj = self.config_vars.get(key)
                if var_obj and hasattr(var_obj, 'set'):
                    # Find the corresponding config key
                    config_key = key.replace('_VAR', '').replace('_ENTRY', '')
                    if config_key in self.config_vars:
                        var_obj.set(self.config_vars[config_key])
    
    def create_database_section(self):
        """Create database configuration section"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Database Configuration")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_entry(frame, "DB_HOST", "Database Host:", "localhost")
        self.create_entry(frame, "DB_USER", "Database Username:", "root")
        self.create_entry(frame, "DB_PASSWORD", "Database Password:", "", show="•")
        self.create_entry(frame, "DB_NAME", "Database Name:", "my_database")
        self.create_path_entry(frame, "MYSQLDUMP_PATH", "MySQLDump Path:", r"C:\xampp\mysql\bin\mysqldump.exe", file=True)
        self.create_path_entry(frame, "MYSQL_PATH", "MySQL Path:", r"C:\xampp\mysql\bin\mysql.exe", file=True)
    
    def create_backup_section(self):
        """Create database backup configuration section"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Database Backup Configuration")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_path_entry(frame, "BACKUP_DIR", "Database Backup Directory:", r"C:\backups\database")
    
    def create_server_section(self):
        """Create server backup configuration section"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Server Backup Configuration")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_path_entry(frame, "SERVER_FOLDER", "Server Resources Folder:", r"C:\server\resources")
        self.create_path_entry(frame, "SERVER_BACKUP_DIR", "Server Backup Directory:", r"C:\backups\server")
        self.create_entry(frame, "SERVER_BACKUP_KEEP_COUNT", "Number of Server Backups to Keep:", "10")
    
    def create_txadmin_section(self):
        """Create TxAdmin configuration section"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="TxAdmin Configuration")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_path_entry(frame, "TXADMIN_SERVER_DIR", "TxAdmin Server Directory:", r"C:\server")
        self.create_path_entry(frame, "TXADMIN_BACKUP_DIR", "TxAdmin Backup Directory:", r"C:\backups\txadmin")
        self.create_path_entry(frame, "TXADMIN_DOWNLOAD_DIR", "TxAdmin Download Directory:", r"C:\downloads")
        self.create_path_entry(frame, "SEVEN_ZIP_PATH", "7-Zip Executable Path:", r"C:\Program Files\7-Zip\7z.exe", file=True)
        self.create_entry(frame, "TXADMIN_KEEP_COUNT", "Number of TxAdmin Backups to Keep:", "5")
    
    def create_schedule_section(self):
        """Create backup schedule configuration section"""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Backup Schedule")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            frame,
            text="Database Backup Hours (comma-separated, 0-23):",
            background=COLORS['panel']
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.config_vars['DB_BACKUP_HOURS_ENTRY'] = tk.StringVar(value=self.config_vars.get('DB_BACKUP_HOURS', '3, 15'))
        ttk.Entry(
            frame,
            textvariable=self.config_vars['DB_BACKUP_HOURS_ENTRY'],
            width=40
        ).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(
            frame,
            text="Server Backup Hours (comma-separated, 0-23):",
            background=COLORS['panel']
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.config_vars['SERVER_BACKUP_HOURS_ENTRY'] = tk.StringVar(value=self.config_vars.get('SERVER_BACKUP_HOURS', '3'))
        ttk.Entry(
            frame,
            textvariable=self.config_vars['SERVER_BACKUP_HOURS_ENTRY'],
            width=40
        ).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
    
    def create_entry(self, parent, key, label, default, show=None):
        """Create a labeled entry field"""
        row = parent.grid_size()[1]
        
        ttk.Label(
            parent,
            text=label,
            background=COLORS['panel']
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Get value from loaded config or use default
        value = self.config_vars.get(key, default)
        
        var = tk.StringVar(value=value)
        self.config_vars[f"{key}_VAR"] = var
        
        entry = ttk.Entry(parent, textvariable=var, width=50)
        if show:
            entry.config(show=show)
        entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=10, pady=5)
    
    def create_path_entry(self, parent, key, label, default, file=False):
        """Create a labeled entry field with browse button"""
        row = parent.grid_size()[1]
        
        ttk.Label(
            parent,
            text=label,
            background=COLORS['panel']
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Get value from loaded config or use default
        value = self.config_vars.get(key, default)
        
        var = tk.StringVar(value=value)
        self.config_vars[f"{key}_VAR"] = var
        
        ttk.Entry(
            parent,
            textvariable=var,
            width=40
        ).grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: self.browse_path(var, file)
        ).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
    
    def browse_path(self, var, is_file=False):
        """Open file/folder browser dialog"""
        if is_file:
            path = filedialog.askopenfilename()
        else:
            path = filedialog.askdirectory()
        
        if path:
            var.set(path)
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            # Build configuration dictionary
            config_dict = {}
            
            # String values
            string_keys = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
                          'BACKUP_DIR', 'MYSQLDUMP_PATH', 'MYSQL_PATH',
                          'SERVER_FOLDER', 'SERVER_BACKUP_DIR',
                          'TXADMIN_SERVER_DIR', 'TXADMIN_BACKUP_DIR',
                          'TXADMIN_DOWNLOAD_DIR', 'SEVEN_ZIP_PATH']
            
            for key in string_keys:
                var = self.config_vars.get(f"{key}_VAR")
                if var:
                    config_dict[key] = var.get()
            
            # Integer values
            int_keys = ['SERVER_BACKUP_KEEP_COUNT', 'TXADMIN_KEEP_COUNT']
            for key in int_keys:
                var = self.config_vars.get(f"{key}_VAR")
                if var:
                    try:
                        config_dict[key] = int(var.get())
                    except ValueError:
                        config_dict[key] = 10  # default
            
            # Array values
            var = self.config_vars.get("DB_BACKUP_HOURS_ENTRY")
            if var:
                hours = [int(h.strip()) for h in var.get().split(',') if h.strip().isdigit()]
                config_dict['DB_BACKUP_HOURS'] = hours
            
            var = self.config_vars.get("SERVER_BACKUP_HOURS_ENTRY")
            if var:
                hours = [int(h.strip()) for h in var.get().split(',') if h.strip().isdigit()]
                config_dict['SERVER_BACKUP_HOURS'] = hours
            
            # Add other fixed values
            config_dict['BACKUP_MINUTE'] = 0
            config_dict['AUTO_UPDATE_TXADMIN'] = True
            config_dict['SERVER_BACKUP_THROTTLE'] = 0.1
            
            # Don't touch Discord webhook config - it's managed by the Discord tab
            # Load existing config to preserve Discord settings
            existing_config = load_config()
            if 'DISCORD_WEBHOOK' in existing_config:
                config_dict['DISCORD_WEBHOOK'] = existing_config['DISCORD_WEBHOOK']
            
            # Save to JSON
            success, result = save_config(config_dict)
            
            if success:
                logging.info(f"Configuration written to: {result}")
                
                self.status_label.config(text="Configuration saved successfully!", foreground="green")
                self.app.log_message(f"Configuration saved to {result}")
                
                # Show detailed message
                messagebox.showinfo(
                    "Success", 
                    f"Configuration saved successfully to:\n{result}\n\n"
                    "The application needs to restart for changes to take effect.\n\n"
                    "Click OK to restart now."
                )
                
                # Restart the application
                self.app.log_message("Restarting application to apply configuration changes...")
                self.app.root.after(500, self.restart_application)
            else:
                raise Exception(result)
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", foreground="red")
            error_msg = f"Failed to save configuration: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def restart_application(self):
        """Restart the application"""
        import subprocess
        import sys
        
        # Close the current application
        self.app.running = False
        
        # Stop remote server if running
        if hasattr(self.app, 'remote_server') and self.app.remote_server:
            self.app.remote_server.stop()
        
        # Get the path to the current script
        if getattr(sys, 'frozen', False):
            # Running as exe
            executable = sys.executable
            subprocess.Popen([executable])
        else:
            # Running as script
            python = sys.executable
            script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.py'))
            subprocess.Popen([python, script])
        
        # Exit current instance
        self.app.root.destroy()
        sys.exit(0)
