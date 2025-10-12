# FIVEM & REDM Server Controller Utility Guide

This comprehensive utility helps you manage FiveM and RedM servers with automated backups, server control, and TxAdmin updates.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Features & Usage](#features--usage)
- [Remote Control](#remote-control)
- [Advanced Options](#advanced-options)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Quick Install (Recommended for Most Users)

1. **Download** the complete package to your computer
2. **Run `install.bat`** by double-clicking it
3. The installer will:
   - Check your Python installation
   - Install all required dependencies automatically
   - Build three executable programs
   - Create Start Menu shortcuts
   - Open the installation folder when complete
4. **Find your applications** in the Start Menu under **"FIVEM & REDM Controller"**

**Note:** The installation process takes 2-5 minutes depending on your computer speed. The installer window will automatically close when complete, and Windows Explorer will open showing your installed programs.

### What Gets Installed

Three applications will be created in the `dist` folder:
Two applications will be created in the `dist` folder:

1. **FIVEM & REDM Server Controller.exe** - Main application for server management
2. **FIVEM & REDM Remote Client.exe** - Remote control client for managing servers from another computer
3. **FIVEM & REDM Configuration Editor.exe** - Easy-to-use configuration editor

---

## Configuration

### First-Time Setup

1. **Open the Configuration Editor** from Start Menu → FIVEM & REDM Controller → Configuration Editor
2. Configure the following settings:
1. **Launch the main application** (`FIVEM & REDM Server Controller.exe`).
2. **Navigate to the Configuration tab** (look for the ⚙️ icon).
3. Configure the following settings directly within the application:

#### Database Settings
- **Database Host**: Your MySQL server address (usually `localhost`)
- **Database Username**: MySQL username (default: `root`)
- **Database Password**: Your MySQL password
- **Database Name**: Name of the database to backup
- **MySQLDump Path**: Full path to `mysqldump.exe`
  - Default XAMPP location: `C:\xampp\mysql\bin\mysqldump.exe`
  - Use the Browse button to find it
- **MySQL Path**: Full path to `mysql.exe`
  - Default XAMPP location: `C:\xampp\mysql\bin\mysql.exe`

#### Backup Locations
- **Database Backup Directory**: Where database backups are saved
  - Example: `C:\backups\database`
- **Server Backup Directory**: Where server file backups are saved
  - Example: `C:\backups\server`
- **Server Resources Folder**: Your FiveM/RedM resources folder
  - Example: `C:\FXServer\server-data\resources`

#### TxAdmin Settings
- **TxAdmin Server Directory**: Main server folder containing `FXServer.exe`
  - Example: `C:\FXServer\server`
- **TxAdmin Backup Directory**: Where TxAdmin backups are saved
  - Example: `C:\backups\txadmin`
- **TxAdmin Download Directory**: Temporary download location
  - Example: `C:\downloads` or `%USERPROFILE%\Downloads`
- **7-Zip Path**: Full path to 7-Zip executable
  - Default: `C:\Program Files\7-Zip\7z.exe`
  - Required for TxAdmin updates

#### Backup Schedule
- **Database Backup Hours**: When to run database backups (0-23)
  - Example: `3, 15` = 3 AM and 3 PM daily
- **Server Backup Hours**: When to run server file backups (0-23)
  - Example: `3` = 3 AM daily

3. **Click "Save Configuration"**. The application will prompt you to restart.
4. **Click OK to restart the application** and apply the new settings.

**Important:** Your configuration is stored in `%APPDATA%\FIVEM-REDM-Controller\config.py` when using the compiled executables. This location persists even if you update the application.
**Important:** Your configuration is stored in a `config.json` file within a `data` folder next to the executable. This location persists even if you update the application.

---

## Features & Usage

### Starting the Application

Launch **FIVEM & REDM Server Controller** from:
- Start Menu → FIVEM & REDM Controller → Server Controller
- Or run `FIVEM & REDM Server Controller.exe` from the installation folder

### Server Control Tab

**View and control your FXServer process:**
- **Current Status**: Shows if server is RUNNING or STOPPED with Process ID
- **Start Server**: Launches `FXServer.exe`
- **Stop Server**: Safely terminates the server process
- **Restart Server**: Stops then restarts the server
- **Command Output**: Shows real-time server control messages

Status updates automatically every 3 seconds.

### Server Backup Tab

**Manage your server resource backups:**
- **Run Manual Server Backup Now**: Creates immediate backup of your resources folder
- **Restore Server Files**: Restore from any previous backup
  - Enter backup number (1 = most recent)
  - Confirms before overwriting current files
- **Available Server Backups**: Lists all backups with timestamps

**Automatic Backups:** Runs daily at configured hours. Keeps the 10 most recent backups by default.

### Database Backup Tab

**Manage your MySQL database backups:**
- **Next Scheduled Backup**: Shows countdown to next automatic backup
- **Run Manual Database Backup**: Creates immediate backup
- **Restore Database**: Restore from any previous backup
  - Enter backup number (1 = most recent)
  - Confirms before overwriting current database
- **Available Database Backups**: Lists all backups with timestamps

**Automatic Backups:** Runs at configured hours. Keeps 100 most recent backups by default.

### TxAdmin Update Tab

**Keep your server software up to date:**
- **Update TxAdmin**: Downloads and installs latest recommended version
  - Automatically creates backup before updating
  - Stops server during update
  - Restarts server after completion
- **Update Progress**: Real-time progress bar and status messages
- **Restore Previous Version**: Rollback to any previous backup
  - Enter backup number (1 = most recent)
  - Useful if an update causes issues

**Automatic Updates:** If enabled in config, checks for updates after database backups and installs automatically.

### Activity Log Tab

**Monitor all operations:**
- Shows timestamped log of all actions
- Includes backup operations, server control, updates, and errors
- Useful for troubleshooting and auditing

### Application Updates

The application automatically checks for updates:
- On startup (once per day)
- Manual check via "Check for Updates" button in status bar
- Shows version comparison and changelog
- Downloads and installs with one click
- Preserves your configuration settings

---

## Remote Control

Control your server from another computer on your network.

### Server Setup (Main Computer)

1. **Open Remote Control tab** in the main application
2. **Enable Remote Control** checkbox
3. Note the displayed information:
   - **Server IP**: Your computer's network address
   - **Port**: Network port (default: 40100)
   - **Authentication Key**: Required to connect (format: xxxx-xxxx-xxxx-xxxx-xxxx)

**Security Notes:**
- Authentication key is automatically generated
- Copy key to clipboard using the 📋 Copy button
- Click 👁 to show/hide the key
- Generate new key anytime with "Generate New Key" button
- Windows Firewall rule is added automatically (may require admin rights)

### Client Setup (Remote Computer)

1. **Install the application** on the remote computer (follow installation steps)
2. **Launch FIVEM & REDM Remote Client** from Start Menu
3. **Enter connection details:**
   - Server IP: From server's Remote Control tab
   - Port: Usually 40100
   - Authentication Key: Paste from server
4. **Click Connect**

**Connection saved:** Details are remembered for next time.

### Remote Features

Once connected, you can:
- **Server Control**: Start, stop, restart the server
- **View Status**: Real-time server status with auto-refresh
- **Database Backups**: Create and restore database backups
- **Server Backups**: Create and restore server file backups
- **TxAdmin Updates**: Update and restore TxAdmin
- **Activity Log**: View server logs and send messages
- **Auto-Refresh**: Lists update automatically every 5 seconds

### Firewall Configuration

If remote connections fail:
1. Ensure Windows Firewall allows the port
2. Manually add rule if needed:
   - Open Windows Defender Firewall
   - Advanced settings → Inbound Rules → New Rule
   - Port: TCP, specific port (40100)
   - Allow the connection
   - Name: FIVEM-REDM-Controller-Remote

---

## Advanced Options

### Manual Build Process

For developers or users who want to build from source:

**Prerequisites:**
- Python 3.8 or newer
- Git (optional, for version control)

**Steps:**
1. Open Command Prompt in the application directory
2. Install dependencies:
   ```
   pip install pyinstaller requests beautifulsoup4 psutil pywin32 winshell
   ```
3. Build executables:
   ```
   cd src
   pyinstaller app.spec --clean --noconfirm
   pyinstaller remote_app.spec --clean --noconfirm
   pyinstaller config_editor.spec --clean --noconfirm
   ```
4. Find executables in `src\dist` folder

### Direct Python Execution

Run without building executables:

**Prerequisites:**
- Python 3.8 or newer
- All dependencies installed (see Manual Build)

**Launch Main Application:**
```bash
python -m fivem_redm_controller
```

**Launch Remote Client:**
```bash
python -m fivem_redm_remote_client
```

**Launch Configuration Editor:**
```bash
python -m fivem_redm_config_editor
```

**Note:** Running directly requires a command prompt. Change to the application directory first.

---

## Troubleshooting

### Installation Issues

If the installer fails:
- Make sure Python 3.8+ is installed
- Run Command Prompt as Administrator
- Manually install dependencies: `pip install pyinstaller requests beautifulsoup4 psutil pywin32 winshell`
- Try running `build_exe.bat` manually

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

## Uninstallation

To uninstall:
1. Delete the Start Menu shortcuts from `%APPDATA%\Microsoft\Windows\Start Menu\Programs\FIVEM & REDM Controller`
2. Delete the installation folder (default: `C:\Program Files\FIVEM-REDM-Controller`)
3. Remove any created backups if no longer needed

## Support

For additional support or to report issues, please contact the developer.