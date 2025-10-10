# FIVEM & REDM Server Controller Utility

## Overview
A comprehensive utility designed to help server owners manage their FiveM and RedM servers with ease. This Python-based application provides automated backups, server control functions, database management, and automatic TxAdmin updates all in one place.

## Features

### 🔄 Server Control
- Start, stop, and restart your server with one click
- Real-time server status monitoring
- Command output display for easy troubleshooting

### 💾 Automated Backups
- Configurable scheduled backups for both database and server files
- Retention policy to manage storage space
- Detailed backup history and restore functionality

### 🛠️ TxAdmin Management
- One-click updates to the latest recommended TxAdmin version
- Automatic backup before updates
- Version rollback capability if needed
- Progress tracking for updates

### 📊 Database Tools
- MySQL database backups with configurable schedule
- Easy restore functionality from any saved backup
- Backup rotation to maintain storage efficiency

### 📝 Activity Logging
- Comprehensive logging of all operations
- Timestamps for all events
- Easy troubleshooting with detailed error messages

## Why Use This Tool?
- **Time-Saving**: Automate routine server maintenance tasks
- **Reliable**: Never worry about losing data with regular backups
- **User-Friendly**: Modern, intuitive interface requires no technical expertise
- **All-in-One**: Replace multiple tools with a single application

## Screenshots

[Screenshots will be added]

## Installation

### Requirements
- Windows server/PC running your FiveM/RedM server
- Python 3.8 or newer
- MySQL database (for database backup features)
- 7-Zip installed (for TxAdmin updates)

### Quick Setup
1. Download from GitHub
2. Install required Python packages: `pip install requests beautifulsoup4 psutil`
3. Configure your paths in `config.py`
4. Run `python app.py` to start the utility

Detailed instructions are included in the `instructions.md` file within the download.

## Download

[GitHub Repository](https://github.com/RosewoodRidge/FIVEM-REDM-Server-Controller)

## Suggestions & Support
Feel free to suggest features or report issues on GitHub. I'm actively maintaining this utility and appreciate all feedback!

## Resource Information

|                             |                                  |
|-----------------------------|----------------------------------|
| Code is accessible          | Yes                              |
| Subscription-based          | No                               |
| Lines (approximately)       | 2,000+                           |
| Requirements                | Python 3.8+, requests, beautifulsoup4, psutil, 7-Zip |
| Support                     | Yes                              |