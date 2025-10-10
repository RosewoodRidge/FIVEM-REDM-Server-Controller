import os
import re
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Configuration ---
# Hard-coded configuration values
LOG_FILE = 'backup.log'

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'your_database_username'        # Replace with your database username
DB_PASSWORD = 'your_database_password'    # Replace with your database password
DB_NAME = 'your_database_name'            # Replace with your database name

# Backup configuration
BACKUP_DIR = 'C:\\path\\to\\database_backups'  # Replace with your database backup directory
MYSQLDUMP_PATH = 'C:\\xampp\\mysql\\bin\\mysqldump.exe'  # Default MySQL dump utility path
MYSQL_PATH = 'C:\\xampp\\mysql\\bin\\mysql.exe'          # Default MySQL client path

# Server backup configuration
SERVER_FOLDER = 'C:\\path\\to\\server\\resources'        # Replace with your server resources folder
SERVER_BACKUP_DIR = 'C:\\path\\to\\server_backups'       # Replace with your server backup directory
SERVER_BACKUP_KEEP_COUNT = 10
SERVER_BACKUP_THROTTLE = 0.1  # seconds delay between files (throttling)

# TxAdmin update configuration
TXADMIN_SERVER_DIR = 'C:\\path\\to\\fivem_server'        # Replace with your main server directory
TXADMIN_BACKUP_DIR = 'C:\\path\\to\\txadmin_backups'     # Replace with your txAdmin backup directory
TXADMIN_DOWNLOAD_DIR = 'C:\\path\\to\\downloads'         # Replace with your download directory
TXADMIN_URL = 'https://runtime.fivem.net/artifacts/fivem/build_server_windows/master'
TXADMIN_KEEP_COUNT = 5
SEVEN_ZIP_PATH = 'C:\\Program Files\\7-Zip\\7z.exe'  # Path to 7-Zip executable
AUTO_UPDATE_TXADMIN = True  # Enable/disable automatic TxAdmin updates

# Backup schedule
DB_BACKUP_HOURS = [3, 15]  # 3 AM and 3 PM
SERVER_BACKUP_HOURS = [3]  # 3 AM only
BACKUP_MINUTE = 0

# --- UI Configuration ---
# Web 3.0 styling colors and fonts with improved contrast
COLORS = {
    'bg': '#0f172a',           # Dark blue background
    'panel': '#1e293b',        # Slightly lighter blue for panels
    'accent': '#3b82f6',       # Bright blue accent
    'accent_hover': '#2563eb', # Darker blue for hover
    'text': '#f8fafc',         # Light text
    'text_secondary': '#94a3b8', # Secondary text (lighter for dark backgrounds)
    'button_text': "#3b3b3b",  # White text for buttons
    'tab_bg': '#0f172a',       # Dark background for tabs
    'tab_fg': "#3b3b3b",       # Light text for tabs
    'tab_selected_bg': '#3b82f6', # Accent color for selected tab
    'tab_selected_fg': "#660000"  # White text for selected tab
}
