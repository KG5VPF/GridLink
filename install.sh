#!/usr/bin/env bash
set -e

APP_NAME="GridLink"
INSTALL_DIR="$HOME/GridLink"
DESKTOP_FILE="$HOME/.local/share/applications/gridlink.desktop"

echo "Installing $APP_NAME..."

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Install/check Linux system dependencies
if command -v apt >/dev/null 2>&1; then
    echo "Installing Linux system dependencies ..."
    sudo apt update
    sudo apt install -y python3-tk python3-venv rsync xclip xsel
else
    echo
    echo "Warning: apt was not found. Please make sure these packages are installed:"
    echo "  python3-tk python3-venv rsync xclip xsel"
    echo
fi

# Check tkinter
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo
    echo "Tkinter is not installed."
    echo "On Linux Mint / Ubuntu, run:"
    echo "  sudo apt install python3-tk"
    echo
    exit 1
fi

# Check venv support
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo
    echo "Python virtual environment support is missing."
    echo "On Linux Mint / Ubuntu, run:"
    echo "  sudo apt install python3-venv"
    echo
    exit 1
fi

# Check clipboard helpers for VarAC/Wine reliability
if ! command -v xclip >/dev/null 2>&1 && ! command -v xsel >/dev/null 2>&1; then
    echo
    echo "Warning: xclip/xsel not found."
    echo "Copy/paste into VarAC under Wine may be unreliable without them."
    echo
fi

mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/share/applications"

echo "Copying files to $INSTALL_DIR ..."
rsync -av --delete \
    --exclude "venv" \
    --exclude ".git" \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    ./ "$INSTALL_DIR/"

echo "Creating virtual environment ..."
python3 -m venv "$INSTALL_DIR/venv"

echo "Installing Python dependencies ..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "Creating menu launcher ..."
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=GridLink
Comment=HF Digital Cellular field communications dashboard
Exec=/bin/bash -c 'cd "$HOME/GridLink" && "$HOME/GridLink/venv/bin/python" "$HOME/GridLink/gridlink.py"'
Icon=$HOME/GridLink/icons/varalert_icon.png
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

echo
echo "$APP_NAME installation complete."
echo "You should now find GridLink in your application menu."
echo "You may need to log out and back in if the menu does not refresh immediately."
