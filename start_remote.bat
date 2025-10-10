@echo off

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

start "FIVEM & REDM Remote Client" /B pythonw.exe src/remote_app.py
