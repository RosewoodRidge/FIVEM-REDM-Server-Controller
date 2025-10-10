import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import shutil
import winshell
from win32com.client import Dispatch

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FIVEM & REDM Server Controller - Installer")
        self.root.geometry("600x500")  # Increased height from 400 to 500
        self.root.resizable(False, False)
        
        # Variables
        self.cancelled = False
        self.current_step = 0
        self.total_steps = 6
        self.installation_complete = False  # Track completion status
        
        # Configure style
        style = ttk.Style()
        style.configure("TLabel", font=('Segoe UI', 10))
        style.configure("Title.TLabel", font=('Segoe UI', 14, 'bold'))
        
        # Title
        title_label = ttk.Label(
            root, 
            text="FIVEM & REDM Server Controller Installer",
            style="Title.TLabel"
        )
        title_label.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(
            root,
            text="Ready to install",
            wraplength=550
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            root,
            mode='determinate',
            length=500
        )
        self.progress.pack(pady=20)
        
        # Percentage label
        self.percent_label = ttk.Label(root, text="0%")
        self.percent_label.pack()
        
        # Log text area - reduced height from 10 to 8
        log_frame = ttk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,  # Reduced from 10 to 8
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Button frame - ensure it's always visible at the bottom
        button_frame = ttk.Frame(root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15, padx=20)
        
        self.install_button = ttk.Button(
            button_frame,
            text="Install",
            command=self.start_installation
        )
        self.install_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_installation
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, step, message):
        """Update progress bar and status"""
        if self.cancelled:
            return False
            
        self.current_step = step
        progress_value = (step / self.total_steps) * 100
        self.progress['value'] = progress_value
        self.percent_label.config(text=f"{int(progress_value)}%")
        self.status_label.config(text=message)
        self.log(f"[Step {step}/{self.total_steps}] {message}")
        self.root.update_idletasks()
        return True
    
    def start_installation(self):
        """Start installation in a separate thread"""
        self.install_button.config(state=tk.DISABLED)
        self.cancelled = False
        
        thread = threading.Thread(target=self.run_installation, daemon=True)
        thread.start()
    
    def cancel_installation(self):
        """Cancel the installation"""
        if self.current_step > 0 and self.current_step < self.total_steps:
            if messagebox.askyesno("Cancel Installation", 
                                   "Are you sure you want to cancel the installation?"):
                self.cancelled = True
                self.log("Installation cancelled by user")
                self.status_label.config(text="Installation cancelled")
        else:
            self.root.destroy()
    
    def run_installation(self):
        """Main installation process"""
        try:
            # Get the directory where the installer is located
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script - go up one level from src directory
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            src_dir = os.path.join(base_dir, "src")
            
            # Step 1: Check Python installation
            if not self.update_progress(1, "Checking Python installation..."):
                return
            
            try:
                result = subprocess.run(
                    [sys.executable, "--version"],
                    capture_output=True,
                    text=True
                )
                self.log(f"Python version: {result.stdout.strip()}")
            except Exception as e:
                self.log(f"Error checking Python: {e}")
                messagebox.showerror("Error", "Python installation not found!")
                return
            
            # Step 2: Install dependencies
            if not self.update_progress(2, "Installing Python dependencies..."):
                return
            
            dependencies = [
                'pyinstaller',
                'requests',
                'beautifulsoup4',
                'psutil',
                'pywin32',
                'winshell'
            ]
            
            for dep in dependencies:
                if self.cancelled:
                    return
                    
                self.log(f"Installing {dep}...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep],
                        capture_output=True,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    self.log(f"✓ {dep} installed successfully")
                except subprocess.CalledProcessError as e:
                    self.log(f"✗ Failed to install {dep}: {e}")
            
            # Step 3: Build executables
            if not self.update_progress(3, "Building executables with PyInstaller..."):
                return
            
            spec_files = [
                ('app.spec', 'FIVEM & REDM Server Controller'),
                ('remote_app.spec', 'FIVEM & REDM Remote Client'),
                ('config_editor.spec', 'FIVEM & REDM Configuration Editor')
            ]
            
            for spec_file, app_name in spec_files:
                if self.cancelled:
                    return
                    
                spec_path = os.path.join(src_dir, spec_file)
                if not os.path.exists(spec_path):
                    self.log(f"✗ Spec file not found: {spec_path}")
                    continue
                
                self.log(f"Building {app_name}...")
                try:
                    # Run PyInstaller from the src directory
                    subprocess.run(
                        [sys.executable, "-m", "PyInstaller", spec_file, "--clean", "--noconfirm"],
                        cwd=src_dir,
                        capture_output=True,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    self.log(f"✓ {app_name} built successfully")
                except subprocess.CalledProcessError as e:
                    self.log(f"✗ Failed to build {app_name}")
            
            # Step 4: Organize files
            if not self.update_progress(4, "Organizing files..."):
                return
            
            dist_dir = os.path.join(src_dir, "dist")
            if os.path.exists(dist_dir):
                self.log(f"Executables created in: {dist_dir}")
            else:
                self.log("✗ Distribution directory not found")
                messagebox.showerror("Error", "Build failed - executables not created")
                return
            
            # Step 5: Create Start Menu shortcuts
            if not self.update_progress(5, "Creating Start Menu shortcuts..."):
                return
            
            try:
                # Create Start Menu folder
                start_menu = winshell.start_menu()
                app_folder = os.path.join(start_menu, "Programs", "FIVEM & REDM Controller")
                os.makedirs(app_folder, exist_ok=True)
                
                # Create shortcuts for each executable
                shortcuts = [
                    ('FIVEM & REDM Server Controller.exe', 'FIVEM & REDM Server Controller.lnk'),
                    ('FIVEM & REDM Remote Client.exe', 'FIVEM & REDM Remote Client.lnk'),
                    ('FIVEM & REDM Configuration Editor.exe', 'FIVEM & REDM Configuration Editor.lnk')
                ]
                
                for exe_name, shortcut_name in shortcuts:
                    exe_path = os.path.join(dist_dir, exe_name)
                    if os.path.exists(exe_path):
                        shortcut_path = os.path.join(app_folder, shortcut_name)
                        
                        shell = Dispatch('WScript.Shell')
                        shortcut = shell.CreateShortCut(shortcut_path)
                        shortcut.Targetpath = exe_path
                        shortcut.WorkingDirectory = dist_dir
                        shortcut.IconLocation = exe_path
                        shortcut.save()
                        
                        self.log(f"✓ Created shortcut: {shortcut_name}")
                    else:
                        self.log(f"✗ Executable not found: {exe_name}")
                
                self.log(f"Shortcuts created in: {app_folder}")
                
            except Exception as e:
                self.log(f"✗ Error creating shortcuts: {e}")
            
            # Step 6: Complete
            if not self.update_progress(6, "Installation complete!"):
                return
            
            dist_dir = os.path.join(src_dir, "dist")
            
            self.log("\n=== Installation Complete ===")
            self.log(f"Executables location: {dist_dir}")
            self.log(f"Start Menu shortcuts created")
            self.log("\nOpening installation folder...")
            
            self.cancel_button.config(text="Close")
            self.installation_complete = True
            
            # Show completion message
            messagebox.showinfo(
                "Installation Complete",
                "FIVEM & REDM Server Controller has been installed successfully!\n\n"
                "The installation folder will now open.\n"
                "You can also launch the applications from your Start Menu."
            )
            
            # Open the dist folder in Windows Explorer
            try:
                if os.path.exists(dist_dir):
                    # Use subprocess to open explorer and select the folder
                    subprocess.Popen(['explorer', dist_dir])
                    self.log(f"Opened folder: {dist_dir}")
            except Exception as e:
                self.log(f"Could not open folder: {e}")
            
            # Close the installer after a short delay
            self.root.after(1000, self.close_installer)
            
        except Exception as e:
            self.log(f"\n✗ Installation failed: {e}")
            messagebox.showerror("Installation Error", f"An error occurred:\n{e}")
            self.install_button.config(state=tk.NORMAL)
    
    def close_installer(self):
        """Close the installer window"""
        if self.installation_complete:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
