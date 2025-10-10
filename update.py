import os
import sys
import json
import shutil
import zipfile
import logging
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
from datetime import datetime, timedelta

# GitHub repository information
GITHUB_REPO = "RosewoodRidge/FIVEM-REDM-Server-Controller"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "2.1"  # Current application version

# File to store last update check time
UPDATE_CHECK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".update_check")
UPDATE_CHECK_INTERVAL = timedelta(hours=24)  # Check once every 24 hours

def get_latest_version():
    """
    Check GitHub API for the latest release version
    Returns tuple (version_string, download_url, description)
    """
    try:
        # Set up headers to avoid GitHub API rate limiting issues
        headers = {
            'User-Agent': 'FIVEM-REDM-Server-Controller-Update-Checker'
        }
        
        # Make request to GitHub API
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        # Extract version from tag name (removing 'v' prefix if present)
        latest_version = data['tag_name']
        if latest_version.lower().startswith('v'):
            latest_version = latest_version[1:]
            
        # Get download URL for the ZIP asset
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'].endswith('.zip'):
                download_url = asset['browser_download_url']
                break
                
        # If no specific asset found, use the source code zip
        if not download_url:
            download_url = data['zipball_url']
            
        return latest_version, download_url, data.get('body', 'No description available')
        
    except Exception as e:
        logging.error(f"Failed to check for updates: {str(e)}")
        return None, None, None

def compare_versions(current, latest):
    """
    Compare version strings (e.g., "2.1" vs "2.2")
    Returns True if latest version is newer
    """
    if not latest:
        return False
        
    try:
        # Split versions into components
        current_parts = [int(part) for part in current.split('.')]
        latest_parts = [int(part) for part in latest.split('.')]
        
        # Add zeros to make lists same length
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        # Compare component by component
        for i in range(max_len):
            if latest_parts[i] > current_parts[i]:
                return True
            elif latest_parts[i] < current_parts[i]:
                return False
                
        return False  # Versions are equal
    except Exception as e:
        logging.error(f"Error comparing versions: {str(e)}")
        return False

def should_check_update():
    """
    Determines if it's time to check for updates based on last check time
    """
    if not os.path.exists(UPDATE_CHECK_FILE):
        return True
        
    try:
        with open(UPDATE_CHECK_FILE, 'r') as f:
            data = json.load(f)
            last_check = datetime.fromisoformat(data.get('last_check', '2000-01-01T00:00:00'))
            
            # Check if enough time has passed
            return datetime.now() - last_check >= UPDATE_CHECK_INTERVAL
    except Exception:
        return True  # If any error occurs, go ahead and check

def save_last_check_time():
    """
    Save the current time as the last update check
    """
    try:
        with open(UPDATE_CHECK_FILE, 'w') as f:
            json.dump({
                'last_check': datetime.now().isoformat()
            }, f)
    except Exception as e:
        logging.error(f"Failed to save update check time: {str(e)}")

def extract_config_values(config_file):
    """
    Extract user-configured values from config.py
    Returns a dictionary of user-modified values
    """
    user_config = {}
    
    try:
        with open(config_file, 'r') as f:
            lines = f.readlines()
            
        # Identify non-default values by looking for specific user configs
        for line in lines:
            line = line.strip()
            
            # Skip comments, empty lines, and default settings
            if not line or line.startswith('#'):
                continue
                
            # Look for variable assignments with user paths or values
            if ' = ' in line and not line.endswith('# Default'):
                # Extract variable and value
                var_name, value = line.split(' = ', 1)
                var_name = var_name.strip()
                
                # Only store if it's a likely configuration value
                if (var_name.isupper() and 
                    ('_PATH' in var_name or '_DIR' in var_name or 
                     '_FOLDER' in var_name or '_HOST' in var_name or
                     '_USER' in var_name or '_PASSWORD' in var_name)):
                    user_config[var_name] = value
                    
        return user_config
    except Exception as e:
        logging.error(f"Error extracting config values: {str(e)}")
        return {}

def update_config_file(new_config_path, user_configs):
    """
    Update the new config.py file with user's custom configurations
    """
    try:
        if not os.path.exists(new_config_path):
            return False
            
        with open(new_config_path, 'r') as f:
            lines = f.readlines()
            
        updated_lines = []
        for line in lines:
            modified = False
            
            # Check if line contains a user-configured variable
            for var_name, value in user_configs.items():
                if line.strip().startswith(f"{var_name} = "):
                    # Replace the line with user's configuration
                    updated_lines.append(f"{var_name} = {value}\n")
                    modified = True
                    break
                    
            if not modified:
                updated_lines.append(line)
                
        # Write the updated config
        with open(new_config_path, 'w') as f:
            f.writelines(updated_lines)
            
        return True
    except Exception as e:
        logging.error(f"Failed to update config file: {str(e)}")
        return False

def apply_update(download_url, progress_callback=None):
    """
    Download and apply update
    Returns tuple (success, message)
    """
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "update.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    try:
        if progress_callback:
            progress_callback("Downloading update...", 10)
        
        # Download the update zip
        with urllib.request.urlopen(download_url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as out_file:
                block_size = 8192
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    
                    downloaded += len(buffer)
                    out_file.write(buffer)
                    
                    if total_size > 0 and progress_callback:
                        progress = int((downloaded / total_size) * 50)
                        progress_callback(f"Downloading update... ({downloaded/1000000:.1f} MB / {total_size/1000000:.1f} MB)", 10 + progress)
        
        if progress_callback:
            progress_callback("Extracting update...", 60)
            
        # Create extraction directory
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract the zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Find the root directory in the extracted content
        root_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if not root_dirs:
            return False, "Invalid update package: No directories found"
            
        # GitHub zips typically have a single root directory
        source_dir = os.path.join(extract_dir, root_dirs[0])
        
        if progress_callback:
            progress_callback("Backing up configuration...", 70)
            
        # Save current config values
        app_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(app_dir, "config.py")
        user_configs = extract_config_values(config_path)
        
        if progress_callback:
            progress_callback("Installing update...", 80)
        
        # Prepare restart script to complete the update
        # This script will run after we exit and:
        # 1. Copy all files from the extracted update to the app directory
        # 2. Update the config.py with user's custom settings
        # 3. Restart the application
        
        restart_script = os.path.join(temp_dir, "complete_update.py")
        with open(restart_script, 'w') as f:
            f.write(f'''
import os
import sys
import time
import shutil
import json
import subprocess

def main():
    # Give the main app time to exit
    time.sleep(2)
    
    app_dir = r"{app_dir}"
    source_dir = r"{source_dir}"
    config_backup = {json.dumps(user_configs)}
    
    # Copy all files from extracted update to app directory
    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        target_item = os.path.join(app_dir, item)
        
        # Skip config.py to not overwrite user settings immediately
        if item == "config.py":
            continue
            
        # Remove existing file/dir
        if os.path.exists(target_item):
            if os.path.isdir(target_item):
                shutil.rmtree(target_item)
            else:
                os.remove(target_item)
                
        # Copy new file/dir
        if os.path.isdir(source_item):
            shutil.copytree(source_item, target_item)
        else:
            shutil.copy2(source_item, target_item)
    
    # Now handle config.py specifically
    source_config = os.path.join(source_dir, "config.py")
    target_config = os.path.join(app_dir, "config.py")
    
    if os.path.exists(source_config):
        # First backup the existing config
        if os.path.exists(target_config):
            shutil.copy2(target_config, target_config + ".bak")
            
        # Copy the new config
        shutil.copy2(source_config, target_config)
        
        # Update with user's settings
        with open(target_config, 'r') as f:
            lines = f.readlines()
            
        updated_lines = []
        for line in lines:
            modified = False
            for var_name, value in config_backup.items():
                if line.strip().startswith(f"{{var_name}} = "):
                    updated_lines.append(f"{{var_name}} = {{value}}\\n")
                    modified = True
                    break
            if not modified:
                updated_lines.append(line)
                
        with open(target_config, 'w') as f:
            f.writelines(updated_lines)
    
    # Clean up the temp directory
    try:
        shutil.rmtree(r"{temp_dir}")
    except:
        pass
        
    # Restart the application
    try:
        python = sys.executable
        script = os.path.join(app_dir, 'app.py')
        subprocess.Popen([python, script])
    except:
        pass

if __name__ == "__main__":
    main()
''')

        # Launch the update script and exit
        if progress_callback:
            progress_callback("Update ready, restarting application...", 100)
            
        # Start the update script
        python = sys.executable
        subprocess.Popen([python, restart_script])
        
        # Return success - the calling code should exit the application
        return True, "Update downloaded successfully. The application will now restart."
        
    except Exception as e:
        error_message = f"Update failed: {str(e)}"
        logging.error(error_message)
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
            
        return False, error_message

class UpdateDialog(tk.Toplevel):
    """Dialog to show update information and allow user to download"""
    
    def __init__(self, parent, version, description, download_url):
        super().__init__(parent)
        
        self.parent = parent
        self.version = version
        self.download_url = download_url
        self.result = None
        
        self.title(f"Update Available - v{version}")
        self.geometry("500x400")
        self.resizable(True, True)
        self.configure(bg='#0f172a')
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Apply styling
        self.style = ttk.Style(self)
        self.style.configure("Update.TLabel", 
                            background='#0f172a',
                            foreground='#f8fafc', 
                            font=('Segoe UI', 10))
        self.style.configure("UpdateTitle.TLabel", 
                            background='#0f172a',
                            foreground='#3b82f6', 
                            font=('Segoe UI', 14, 'bold'))
        
        # Title label
        ttk.Label(self, 
                text=f"Version {version} Available", 
                style="UpdateTitle.TLabel").pack(pady=(20, 5), padx=20)
        
        ttk.Label(self, 
                text="A new version of the FIVEM & REDM Server Controller is available.", 
                style="Update.TLabel").pack(pady=(5, 15), padx=20)
        
        # Frame for update description
        desc_frame = ttk.Frame(self)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Update description with scrollbar
        self.desc_text = tk.Text(desc_frame, 
                                wrap=tk.WORD, 
                                bg='#1e293b',
                                fg='#f8fafc',
                                border=0,
                                height=10)
        scrollbar = ttk.Scrollbar(desc_frame, command=self.desc_text.yview)
        self.desc_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert description text
        self.desc_text.insert(tk.END, description)
        self.desc_text.config(state=tk.DISABLED)
        
        # Progress bar (hidden initially)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_frame = ttk.Frame(self)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, 
                                       text="", 
                                       style="Update.TLabel")
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, 
                                          variable=self.progress_var,
                                          length=100, 
                                          mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))
        
        self.progress_frame.pack_forget()  # Hide initially
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Update button
        self.update_button = ttk.Button(button_frame, 
                                      text="Update Now", 
                                      command=self.download_update)
        self.update_button.pack(side=tk.RIGHT, padx=5)
        
        # Remind later button
        ttk.Button(button_frame, 
                 text="Remind Me Later", 
                 command=self.remind_later).pack(side=tk.RIGHT, padx=5)
        
        # Skip version button
        ttk.Button(button_frame, 
                 text="Skip This Version", 
                 command=self.skip_version).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog on parent window
        self.center_on_parent()
        
        # Wait for the dialog to be closed
        self.wait_window()
    
    def center_on_parent(self):
        """Center this window on the parent window"""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate position
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # Set position
        self.geometry(f"+{x}+{y}")
    
    def download_update(self):
        """Start downloading and applying the update"""
        self.update_button.config(state=tk.DISABLED)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Start the update process in a separate thread
        threading.Thread(
            target=self._do_update,
            daemon=True
        ).start()
    
    def _do_update(self):
        """Thread function to download and apply update"""
        success, message = apply_update(
            self.download_url,
            progress_callback=self.update_progress
        )
        
        if success:
            messagebox.showinfo("Update Ready", 
                                "The application will now restart with the updated version.")
            self.result = "update"
            self.parent.after(0, self.parent.quit)  # Schedule app to exit
        else:
            messagebox.showerror("Update Failed", message)
            self.update_button.config(state=tk.NORMAL)
    
    def update_progress(self, message, progress):
        """Update the progress bar and message"""
        self.progress_var.set(progress)
        self.progress_label.config(text=message)
        self.update_idletasks()
    
    def remind_later(self):
        """Close dialog and remind later"""
        self.result = "later"
        self.destroy()
    
    def skip_version(self):
        """Skip this version"""
        with open(UPDATE_CHECK_FILE, 'w') as f:
            data = {
                'last_check': datetime.now().isoformat(),
                'skipped_version': self.version
            }
            json.dump(data, f)
            
        self.result = "skip"
        self.destroy()

def check_for_updates(root=None, force=False):
    """
    Check for updates and show dialog if updates are available
    Returns True if application should exit for update
    """
    try:
        # Skip check if it's not time yet, unless forced
        if not force and not should_check_update():
            return False
            
        # Record that we checked
        save_last_check_time()
            
        # Get latest version
        latest_version, download_url, description = get_latest_version()
        
        # Check if new version is available
        if not latest_version or not download_url:
            logging.warning("Could not get update information")
            return False
            
        # Check for skipped version
        try:
            with open(UPDATE_CHECK_FILE, 'r') as f:
                data = json.load(f)
                if data.get('skipped_version') == latest_version:
                    return False
        except Exception:
            pass
            
        if compare_versions(CURRENT_VERSION, latest_version):
            if root:
                # Show update dialog
                dialog = UpdateDialog(root, latest_version, description, download_url)
                if dialog.result == "update":
                    return True  # App should exit for update
            else:
                logging.info(f"Update available: v{latest_version}")
                
        return False
        
    except Exception as e:
        logging.error(f"Error checking for updates: {str(e)}")
        return False

if __name__ == "__main__":
    # For testing the update checker directly
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    result = check_for_updates(root, force=True)
    if not result:
        root.destroy()
