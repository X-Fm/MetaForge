
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

## Supported File Types

    Video : .mp4  .mov  .mkv
    Image : .jpg  .jpeg  .png

---
---

# TERMUX (Android)

---

### Step 1 - Update Termux packages

    pkg update && pkg upgrade -y

---

### Step 2 - Install required packages

    pkg install python ffmpeg exiftool git -y

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

    pkg update && pkg upgrade -y && pkg install python ffmpeg exiftool git -y && git clone https://github.com/X-Fm/MetaForge.git && cd MetaForge && pip install -r requirements.txt --break-system-packages && python meta_forge.py

---
---

# LINUX (Debian / Ubuntu / Kali)

---

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
---

## Output File Naming

    Video : VID + date + time + ext   ->   VID02042026155823.mp4
    Image : IMG + date + time + ext   ->   IMG02042026155823.jpg

Output files are saved in ./meta_output/ folder by default.

---

## Notes

- If exiftool is not installed, the script falls back to Pillow + piexif for images.
- If ffmpeg is not installed, the script copies the original video and applies exiftool only.
- GPS auto-detection requires termux-api package and Termux:API app on Android.
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
