@echo off
setlocal enabledelayedexpansion

echo ========================================
echo FIVEM ^& REDM Server Controller Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :install_python
    if !errorlevel! neq 0 exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python version: !PYTHON_VERSION!
echo.

goto :continue_install

:install_python
echo Python is not installed.
echo.
set /p "choice=Would you like to install Python automatically? (Y/N): "
if /i not "!choice!"=="Y" (
    echo Please install Python manually from https://www.python.org/downloads/
    pause
    exit /b 1
)

set "TEMP_DIR=%TEMP%\python_install"
if not exist "!TEMP_DIR!" mkdir "!TEMP_DIR!"

set "INSTALLER=!TEMP_DIR!\python-installer.exe"
echo Downloading Python 3.14.0...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe' -OutFile '!INSTALLER!'"

if not exist "!INSTALLER!" (
    echo ERROR: Download failed
    pause
    exit /b 1
)

echo Installing Python...
"!INSTALLER!" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0
del "!INSTALLER!"

REM Refresh PATH
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "PATH=!PATH!;%%b"

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo WARNING: Python installed but not in PATH. Please restart installer.
    pause
    exit /b 1
)

echo Python installed successfully!
exit /b 0

:continue_install
REM Step 2: Install dependencies
echo [Step 2/6] Installing Python dependencies...
echo This may take a few minutes...
echo.

set PACKAGES=pyinstaller requests beautifulsoup4 psutil pywin32 winshell Pillow

for %%p in (%PACKAGES%) do (
    echo Installing %%p...
    python -m pip install %%p --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo WARNING: Failed to install %%p
    ) else (
        echo OK: %%p installed successfully
    )
)
echo.

REM Step 2.5: Check for icon file in src folder
echo [Step 2.5/6] Checking for icon file...
cd src
if not exist "icon.ico" (
    echo WARNING: icon.ico not found in src folder.
    echo Creating a default icon placeholder...
    
    REM Create a simple 1x1 pixel ico file using Python
    python -c "from PIL import Image; img = Image.new('RGB', (256, 256), color='blue'); img.save('icon.ico')" 2>nul
    
    if errorlevel 1 (
        echo ERROR: Could not create default icon. Please provide an icon.ico file in the src folder.
        cd ..
        pause
        exit /b 1
    )
    echo OK: Created default icon
) else (
    echo OK: icon.ico found
)
cd ..
echo.

REM Step 3: Build executables
echo [Step 3/6] Building executables with PyInstaller...
echo This will take several minutes...
echo.

cd src

REM Build main application - SHOW OUTPUT for debugging
echo Building FIVEM ^& REDM Server Controller...
echo Running: python -m PyInstaller app.spec --clean --noconfirm
echo.
python -m PyInstaller app.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Failed to build main application
    echo.
    echo Common causes:
    echo - Missing icon.ico file in src folder
    echo - Missing dependencies
    echo - Invalid .spec file configuration
    echo.
    echo Please check the error messages above.
    cd ..
    pause
    exit /b 1
)
echo OK: Main application built
echo.

REM Build remote client
echo Building FIVEM ^& REDM Remote Client...
python -m PyInstaller remote_app.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Failed to build remote client
    echo Check error messages above for details.
    cd ..
    pause
    exit /b 1
)
echo OK: Remote client built
echo.

cd ..

REM Step 4: Verify executables
echo [Step 4/6] Verifying executables...
set DIST_DIR=src\dist
set ALL_BUILT=1

if not exist "%DIST_DIR%\FIVEM & REDM Server Controller.exe" (
    echo ERROR: Main application executable not found
    set ALL_BUILT=0
)
if not exist "%DIST_DIR%\FIVEM & REDM Remote Client.exe" (
    echo ERROR: Remote client executable not found
    set ALL_BUILT=0
)

if !ALL_BUILT! equ 0 (
    echo.
    echo Build completed with errors. Some executables are missing.
    echo Check the build output above for details.
    pause
    exit /b 1
)
echo OK: All executables created successfully
echo.

REM Step 5: Create Start Menu shortcuts
echo [Step 5/6] Creating Start Menu shortcuts...

set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
set APP_FOLDER=%START_MENU%\FIVEM ^& REDM Controller

REM Create Start Menu folder
if not exist "%APP_FOLDER%" mkdir "%APP_FOLDER%"

REM Create shortcuts using PowerShell
echo Creating shortcuts...

REM Main application shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APP_FOLDER%\FIVEM ^& REDM Server Controller.lnk'); $s.TargetPath = '%CD%\%DIST_DIR%\FIVEM ^& REDM Server Controller.exe'; $s.WorkingDirectory = '%CD%\%DIST_DIR%'; $s.Save()" >nul 2>&1

REM Remote client shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APP_FOLDER%\FIVEM ^& REDM Remote Client.lnk'); $s.TargetPath = '%CD%\%DIST_DIR%\FIVEM ^& REDM Remote Client.exe'; $s.WorkingDirectory = '%CD%\%DIST_DIR%'; $s.Save()" >nul 2>&1

echo OK: Start Menu shortcuts created
echo.

REM Step 6: Complete
echo [Step 6/6] Installation complete!
echo.
echo ========================================
echo Installation Summary
echo ========================================
echo Executables location: %CD%\%DIST_DIR%
echo Start Menu shortcuts: %APP_FOLDER%
echo.
echo Applications installed:
echo - FIVEM ^& REDM Server Controller
echo - FIVEM ^& REDM Remote Client
echo.
echo Opening installation folder...
echo.

REM Open the dist folder in Windows Explorer
start "" explorer "%CD%\%DIST_DIR%"

echo Installation completed successfully!
echo You can now close this window or press any key to exit.
pause >nul
exit /b 0
