#!/data/data/com.termux/files/usr/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║         META FORGE - Installer Script v2.5           ║
# ║              Developer: Forrukh (FmIt)               ║
# ╚══════════════════════════════════════════════════════╝

RED="\033[91m"
GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
BOLD="\033[1m"
RESET="\033[0m"

ok()   { echo -e "${GREEN}  ✔  $1${RESET}"; }
err()  { echo -e "${RED}  ✘  $1${RESET}"; }
info() { echo -e "${CYAN}  ℹ  $1${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠  $1${RESET}"; }

clear
echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ███╗   ███╗███████╗████████╗ █████╗                 ║"
echo "║  ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗                ║"
echo "║  ██╔████╔██║█████╗     ██║   ███████║                 ║"
echo "║  ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║                 ║"
echo "║  ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║                 ║"
echo "║  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝  FORGE v2.5   ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║           Installer for Termux / Linux               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Detect environment ──
if [ -d "/data/data/com.termux" ]; then
    PLATFORM="termux"
    INSTALL_DIR="${PREFIX}/bin"
    info "Platform: Termux"
else
    PLATFORM="linux"
    INSTALL_DIR="/usr/local/bin"
    info "Platform: Linux"
fi

# ── Find script files (running from cloned repo) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PY="${SCRIPT_DIR}/meta_forge.py"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"

if [ ! -f "$SOURCE_PY" ]; then
    err "meta_forge.py not found in: $SCRIPT_DIR"
    err "Make sure you ran:"
    echo -e "${YELLOW}    git clone https://github.com/X-Fm/MetaForge.git${RESET}"
    echo -e "${YELLOW}    cd MetaForge && ./install.sh${RESET}"
    exit 1
fi

ok "Found: meta_forge.py"

# ── Update package list ──
info "Updating packages..."
if [ "$PLATFORM" = "termux" ]; then
    pkg update -y 2>/dev/null | tail -3
else
    sudo apt-get update -qq 2>/dev/null
fi

# ── Install system packages ──
info "Installing system packages..."
if [ "$PLATFORM" = "termux" ]; then
    pkg install -y python ffmpeg exiftool termux-api git curl wget termux-tools 2>/dev/null | grep -E "(installed|already|newly)"
else
    sudo apt-get install -y python3 python3-pip ffmpeg libimage-exiftool-perl git curl 2>/dev/null | grep -E "(installed|already)"
fi
ok "System packages ready"

# ── Install Python requirements ──
info "Installing Python requirements..."
if [ -f "$REQUIREMENTS" ]; then
    # Use requirements.txt from the cloned repo
    if [ "$PLATFORM" = "termux" ]; then
        pip install -r "$REQUIREMENTS" --break-system-packages --quiet 2>/dev/null
    else
        pip3 install -r "$REQUIREMENTS" --quiet 2>/dev/null
    fi
    ok "Python packages installed from requirements.txt"
else
    # Fallback: install manually if requirements.txt missing
    warn "requirements.txt not found, installing manually..."
    if [ "$PLATFORM" = "termux" ]; then
        pip install Pillow piexif --break-system-packages --quiet 2>/dev/null
    else
        pip3 install Pillow piexif --quiet 2>/dev/null
    fi
    ok "Python packages installed (manual)"
fi

# ── Storage permission (Termux only) ──
if [ "$PLATFORM" = "termux" ]; then
    if [ ! -d "$HOME/storage" ]; then
        warn "Setting up storage access..."
        termux-setup-storage
        sleep 2
    fi
    ok "Storage access: ready"
fi

# ── Install globally ──
info "Installing MetaForge globally..."

if [ "$PLATFORM" = "termux" ]; then
    GLOBAL_PATH="${PREFIX}/bin/metaforge"
    cp "$SOURCE_PY" "$GLOBAL_PATH"
    chmod +x "$GLOBAL_PATH"

    # Fix shebang for Termux python path
    PYTHON_PATH="$(which python 2>/dev/null || which python3 2>/dev/null)"
    if [ -n "$PYTHON_PATH" ]; then
        sed -i "1s|.*|#!${PYTHON_PATH}|" "$GLOBAL_PATH"
    fi

else
    GLOBAL_PATH="${INSTALL_DIR}/metaforge"
    sudo cp "$SOURCE_PY" "$GLOBAL_PATH"
    sudo chmod +x "$GLOBAL_PATH"

    PYTHON_PATH="$(which python3 2>/dev/null || which python 2>/dev/null)"
    if [ -n "$PYTHON_PATH" ]; then
        sudo sed -i "1s|.*|#!${PYTHON_PATH}|" "$GLOBAL_PATH"
    fi
fi

ok "Installed globally → $GLOBAL_PATH"

# ── Done ──
echo ""
echo -e "${CYAN}${BOLD}  ✦ Installation Complete! ✦${RESET}"
echo -e "${YELLOW}  ─────────────────────────────────────────${RESET}"
echo -e "${GREEN}  Command  :${RESET}  metaforge"
echo -e "${GREEN}  Or       :${RESET}  python ${SOURCE_PY}"
echo ""
if [ "$PLATFORM" = "termux" ]; then
    echo -e "${YELLOW}  ⚠  For GPS: Install Termux:API app from F-Droid${RESET}"
    echo ""
fi
echo -e "${CYAN}  Telegram : https://t.me/fmitofficial${RESET}"
echo -e "${CYAN}  GitHub   : https://github.com/X-Fm/MetaForge${RESET}"
echo ""