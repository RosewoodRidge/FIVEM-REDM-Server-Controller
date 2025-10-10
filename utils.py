import os
import sys
import logging
from datetime import datetime, timedelta
from config import LOG_FILE, DB_BACKUP_HOURS, SERVER_BACKUP_HOURS, BACKUP_MINUTE

# --- Setup Logging ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
        # Database backups at configured hours
        for hour in DB_BACKUP_HOURS:
            backup_time = now.replace(
                day=now.day + day_offset,
                hour=hour, 
                minute=BACKUP_MINUTE, 
                second=0, 
                microsecond=0
            )
            if backup_time > now:
                potential_times.append((backup_time, "Database"))
        
        # Server backups at configured hours
        for hour in SERVER_BACKUP_HOURS:
            backup_time = now.replace(
                day=now.day + day_offset,
                hour=hour, 
                minute=BACKUP_MINUTE, 
                second=0, 
                microsecond=0
            )
            if backup_time > now:
                potential_times.append((backup_time, "Server"))
    
    # Return the closest backup time
    if potential_times:
        potential_times.sort(key=lambda x: x[0])  # Sort by time
        return potential_times[0]  # Return time and type
    else:
        # Fallback to tomorrow
        tomorrow = now + timedelta(days=1)
        return (tomorrow.replace(hour=DB_BACKUP_HOURS[0], minute=BACKUP_MINUTE, second=0, microsecond=0), "Database")
