import os
import sys
import logging
import subprocess
from datetime import datetime, timedelta
from config import LOG_FILE, DB_BACKUP_HOURS, SERVER_BACKUP_HOURS, BACKUP_MINUTE
from config_manager import get_logs_dir, is_windows

# Ensure logs directory exists
logs_dir = get_logs_dir()

# --- Setup Logging ---
logging.basicConfig(
    filename=os.path.join(logs_dir, 'app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_firewall_rule(rule_name):
    """Check if a firewall rule exists (Windows only)."""
    if not is_windows():
        logging.info("Firewall rules are not applicable on non-Windows systems")
        return True  # Return True to skip firewall checks on Linux
    
    try:
        # Use subprocess.run to check for the rule
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={rule_name}'],
            capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "No rules match the specified criteria." not in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If netsh fails or rule doesn't exist, it will often return a non-zero exit code
        return False

def add_firewall_rule(rule_name, port):
    """Add a firewall rule to allow TCP traffic on a specific port (Windows only)."""
    if not is_windows():
        logging.info(f"Firewall rule management not needed on {sys.platform}")
        success_msg = f"Firewall rules not applicable on non-Windows systems"
        logging.info(success_msg)
        return True, success_msg

    if check_firewall_rule(rule_name):
        success_msg = f"Firewall rule '{rule_name}' already exists."
        logging.info(success_msg)
        return True, success_msg

    try:
        # Command to add the firewall rule
        command = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=allow',
            'protocol=TCP',
            f'localport={port}'
        ]
        # Run with admin rights if possible, but will fail gracefully if not
        subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        success_msg = f"Successfully added firewall rule '{rule_name}' for port {port}."
        logging.info(success_msg)
        return True, success_msg
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to add firewall rule. Try running as Administrator. Error: {e.stderr}"
        logging.error(error_message)
        return False, error_message
    except FileNotFoundError:
        error_message = "netsh command not found. Cannot manage firewall."
        logging.error(error_message)
        return False, error_message

def restart_application():
    """Restart the current application"""
    python = sys.executable
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app.py'))
    os.execl(python, python, script)

def calculate_next_backup_time():
    """
    Calculate the next scheduled backup time based on current time and schedule
    """
    now = datetime.now()
    
    # Check all possible backup times for today and tomorrow
    potential_times = []
    for day_offset in [0, 1]:  # Today and tomorrow
        check_date = (now + timedelta(days=day_offset)).date()
        
        # Database backups at configured hours
        for hour in DB_BACKUP_HOURS:
            backup_time = datetime.combine(check_date, datetime.min.time()).replace(hour=hour, minute=BACKUP_MINUTE)
            if backup_time > now:
                potential_times.append((backup_time, "Database"))
        
        # Server backups at configured hours
        for hour in SERVER_BACKUP_HOURS:
            backup_time = datetime.combine(check_date, datetime.min.time()).replace(hour=hour, minute=BACKUP_MINUTE)
            if backup_time > now:
                potential_times.append((backup_time, "Server"))
    
    # Return the closest backup time
    if potential_times:
        potential_times.sort(key=lambda x: x[0])  # Sort by time
        return potential_times[0]  # Return time and type
    else:
        # Fallback to tomorrow's first backup
        tomorrow = now + timedelta(days=1)
        first_hour = min(DB_BACKUP_HOURS + SERVER_BACKUP_HOURS)
        backup_time = datetime.combine(tomorrow.date(), datetime.min.time()).replace(hour=first_hour, minute=BACKUP_MINUTE)
        return backup_time, "Database/Server"
