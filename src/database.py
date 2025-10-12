import os
import subprocess
import logging
from datetime import datetime
# Import from config which will have values applied from JSON
from config import (
    BACKUP_DIR, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME,
    MYSQLDUMP_PATH, MYSQL_PATH
)

def create_backup():
    """
    Connects to the database and performs a mysqldump.
    The backup file is saved in the specified directory with a timestamp.
    Returns tuple (success, message or filename)
    """
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            logging.info(f"Created backup directory: {BACKUP_DIR}")
        except OSError as e:
            logging.error(f"Failed to create backup directory {BACKUP_DIR}: {e}")
            return False, str(e)

    # Create a unique filename with a timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = os.path.join(BACKUP_DIR, f"backup-{timestamp}.sql")

    # Construct mysqldump command
    command = [
        MYSQLDUMP_PATH,
        f'--host={DB_HOST}',
        f'--user={DB_USER}',
    ]
    if DB_PASSWORD:
        command.append(f'--password={DB_PASSWORD}')
    
    command.append(DB_NAME)

    logging.info(f"Starting backup for database '{DB_NAME}'...")

    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            process = subprocess.run(
                command,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        logging.info(f"Successfully created backup: {backup_file}")
        return True, backup_file

    except FileNotFoundError:
        error_message = f"Error: The 'mysqldump' executable was not found at the specified path: '{MYSQLDUMP_PATH}'. Please check the path."
        logging.error(error_message)
        return False, error_message
    except subprocess.CalledProcessError as e:
        error_message = f"Backup failed with error: {e.stderr}"
        logging.error(error_message)
        if os.path.exists(backup_file):
            os.remove(backup_file)
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logging.error(error_message)
        return False, error_message

def restore_backup(backup_file):
    """
    Restores the database from the specified backup file.
    Returns tuple (success, message)
    """
    if not os.path.exists(backup_file):
        return False, f"Backup file not found: {backup_file}"
    
    # Construct mysql command to restore
    command = [
        MYSQL_PATH,
        f'--host={DB_HOST}',
        f'--user={DB_USER}',
    ]
    if DB_PASSWORD:
        command.append(f'--password={DB_PASSWORD}')
    
    command.append(DB_NAME)

    logging.info(f"Starting restore from backup: {backup_file}")

    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            process = subprocess.run(
                command,
                stdin=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        success_message = f"Successfully restored from backup: {backup_file}"
        logging.info(success_message)
        return True, success_message

    except FileNotFoundError:
        error_message = f"Error: The 'mysql' executable was not found at the specified path: '{MYSQL_PATH}'. Please check the path."
        logging.error(error_message)
        return False, error_message
    except subprocess.CalledProcessError as e:
        error_message = f"Restore failed with error: {e.stderr}"
        logging.error(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logging.error(error_message)
        return False, error_message

def delete_old_backups(backup_dir=BACKUP_DIR, keep_count=100):
    """
    Keeps the most recent 'keep_count' .sql backup files in the backup directory,
    deleting older ones.
    """
    # Get all .sql files with their paths
    backup_files = []
    for fname in os.listdir(backup_dir):
        if fname.endswith('.sql'):
            fpath = os.path.join(backup_dir, fname)
            try:
                backup_files.append((fpath, os.path.getmtime(fpath)))
            except Exception as e:
                logging.warning(f"Failed to access {fpath}: {e}")
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    
    # Delete files beyond the keep_count
    deleted = 0
    for fpath, _ in backup_files[keep_count:]:
        try:
            os.remove(fpath)
            deleted += 1
            logging.info(f"Deleted old backup: {fpath}")
        except Exception as e:
            logging.warning(f"Failed to delete {fpath}: {e}")
    
    return deleted

def get_backup_files():
    """
    Returns a list of backup files sorted by date (newest first)
    """
    backup_files = []
    if os.path.exists(BACKUP_DIR):
        for fname in os.listdir(BACKUP_DIR):
            if fname.endswith('.sql'):
                fpath = os.path.join(BACKUP_DIR, fname)
                try:
                    backup_files.append((fpath, os.path.getmtime(fpath), fname))
                except Exception as e:
                    logging.warning(f"Failed to access {fpath}: {e}")
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files
