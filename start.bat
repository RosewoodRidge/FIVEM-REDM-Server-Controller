@echo off

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

start "FIVEM & REDM Server Controller" /B pythonw.exe src/app.py
