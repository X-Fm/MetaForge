# Meta Forge v2.0
EXIF | GPS | Device Metadata Injector

Developer : FmIt
Contact   : https://t.me/fmitofficial
GitHub    : https://github.com/X-Fm/MetaForge

---

## Features

- Inject device info (Make, Model) into video and image files
- Inject GPS coordinates (Auto / Random City / City List / Manual)
- 50+ world cities across all continents
- 30+ latest phone models (Samsung, Apple, Xiaomi, OPPO, Google, etc.)
- Dual-tool processing: exiftool (primary) + ffmpeg + PIL fallback
- Animated green progress bar (0-100%)
- Auto output filename: VID02042026155823.mp4 / IMG02042026155823.jpg
- Network-based location fallback (IP geolocation)

---

## Installation and Run

---

### Termux (Android)

Step 1 - Update and install system packages:

    pkg update && pkg upgrade -y
    pkg install python ffmpeg exiftool -y

Step 2 - Install Python libraries:

    pip install -r requirements.txt --break-system-packages

Step 3 - Run:

    python meta_forge.py

---

### Linux (Debian / Kali)

Step 1 - Install system packages:

    sudo apt update
    sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl -y

Step 2 - Install Python libraries:

    pip3 install -r requirements.txt

Step 3 - Run:

    python3 meta_forge.py

---

### Ubuntu (22.04 / 24.04)

Step 1 - Install system packages:

    sudo apt update
    sudo apt install python3 python3-pip python3-venv ffmpeg libimage-exiftool-perl -y

Step 2 - (Recommended) Use virtual environment:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Step 3 - Run:

    python3 meta_forge.py

To deactivate venv later:

    deactivate

---

## Clone from GitHub

    git clone https://github.com/X-Fm/MetaForge.git
    cd MetaForge

Then follow the installation steps above for your platform.

---

## Output File Naming

    Video : VID + date + time + ext   ->   VID02042026155823.mp4
    Image : IMG + date + time + ext   ->   IMG02042026155823.jpg

Output files are saved in ./meta_output/ folder by default.

---

## Supported File Types

    Video : .mp4  .mov  .mkv
    Image : .jpg  .jpeg  .png

---

## Requirements

    Tool        Purpose                         Install
    ---------   ---------------------------     -----------------------------------
    python3     Run the script                  pkg install python
    ffmpeg      Video encode + metadata         pkg install ffmpeg
    exiftool    EXIF/metadata injection         pkg install exiftool
    Pillow      Image fallback processing       pip install Pillow
    piexif      EXIF write for images           pip install piexif

---

## Quick One-Line Setup

Termux:

    pkg update -y && pkg install python ffmpeg exiftool -y && pip install Pillow piexif --break-system-packages

Linux / Ubuntu / Kali:

    sudo apt update && sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl -y && pip3 install Pillow piexif

---

## Notes

- If exiftool is not installed, the script falls back to Pillow + piexif for images.
- If ffmpeg is not installed, the script copies the original video and applies exiftool only.
- GPS auto-detection requires termux-api package and the Termux:API app on Android.
- If GPS fails, the script automatically detects location via network (IP-based).

For GPS auto-detect in Termux:

    pkg install termux-api
    Then install Termux:API app from F-Droid

---

## Links

- GitHub   : https://github.com/X-Fm/MetaForge
- Telegram : https://t.me/fmitofficial

---

Meta Forge v2.0 - FmIt | t.me/fmitofficial | github.com/X-Fm/MetaForge