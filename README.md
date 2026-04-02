
# Meta Forge v2.0
**EXIF GPS Device Metadata Injector**

> Developer : **FmIt**
> Contact   : [https://t.me/fmitofficial](https://t.me/fmitofficial)

---

## âœ¨ Features

- Inject device info (Make, Model) into video & image files
- Inject GPS coordinates (Auto / Random City / Manual)
- 50+ world cities across all continents
- 30+ latest phone models (Samsung, Apple, Xiaomi, OPPO, Google, etc.)
- Dual-tool processing: **exiftool** (primary) + **ffmpeg** + PIL fallback
- Animated green progress bar (0“100%)
- Auto output filename: `VID02042026155823.mp4` / `IMG02042026155823.jpg`

---

##  Installation & Run

---

###  Termux (Android)

**Step 1 â€” Update & install system packages:**
```bash
pkg update && pkg upgrade -y
pkg install python ffmpeg exiftool -y
```

**Step 2 â€” Install Python libraries:**
```bash
pip install -r requirements.txt --break-system-packages
```

**Step 3 â€” Run:**
```bash
python meta_forge.py
```

---

### Linux (Debian / Ubuntu / Kali)

**Step 1 â€” Install system packages:**
```bash
sudo apt update
sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl -y
```

**Step 2 â€” Install Python libraries:**
```bash
pip3 install -r requirements.txt
```

**Step 3 â€” Run:**
```bash
python3 meta_forge.py
```

---

### linux¸ Ubuntu (22.04 / 24.04)

**Step 1 â€” Install system packages:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg libimage-exiftool-perl -y
```

**Step 2 ” (Recommended) Use virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 3 â€” Run:**
```bash
python3 meta_forge.py
```

> To deactivate venv later: `deactivate`

---

## Output File Naming

| Type  | Format                     | Example                    |
|-------|----------------------------|----------------------------|
| Video | `VID` + date + time + ext  | `VID02042026155823.mp4`    |
| Image | `IMG` + date + time + ext  | `IMG02042026155823.jpg`    |

Output files are saved in `./meta_output/` folder by default.

---

## Supported File Types

| Type   | Extensions              |
|--------|-------------------------|
| Video  | `.mp4` `.mov` `.mkv`    |
| Image  | `.jpg` `.jpeg` `.png`   |

---

##  Requirements Summary

| Tool        | Purpose                        | Install                                  |
|-------------|-------------------------------|------------------------------------------|
| `python3`   | Run the script                 | `pkg install python` / `apt install python3` |
| `ffmpeg`    | Video encode + metadata        | `pkg install ffmpeg` / `apt install ffmpeg` |
| `exiftool`  | EXIF/metadata injection        | `pkg install exiftool` / `apt install libimage-exiftool-perl` |
| `Pillow`    | Image fallback processing      | `pip install Pillow` |
| `piexif`    | EXIF write for images          | `pip install piexif` |

---

## âš¡ Quick One-Line Setup

**Termux:**
```bash
pkg update -y && pkg install python ffmpeg exiftool -y && pip install Pillow piexif --break-system-packages
```

**Linux / Ubuntu / Kali:**
```bash
sudo apt update && sudo apt install python3 python3-pip ffmpeg libimage-exiftool-perl -y && pip3 install Pillow piexif
```

---

## Notes

- If `exiftool` is not installed, the script falls back to `Pillow + piexif` for images.
- If `ffmpeg` is not installed, the script copies the original video and applies `exiftool` only.
- GPS auto-detection requires `termux-api` package and the **Termux:API** app installed on Android.

```bash
# For GPS auto-detect in Termux:
pkg install termux-api
# Then install Termux:API app from F-Droid
```

---

*Meta Forge v2.0” FmIt | t.me/fmitofficial*
