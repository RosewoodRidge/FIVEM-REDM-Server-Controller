import os
import shutil
import time
import logging
import zipfile
import glob
from datetime import datetime
from config import SERVER_FOLDER, SERVER_BACKUP_DIR, SERVER_BACKUP_KEEP_COUNT, SERVER_BACKUP_THROTTLE

# Create server backup directory if it doesn't exist
os.makedirs(SERVER_BACKUP_DIR, exist_ok=True)

def backup_server_folder(callback=None):
    """
    Creates a zip backup of the server folder with throttling to reduce resource usage.
    Returns tuple (success, message or filename)
    """
    # Ensure backup directory exists
    os.makedirs(SERVER_BACKUP_DIR, exist_ok=True)
    
    # Create a unique filename with a timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = os.path.join(SERVER_BACKUP_DIR, f"server-backup-{timestamp}.zip")
    
    if callback:
        callback(f"Starting server backup to {backup_file}...")
    logging.info(f"Starting server backup to {backup_file}...")
    
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the directory
            file_count = 0
            for root, dirs, files in os.walk(SERVER_FOLDER):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate path in zip file
                    rel_path = os.path.relpath(file_path, os.path.dirname(SERVER_FOLDER))
                    
                    if callback and file_count % 10 == 0:  # Update status every 10 files
                        callback(f"Backing up: {rel_path}")
                    
                    # Add file to zip
                    zipf.write(file_path, rel_path)
                    
                    # Throttle to reduce resource usage
                    time.sleep(SERVER_BACKUP_THROTTLE)
                    file_count += 1
        
        success_message = f"Successfully created server backup: {backup_file}"
        logging.info(success_message)
        return True, backup_file
        
    except Exception as e:
        error_message = f"Server backup failed: {str(e)}"
        logging.error(error_message)
        if os.path.exists(backup_file):
            os.remove(backup_file)
        return False, error_message

def restore_server_backup(backup_file, callback=None):
    """
    Restores the server folder from a backup.
    Returns tuple (success, message)
    """
    if not os.path.exists(backup_file):
        return False, f"Backup file not found: {backup_file}"
    
    if callback:
        callback(f"Starting server restore from {backup_file}...")
    logging.info(f"Starting server restore from {backup_file}...")
    
    # Create a temporary directory for extraction
    temp_dir = os.path.join(SERVER_BACKUP_DIR, "temp_extract")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Extract the zip file
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            file_count = 0
            for file in zipf.namelist():
                if callback and file_count % 10 == 0:  # Update status every 10 files
                    callback(f"Extracting: {file}")
                zipf.extract(file, temp_dir)
                time.sleep(SERVER_BACKUP_THROTTLE)  # Throttle
                file_count += 1
        
        # Get the extracted txData directory
        extracted_dir = os.path.join(temp_dir, os.path.basename(SERVER_FOLDER))
        
        if callback:
            callback("Removing existing server files...")
        
        # Backup current server directory before removing
        if os.path.exists(SERVER_FOLDER):
            # Rename existing directory temporarily
            temp_old_dir = f"{SERVER_FOLDER}_old_{int(time.time())}"
            os.rename(SERVER_FOLDER, temp_old_dir)
        
        if callback:
            callback("Copying restored files to server directory...")
        
        # Copy restored files to server directory
        shutil.copytree(extracted_dir, SERVER_FOLDER)
        
        # Remove temporary directories
        shutil.rmtree(temp_dir)
        if os.path.exists(temp_old_dir):
            shutil.rmtree(temp_old_dir)
        
        success_message = f"Successfully restored server from backup: {backup_file}"
        logging.info(success_message)
        return True, success_message
        
    except Exception as e:
        error_message = f"Server restore failed: {str(e)}"
        logging.error(error_message)
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False, error_message

def delete_old_server_backups(keep_count=SERVER_BACKUP_KEEP_COUNT):
    """
    Keeps the most recent 'keep_count' server backup files, deleting older ones.
    """
    # Get all .zip files with their paths
    backup_files = []
    for fname in glob.glob(os.path.join(SERVER_BACKUP_DIR, 'server-backup-*.zip')):
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
            logging.info(f"Deleted old server backup: {fpath}")
        except Exception as e:
            logging.warning(f"Failed to delete {fpath}: {e}")
    
    return deleted

def get_server_backup_files():
    """
    Returns a list of server backup files sorted by date (newest first)
    """
    backup_files = []
    if os.path.exists(SERVER_BACKUP_DIR):
        for fname in glob.glob(os.path.join(SERVER_BACKUP_DIR, 'server-backup-*.zip')):
            try:
                basename = os.path.basename(fname)
                backup_files.append((fname, os.path.getmtime(fname), basename))
            except Exception as e:
                logging.warning(f"Failed to access {fname}: {e}")
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files
