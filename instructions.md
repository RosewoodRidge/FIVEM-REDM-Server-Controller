# FIVEM & REDM Server Controller Utility Guide

This comprehensive utility helps you manage FiveM and RedM servers with automated backups, server control, and TxAdmin updates.

## Installation

### Step 1: Install Python

1. Download and install Python 3.8 or newer from [python.org](https://www.python.org/downloads/windows/)
2. **IMPORTANT:** Check the box "Add Python to PATH" during installation

### Step 2: Install Dependencies

Run the following command in Command Prompt or PowerShell to install required packages:

```
pip install requests beautifulsoup4 psutil
```

### Step 3: Configure the Application

1. Open the `config.py` file with a text editor
2. Update the following settings:

#### Database Configuration
```python
DB_HOST = 'localhost'  # Your MySQL server hostname
DB_USER = 'your_db_user'  # MySQL username
DB_PASSWORD = 'your_password'  # MySQL password
DB_NAME = 'your_db_name'  # Database to backup
BACKUP_DIR = 'C:\\path\\to\\database\\backups'  # Where to store database backups
MYSQLDUMP_PATH = 'C:\\xampp\\mysql\\bin\\mysqldump.exe'  # Path to mysqldump.exe
MYSQL_PATH = 'C:\\xampp\\mysql\\bin\\mysql.exe'  # Path to mysql.exe
```

#### Server Backup Configuration
```python
SERVER_FOLDER = 'C:\\path\\to\\server\\resources'  # FiveM/RedM resources folder
SERVER_BACKUP_DIR = 'C:\\path\\to\\server\\backups'  # Where to store server backups
SERVER_BACKUP_KEEP_COUNT = 10  # Number of server backups to keep
```

#### TxAdmin Configuration
```python
TXADMIN_SERVER_DIR = 'C:\\path\\to\\server'  # Main server directory
TXADMIN_BACKUP_DIR = 'C:\\path\\to\\txadmin\\backups'  # Where to store TxAdmin backups
TXADMIN_DOWNLOAD_DIR = 'C:\\path\\to\\downloads'  # Where to download TxAdmin updates
SEVEN_ZIP_PATH = 'C:\\Program Files\\7-Zip\\7z.exe'  # Path to 7-Zip executable
```

#### Backup Schedule
```python
DB_BACKUP_HOURS = [3, 15]  # Database backups at 3 AM and 3 PM
SERVER_BACKUP_HOURS = [3]  # Server backups at 3 AM only
BACKUP_MINUTE = 0  # Minute of the hour to run backups
```

## Features & Usage

### Server Control

The "Server Control" tab allows you to:

- **View Server Status**: See if FXServer.exe is running
- **Start Server**: Launch FXServer.exe
- **Stop Server**: Terminate FXServer.exe
- **Restart Server**: Stop and restart FXServer.exe

Command output is displayed in real-time in the window.

### Server Backup

The "Server Backup" tab allows you to:

- **Run Manual Backup**: Create a full backup of your server resources folder
- **Restore Server Files**: Restore from a previous backup (select by index)
- **View Backup History**: See a list of available server backups

Automated server backups occur daily at the time specified in config.py.

### Database Backup

The "Database Backup" tab allows you to:

- **Run Manual Database Backup**: Create a full MySQL database backup
- **Restore Database**: Restore from a previous backup (select by index)
- **View Backup History**: See a list of available database backups

Automated database backups occur at the times specified in config.py.

### TxAdmin Update

The "TxAdmin Update" tab allows you to:

- **Update TxAdmin**: Download and install the latest recommended version
- **Restore Previous Version**: Rollback to a previous TxAdmin version
- **Track Update Progress**: Monitor the download and installation progress

The utility automatically creates a backup before updating TxAdmin.

### Activity Log

The "Activity Log" tab shows a chronological record of all operations performed by the utility, including:

- Backup/restore operations
- Server start/stop events
- TxAdmin updates
- Error messages

## Running as a Service

To ensure the utility runs automatically when the server starts:

### Option 1: Windows Task Scheduler

1. Open Task Scheduler
2. Create a new task with these settings:
   - Run whether user is logged on or not
   - Trigger: At startup
   - Action: Start program
   - Program/script: `C:\path\to\pythonw.exe`
   - Arguments: `"C:\path\to\app.py"`
   - Start in: `"C:\path\to\application\directory"`

### Option 2: Create a Windows Service

Use NSSM (Non-Sucking Service Manager) to create a Windows service:

1. Download NSSM from [nssm.cc](http://nssm.cc/download)
2. Run: `nssm.exe install FiveM-RedM-Controller`
3. Path: `C:\path\to\pythonw.exe`
4. Arguments: `"C:\path\to\app.py"`
5. Directory: `"C:\path\to\application\directory"`

## Troubleshooting

### MySQL Connection Issues

If database backups fail:
- Verify your MySQL credentials in config.py
- Check that mysqldump.exe exists at the specified path
- Ensure the MySQL server is running

### Server Start/Stop Issues

If server control fails:
- Verify the FXServer.exe path in config.py
- Check Windows permissions for the executing user
- Look for error messages in the Activity Log tab

### TxAdmin Update Issues

If TxAdmin updates fail:
- Verify 7-Zip is installed and the path is correct in config.py
- Ensure the download directory is writable
- Check your internet connection
- Stop the FXServer process manually before updating if issues persist

## Support

For additional support or to report issues, please contact the developer.