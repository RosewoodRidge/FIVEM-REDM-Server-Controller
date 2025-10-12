import os
import sys
import json
import logging
import platform

def get_config_dir():
    """Get the directory where config files should be stored"""
    if getattr(sys, 'frozen', False):
        # Running as executable - store in data folder next to exe
        exe_dir = os.path.dirname(sys.executable)
        config_dir = os.path.join(exe_dir, 'data')
    else:
        # Running in development mode - store in src/data
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_file():
    """Get the path to the configuration JSON file"""
    return os.path.join(get_config_dir(), 'config.json')

def get_platform():
    """Get the current platform (windows, linux, darwin)"""
    return platform.system().lower()

def is_windows():
    """Check if running on Windows"""
    return get_platform() == 'windows'

def is_linux():
    """Check if running on Linux"""
    return get_platform() == 'linux'

def get_default_mysqldump_path():
    """Get platform-specific default mysqldump path"""
    if is_windows():
        return r'C:\xampp\mysql\bin\mysqldump.exe'
    else:
        return 'mysqldump'  # Should be in PATH on Linux

def get_default_mysql_path():
    """Get platform-specific default mysql path"""
    if is_windows():
        return r'C:\xampp\mysql\bin\mysql.exe'
    else:
        return 'mysql'  # Should be in PATH on Linux

def get_default_7zip_path():
    """Get platform-specific default 7-zip path"""
    if is_windows():
        return r'C:\Program Files\7-Zip\7z.exe'
    else:
        return '7z'  # Should be in PATH on Linux

def load_config():
    """Load configuration from JSON file, return defaults if file doesn't exist"""
    config_file = get_config_file()
    
    # Default configuration with platform-specific paths
    default_config = {
        'DB_HOST': 'localhost',
        'DB_USER': 'root',
        'DB_PASSWORD': '',
        'DB_NAME': 'my_database',
        'BACKUP_DIR': os.path.join(os.path.expanduser('~'), 'backups', 'database'),
        'MYSQLDUMP_PATH': get_default_mysqldump_path(),
        'MYSQL_PATH': get_default_mysql_path(),
        'SERVER_FOLDER': os.path.join(os.path.expanduser('~'), 'server', 'resources'),
        'SERVER_BACKUP_DIR': os.path.join(os.path.expanduser('~'), 'backups', 'server'),
        'SERVER_BACKUP_KEEP_COUNT': 10,
        'TXADMIN_SERVER_DIR': os.path.join(os.path.expanduser('~'), 'server'),
        'TXADMIN_BACKUP_DIR': os.path.join(os.path.expanduser('~'), 'backups', 'txadmin'),
        'TXADMIN_DOWNLOAD_DIR': os.path.join(os.path.expanduser('~'), 'downloads'),
        'SEVEN_ZIP_PATH': get_default_7zip_path(),
        'TXADMIN_KEEP_COUNT': 5,
        'DB_BACKUP_HOURS': [3, 15],
        'SERVER_BACKUP_HOURS': [3],
        'BACKUP_MINUTE': 0,
        'AUTO_UPDATE_TXADMIN': True,
        'SERVER_BACKUP_THROTTLE': 0.1,
        'DISCORD_WEBHOOK': {
            'enabled': False,
            'webhook_url': '',
            'notifications': {
                'server_start': True,
                'server_stop': True,
                'server_restart': True,
                'database_backup': True,
                'server_backup': True,
                'txadmin_update': True,
                'backup_failed': True,
                'server_error': True
            },
            'messages': {},
            'colors': {}
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults (user config takes precedence)
                default_config.update(user_config)
                logging.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logging.error(f"Failed to load config file: {e}")
    else:
        logging.info(f"Config file not found, using defaults. Will create: {config_file}")
    
    return default_config

def save_config(config_dict):
    """Save configuration to JSON file"""
    config_file = get_config_file()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=4)
        logging.info(f"Configuration saved to {config_file}")
        return True, config_file
    except Exception as e:
        logging.error(f"Failed to save config: {e}")
        return False, str(e)

def apply_config_to_module(config_dict):
    """Apply configuration dictionary to the config module"""
    import config
    
    for key, value in config_dict.items():
        if hasattr(config, key):
            setattr(config, key, value)
            logging.debug(f"Set config.{key} = {value}")
    
    logging.info("Applied configuration to config module")

def get_data_dir():
    """Get the directory where all application data should be stored"""
    if getattr(sys, 'frozen', False):
        # Running as executable - store in data folder next to exe
        exe_dir = os.path.dirname(sys.executable)
        data_dir = os.path.join(exe_dir, 'data')
    else:
        # Running in development mode - store in src/data
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_logs_dir():
    """Get the directory where logs should be stored"""
    if getattr(sys, 'frozen', False):
        # Running as executable - store in logs folder next to exe
        exe_dir = os.path.dirname(sys.executable)
        logs_dir = os.path.join(exe_dir, 'logs')
    else:
        # Running in development mode - store in parent logs folder
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir
