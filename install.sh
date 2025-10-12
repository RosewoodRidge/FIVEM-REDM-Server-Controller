#!/bin/bash
# filepath: c:\Users\maiso\OneDrive\Documents\[RRRP]\Python\FIVEM-REDM Server Controller Utility\FIVEM-REDM-Server-Controller\install.sh

# FIVEM & REDM Server Controller Installer (Linux Version)
# This installer sets up the application on Linux systems

set -e  # Exit on error

echo "========================================"
echo "FIVEM & REDM Server Controller Installer"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if Python is installed
echo "[Step 1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed.${NC}"
    echo ""
    echo "Please install Python 3.8 or newer:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-tk"
    echo "  Fedora/RHEL:   sudo dnf install python3 python3-pip python3-tkinter"
    echo "  Arch:          sudo pacman -S python python-pip tk"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python version: $PYTHON_VERSION${NC}"
echo ""

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}ERROR: pip3 is not installed.${NC}"
    echo "Please install pip3 for your distribution."
    exit 1
fi

# Check for tkinter
echo "Checking for tkinter..."
if ! python3 -c "import tkinter" &> /dev/null; then
    echo -e "${YELLOW}WARNING: tkinter is not installed.${NC}"
    echo "Please install tkinter for your distribution:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  Fedora/RHEL:   sudo dnf install python3-tkinter"
    echo "  Arch:          sudo pacman -S tk"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Install dependencies
echo "[Step 2/6] Installing Python dependencies..."
echo "This may take a few minutes..."
echo ""

PACKAGES="pyinstaller requests beautifulsoup4 psutil Pillow"

for package in $PACKAGES; do
    echo "Installing $package..."
    if pip3 install "$package" --quiet --disable-pip-warnings 2>&1 | grep -v "already satisfied"; then
        echo -e "${GREEN}OK: $package installed successfully${NC}"
    else
        echo -e "${YELLOW}OK: $package already installed${NC}"
    fi
done
echo ""

# Step 2.5: Check for icon file
echo "[Step 2.5/6] Checking for icon file..."
cd src
if [ ! -f "icon.png" ]; then
    echo -e "${YELLOW}WARNING: icon.png not found in src folder.${NC}"
    echo "Creating a default icon placeholder..."
    
    python3 -c "from PIL import Image; img = Image.new('RGB', (256, 256), color='blue'); img.save('icon.png')" 2>/dev/null || {
        echo -e "${RED}ERROR: Could not create default icon.${NC}"
        echo "Please provide an icon.png file in the src folder."
        cd ..
        exit 1
    }
    echo -e "${GREEN}OK: Created default icon${NC}"
else
    echo -e "${GREEN}OK: icon.png found${NC}"
fi
cd ..
echo ""

# Step 3: Build executables
echo "[Step 3/6] Building executables with PyInstaller..."
echo "This will take several minutes..."
echo ""

cd src

# Build main application
echo "Building FIVEM & REDM Server Controller..."
echo "Running: python3 -m PyInstaller app.spec --clean --noconfirm"
echo ""
if python3 -m PyInstaller app.spec --clean --noconfirm; then
    echo -e "${GREEN}OK: Main application built${NC}"
else
    echo -e "${RED}ERROR: Failed to build main application${NC}"
    echo ""
    echo "Common causes:"
    echo "- Missing icon.png file in src folder"
    echo "- Missing dependencies"
    echo "- Invalid .spec file configuration"
    echo ""
    cd ..
    exit 1
fi
echo ""

# Build remote client
echo "Building FIVEM & REDM Remote Client..."
if python3 -m PyInstaller remote_app.spec --clean --noconfirm; then
    echo -e "${GREEN}OK: Remote client built${NC}"
else
    echo -e "${RED}ERROR: Failed to build remote client${NC}"
    echo "Check error messages above for details."
    cd ..
    exit 1
fi
echo ""

cd ..

# Step 4: Verify executables
echo "[Step 4/6] Verifying executables..."
DIST_DIR="src/dist"
ALL_BUILT=1

if [ ! -f "$DIST_DIR/FIVEM-REDM-Server-Controller" ]; then
    echo -e "${RED}ERROR: Main application executable not found${NC}"
    ALL_BUILT=0
fi
if [ ! -f "$DIST_DIR/FIVEM-REDM-Remote-Client" ]; then
    echo -e "${RED}ERROR: Remote client executable not found${NC}"
    ALL_BUILT=0
fi

if [ $ALL_BUILT -eq 0 ]; then
    echo ""
    echo "Build completed with errors. Some executables are missing."
    echo "Check the build output above for details."
    exit 1
fi

# Make executables executable
chmod +x "$DIST_DIR/FIVEM-REDM-Server-Controller"
chmod +x "$DIST_DIR/FIVEM-REDM-Remote-Client"

echo -e "${GREEN}OK: All executables created successfully${NC}"
echo ""

# Step 5: Create desktop entries and shortcuts
echo "[Step 5/6] Creating application shortcuts..."

APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

CURRENT_DIR="$(pwd)"

# Main application desktop entry
cat > "$APPS_DIR/fivem-redm-controller.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FIVEM & REDM Server Controller
Comment=Manage FIVEM and REDM servers
Exec=$CURRENT_DIR/$DIST_DIR/FIVEM-REDM-Server-Controller
Icon=$CURRENT_DIR/src/icon.png
Terminal=false
Categories=Utility;System;
EOF

# Remote client desktop entry
cat > "$APPS_DIR/fivem-redm-remote.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FIVEM & REDM Remote Client
Comment=Remote control for FIVEM and REDM servers
Exec=$CURRENT_DIR/$DIST_DIR/FIVEM-REDM-Remote-Client
Icon=$CURRENT_DIR/src/icon.png
Terminal=false
Categories=Utility;System;Network;
EOF

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo -e "${GREEN}OK: Application shortcuts created${NC}"
echo ""

# Step 6: Complete
echo "[Step 6/6] Installation complete!"
echo ""
echo "========================================"
echo "Installation Summary"
echo "========================================"
echo "Executables location: $CURRENT_DIR/$DIST_DIR"
echo "Desktop entries: $APPS_DIR"
echo ""
echo "Applications installed:"
echo "- FIVEM & REDM Server Controller"
echo "- FIVEM & REDM Remote Client"
echo ""
echo "You can find the applications in your application menu."
echo ""
echo "To run from command line:"
echo "  Main:   $DIST_DIR/FIVEM-REDM-Server-Controller"
echo "  Remote: $DIST_DIR/FIVEM-REDM-Remote-Client"
echo ""

# Open file manager if available
if command -v xdg-open &> /dev/null; then
    echo "Opening installation folder..."
    xdg-open "$DIST_DIR" 2>/dev/null || true
fi

echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""