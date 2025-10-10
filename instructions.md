# FIVEM & REDM Server Controller Utility Guide

This comprehensive utility helps you manage FiveM and RedM servers with automated backups, server control, and TxAdmin updates.

## Installation

### Step 1: Install Python

1. Download and install Python 3.8 or newer from [python.org](https://www.python.org/downloads/windows/)
2. **IMPORTANT:** Check the box "Add Python to PATH" during installation

### Step 2: Install Dependencies

Run the following command in Command Prompt or PowerShell to install required packages:


pip install requests beautifulsoup4 psutil


### Step 3: Configure the Application

1. Open the `config.py` file with a text editor
2. Update the following settings:

#### Database Configuration

DB_HOST = 'localhost'  # Your MySQL server hostname
DB_USER = 'your_db_user'  # MySQL username
DB_PASSWORD = 'your_password'  # MySQL password
DB_NAME = 'your_db_name'  # Database to backup
BACKUP_DIR = 'C:\\path\\to\\database\\backups'  # Where to store database backups
MYSQLDUMP_PATH = 'C:\\xampp\\mysql\\bin\\mysqldump.exe'  # Path to mysqldump.exe
MYSQL_PATH = 'C:\\xampp\\mysql\\bin\\mysql.exe'  # Path to mysql.exe


#### Server Backup Configuration

SERVER_FOLDER = 'C:\\path\\to\\server\\resources'  # FiveM/RedM resources folder
SERVER_BACKUP_DIR = 'C:\\path\\to\\server\\backups'  # Where to store server backups
SERVER_BACKUP_KEEP_COUNT = 10  # Number of server backups to keep


#### TxAdmin Configuration

TXADMIN_SERVER_DIR = 'C:\\path\\to\\server'  # Main server directory
TXADMIN_BACKUP_DIR = 'C:\\path\\to\\txadmin\\backups'  # Where to store TxAdmin backups
TXADMIN_DOWNLOAD_DIR = 'C:\\path\\to\\downloads'  # Where to download TxAdmin updates
SEVEN_ZIP_PATH = 'C:\\Program Files\\7-Zip\\7z.exe'  # Path to 7-Zip executable


#### Backup Schedule

DB_BACKUP_HOURS = [3, 15]  # Database backups at 3 AM and 3 PM
SERVER_BACKUP_HOURS = [3]  # Server backups at 3 AM only
BACKUP_MINUTE = 0  # Minute of the hour to run backups

## Features & Usage

#### Start the App

To run the applications without a console window, use the provided launcher files:
- **For the main server controller:** Double-click `start.bat`
- **For the remote client:** Double-click `start_remote.bat`

These will launch the applications in the background. If you need to see console output for debugging, you can still run the `app.py` or `remote_app.py` files directly with `python.exe`.

### Server Control

The "Server Control" tab allows you to:

- **View Server Status**: See if FXServer.exe is running
- **Start Server**: Launch FXServer.exe
- **Stop Server**: Terminate FXServer.exe
- **Restart Server**: Stop and restart FXServer.exe

Command output is displayed in real-time in the window.

### Remote Control

The utility includes a remote client that allows you to manage your server from another computer on the network.

#### Enabling Remote Access on the Server

1.  In the main application, go to the **Remote Control** tab.
2.  Check the **Enable Remote Control** box.
3.  The server will start, and the **Server IP**, **Port**, and **Authentication Key** will be displayed.
4.  The application will attempt to create a Windows Firewall rule automatically. If it fails (e.g., due to permissions), you may need to manually allow incoming TCP connections on the specified port.

#### Connecting with the Remote Client

1.  On a different computer, run `start_remote.bat`.
2.  Enter the **Server IP**, **Port**, and **Authentication Key** provided by the main application.
3.  Click **Connect**. Your connection details will be saved for the next time you open the remote client.
4.  Once connected, you will have access to the server management tabs.

#### Remote Features

The remote client provides access to most of the main application's features, including:
-   **Server Control**: Start, stop, and restart the server.
-   **Backups**: Run and restore server, database, and TxAdmin backups.
-   **TxAdmin Updates**: Initiate a TxAdmin update.
-   **Activity Log**: View logs from the server and send messages.

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