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

# Set up specific logger for update operations
update_logger = logging.getLogger('update')
update_logger.setLevel(logging.DEBUG)

# Add file handler if not already added
if not update_logger.handlers:
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create file handler
    fh = logging.FileHandler(os.path.join(logs_dir, 'update.log'))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    update_logger.addHandler(fh)

# GitHub repository information
GITHUB_REPO = "RosewoodRidge/FIVEM-REDM-Server-Controller"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "2.6.0"  # Current application version

update_logger.info(f"Current application version: {CURRENT_VERSION}")

# File to store last update check time
UPDATE_CHECK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".update_check")
UPDATE_CHECK_INTERVAL = timedelta(hours=24)  # Check once every 24 hours

def get_latest_version():
    """
    Check GitHub API for the latest release version
    Returns tuple (version_string, download_url, description)
    """
    try:
        update_logger.info(f"Checking for latest version from: {GITHUB_API_URL}")
        
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
        
        update_logger.info(f"Latest version from GitHub: {latest_version}")
        
        # Get download URL for the ZIP asset
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'].endswith('.zip'):
                download_url = asset['browser_download_url']
                update_logger.info(f"Found download URL: {download_url}")
                break
                
        # If no specific asset found, use the source code zip
        if not download_url:
            download_url = data['zipball_url']
            update_logger.info(f"Using source code URL: {download_url}")
            
        return latest_version, download_url, data.get('body', 'No description available')
        
    except Exception as e:
        update_logger.error(f"Failed to check for updates: {str(e)}", exc_info=True)
        return None, None, None

def compare_versions(current, latest):
    """
    Compare version strings (e.g., "2.0" vs "2.1")
    Returns True if latest version is newer
    """
    if not latest:
        update_logger.warning("No latest version to compare")
        return False
        
    try:
        update_logger.info(f"Comparing versions: current={current}, latest={latest}")
        
        # Split versions into components
        current_parts = [int(part) for part in current.split('.')]
        latest_parts = [int(part) for part in latest.split('.')]
        
        # Log parts for debugging
        update_logger.debug(f"Current parts: {current_parts}, Latest parts: {latest_parts}")
        
        # Add zeros to make lists same length
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        # Compare component by component
        for i in range(max_len):
            update_logger.debug(f"Comparing position {i}: current={current_parts[i]}, latest={latest_parts[i]}")
            if latest_parts[i] > current_parts[i]:
                update_logger.info(f"Latest version ({latest}) is newer than current ({current})")
                return True
            elif latest_parts[i] < current_parts[i]:
                update_logger.info(f"Current version ({current}) is newer than latest ({latest})")
                return False
        
        update_logger.info(f"Versions are equal: {current} = {latest}")
        return False  # Versions are equal
    except Exception as e:
        update_logger.error(f"Error comparing versions: {str(e)}", exc_info=True)
        return False

def should_check_update():
    """
    Determines if it's time to check for updates based on last check time
    """
    if not os.path.exists(UPDATE_CHECK_FILE):
        update_logger.info("No previous update check record found, should check now")
        return True
        
    try:
        with open(UPDATE_CHECK_FILE, 'r') as f:
            data = json.load(f)
            last_check = datetime.fromisoformat(data.get('last_check', '2000-01-01T00:00:00'))
            
            # Check if enough time has passed
            time_since_check = datetime.now() - last_check
            should_check = time_since_check >= UPDATE_CHECK_INTERVAL
            update_logger.info(f"Last check was {time_since_check.total_seconds()/3600:.1f} hours ago. Should check: {should_check}")
            return should_check
    except Exception as e:
        update_logger.error(f"Error checking update time: {str(e)}", exc_info=True)
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
        update_logger.info("Saved last update check time")
    except Exception as e:
        update_logger.error(f"Failed to save update check time: {str(e)}", exc_info=True)

def extract_config_values(config_file):
    """
    Extract user-configured values from config.py
    Returns a dictionary of user-modified values
    """
    user_config = {}
    
    try:
        update_logger.info(f"Extracting config values from {config_file}")
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
                    update_logger.debug(f"Found config value: {var_name}")
        
        update_logger.info(f"Extracted {len(user_config)} configuration values")
        return user_config
    except Exception as e:
        update_logger.error(f"Error extracting config values: {str(e)}", exc_info=True)
        return {}

def update_config_file(new_config_path, user_configs):
    """
    Update the new config.py file with user's custom configurations
    """
    try:
        if not os.path.exists(new_config_path):
            update_logger.error(f"Config file not found: {new_config_path}")
            return False
            
        update_logger.info(f"Updating config file with user settings: {new_config_path}")
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
                    update_logger.debug(f"Updated config value: {var_name}")
                    break
                    
            if not modified:
                updated_lines.append(line)
                
        # Write the updated config
        with open(new_config_path, 'w') as f:
            f.writelines(updated_lines)
            
        update_logger.info("Config file updated successfully")
        return True
    except Exception as e:
        update_logger.error(f"Failed to update config file: {str(e)}", exc_info=True)
        return False

def apply_update(download_url, progress_callback=None):
    """
    Download and apply update
    Returns tuple (success, message)
    """
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "update.zip")
    extract_dir = os.path.join(temp_dir, "extracted")
    
    update_logger.info(f"Starting update process. Temp directory: {temp_dir}")
    update_logger.info(f"Download URL: {download_url}")
    
    try:
        if progress_callback:
            progress_callback("Downloading update...", 10)
        
        # Download the update zip
        update_logger.info("Beginning download...")
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
        
        update_logger.info(f"Download complete: {zip_path}")
        
        if progress_callback:
            progress_callback("Extracting update...", 60)
            
        # Create extraction directory
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract the zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        update_logger.info(f"Extraction complete to: {extract_dir}")
            
        # Find the root directory in the extracted content
        root_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if not root_dirs:
            error_msg = "Invalid update package: No directories found"
            update_logger.error(error_msg)
            return False, error_msg
            
        update_logger.info(f"Found root directories: {root_dirs}")
        
        # GitHub zips typically have a single root directory
        source_dir = os.path.join(extract_dir, root_dirs[0])
        update_logger.info(f"Using source directory: {source_dir}")
        
        if progress_callback:
            progress_callback("Backing up configuration...", 70)
            
        # Save current config values
        app_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(app_dir, "config.py")
        user_configs = extract_config_values(config_path)
        
        if progress_callback:
            progress_callback("Installing update...", 80)
        
        # Create a batch file to handle the update after the app exits
        # This approach is more reliable than using Python for this task
        bat_path = os.path.join(temp_dir, "update.bat")
        update_logger.info(f"Creating update batch file: {bat_path}")
        
        # Create a temporary Python script to update the config
        config_updater_path = os.path.join(temp_dir, "update_config.py")
        with open(config_updater_path, 'w') as f:
            f.write(f'''
import json
import sys

def update_config():
    try:
        with open(r"{config_path}", 'r') as f:
            config_content = f.read()
        
        # Load user configs
        user_configs = {json.dumps(user_configs)}
        
        # Update config
        with open(r"{config_path}", 'w') as f:
            for line in config_content.splitlines():
                modified = False
                for var_name, value in user_configs.items():
                    if line.strip().startswith(f"{{var_name}} = "):
                        f.write(f"{{var_name}} = {{value}}\\n")
                        modified = True
                        break
                if not modified:
                    f.write(line + "\\n")
        print("Config updated successfully")
        return 0
    except Exception as e:
        print(f"Error updating config: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(update_config())
''')
        
        # Create the actual batch file for update
        with open(bat_path, 'w') as f:
            f.write(f'''@echo off
echo Starting update process...
timeout /t 3 /nobreak > nul

echo Copying files from {source_dir} to {app_dir}...
xcopy "{source_dir}\\*" "{app_dir}" /E /I /Y /Q

echo Updating configuration...
"{sys.executable}" "{config_updater_path}"

echo Cleaning up temporary files...
rmdir /S /Q "{temp_dir}"

echo Starting application...
start "" "{sys.executable}" "{os.path.join(app_dir, 'app.py')}"
exit
''')

        # Launch the update batch file and exit
        if progress_callback:
            progress_callback("Update ready, restarting application...", 100)
        
        update_logger.info(f"Starting update batch file: {bat_path}")
        subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Return success - the calling code should exit the application
        return True, "Update downloaded successfully. The application will now restart."
        
    except Exception as e:
        error_message = f"Update failed: {str(e)}"
        update_logger.error(error_message, exc_info=True)
        
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
        
        update_logger.info(f"Showing update dialog for version {version}")
        
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
        update_logger.info("User clicked 'Update Now'")
        
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
        
        update_logger.info(f"Update process result: success={success}, message={message}")
        
        if success:
            messagebox.showinfo("Update Ready", 
                                "The application will now restart with the updated version.")
            self.result = "update"
            update_logger.info("Scheduling application exit for update")
            # Use destroy instead of quit to ensure the app exits completely
            self.parent.after(0, self.parent.destroy)
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
        update_logger.info("User chose to be reminded later")
        self.result = "later"
        self.destroy()
    
    def skip_version(self):
        """Skip this version"""
        update_logger.info(f"User chose to skip version {self.version}")
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
        update_logger.info(f"Checking for updates (force={force})")
        
        # Skip check if it's not time yet, unless forced
        if not force and not should_check_update():
            update_logger.info("Skipping update check (not time yet)")
            return False
            
        # Record that we checked
        save_last_check_time()
            
        # Get latest version
        latest_version, download_url, description = get_latest_version()
        
        # Check if new version is available
        if not latest_version or not download_url:
            update_logger.warning("Could not get update information")
            return False
            
        # Check for skipped version
        try:
            with open(UPDATE_CHECK_FILE, 'r') as f:
                data = json.load(f)
                if data.get('skipped_version') == latest_version:
                    update_logger.info(f"User previously skipped version {latest_version}")
                    return False
        except Exception:
            pass
            
        # Check if the latest version is newer
        update_available = compare_versions(CURRENT_VERSION, latest_version)
        update_logger.info(f"Update available: {update_available}")
        
        if update_available:
            if root:
                # Show update dialog
                update_logger.info("Showing update dialog")
                dialog = UpdateDialog(root, latest_version, description, download_url)
                if dialog.result == "update":
                    update_logger.info("User accepted update, application should exit")
                    return True  # App should exit for update
            else:
                update_logger.info(f"Update available: v{latest_version} (no UI to show)")
        else:
            update_logger.info("No update needed, current version is up-to-date")
                
        return False
        
    except Exception as e:
        update_logger.error(f"Error checking for updates: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # For testing the update checker directly
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    result = check_for_updates(root, force=True)
    update_logger.info(f"Direct check result: {result}")
    if not result:
        root.destroy()
