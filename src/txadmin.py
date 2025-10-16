import os
import logging
import requests
import subprocess
import zipfile
import shutil
import glob
import time
import psutil
import tarfile
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config_manager import is_windows
import stat
import json

from config import (
    TXADMIN_SERVER_DIR, TXADMIN_BACKUP_DIR, TXADMIN_DOWNLOAD_DIR,
    TXADMIN_URL, TXADMIN_KEEP_COUNT, SEVEN_ZIP_PATH, AUTO_UPDATE_TXADMIN
)

# Don't create directories on import - do it in a function instead
def ensure_txadmin_backup_dir():
    """Ensure the txadmin backup directory exists"""
    os.makedirs(TXADMIN_BACKUP_DIR, exist_ok=True)

# Path to store current version information
TXADMIN_VERSION_FILE = os.path.join(TXADMIN_BACKUP_DIR, "current_version.json")

def find_fxserver_processes():
    """
    Finds all processes with FXServer in the name
    Returns a list of process objects
    """
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            process_name = proc.info['name'] if proc.info['name'] else ''
            if 'FXServer' in process_name or 'fxserver' in process_name.lower():
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def stop_fxserver(callback=None):
    """
    Stops all FXServer processes if they're running
    Returns tuple (was_running, success, message)
    """
    processes = find_fxserver_processes()
    if not processes:
        if callback:
            callback("No FXServer processes found")
        return False, True, "No FXServer processes were running"
    
    try:
        server_path = None
        terminated_count = 0
        
        if callback:
            callback(f"Found {len(processes)} FXServer processes. Stopping all...")
        
        # Try to get server path from first process
        for proc in processes:
            try:
                if not server_path and hasattr(proc, 'exe'):
                    server_path = proc.exe()
                    break
            except:
                pass
        
        # Terminate all FXServer processes
        for proc in processes:
            try:
                pid = proc.pid
                proc.terminate()
                terminated_count += 1
                if callback:
                    callback(f"Terminated FXServer process with PID: {pid}")
            except:
                pass
        
        # Wait for processes to end
        remaining_processes = []
        for _ in range(15):  # Wait up to 15 seconds
            remaining_processes = find_fxserver_processes()
            if not remaining_processes:
                if callback:
                    callback("All FXServer processes have been stopped")
                return True, True, server_path
            time.sleep(1)
        
        # Force kill any remaining processes
        if remaining_processes:
            for proc in remaining_processes:
                try:
                    pid = proc.pid
                    proc.kill()
                    if callback:
                        callback(f"Force killed FXServer process with PID: {pid}")
                except:
                    pass
            
            time.sleep(2)  # Give a little more time after force kill
        
        if callback:
            callback(f"Stopped {terminated_count} FXServer processes")
        
        return True, True, server_path
    
    except Exception as e:
        error_message = f"Failed to stop FXServer processes: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message)
        return True, False, error_message

def take_ownership_and_remove(path, callback=None):
    """
    Takes ownership of files/folders and then removes them
    Handles locked files by changing permissions
    """
    # Try standard removal first
    try:
        if os.path.isfile(path):
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            os.unlink(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                    except:
                        pass  # Just try to change what we can
            shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception as e:
        if callback:
            callback(f"Standard removal failed: {str(e)}")
        
        # Windows-specific elevated removal
        if is_windows():
            try:
                if os.path.exists(path):
                    # Try running rmdir or del with /F flag using cmd
                    if os.path.isdir(path):
                        subprocess.run(['cmd', '/c', f'rmdir /S /Q "{path}"'], shell=True)
                    else:
                        subprocess.run(['cmd', '/c', f'del /F /Q "{path}"'], shell=True)
                return True
            except Exception as e2:
                if callback:
                    callback(f"Failed to remove with elevated privileges: {str(e2)}")
                return False
        else:
            # On Linux, try with sudo if available
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        subprocess.run(['sudo', 'rm', '-rf', path], check=True)
                    else:
                        subprocess.run(['sudo', 'rm', '-f', path], check=True)
                return True
            except:
                if callback:
                    callback(f"Failed to remove: {str(e)}")
                return False

def start_fxserver(server_path=None, callback=None):
    """
    Starts the FXServer.exe process
    Returns tuple (success, message)
    """
    try:
        # If path not provided, try to find it in the server directory
        if not server_path:
            server_path = os.path.join(TXADMIN_SERVER_DIR, "FXServer.exe")
        
        # Check if the executable exists
        if not os.path.exists(server_path):
            error_message = f"FXServer.exe not found at: {server_path}"
            logging.error(error_message)
            if callback:
                callback(error_message)
            return False, error_message
        
        if callback:
            callback(f"Starting FXServer.exe from {server_path}...")
        
        # Launch the process without waiting
        subprocess.Popen(server_path, cwd=os.path.dirname(server_path))
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's running
        processes = find_fxserver_processes()
        if processes:
            # Get the first process from the list
            process = processes[0]
            if callback:
                callback(f"FXServer.exe started successfully (PID: {process.pid})")
            return True, f"FXServer.exe started with PID: {process.pid}"
        else:
            error_message = "FXServer.exe failed to start"
            logging.error(error_message)
            if callback:
                callback(error_message)
            return False, error_message
        
    except Exception as e:
        error_message = f"Failed to start FXServer.exe: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message)
        return False, error_message

def get_latest_txadmin_url(callback=None):
    """
    Scrapes the FiveM website to get the latest recommended txAdmin download URL
    """
    if callback:
        callback("Checking for latest txAdmin version...", 5)
    
    try:
        # Get the main artifacts page
        response = requests.get(TXADMIN_URL)
        response.raise_for_status()
        
        # Parse HTML to find the recommended version link
        soup = BeautifulSoup(response.text, 'html.parser')
        recommended_button = soup.find('a', class_='button is-link is-primary')
        
        if not recommended_button:
            raise ValueError("Couldn't find the recommended version link")
            
        # Extract the href attribute which contains the download link
        download_path = recommended_button['href']
        
        # Check if the download path contains the server.7z file directly
        if 'server.7z' in download_path:
            # If the path doesn't start with a slash and doesn't include /master/,
            # we need to make sure it's properly formed
            if not download_path.startswith('/') and '/master/' not in download_path:
                # Check if download_path has a folder structure like 12345-hash/server.7z
                if '/' in download_path and not download_path.startswith('http'):
                    # Ensure we have the /master/ segment
                    base_url = TXADMIN_URL
                    if base_url.endswith('/master'):
                        base_url = base_url + '/'
                    elif not base_url.endswith('/master/'):
                        if base_url.endswith('/'):
                            base_url = base_url + 'master/'
                        else:
                            base_url = base_url + '/master/'
                    
                    # Construct the full URL
                    download_url = urljoin(base_url, download_path)
                else:
                    # Just use urljoin for standard paths
                    download_url = urljoin(TXADMIN_URL, download_path)
            else:
                # Standard urljoin for paths with leading slash or already containing /master/
                download_url = urljoin(TXADMIN_URL, download_path)
        else:
            # Standard urljoin for other types of paths
            download_url = urljoin(TXADMIN_URL, download_path)
        
        # Debug log the URL
        logging.info(f"Constructed download URL: {download_url}")
        
        if callback:
            callback(f"Found latest txAdmin version: {download_url}", 5)
        
        return download_url
    
    except Exception as e:
        error_message = f"Failed to get latest txAdmin URL: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message, 5)
        return None

def check_for_txadmin_updates(callback=None):
    """
    Checks if a new TxAdmin version is available
    Returns tuple (update_available, current_url, latest_url)
    """
    if callback:
        callback("Checking for TxAdmin updates...")
    
    # Get the current version URL
    current_version_url = get_stored_txadmin_version()
    
    # Get the latest version URL
    latest_version_url = get_latest_txadmin_url(callback)
    
    if not latest_version_url:
        if callback:
            callback("Failed to get latest TxAdmin version URL")
        return False, current_version_url, None
    
    # Check if we have a current version stored and if it's different
    if current_version_url and current_version_url == latest_version_url:
        if callback:
            callback(f"TxAdmin is up to date (version: {extract_version_from_url(latest_version_url)})")
        return False, current_version_url, latest_version_url
    
    # If we don't have a current version stored or it's different, update is available
    if callback:
        if current_version_url:
            callback(f"TxAdmin update available! Current: {extract_version_from_url(current_version_url)}, Latest: {extract_version_from_url(latest_version_url)}")
        else:
            callback(f"TxAdmin initial version detected: {extract_version_from_url(latest_version_url)}")
    
    return True, current_version_url, latest_version_url

def extract_version_from_url(url):
    """Extract version number from URL string"""
    if not url:
        return "unknown"
    
    try:
        # Try to extract version number like "17000" from URLs like
        # "https://runtime.fivem.net/artifacts/fivem/build_server_windows/master/17000-e0ef7490f76a24505b8bac7065df2b7075e610ba/server.7z"
        parts = url.split('/')
        for part in parts:
            if '-' in part and part[0].isdigit():
                return part.split('-')[0]  # Return the numeric part
        return "unknown"
    except:
        return "unknown"

def get_stored_txadmin_version():
    """Get the stored TxAdmin version URL"""
    if not os.path.exists(TXADMIN_VERSION_FILE):
        return None
    
    try:
        with open(TXADMIN_VERSION_FILE, 'r') as f:
            data = json.load(f)
            return data.get('version_url')
    except Exception as e:
        logging.error(f"Failed to read stored TxAdmin version: {str(e)}")
        return None

def store_txadmin_version(version_url):
    """Store the current TxAdmin version URL"""
    try:
        with open(TXADMIN_VERSION_FILE, 'w') as f:
            json.dump({'version_url': version_url, 'updated_at': datetime.now().isoformat()}, f)
        return True
    except Exception as e:
        logging.error(f"Failed to store TxAdmin version: {str(e)}")
        return False

def auto_update_txadmin(callback=None):
    """
    Checks for updates and automatically updates TxAdmin if new version is available
    Returns tuple (updated, message)
    """
    update_available, current_url, latest_url = check_for_txadmin_updates(callback)
    
    if not update_available:
        return False, "No update available"
    
    if callback:
        callback("Starting automatic TxAdmin update...")
    
    try:
        # Step 1: Backup current server
        if callback:
            callback("Backing up current server before update...")
        backup_success, backup_result = backup_txadmin(callback)
        if not backup_success:
            return False, f"Backup failed: {backup_result}"
        
        # Step 2: Download the update
        if callback:
            callback(f"Downloading update from {latest_url}...")
        download_success, download_path = download_txadmin(latest_url, callback)
        if not download_success:
            return False, f"Download failed: {download_path}"
        
        # Step 3: Extract the update
        if callback:
            callback("Extracting update...")
        extract_success, extract_message = extract_txadmin(download_path, callback)
        if not extract_success:
            return False, f"Extraction failed: {extract_message}"
        
        # Step 4: Clean up old backups
        if callback:
            callback("Cleaning up old backups...")
        deleted = delete_old_txadmin_backups()
        if deleted > 0 and callback:
            callback(f"Deleted {deleted} old backup(s)")
        
        # Step 5: Update stored version
        store_txadmin_version(latest_url)
        
        # Step 6: Done
        if callback:
            callback(f"TxAdmin updated successfully to version {extract_version_from_url(latest_url)}")
        
        return True, f"Updated to version {extract_version_from_url(latest_url)}"
        
    except Exception as e:
        error_message = f"Auto-update failed: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message)
        return False, error_message

def backup_txadmin(callback=None):
    """
    Creates a backup of the current txAdmin server folder.
    Returns tuple (success, backup_file_path)
    """
    if callback:
        callback("Creating backup of the current txAdmin server...", 10)
    
    # Ensure backup directory exists
    ensure_txadmin_backup_dir()
    
    try:
        # Create a unique filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = os.path.join(TXADMIN_BACKUP_DIR, f"txadmin-backup-{timestamp}.zip")
        
        # Check if server directory exists
        if not os.path.exists(TXADMIN_SERVER_DIR):
            raise FileNotFoundError(f"Server directory not found: {TXADMIN_SERVER_DIR}")
        
        # Create a zip backup
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(TXADMIN_SERVER_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, os.path.dirname(TXADMIN_SERVER_DIR))
                    zipf.write(file_path, rel_path)
        
        if callback:
            callback(f"Successfully created txAdmin backup: {backup_file}", 10)
        
        return True, backup_file
    
    except Exception as e:
        error_message = f"Failed to backup txAdmin: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message, 10)
        return False, error_message

def download_txadmin(url, callback=None):
    """
    Downloads the txAdmin update from the specified URL.
    Returns tuple (success, file_path)
    """
    if callback:
        callback(f"Downloading txAdmin update from {url}...", 20)
    
    try:
        # Ensure download directory exists
        os.makedirs(TXADMIN_DOWNLOAD_DIR, exist_ok=True)
        
        # Set up the file path
        file_path = os.path.join(TXADMIN_DOWNLOAD_DIR, "server.7z")
        
        # Download with progress updates
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            # Display download progress
            if total_size > 0:
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress_percent = 20 + int((downloaded / total_size) * 60)  # 20-80%
                            if callback:
                                callback(f"Downloaded {downloaded / (1024*1024):.1f} MB of {total_size / (1024*1024):.1f} MB ({progress_percent-20:.0f}%)", progress_percent)
            else:
                # For responses without content length
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
        
        if callback:
            callback(f"Download complete: {file_path}", 80)
        
        return True, file_path
    
    except Exception as e:
        error_message = f"Failed to download txAdmin update: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message, 80)
        return False, error_message

def extract_txadmin(file_path, callback=None):
    """
    Extracts the txAdmin archive to the server directory.
    Uses 7-Zip on Windows, tar on Linux.
    Returns tuple (success, message)
    """
    if callback:
        callback(f"Extracting txAdmin update from {file_path}...", 80)
    
    try:
        # Check if the 7z file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Update file not found: {file_path}")
        
        # Stop FXServer if running before extraction
        was_running, stop_success, server_info = stop_fxserver(callback)
        if was_running and not stop_success:
            if callback:
                callback("Warning: Could not stop all FXServer processes. Update may fail.")
        
        # Wait for processes to fully stop
        if was_running:
            time.sleep(3)
        
        # Platform-specific extraction
        if is_windows():
            # Use 7-Zip on Windows
            if not os.path.exists(SEVEN_ZIP_PATH):
                # Try to find 7z in PATH
                seven_zip = shutil.which('7z')
                if not seven_zip:
                    raise FileNotFoundError(f"7-Zip executable not found. Please install 7-Zip or configure SEVEN_ZIP_PATH in settings.")
            else:
                seven_zip = SEVEN_ZIP_PATH
            
            # Extract the 7z archive using 7-Zip command line
            if callback:
                callback("Extracting files...", 85)
            
            extract_command = [
                seven_zip,
                'x',
                file_path,
                f'-o{TXADMIN_SERVER_DIR}',
                '-y'
            ]
            
            process = subprocess.run(
                extract_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                raise Exception(f"7-Zip extraction failed: {process.stderr}")
        else:
            # Use tar on Linux (FiveM distributes .tar.xz for Linux)
            if callback:
                callback("Extracting files...", 85)
            
            # Determine compression type
            if file_path.endswith('.tar.xz'):
                mode = 'r:xz'
            elif file_path.endswith('.tar.gz'):
                mode = 'r:gz'
            else:
                mode = 'r'
            
            with tarfile.open(file_path, mode) as tar:
                tar.extractall(path=TXADMIN_SERVER_DIR)
        
        if callback:
            callback("Extraction complete!", 95)
        
        # Restart FXServer if it was running before
        if was_running:
            if callback:
                callback("Restarting FXServer.exe...", 97)
            restart_success, restart_message = start_fxserver(
                server_path=server_info if isinstance(server_info, str) else None, 
                callback=callback
            )
            
            if not restart_success:
                if callback:
                    callback(f"Warning: Failed to restart FXServer.exe: {restart_message}", 97)
        
        return True, "TxAdmin update extracted successfully"
    
    except Exception as e:
        error_message = f"Failed to extract txAdmin update: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message, 80)
        return False, error_message

def restore_txadmin_backup(backup_file, callback=None):
    """
    Restores txAdmin from a backup file.
    Returns tuple (success, message)
    """
    if callback:
        callback(f"Restoring txAdmin from backup {backup_file}...")
    
    try:
        # Check if the backup file exists
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Stop FXServer.exe if it's running
        was_running, stop_success, server_info = stop_fxserver(callback)
        
        if was_running and not stop_success:
            if callback:
                callback("Warning: Could not stop all FXServer processes. Restore may fail or require a restart.")
        
        # Wait a little extra time to ensure processes are fully terminated
        time.sleep(3)
        
        # Check if server directory exists, clear it if it does
        if os.path.exists(TXADMIN_SERVER_DIR):
            if callback:
                callback("Removing existing server files...")
            
            # Try multiple attempts to remove the directory
            removal_success = False
            for attempt in range(3):
                try:
                    if callback and attempt > 0:
                        callback(f"Removal attempt {attempt+1}...")
                    
                    if take_ownership_and_remove(TXADMIN_SERVER_DIR, callback):
                        removal_success = True
                        break
                    
                    # Wait before retrying
                    time.sleep(2)
                except Exception as e:
                    if callback:
                        callback(f"Removal attempt {attempt+1} failed: {str(e)}")
                    time.sleep(2)
            
            if not removal_success:
                raise Exception("Failed to remove existing server directory after multiple attempts")
        
        # Create server directory
        os.makedirs(TXADMIN_SERVER_DIR, exist_ok=True)
        
        # Extract the backup zip
        if callback:
            callback("Extracting backup files...")
        
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(TXADMIN_SERVER_DIR))
        
        if callback:
            callback("Restore complete!")
        
        # Restart FXServer if it was running before
        if was_running:
            if callback:
                callback("Restarting FXServer.exe...")
            restart_success, restart_message = start_fxserver(
                server_path=server_info if isinstance(server_info, str) else None, 
                callback=callback
            )
            
            if not restart_success:
                if callback:
                    callback(f"Warning: Failed to restart FXServer.exe: {restart_message}")
        
        return True, "TxAdmin restored successfully from backup"
    
    except Exception as e:
        error_message = f"Failed to restore txAdmin: {str(e)}"
        logging.error(error_message)
        if callback:
            callback(error_message)
        return False, error_message

def delete_old_txadmin_backups(keep_count=TXADMIN_KEEP_COUNT):
    """
    Keeps the most recent 'keep_count' txAdmin backup files, deleting older ones.
    """
    # Get all zip files with their paths
    backup_files = []
    for fname in glob.glob(os.path.join(TXADMIN_BACKUP_DIR, 'txadmin-backup-*.zip')):
        try:
            backup_files.append((fname, os.path.getmtime(fname)))
        except Exception as e:
            logging.warning(f"Failed to access {fname}: {e}")
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    
    # Delete files beyond the keep_count
    deleted = 0
    for fpath, _ in backup_files[keep_count:]:
        try:
            os.remove(fpath)
            deleted += 1
            logging.info(f"Deleted old txAdmin backup: {fpath}")
        except Exception as e:
            logging.warning(f"Failed to delete {fpath}: {e}")
    
    return deleted

def get_txadmin_backups():
    """
    Returns a list of txAdmin backup files sorted by date (newest first)
    """
    backup_files = []
    if os.path.exists(TXADMIN_BACKUP_DIR):
        for fname in glob.glob(os.path.join(TXADMIN_BACKUP_DIR, 'txadmin-backup-*.zip')):
            try:
                basename = os.path.basename(fname)
                backup_files.append((fname, os.path.getmtime(fname), basename))
            except Exception as e:
                logging.warning(f"Failed to access {fname}: {e}")
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files
