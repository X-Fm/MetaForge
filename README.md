# Meta Forge v2.5
EXIF | GPS | Device Metadata Injector

Developer : Forrukh (FmIt)
[![Contact on Telegram](https://img.shields.io/badge/Telegram-Contact-blue?logo=telegram)](https://t.me/fmitofficial)
GitHub    : https://github.com/X-Fm/MetaForge

![Meta Forge Screenshot 1](https://raw.githubusercontent.com/X-Fm/MetaForge/a38d5e699f5f96b8ded0c72520f4985850170e33/IMG_20260402_212531.jpg)
![Meta Forge Screenshot 2](https://raw.githubusercontent.com/X-Fm/MetaForge/a38d5e699f5f96b8ded0c72520f4985850170e33/IMG_20260402_212554.jpg)

---

## Features

- Inject device info (Make, Model) into video and image files
- Inject GPS coordinates (Auto / Random City / City List / Manual)
- 50+ world cities across all continents with correct timezones
- 30+ latest phone models (Samsung, Apple, Xiaomi, OPPO, Google, etc.)
- Dual-tool processing: exiftool (primary) + ffmpeg + PIL fallback
- Animated green progress bar (0-100%)
- Auto output filename: VID20260404112703.mp4 / IMG20260404112713.jpg
- Smart GPS detection: GPS chip → WiFi/Tower → IP → Timezone fallback
- Auto update system: checks GitHub on every run
- Exit/Back option at every step

---

## Supported File Types

    Video : .mp4  .mov  .mkv
    Image : .jpg  .jpeg  .png

---

## Output File Naming

    Video : VID + YYYYMMDD + HHMMSS + ext   ->   VID20260404112703.mp4
    Image : IMG + YYYYMMDD + HHMMSS + ext   ->   IMG20260404112713.jpg

    Termux output : /sdcard/meta/
    Linux output  : ./meta_output/

---
---

# TERMUX (Android)

---

## ⚡ Easy Install (Recommended)

Clone the repo and run the installer.
It will install all dependencies and add `metaforge` as a global command automatically:

    git clone https://github.com/X-Fm/MetaForge.git
    cd MetaForge
    chmod +x install.sh
    ./install.sh

After install, run from anywhere:

    metaforge

---

## Manual Install (Step by Step)

### Step 1 - Update Termux packages

    pkg update && pkg upgrade -y

---

### Step 2 - Install required packages

    pkg install python ffmpeg exiftool git termux-api -y

---

### Step 3 - Clone the project from GitHub

    git clone https://github.com/X-Fm/MetaForge.git

---

### Step 4 - Open the project folder

    cd MetaForge

---

### Step 5 - Install Python requirements

    pip install -r requirements.txt --break-system-packages

---

### Step 6 - Run the script

    python meta_forge.py

---

### Termux - All steps in one block (copy and paste)

    pkg update && pkg upgrade -y && pkg install python ffmpeg exiftool git termux-api -y && git clone https://github.com/X-Fm/MetaForge.git && cd MetaForge && pip install -r requirements.txt --break-system-packages && python meta_forge.py

---

### Termux - Global Install (manual)

Step 1 - Make the script executable:

    chmod +x meta_forge.py

Step 2 - Copy to system PATH:

    cp meta_forge.py $PREFIX/bin/metaforge

Step 3 - Now run from anywhere:

    metaforge

Uninstall:

    rm $PREFIX/bin/metaforge

---
---

# LINUX (Debian / Ubuntu / Kali)

---

## ⚡ Easy Install (Recommended)

Clone the repo and run the installer.
It will install all dependencies and add `metaforge` as a global command automatically:

    git clone https://github.com/X-Fm/MetaForge.git
    cd MetaForge
    chmod +x install.sh
    ./install.sh

After install, run from anywhere:

    metaforge

---

## Manual Install (Step by Step)

### Step 1 - Update system packages

    sudo apt update && sudo apt upgrade -y

---

### Step 2 - Install required packages

    sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl git -y

---

### Step 3 - Clone the project from GitHub

    git clone https://github.com/X-Fm/MetaForge.git

---

### Step 4 - Open the project folder

    cd MetaForge

---

### Step 5 - Install Python requirements

    pip3 install -r requirements.txt

---

### Step 6 - Run the script

    python3 meta_forge.py

---

### Linux - All steps in one block (copy and paste)

    sudo apt update && sudo apt upgrade -y && sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl git -y && git clone https://github.com/X-Fm/MetaForge.git && cd MetaForge && pip3 install -r requirements.txt && python3 meta_forge.py

---

### Linux - Global Install (manual)

Step 1 - Make the script executable:

    chmod +x meta_forge.py

Step 2 - Copy to system PATH:

    sudo cp meta_forge.py /usr/local/bin/metaforge

Step 3 - Now run from anywhere:

    metaforge

Uninstall:

    sudo rm /usr/local/bin/metaforge

---
---

## Auto Update System

Every time MetaForge runs, it checks GitHub for a newer version.

If an update is found:

    Current : v2.4
    Latest  : v2.5
    Auto update now? [y/n/q]: y
    -> Downloads new version
    -> Creates backup of old version (meta_forge.py.backup)
    -> Replaces current script automatically
    -> Works for both direct run and global install

---

## GPS Location Detection (Auto mode)

MetaForge tries to get your real location in this order:

    1. GPS chip (offline, most accurate)      up to 8s
    2. Network/Tower GPS (online)             up to 4s
    3. WiFi scan + Google Geolocation         up to 4s
    4. IP-based geolocation (3 APIs)          up to 3s each
    5. Timezone-based city (device timezone)  instant
    6. Random city                            fallback

---

## Requirements

    Tool        Purpose                         Install
    ---------   ---------------------------     -----------------------------------
    python3     Run the script                  pkg install python
    ffmpeg      Video encode + metadata         pkg install ffmpeg
    exiftool    EXIF/metadata injection         pkg install exiftool
    termux-api  GPS + WiFi location             pkg install termux-api
    Pillow      Image fallback processing       pip install Pillow
    piexif      EXIF write for images           pip install piexif

---

## Quick One-Line Setup

Termux:

    pkg update -y && pkg install python ffmpeg exiftool git termux-api -y && pip install Pillow piexif --break-system-packages

Linux / Ubuntu / Kali:

    sudo apt update && sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl git -y && pip3 install Pillow piexif

---

## Notes

- If exiftool is not installed, the script falls back to Pillow + piexif for images.
- If ffmpeg is not installed, the script copies the original video and applies exiftool only.
- GPS auto-detection requires termux-api package and Termux:API app on Android.
- Auto update requires internet connection.
- Backup of previous version is always saved before updating.

For GPS auto-detect in Termux:

    pkg install termux-api
    Then install Termux:API app from F-Droid

---

## Links

- GitHub   : https://github.com/X-Fm/MetaForge
- [![Contact on Telegram](https://img.shields.io/badge/Telegram-Contact-blue?logo=telegram)](https://t.me/fmitofficial)
---

Meta Forge v2.5 - Forrukh (FmIt) | [![Contact on Telegram](https://img.shields.io/badge/Telegram-Contact-blue?logo=telegram)](https://t.me/fmitofficial) | github.com/X-Fm/MetaForge