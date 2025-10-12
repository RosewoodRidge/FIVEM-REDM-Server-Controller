import os
import re
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Configuration ---
# Hard-coded configuration values
LOG_FILE = 'logs\\backup.log'

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'rr_web_root'
DB_PASSWORD = 'hUenD3uVG)3j*7we'
DB_NAME = 'vorpcore_d7f8d9'

# Backup configuration
BACKUP_DIR = r'C:\\Users\\Administrator\\Documents\\server_backups\\database'
MYSQLDUMP_PATH = r'C:\\xampp\\mysql\\bin\\mysqldump.exe'
MYSQL_PATH = r'C:\\xampp\\mysql\\bin\\mysql.exe'

# Server backup configuration
SERVER_FOLDER = r'C:\\Users\\Administrator\\Desktop\\txData\\VORPCore_D7F8D9.base\\resources'
SERVER_BACKUP_DIR = r'C:\\Users\\Administrator\\Documents\\server_backups\\server'
SERVER_BACKUP_KEEP_COUNT = 10
SERVER_BACKUP_THROTTLE = 0.1  # seconds delay between files (throttling)

# TxAdmin update configuration
TXADMIN_SERVER_DIR = r'C:\\Users\\Administrator\\Desktop\\server'
TXADMIN_BACKUP_DIR = r'C:\\Users\\Administrator\\Documents\\server_backups\\txadmin'
TXADMIN_DOWNLOAD_DIR = r'C:\\Users\\Administrator\\Downloads'
TXADMIN_URL = 'https://runtime.fivem.net/artifacts/fivem/build_server_windows/master'
TXADMIN_KEEP_COUNT = 5
SEVEN_ZIP_PATH = r'C:\\Program Files\\7-Zip\\7z.exe'
AUTO_UPDATE_TXADMIN = True  # Enable/disable automatic TxAdmin updates

# Backup schedule
DB_BACKUP_HOURS = [3, 15]
SERVER_BACKUP_HOURS = [3]
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
