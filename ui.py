import tkinter as tk
from tkinter import ttk, scrolledtext
from config import COLORS

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
    
    # Entry styling with black text for better visibility on light backgrounds
    style.configure("TEntry", 
                    fieldbackground=COLORS['panel'],
                    foreground='#000000',  # Changed to black text for visibility
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
