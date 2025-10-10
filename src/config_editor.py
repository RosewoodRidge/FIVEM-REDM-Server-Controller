import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging

# Ensure logs directory exists
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(logs_dir, 'config_editor.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Colors matching the main app
COLORS = {
    'bg': '#0f172a',
    'panel': '#1e293b',
    'accent': '#3b82f6',
    'accent_hover': '#2563eb',
    'text': '#f8fafc',
    'text_secondary': '#94a3b8',
    'button_text': "#3b3b3b",
}

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("FIVEM & REDM Server Controller - Configuration Editor")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg'])
        
        # Store config file path
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
        
        # Dictionary to store configuration values
        self.config_vars = {}
        
        # Apply styling
        self.apply_styles()
        
        # Create main frame with scrollbar
        main_container = ttk.Frame(root)
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
        
        # Load current configuration
        self.load_config()
        
        # Create configuration sections
        self.create_database_section()
        self.create_backup_section()
        self.create_server_section()
        self.create_txadmin_section()
        self.create_schedule_section()
        
        # Buttons at the bottom
        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.root.destroy,
            style="TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            button_frame,
            text="Ready",
            foreground=COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT)
    
    def apply_styles(self):
        """Apply modern styling to widgets"""
        style = ttk.Style()
        style.configure("TFrame", background=COLORS['bg'])
        style.configure("TLabel", background=COLORS['bg'], foreground=COLORS['text'])
        style.configure("TLabelframe", background=COLORS['panel'], foreground=COLORS['text'])
        style.configure("TLabelframe.Label", background=COLORS['panel'], foreground=COLORS['text'], font=('Segoe UI', 11, 'bold'))
        style.configure("TButton", background=COLORS['accent'], foreground=COLORS['button_text'], padding=10)
        style.configure("Primary.TButton", background=COLORS['accent'], foreground=COLORS['button_text'], padding=12, font=('Segoe UI', 11, 'bold'))
        style.configure("TEntry", fieldbackground=COLORS['panel'], foreground='#000000', borderwidth=1, padding=8)
    
    def load_config(self):
        """Load configuration from config.py"""
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Parse configuration values using regex
            patterns = {
                'DB_HOST': r"DB_HOST\s*=\s*['\"]([^'\"]*)['\"]",
                'DB_USER': r"DB_USER\s*=\s*['\"]([^'\"]*)['\"]",
                'DB_PASSWORD': r"DB_PASSWORD\s*=\s*['\"]([^'\"]*)['\"]",
                'DB_NAME': r"DB_NAME\s*=\s*['\"]([^'\"]*)['\"]",
                'BACKUP_DIR': r"BACKUP_DIR\s*=\s*['\"]([^'\"]*)['\"]",
                'MYSQLDUMP_PATH': r"MYSQLDUMP_PATH\s*=\s*['\"]([^'\"]*)['\"]",
                'MYSQL_PATH': r"MYSQL_PATH\s*=\s*['\"]([^'\"]*)['\"]",
                'SERVER_FOLDER': r"SERVER_FOLDER\s*=\s*['\"]([^'\"]*)['\"]",
                'SERVER_BACKUP_DIR': r"SERVER_BACKUP_DIR\s*=\s*['\"]([^'\"]*)['\"]",
                'SERVER_BACKUP_KEEP_COUNT': r"SERVER_BACKUP_KEEP_COUNT\s*=\s*(\d+)",
                'TXADMIN_SERVER_DIR': r"TXADMIN_SERVER_DIR\s*=\s*['\"]([^'\"]*)['\"]",
                'TXADMIN_BACKUP_DIR': r"TXADMIN_BACKUP_DIR\s*=\s*['\"]([^'\"]*)['\"]",
                'TXADMIN_DOWNLOAD_DIR': r"TXADMIN_DOWNLOAD_DIR\s*=\s*['\"]([^'\"]*)['\"]",
                'SEVEN_ZIP_PATH': r"SEVEN_ZIP_PATH\s*=\s*['\"]([^'\"]*)['\"]",
                'TXADMIN_KEEP_COUNT': r"TXADMIN_KEEP_COUNT\s*=\s*(\d+)",
                'DB_BACKUP_HOURS': r"DB_BACKUP_HOURS\s*=\s*\[([^\]]*)\]",
                'SERVER_BACKUP_HOURS': r"SERVER_BACKUP_HOURS\s*=\s*\[([^\]]*)\]",
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1)
                    # Convert escaped backslashes back to single for display
                    if '\\\\' in value:
                        value = value.replace('\\\\', '\\')
                    self.config_vars[key] = value
                else:
                    self.config_vars[key] = ""
            
            logging.info("Configuration loaded successfully")
        
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
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
        
        if key not in self.config_vars or not self.config_vars[key]:
            self.config_vars[key] = default
        
        var = tk.StringVar(value=self.config_vars[key])
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
        
        if key not in self.config_vars or not self.config_vars[key]:
            self.config_vars[key] = default
        
        var = tk.StringVar(value=self.config_vars[key])
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
        """Save configuration back to config.py"""
        try:
            # Read current config file
            with open(self.config_file, 'r') as f:
                lines = f.readlines()
            
            # Update lines with new values
            new_lines = []
            for line in lines:
                updated = False
                
                # Handle path variables (need double backslashes)
                path_keys = ['BACKUP_DIR', 'MYSQLDUMP_PATH', 'MYSQL_PATH', 'SERVER_FOLDER', 
                            'SERVER_BACKUP_DIR', 'TXADMIN_SERVER_DIR', 'TXADMIN_BACKUP_DIR', 
                            'TXADMIN_DOWNLOAD_DIR', 'SEVEN_ZIP_PATH']
                
                for key in path_keys:
                    if line.strip().startswith(f"{key} ="):
                        var = self.config_vars.get(f"{key}_VAR")
                        if var:
                            value = var.get()
                            # Convert single backslashes to double for Python
                            value = value.replace('\\', '\\\\')
                            new_lines.append(f"{key} = '{value}'\n")
                            updated = True
                            break
                
                # Handle string variables
                string_keys = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
                for key in string_keys:
                    if line.strip().startswith(f"{key} ="):
                        var = self.config_vars.get(f"{key}_VAR")
                        if var:
                            value = var.get()
                            new_lines.append(f"{key} = '{value}'\n")
                            updated = True
                            break
                
                # Handle integer variables
                int_keys = ['SERVER_BACKUP_KEEP_COUNT', 'TXADMIN_KEEP_COUNT']
                for key in int_keys:
                    if line.strip().startswith(f"{key} ="):
                        var = self.config_vars.get(f"{key}_VAR")
                        if var:
                            value = var.get()
                            new_lines.append(f"{key} = {value}\n")
                            updated = True
                            break
                
                # Handle backup hours arrays
                if line.strip().startswith("DB_BACKUP_HOURS ="):
                    var = self.config_vars.get("DB_BACKUP_HOURS_ENTRY")
                    if var:
                        hours = [h.strip() for h in var.get().split(',')]
                        new_lines.append(f"DB_BACKUP_HOURS = [{', '.join(hours)}]\n")
                        updated = True
                
                elif line.strip().startswith("SERVER_BACKUP_HOURS ="):
                    var = self.config_vars.get("SERVER_BACKUP_HOURS_ENTRY")
                    if var:
                        hours = [h.strip() for h in var.get().split(',')]
                        new_lines.append(f"SERVER_BACKUP_HOURS = [{', '.join(hours)}]\n")
                        updated = True
                
                if not updated:
                    new_lines.append(line)
            
            # Write updated config
            with open(self.config_file, 'w') as f:
                f.writelines(new_lines)
            
            self.status_label.config(text="Configuration saved successfully!", foreground="green")
            logging.info("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully!\n\nPlease restart the application for changes to take effect.")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", foreground="red")
            logging.error(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

def main():
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()

if __name__ == '__main__':
    main()
