import tkinter as tk
from tkinter import ttk

from app.common import ModernScrolledText

class ActivityLogTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Activity Log")
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        # Log output
        self.log_text = ModernScrolledText(
            self.tab, 
            wrap=tk.WORD, 
            height=30
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
