@echo off
REM FIVEM & REDM Server Controller Installer

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Run the Python installer GUI without showing command prompt
start "" /B pythonw.exe src/install.py

REM Exit the batch file
exit
