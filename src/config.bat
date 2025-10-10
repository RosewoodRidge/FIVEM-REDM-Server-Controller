@echo off
echo Starting Configuration Editor...

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Run the config editor and log any output
start "FIVEM & REDM Configuration" /B pythonw.exe config_editor.py 2>> logs\config_editor_errors.log

if errorlevel 1 (
    echo An error occurred. Check logs\config_editor_errors.log for details.
    pause
)
