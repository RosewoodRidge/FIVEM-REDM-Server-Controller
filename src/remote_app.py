import os
import sys
import logging
import traceback

# Import config manager functions
from config_manager import get_logs_dir

# Ensure logs directory exists
logs_dir = get_logs_dir()

# Setup logging
logging.basicConfig(
    filename=os.path.join(logs_dir, 'remote_app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

logging.info("Remote application starting...")

def main():
    """Main function to run the remote GUI application"""
    try:
        # Import tkinter
        import tkinter as tk
        from tkinter import messagebox
        
        logging.info("Tkinter imported successfully")
        
        # Import the remote application module
        from remote_app.main import RemoteBackupApp
        
        logging.info("RemoteBackupApp imported successfully")
        
        # Create root window
        root = tk.Tk()
        logging.info("Root window created")
        
        # Create app
        app = RemoteBackupApp(root)
        logging.info("RemoteBackupApp initialized")
        
        # Start main loop
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"Import Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(error_msg)
        
        # Try to show error in a message box
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Import Error", 
                f"Failed to import required modules:\n\n{str(e)}\n\n"
                f"Check {os.path.join(logs_dir, 'remote_app.log')} for details.")
            root.destroy()
        except:
            pass
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Startup Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(error_msg)
        
        # Try to show error in a message box
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", 
                f"Failed to start remote application:\n\n{str(e)}\n\n"
                f"Check {os.path.join(logs_dir, 'remote_app.log')} for details.")
            root.destroy()
        except:
            pass
        sys.exit(1)

if __name__ == '__main__':
    main()
