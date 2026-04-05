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

GITHUB_USER="X-Fm"
GITHUB_REPO="MetaForge"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/main"
SCRIPT_URL="${RAW_BASE}/meta_forge.py"

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

# ── Update package list ──
info "Updating packages..."
if [ "$PLATFORM" = "termux" ]; then
    pkg update -y 2>/dev/null | tail -3
else
    sudo apt-get update -qq 2>/dev/null
fi

# ── Install dependencies ──
info "Installing dependencies..."
if [ "$PLATFORM" = "termux" ]; then
    pkg install -y python ffmpeg exiftool termux-api 2>/dev/null | grep -E "(installed|already)"
    pip install pillow piexif --quiet 2>/dev/null
else
    sudo apt-get install -y python3 ffmpeg libimage-exiftool-perl 2>/dev/null | grep -E "(installed|already)"
    pip3 install pillow piexif --quiet 2>/dev/null
fi

ok "Dependencies ready"

# ── Storage permission (Termux) ──
if [ "$PLATFORM" = "termux" ]; then
    if [ ! -d "$HOME/storage" ]; then
        warn "Setting up storage access..."
        termux-setup-storage
        sleep 2
    fi
    ok "Storage access: ready"
fi

# ── Download script ──
info "Downloading MetaForge v2.5..."
TMP_FILE="/tmp/meta_forge_tmp.py"

if command -v curl &>/dev/null; then
    curl -sL --retry 3 -o "$TMP_FILE" "$SCRIPT_URL"
elif command -v wget &>/dev/null; then
    wget -q --tries=3 -O "$TMP_FILE" "$SCRIPT_URL"
else
    err "curl/wget not found! Install: pkg install curl"
    exit 1
fi

if [ ! -s "$TMP_FILE" ]; then
    err "Download failed! Check internet connection."
    exit 1
fi

ok "Downloaded successfully"

# ── Install to PATH ──
INSTALL_PATH="${INSTALL_DIR}/metaforge"

if [ "$PLATFORM" = "termux" ]; then
    cp "$TMP_FILE" "$INSTALL_PATH"
    chmod +x "$INSTALL_PATH"
else
    sudo cp "$TMP_FILE" "$INSTALL_PATH"
    sudo chmod +x "$INSTALL_PATH"
fi

# ── Also install as python script ──
if [ "$PLATFORM" = "termux" ]; then
    cp "$TMP_FILE" "$HOME/meta_forge.py"
    chmod +x "$HOME/meta_forge.py"
fi

rm -f "$TMP_FILE"
ok "Installed to: $INSTALL_PATH"

# ── Verify ──
echo ""
echo -e "${CYAN}${BOLD}  Installation Complete!${RESET}"
echo -e "${YELLOW}  ─────────────────────────────────────${RESET}"

if [ "$PLATFORM" = "termux" ]; then
    echo -e "${GREEN}  Run with:${RESET}  metaforge"
    echo -e "${GREEN}  Or:${RESET}       python ~/meta_forge.py"
    echo ""
    echo -e "${YELLOW}  ⚠  Make sure Termux:API app is installed${RESET}"
    echo -e "${YELLOW}     from F-Droid for GPS features!${RESET}"
else
    echo -e "${GREEN}  Run with:${RESET}  metaforge"
    echo -e "${GREEN}  Or:${RESET}       python3 /path/to/meta_forge.py"
fi

echo ""
echo -e "${CYAN}  Telegram: https://t.me/fmitofficial${RESET}"
echo -e "${CYAN}  GitHub:   https://github.com/${GITHUB_USER}/${GITHUB_REPO}${RESET}"
echo ""