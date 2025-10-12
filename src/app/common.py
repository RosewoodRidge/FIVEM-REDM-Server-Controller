import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

from config import COLORS
from settings import update_setting as update_setting_func

def update_setting(*args, **kwargs):
    """Pass through to settings module"""
    return update_setting_func(*args, **kwargs)

class ModernScrolledText(scrolledtext.ScrolledText):
    """Custom ScrolledText widget with Web 3.0 styling"""
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        
        # Apply custom styling with improved contrast
        self.config(
            background=COLORS['panel'],
            foreground=COLORS['text'],
            insertbackground=COLORS['text'],  # cursor color
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['text'],
            borderwidth=0,
            font=('Consolas', 9)
        )

def apply_styles():
    """Apply Web 3.0 styling to ttk widgets with improved contrast"""
    style = ttk.Style()
    
    # Configure the main theme
    style.configure("TFrame", background=COLORS['bg'])
    style.configure("TLabel", 
                    background=COLORS['bg'], 
                    foreground=COLORS['text'],
                    font=('Segoe UI', 10))
    
    # LabelFrame styling
    style.configure("TLabelframe", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
    style.configure("TLabelframe.Label", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'],
                    font=('Segoe UI', 11, 'bold'))
    
    # Button styling with improved contrast
    style.configure("TButton", 
                    background=COLORS['accent'],
                    foreground=COLORS['button_text'],
                    padding=10,
                    font=('Segoe UI', 10, 'bold'))
    style.map("TButton",
              background=[('active', COLORS['accent_hover'])],
              foreground=[('active', COLORS['button_text'])])
    
    # Primary action button
    style.configure("Primary.TButton", 
                    background=COLORS['accent'],
                    foreground=COLORS['button_text'],
                    padding=12,
                    font=('Segoe UI', 11, 'bold'))
    style.map("Primary.TButton",
              background=[('active', COLORS['accent_hover'])],
              foreground=[('active', COLORS['button_text'])])
    
    # Link-style button
    style.configure("Link.TButton", 
                    background=COLORS['bg'],
                    foreground=COLORS['accent'],
                    padding=2,
                    font=('Segoe UI', 9, 'underline'),
                    borderwidth=0)
    style.map("Link.TButton",
              background=[('active', COLORS['bg'])],
              foreground=[('active', COLORS['accent_hover'])])
    
    # Entry styling
    style.configure("TEntry", 
                    fieldbackground=COLORS['panel'],
                    foreground='#000000',  # Black text for visibility
                    borderwidth=1,
                    padding=8)
    
    # Tab styling with improved visibility
    style.configure("TNotebook", 
                    background=COLORS['bg'],
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab", 
                    background=COLORS['tab_bg'],
                    foreground=COLORS['tab_fg'],
                    padding=[15, 5],
                    font=('Segoe UI', 10))
    style.map("TNotebook.Tab",
              background=[('selected', COLORS['tab_selected_bg'])],
              foreground=[('selected', COLORS['tab_selected_fg'])])
              
    # Make sure text is visible inside panels
    style.configure("TFrame.Label", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
                    
    # Fix contrast for labels inside panels
    style.configure("Panel.TLabel", 
                    background=COLORS['panel'],
                    foreground=COLORS['text'])
    
    # Success and error styles for status indicators
    style.configure("Success.TLabel",
                    background=COLORS['panel'],
                    foreground='green',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Error.TLabel",
                    background=COLORS['panel'],
                    foreground='red',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Warning.TLabel",
                    background=COLORS['panel'],
                    foreground='orange',
                    font=('Segoe UI', 11, 'bold'))
    style.configure("Disconnected.TLabel",
                    background=COLORS['bg'],
                    foreground='red',
                    font=('Segoe UI', 10, 'bold'))
    style.configure("Connected.TLabel",
                    background=COLORS['bg'],
                    foreground='green',
                    font=('Segoe UI', 10, 'bold'))

def log_message(text_widget, message):
    """Add a message to the log display"""
    text_widget.config(state=tk.NORMAL)
    timestamp = datetime.now().strftime('%H:%M:%S')
    text_widget.insert(tk.END, f"[{timestamp}] {message}\n")
    text_widget.see(tk.END)
    text_widget.config(state=tk.DISABLED)
