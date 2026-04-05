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

# ── GitHub Info ──
GITHUB_USER="X-Fm"
GITHUB_REPO="MetaForge"
GITHUB_BRANCH="main"

# ── Direct download URLs (3 fallback methods) ──
RAW_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/meta_forge.py"
GITHUB_URL="https://github.com/${GITHUB_USER}/${GITHUB_REPO}/raw/${GITHUB_BRANCH}/meta_forge.py"
CLONE_URL="https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git"

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
    pkg install -y python ffmpeg exiftool termux-api git curl wget 2>/dev/null | grep -E "(installed|already|newly)"
    pip install pillow piexif --break-system-packages --quiet 2>/dev/null
else
    sudo apt-get install -y python3 python3-pip ffmpeg libimage-exiftool-perl git curl wget 2>/dev/null | grep -E "(installed|already)"
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
DOWNLOAD_OK=false

# Method 1: curl with full headers
if command -v curl &>/dev/null; then
    info "Trying curl..."
    curl -L \
        --retry 3 \
        --retry-delay 2 \
        --max-time 30 \
        --connect-timeout 10 \
        -H "User-Agent: Mozilla/5.0 (Linux; Android 13; Termux)" \
        -H "Accept: text/plain,*/*" \
        -o "$TMP_FILE" \
        "$RAW_URL" 2>/dev/null

    if [ -s "$TMP_FILE" ] && grep -q "CURRENT_VERSION" "$TMP_FILE" 2>/dev/null; then
        DOWNLOAD_OK=true
        ok "Downloaded via curl (raw)"
    fi
fi

# Method 2: curl github.com/raw fallback
if [ "$DOWNLOAD_OK" = false ] && command -v curl &>/dev/null; then
    info "Trying curl (github.com fallback)..."
    curl -L \
        --retry 3 \
        --max-time 30 \
        -H "User-Agent: Mozilla/5.0 (Linux; Android 13)" \
        -o "$TMP_FILE" \
        "$GITHUB_URL" 2>/dev/null

    if [ -s "$TMP_FILE" ] && grep -q "CURRENT_VERSION" "$TMP_FILE" 2>/dev/null; then
        DOWNLOAD_OK=true
        ok "Downloaded via curl (github fallback)"
    fi
fi

# Method 3: wget fallback
if [ "$DOWNLOAD_OK" = false ] && command -v wget &>/dev/null; then
    info "Trying wget..."
    wget -q \
        --tries=3 \
        --timeout=30 \
        --user-agent="Mozilla/5.0 (Linux; Android 13)" \
        -O "$TMP_FILE" \
        "$RAW_URL" 2>/dev/null

    if [ -s "$TMP_FILE" ] && grep -q "CURRENT_VERSION" "$TMP_FILE" 2>/dev/null; then
        DOWNLOAD_OK=true
        ok "Downloaded via wget"
    fi
fi

# Method 4: git clone fallback
if [ "$DOWNLOAD_OK" = false ] && command -v git &>/dev/null; then
    info "Trying git clone..."
    CLONE_DIR="/tmp/MetaForge_clone"
    rm -rf "$CLONE_DIR"
    git clone --depth=1 "$CLONE_URL" "$CLONE_DIR" 2>/dev/null
    if [ -f "$CLONE_DIR/meta_forge.py" ]; then
        cp "$CLONE_DIR/meta_forge.py" "$TMP_FILE"
        rm -rf "$CLONE_DIR"
        DOWNLOAD_OK=true
        ok "Downloaded via git clone"
    fi
fi

# ── Check download result ──
if [ "$DOWNLOAD_OK" = false ]; then
    err "Download failed! Try manually:"
    echo -e "${YELLOW}  git clone https://github.com/X-Fm/MetaForge.git${RESET}"
    echo -e "${YELLOW}  cd MetaForge && python meta_forge.py${RESET}"
    exit 1
fi

ok "Download complete"

# ── Install to PATH ──
INSTALL_PATH="${INSTALL_DIR}/metaforge"

if [ "$PLATFORM" = "termux" ]; then
    cp "$TMP_FILE" "$INSTALL_PATH"
    chmod +x "$INSTALL_PATH"
    # Also save to home
    cp "$TMP_FILE" "$HOME/meta_forge.py"
    chmod +x "$HOME/meta_forge.py"
else
    sudo cp "$TMP_FILE" "$INSTALL_PATH"
    sudo chmod +x "$INSTALL_PATH"
fi

rm -f "$TMP_FILE"
ok "Installed to: $INSTALL_PATH"

# ── Done ──
echo ""
echo -e "${CYAN}${BOLD}  Installation Complete!${RESET}"
echo -e "${YELLOW}  ─────────────────────────────────────${RESET}"

if [ "$PLATFORM" = "termux" ]; then
    echo -e "${GREEN}  Run with:${RESET}  metaforge"
    echo -e "${GREEN}  Or:      ${RESET}  python ~/meta_forge.py"
    echo ""
    echo -e "${YELLOW}  ⚠  Install Termux:API app from F-Droid${RESET}"
    echo -e "${YELLOW}     for GPS auto-detection!${RESET}"
else
    echo -e "${GREEN}  Run with:${RESET}  metaforge"
    echo -e "${GREEN}  Or:      ${RESET}  python3 meta_forge.py"
fi

echo ""
echo -e "${CYAN}  Telegram : https://t.me/fmitofficial${RESET}"
echo -e "${CYAN}  GitHub   : https://github.com/${GITHUB_USER}/${GITHUB_REPO}${RESET}"
echo ""