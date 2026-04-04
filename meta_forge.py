#!/usr/bin/env python3
# ╔═══════════════════════════════════════════════════════╗
# ║           META FORGE - EXIF/Metadata Injector         ║
# ║         Device | GPS | Timestamp Spoofer              ║
# ╚═══════════════════════════════════════════════════════╝

import os
import subprocess
import json
import random
import shutil
import sys
import time
import threading
from datetime import datetime

# ─────────────────────────────────────────────
# 🎨 Terminal Color Codes
# ─────────────────────────────────────────────
class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

def color(text, *codes):
    return "".join(codes) + text + C.RESET

# ─────────────────────────────────────────────
# 📊 Dual-Color Progress Bar
# ─────────────────────────────────────────────
class ProgressBar:
    """
    Dual-color animated progress bar.
    Left half  → CYAN  (░░░ fill)
    Right half → MAGENTA (░░░ fill)
    Midpoint crossover creates a 2-color effect.
    """
    BAR_WIDTH = 40

    def __init__(self, label="Processing"):
        self.label = label
        self._pct  = 0
        self._done = False
        self._lock = threading.Lock()
        self._thread = None

    def _render(self, pct):
        filled = int(self.BAR_WIDTH * pct / 100)
        mid    = self.BAR_WIDTH // 2

        bar = ""
        for i in range(self.BAR_WIDTH):
            ch = "█" if i < filled else "░"
            bar += C.GREEN + ch
        bar += C.RESET

        # percentage color
        if pct < 100:
            pct_color = C.GREEN
        else:
            pct_color = C.GREEN

        label_str = color(f"  {self.label:20s}", C.WHITE)
        bracket_l = color("[", C.DIM)
        bracket_r = color("]", C.DIM)
        pct_str   = color(f" {pct:3d}%", pct_color, C.BOLD)

        sys.stdout.write(f"\r{label_str} {bracket_l}{bar}{bracket_r}{pct_str}")
        sys.stdout.flush()

    def _animate(self, target, duration):
        """Smooth animate from current % to target % over `duration` seconds."""
        start = self._pct
        steps = max(1, int(abs(target - start)))
        delay = duration / steps
        for i in range(steps + 1):
            with self._lock:
                if self._done:
                    break
                self._pct = start + int((target - start) * i / steps)
            self._render(self._pct)
            time.sleep(delay)

    def update(self, target_pct, label=None, duration=0.6):
        """Animate bar to target_pct. Blocking call."""
        if label:
            self.label = label
        self._animate(int(target_pct), duration)

    def finish(self, label="Done!"):
        """Animate to 100% and print newline."""
        self.label = label
        self._animate(100, 0.4)
        with self._lock:
            self._pct  = 100
            self._done = True
        self._render(100)
        print()  # newline after bar

    def start(self, label=None):
        """Show bar at 0%."""
        if label:
            self.label = label
        self._pct  = 0
        self._done = False
        self._render(0)


def run_with_progress(label, cmd, bar, start_pct, end_pct):
    """
    Run a subprocess while animating the bar from start_pct → end_pct.
    Returns (returncode, stderr_text).
    """
    bar.update(start_pct, label=label, duration=0.3)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # animate while process runs
    span   = end_pct - start_pct
    step   = 0
    target = start_pct
    while proc.poll() is None:
        # creep toward end_pct slowly
        if target < end_pct - 5:
            target += max(1, span // 20)
            bar.update(target, duration=0.5)
        time.sleep(0.4)

    stdout, stderr = proc.communicate()
    return proc.returncode, stderr.decode()


def banner():
    print(color("""
╔══════════════════════════════════════════════════════╗
║  ███╗   ███╗███████╗████████╗ █████╗                 ║
║  ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗                ║
║  ██╔████╔██║█████╗     ██║   ███████║                 ║
║  ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║                 ║
║  ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║                 ║
║  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝  FORGE v2.1   ║
╠══════════════════════════════════════════════════════╣
║       EXIF • GPS • Device Metadata Injector          ║
╠══════════════════════════════════════════════════════╣
║  Developer : Forrukh                                    ║
║  Contact   : https://t.me/fmitofficial               ║
╚══════════════════════════════════════════════════════╝""", C.CYAN, C.BOLD))
    print(color(f"  ⏱  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Termux Ready\n", C.DIM))

def section(title):
    print(color(f"\n┌─── {title} ", C.YELLOW, C.BOLD) + color("─" * (46 - len(title)) + "┐", C.YELLOW))

def ok(msg):   print(color(f"  ✔  {msg}", C.GREEN))
def err(msg):  print(color(f"  ✘  {msg}", C.RED))
def info(msg): print(color(f"  ℹ  {msg}", C.CYAN))
def warn(msg): print(color(f"  ⚠  {msg}", C.YELLOW))

def prompt(msg, default=""):
    arrow = color("  ▶ ", C.MAGENTA, C.BOLD)
    val = input(f"{arrow}{color(msg, C.WHITE)} ").strip()
    return val if val else default

def menu(title, options: dict, prompt_text="Select"):
    """Display numbered menu, return chosen key"""
    section(title)
    for k, v in options.items():
        label = v[0] if isinstance(v, tuple) else v
        print(color(f"  [{k}]", C.CYAN, C.BOLD) + color(f"  {label}", C.WHITE))
    choice = prompt(f"{prompt_text} [1-{len(options)}]:")
    return choice if choice in options else None

# ─────────────────────────────────────────────
# 🔧 Tool Checks
# ─────────────────────────────────────────────
def check_tools():
    section("Tool Check")
    tools = {
        "ffmpeg":   shutil.which("ffmpeg"),
        "exiftool": shutil.which("exiftool"),
    }
    for t, path in tools.items():
        if path:
            ok(f"{t:12s}  →  {path}")
        else:
            warn(f"{t:12s}  →  NOT FOUND  (install: pkg install {t})")
    print(color("  └" + "─" * 50, C.YELLOW))
    return tools

# ─────────────────────────────────────────────
# 📱 Device Presets (Latest Models 2024-2025)
# ─────────────────────────────────────────────
DEVICES = {
    "1":  ("Auto-detect (Termux)",         None),
    # Samsung
    "2":  ("Samsung Galaxy S25 Ultra",     ("Samsung", "SM-S938B")),
    "3":  ("Samsung Galaxy S25+",          ("Samsung", "SM-S936B")),
    "4":  ("Samsung Galaxy S24 FE",        ("Samsung", "SM-S721B")),
    "5":  ("Samsung Galaxy Z Fold 6",      ("Samsung", "SM-F956B")),
    "6":  ("Samsung Galaxy Z Flip 6",      ("Samsung", "SM-F741B")),
    "7":  ("Samsung Galaxy A55",           ("Samsung", "SM-A556B")),
    "8":  ("Samsung Galaxy A35",           ("Samsung", "SM-A356B")),
    # Apple
    "9":  ("iPhone 16 Pro Max",            ("Apple",   "iPhone 16 Pro Max")),
    "10": ("iPhone 16 Pro",                ("Apple",   "iPhone 16 Pro")),
    "11": ("iPhone 16",                    ("Apple",   "iPhone 16")),
    "12": ("iPhone 15 Pro Max",            ("Apple",   "iPhone 15 Pro Max")),
    "13": ("iPhone 15",                    ("Apple",   "iPhone 15")),
    # Xiaomi
    "14": ("Xiaomi 15 Pro",                ("Xiaomi",  "2501129C")),
    "15": ("Xiaomi 14 Ultra",              ("Xiaomi",  "2401100C")),
    "16": ("Xiaomi 14T Pro",               ("Xiaomi",  "24091PN0DG")),
    "17": ("Redmi Note 14 Pro+",           ("Xiaomi",  "2410129DC")),
    "18": ("POCO X7 Pro",                  ("POCO",    "25010PN2DG")),
    # OPPO / OnePlus
    "19": ("OPPO Find X8 Pro",             ("OPPO",    "PJD110")),
    "20": ("OPPO Reno 13 Pro",             ("OPPO",    "CPH2671")),
    "21": ("OnePlus 13",                   ("OnePlus", "CPH2673")),
    "22": ("OnePlus 13R",                  ("OnePlus", "CPH2657")),
    # Vivo / iQOO
    "23": ("Vivo X200 Pro",                ("vivo",    "V2413A")),
    "24": ("iQOO 13",                      ("vivo",    "V2401A")),
    # Google
    "25": ("Google Pixel 9 Pro XL",        ("Google",  "Pixel 9 Pro XL")),
    "26": ("Google Pixel 9 Pro",           ("Google",  "Pixel 9 Pro")),
    "27": ("Google Pixel 9",               ("Google",  "Pixel 9")),
    # Huawei
    "28": ("Huawei Pura 70 Ultra",         ("HUAWEI",  "BVL-AL90")),
    "29": ("Huawei Nova 13 Pro",           ("HUAWEI",  "JAD-AL50")),
    # Realme
    "30": ("Realme GT 7 Pro",              ("realme",  "RMX3901")),
    "31": ("Realme 14 Pro+",               ("realme",  "RMX4091")),
    # Custom
    "32": ("Custom...",                    "CUSTOM"),
}

# ─────────────────────────────────────────────
# 🌍 Top 50 Cities — All Continents
# ─────────────────────────────────────────────
CITIES = {
    # 🌏 Asia
    "Dhaka, Bangladesh":        ("23.8103",  "90.4125"),
    "Chittagong, Bangladesh":   ("22.3569",  "91.7832"),
    "Mumbai, India":            ("19.0760",  "72.8777"),
    "Delhi, India":             ("28.7041",  "77.1025"),
    "Kolkata, India":           ("22.5726",  "88.3639"),
    "Karachi, Pakistan":        ("24.8607",  "67.0011"),
    "Lahore, Pakistan":         ("31.5204",  "74.3587"),
    "Colombo, Sri Lanka":       ("6.9271",   "79.8612"),
    "Kathmandu, Nepal":         ("27.7172",  "85.3240"),
    "Kabul, Afghanistan":       ("34.5553",  "69.2075"),
    "Tehran, Iran":             ("35.6892",  "51.3890"),
    "Dubai, UAE":               ("25.2048",  "55.2708"),
    "Riyadh, Saudi Arabia":     ("24.7136",  "46.6753"),
    "Baghdad, Iraq":            ("33.3152",  "44.3661"),
    "Istanbul, Turkey":         ("41.0082",  "28.9784"),
    "Beijing, China":           ("39.9042",  "116.4074"),
    "Shanghai, China":          ("31.2304",  "121.4737"),
    "Tokyo, Japan":             ("35.6762",  "139.6503"),
    "Seoul, South Korea":       ("37.5665",  "126.9780"),
    "Bangkok, Thailand":        ("13.7563",  "100.5018"),
    "Jakarta, Indonesia":       ("-6.2088",  "106.8456"),
    "Singapore":                ("1.3521",   "103.8198"),
    "Kuala Lumpur, Malaysia":   ("3.1390",   "101.6869"),
    "Manila, Philippines":      ("14.5995",  "120.9842"),
    "Yangon, Myanmar":          ("16.8661",  "96.1951"),
    "Tashkent, Uzbekistan":     ("41.2995",  "69.2401"),
    # 🌍 Africa
    "Cairo, Egypt":             ("30.0444",  "31.2357"),
    "Lagos, Nigeria":           ("6.5244",   "3.3792"),
    "Nairobi, Kenya":           ("-1.2921",  "36.8219"),
    "Casablanca, Morocco":      ("33.5731",  "-7.5898"),
    "Johannesburg, S. Africa":  ("-26.2041", "28.0473"),
    "Addis Ababa, Ethiopia":    ("9.0320",   "38.7469"),
    # 🌎 Europe
    "London, UK":               ("51.5074",  "-0.1278"),
    "Paris, France":            ("48.8566",  "2.3522"),
    "Berlin, Germany":          ("52.5200",  "13.4050"),
    "Rome, Italy":              ("41.9028",  "12.4964"),
    "Madrid, Spain":            ("40.4168",  "-3.7038"),
    "Moscow, Russia":           ("55.7558",  "37.6173"),
    "Amsterdam, Netherlands":   ("52.3676",  "4.9041"),
    "Stockholm, Sweden":        ("59.3293",  "18.0686"),
    # 🌎 Americas
    "New York, USA":            ("40.7128",  "-74.0060"),
    "Los Angeles, USA":         ("34.0522",  "-118.2437"),
    "Chicago, USA":             ("41.8781",  "-87.6298"),
    "Toronto, Canada":          ("43.6532",  "-79.3832"),
    "Mexico City, Mexico":      ("19.4326",  "-99.1332"),
    "São Paulo, Brazil":        ("-23.5505", "-46.6333"),
    "Buenos Aires, Argentina":  ("-34.6037", "-58.3816"),
    "Bogotá, Colombia":         ("4.7110",   "-74.0721"),
    # 🌏 Oceania
    "Sydney, Australia":        ("-33.8688", "151.2093"),
    "Melbourne, Australia":     ("-37.8136", "144.9631"),
}

def random_city():
    city = random.choice(list(CITIES.keys()))
    lat, lon = CITIES[city]
    info(f"Random city → {city} ({lat}, {lon})")
    return lat, lon, city

def get_auto_gps():
    """Try termux-location with multiple providers"""
    for provider in ["gps", "network", "passive"]:
        try:
            result = subprocess.run(
                ["termux-location", "-p", provider, "-r", "once"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                lat = str(data.get("latitude", ""))
                lon = str(data.get("longitude", ""))
                if lat and lon and lat != "0.0":
                    ok(f"GPS ({provider}): {lat}, {lon}")
                    return lat, lon, "GPS Auto"
        except:
            pass
    return None, None, None

def get_network_location():
    """Multi-API IP-based location fallback"""
    apis = [
        ("https://ipapi.co/json/",      "latitude",  "longitude",  "city", "country_name"),
        ("https://ip-api.com/json/",    "lat",       "lon",        "city", "country"),
        ("https://ipinfo.io/json",      None,        None,         "city", "country"),
    ]
    for url, lat_key, lon_key, city_key, country_key in apis:
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "6", "-A",
                 "Mozilla/5.0 (Linux; Android 13)", url],
                capture_output=True, text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                continue
            data = json.loads(result.stdout)

            # ipinfo returns loc as "lat,lon"
            if lat_key is None and "loc" in data:
                parts = data["loc"].split(",")
                if len(parts) == 2:
                    lat, lon = parts[0].strip(), parts[1].strip()
                else:
                    continue
            else:
                lat = str(data.get(lat_key, ""))
                lon = str(data.get(lon_key, ""))

            city    = data.get(city_key, "")
            country = data.get(country_key, "")

            if lat and lon and lat not in ("", "0", "0.0"):
                label = f"{city}, {country}".strip(", ")
                return lat, lon, label
        except:
            pass
    return None, None, None

# ─────────────────────────────────────────────
# 🎬 VIDEO Processing (ffmpeg + exiftool)
# ─────────────────────────────────────────────
def process_video(file_path, brand, model, lat, lon, output_path, tools, now):
    fname = os.path.basename(file_path)
    info(f"Video → {fname}")

    bar = ProgressBar()
    bar.start(label="Preparing ...")
    bar.update(5, duration=0.2)

    if tools["ffmpeg"]:
        # Detect input video bitrate to match output
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", file_path
        ]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True)
        orig_bitrate = "8000k"
        orig_audio_bitrate = "192k"
        try:
            pdata = json.loads(probe.stdout)
            fmt_bitrate = int(pdata.get("format", {}).get("bit_rate", 0))
            if fmt_bitrate > 0:
                # keep original bitrate, min 6mbps max 20mbps
                vbr = max(6000, min(20000, fmt_bitrate // 1000))
                orig_bitrate = f"{vbr}k"
            for stream in pdata.get("streams", []):
                if stream.get("codec_type") == "audio":
                    abr = int(stream.get("bit_rate", 192000)) // 1000
                    orig_audio_bitrate = f"{max(128, min(320, abr))}k"
        except:
            pass

        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-map_metadata", "-1",
            # Video: high quality, match original resolution
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", "yuv420p",
            "-preset", "slow",
            "-crf", "16",
            "-b:v", orig_bitrate,
            "-maxrate", orig_bitrate,
            "-bufsize", f"{int(orig_bitrate[:-1])*2}k",
            "-movflags", "+faststart",
            # Audio: high quality
            "-c:a", "aac",
            "-b:a", orig_audio_bitrate,
            "-ar", "48000",
            "-ac", "2",
            # Metadata — natural, no encoder/composer
            "-metadata", f"make={brand}",
            "-metadata", f"model={model}",
            "-metadata", f"creation_time={now}",
            "-metadata", f"location={lat},{lon}",
            "-metadata", f"com.apple.quicktime.location.ISO6709=+{lat}+{lon}/",
            "-metadata:s:v:0", "handler_name=VideoHandle",
            "-metadata:s:a:0", "handler_name=SoundHandle",
            output_path
        ]
        rc, stderr = run_with_progress("ffmpeg encoding ...", cmd, bar, 10, 70)
        if rc != 0:
            print()
            err(f"ffmpeg failed:\n{stderr[-300:]}")
            return False
        bar.update(72, label="ffmpeg done ✔", duration=0.2)
    else:
        shutil.copy2(file_path, output_path)
        bar.update(72, label="Copied (no ffmpeg)", duration=0.3)
        warn("\nffmpeg not found — copied original")

    # exiftool pass
    if tools["exiftool"]:
        lat_f, lon_f = float(lat), float(lon)
        lat_ref = "N" if lat_f >= 0 else "S"
        lon_ref = "E" if lon_f >= 0 else "W"
        et_cmd = [
            "exiftool", "-overwrite_original",
            f"-Make={brand}",
            f"-Model={model}",
            f"-DateTimeOriginal={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-CreateDate={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-GPSLatitude={abs(lat_f)}",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon_f)}",
            f"-GPSLongitudeRef={lon_ref}",
            f"-Software={brand} Camera",
            output_path
        ]
        rc2, se2 = run_with_progress("Injecting metadata ...", et_cmd, bar, 75, 95)
        if rc2 == 0:
            bar.finish(label="Metadata injected ✔")
            ok("exiftool: done")
        else:
            bar.finish(label="exiftool partial ⚠")
            warn(f"exiftool: {se2[:150]}")
    else:
        bar.finish(label="Complete ✔")

    return True

# ─────────────────────────────────────────────
# 🖼️ IMAGE Processing (exiftool preferred + PIL fallback)
# ─────────────────────────────────────────────
def inject_icc_device_info(file_path, brand, model):
    """
    Patch ICC profile DeviceManufacturer (dmnd) and DeviceModel (dmdd)
    fields directly in the JPEG binary.
    ICC profile is embedded in JPEG APP2 marker (0xFFE2).
    dmnd tag = 0x646D6E64, dmdd tag = 0x646D6464
    Each tag: 4B sig + 4B type('desc'=0x64657363) + 4B reserved +
              4B count + count bytes ASCII
    """
    try:
        with open(file_path, "rb") as f:
            data = bytearray(f.read())

        # Find APP2 ICC marker
        i = 0
        icc_start = -1
        while i < len(data) - 1:
            if data[i] == 0xFF and data[i+1] == 0xE2:
                # Check ICC signature at offset +4
                if data[i+4:i+16] == b'ICC_PROFILE\x00':
                    icc_start = i
                    break
            i += 1

        if icc_start == -1:
            return False  # No ICC profile found

        # APP2 length
        app2_len = (data[icc_start+2] << 8) | data[icc_start+3]
        icc_data_start = icc_start + 4 + 12  # skip marker+len+ICC header
        icc_end = icc_start + 2 + app2_len

        icc = data[icc_data_start:icc_end]

        def make_desc_tag(tag_sig, text):
            """Build an ICC 'desc' tag: sig(4) + 'desc'(4) + 0(4) + len(4) + text"""
            encoded = text.encode("ascii", errors="replace") + b'\x00'
            return (tag_sig +
                    b'desc' +
                    b'\x00\x00\x00\x00' +
                    len(encoded).to_bytes(4, 'big') +
                    encoded)

        # Patch or append dmnd (Device Manufacturer Description)
        dmnd_sig = b'dmnd'
        dmdd_sig = b'dmdd'

        def patch_tag(icc_bytes, sig, text):
            pos = icc_bytes.find(sig)
            if pos != -1:
                # tag exists — build replacement of same offset
                new_tag = make_desc_tag(sig, text)
                # just rebuild tag at position (variable length — safest to append)
                return icc_bytes  # skip in-place patch, use exiftool fallback
            return icc_bytes  # not found

        # Simpler: write dmnd/dmdd as XMP sidecar via exiftool approach
        # ICC binary patching is complex — use struct approach via Python
        # Build minimal sRGB-like ICC with device info
        # Tag table entry: 4B tag + 4B offset + 4B size
        # We'll just return False and let the caller use XMP fallback
        return False

    except Exception:
        return False


def inject_icc_via_xmp(output_path, brand, model, tools):
    """Write device info to XMP fields which map to ICC in some viewers"""
    if not tools["exiftool"]:
        return
    subprocess.run([
        "exiftool", "-overwrite_original",
        f"-XMP:DeviceManufacturer={brand}",
        f"-XMP:DeviceModel={model}",
        f"-XMP-tiff:Make={brand}",
        f"-XMP-tiff:Model={model}",
        output_path
    ], capture_output=True)


def get_timezone_offset(lat_f, lon_f):
    """
    Get UTC offset in seconds for given GPS coordinates.
    Uses timezonefinder if available, else falls back to device timezone.
    """
    try:
        from timezonefinder import TimezoneFinder
        import zoneinfo
        tf  = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat_f, lng=lon_f)
        if tz_name:
            tz  = zoneinfo.ZoneInfo(tz_name)
            loc_now = datetime.now(tz)
            offset  = loc_now.utcoffset()
            total_s = int(offset.total_seconds())
            h, m    = divmod(abs(total_s) // 60, 60)
            sign    = "+" if total_s >= 0 else "-"
            tz_str  = f"{sign}{h:02d}:{m:02d}"
            return loc_now, tz_str, tz_name
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: device timezone
    now_local = datetime.now().astimezone()
    tz_offset = now_local.strftime('%z')
    tz_str    = tz_offset[:3] + ":" + tz_offset[3:]
    import time as _time
    tz_name   = _time.tzname[0]
    return now_local, tz_str, tz_name


def process_image(file_path, brand, model, lat, lon, output_path, tools, now):
    fname = os.path.basename(file_path)
    info(f"Image → {fname}")

    bar = ProgressBar()
    bar.start(label="Preparing ...")
    bar.update(8, duration=0.2)

    shutil.copy2(file_path, output_path)
    bar.update(20, label="File copied ✔", duration=0.2)

    lat_f, lon_f = float(lat), float(lon)

    # Get timezone from GPS location
    loc_now, tz_str, tz_name = get_timezone_offset(lat_f, lon_f)
    info(f"Location TZ: {tz_name} ({tz_str})")

    dt_str    = loc_now.strftime('%Y:%m:%d %H:%M:%S')
    dt_tz_str = dt_str + tz_str                        # 2026:04:04 12:57:49+06:00

    # GPS timestamp always UTC
    import datetime as _dt
    utc_now   = datetime.utcnow()

    if tools["exiftool"]:
        lat_ref = "N" if lat_f >= 0 else "S"
        lon_ref = "E" if lon_f >= 0 else "W"
        focal   = random.choice(["24/1","26/1","27/1","50/1","85/1"])
        fstop   = random.choice(["18/10","20/10","22/10","28/10","18/5"])
        iso     = random.choice(["50","64","100","125","200","400"])
        shutter = random.choice(["1/1000","1/500","1/250","1/125","1/60"])
        cmd = [
            "exiftool", "-overwrite_original",
            f"-Make={brand}",
            f"-Model={model}",
            f"-LensModel={brand} {focal}mm f/{float(fstop.split('/')[0])/float(fstop.split('/')[1]):.1f}",
            f"-FocalLength={focal}",
            f"-FNumber={fstop}",
            f"-ISO={iso}",
            f"-ExposureTime={shutter}",
            f"-Software={brand} Camera",
            f"-DateTimeOriginal={dt_tz_str}",
            f"-CreateDate={dt_tz_str}",
            f"-ModifyDate={dt_tz_str}",
            f"-GPSLatitude={abs(lat_f)}",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon_f)}",
            f"-GPSLongitudeRef={lon_ref}",
            f"-GPSAltitude=15",
            f"-GPSAltitudeRef=0",
            f"-GPSTimeStamp={utc_now.strftime('%H:%M:%S')}",
            f"-GPSDateStamp={utc_now.strftime('%Y:%m:%d')}",
            f"-ImageDescription=Shot on {brand} {model}",
            f"-Comment=Shot on {brand} {model}",
            f"-Artist={brand}",
            f"-Copyright={brand} {datetime.now().year}",
            f"-ProfileDescription={brand} {model}",
            f"-PrimaryPlatform=Unknown",
            f"-XMP:DeviceManufacturer={brand}",
            f"-XMP:DeviceModel={model}",
            f"-XMP-tiff:Make={brand}",
            f"-XMP-tiff:Model={model}",
            "-JpegQuality=95",
            output_path
        ]
        rc, stderr = run_with_progress("Injecting EXIF ...", cmd, bar, 25, 85)
        if rc == 0:
            # Second pass: ICC DeviceManufacturer + DeviceModel via -ICC_Profile
            icc_cmd = [
                "exiftool", "-overwrite_original",
                f"-ICC_Profile:DeviceManufacturer={brand[:4].ljust(4)}",
                f"-ICC_Profile:DeviceModel={model[:4].ljust(4)}",
                f"-ICC_Profile:ProfileDescription={brand} {model}",
                output_path
            ]
            subprocess.run(icc_cmd, capture_output=True)
            bar.finish(label="EXIF injected ✔")
            ok("exiftool: metadata injected")
            return True
        else:
            bar.update(90, label="exiftool error ⚠", duration=0.2)
            warn(f"\nexiftool error: {stderr[:200]}")

    # PIL fallback — save at high quality
    bar.update(92, label="PIL fallback ...", duration=0.2)
    try:
        from PIL import Image
        import piexif
        from piexif.helper import deg_to_dms_rational

        img = Image.open(file_path)
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make]             = brand.encode()
        exif_dict["0th"][piexif.ImageIFD.Model]            = model.encode()
        exif_dict["0th"][piexif.ImageIFD.Software]         = f"{brand} Camera".encode()
        exif_dict["0th"][piexif.ImageIFD.XPComment]        = f"Shot on {brand} {model}".encode("utf-16le")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode()
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized]= dt_str.encode()
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude]        = deg_to_dms_rational(lat_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef]     = ("N" if lat_f >= 0 else "S").encode()
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude]       = deg_to_dms_rational(lon_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef]    = ("E" if lon_f >= 0 else "W").encode()
        exif_bytes = piexif.dump(exif_dict)
        # Save at high quality
        img.save(output_path, exif=exif_bytes, quality=95, optimize=False, subsampling=0)
        bar.finish(label="PIL done ✔")
        ok("PIL/piexif fallback: done")
        return True
    except Exception as e:
        bar.finish(label="Failed ✘")
        err(f"PIL failed: {e}")
        return False

# ─────────────────────────────────────────────
# 📋 EXIF Verify
# ─────────────────────────────────────────────
def verify_metadata(file_path, tools):
    if not tools["exiftool"]:
        return
    section("Verify Output Metadata")
    result = subprocess.run(
        ["exiftool", "-Make", "-Model", "-GPSLatitude", "-GPSLongitude",
         "-DateTimeOriginal", "-CreateDate", file_path],
        capture_output=True, text=True
    )
    for line in result.stdout.strip().splitlines():
        print(color(f"  │  {line}", C.CYAN))
    print(color("  └" + "─" * 50, C.YELLOW))

# ─────────────────────────────────────────────
# 🚀 MAIN
# ─────────────────────────────────────────────
def main():
    os.system("clear")
    banner()

    tools = check_tools()

    # ── File Selection ──
    section("File Selection")
    print(color("  [1]", C.CYAN, C.BOLD) + color("  Browse /sdcard (folder navigator)", C.WHITE))
    print(color("  [2]", C.CYAN, C.BOLD) + color("  Manual path input", C.WHITE))
    file_mode = prompt("Select option [1/2]:", "1")

    valid_files = []
    MEDIA_EXT = (".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png")

    if file_mode == "1":
        # ── Interactive folder browser ──
        def scan_folder_with_progress(path):
            """Scan folder showing animated progress"""
            MEDIA_EXT = (".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png")
            dirs_with_media = []
            media_files     = []
            spin = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
            spin_i = 0
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                return [], []

            for e in entries:
                if e.startswith("."):
                    continue
                full = os.path.join(path, e)
                # spinner
                sys.stdout.write(f"\r  {color(spin[spin_i % len(spin)], C.CYAN, C.BOLD)}  "
                                 f"{color('Scanning: ', C.DIM)}{color(e[:40], C.WHITE):<42}")
                sys.stdout.flush()
                spin_i += 1

                if os.path.isdir(full):
                    has_media = False
                    try:
                        for root, _, fnames in os.walk(full):
                            if any(f.lower().endswith(MEDIA_EXT) for f in fnames):
                                has_media = True
                                break
                    except:
                        pass
                    if has_media:
                        dirs_with_media.append(e)
                elif e.lower().endswith(MEDIA_EXT):
                    media_files.append(e)

            sys.stdout.write(f"\r  {color('✔', C.GREEN, C.BOLD)}  "
                             f"{color(f'Found {len(dirs_with_media)} folder(s), {len(media_files)} file(s)', C.GREEN):<50}\n")
            sys.stdout.flush()
            return dirs_with_media, media_files

        def browse_folder(current_path):
            """Returns list of selected files"""
            while True:
                os.system("clear")
                banner()
                section(f"Browser: {current_path}")

                # Scan with progress
                dirs_with_media, media_files = scan_folder_with_progress(current_path)
                if not dirs_with_media and not media_files and current_path == "/sdcard":
                    err("Permission denied! Run: termux-setup-storage")
                    return []

                items = []  # (display, full_path, is_dir)

                # Back option
                if current_path != "/sdcard":
                    print(color("  [ 0]", C.YELLOW, C.BOLD) +
                          color("  [..] Back", C.YELLOW))

                # Folders
                for d in dirs_with_media:
                    idx = len(items) + 1
                    items.append((d, os.path.join(current_path, d), True))
                    print(color(f"  [{idx:>3}]", C.CYAN, C.BOLD) +
                          color(f"  [DIR]  {d}", C.CYAN))

                # Media files
                for f in media_files:
                    idx = len(items) + 1
                    ext = os.path.splitext(f)[1].upper().replace(".", "")
                    ec  = C.MAGENTA if ext in ("MP4","MOV","MKV") else C.GREEN
                    items.append((f, os.path.join(current_path, f), False))
                    print(color(f"  [{idx:>3}]", C.CYAN, C.BOLD) +
                          color(f"  [{ext}]  ", ec) +
                          color(f"{f}", C.WHITE))

                if not items:
                    warn("No folders with media or media files found here.")

                print()
                print(color("  [*] Select ALL files in this folder", C.DIM))
                print(color("  Multi: 2,3,5  |  Range: 2-6  |  0=Back", C.DIM))
                sel = prompt("Enter number(s):")

                # Back
                if sel.strip() == "0":
                    parent = os.path.dirname(current_path)
                    if parent == current_path:
                        return []
                    current_path = parent
                    continue

                # Select all files in current folder
                if sel.strip() == "*":
                    selected = [it[1] for it in items if not it[2]]
                    if selected:
                        return selected
                    warn("No files in this folder")
                    continue

                # Parse selection
                chosen_idx = set()
                for part in sel.split(","):
                    part = part.strip()
                    if "-" in part:
                        try:
                            a, b = part.split("-")
                            chosen_idx.update(range(int(a), int(b)+1))
                        except:
                            warn(f"Invalid range: {part}")
                    else:
                        try:
                            chosen_idx.add(int(part))
                        except:
                            warn(f"Invalid: {part}")

                result_files = []
                enter_dir    = None
                for idx in sorted(chosen_idx):
                    if 1 <= idx <= len(items):
                        name, path, is_dir = items[idx-1]
                        if is_dir:
                            enter_dir = path  # enter first selected dir
                        else:
                            result_files.append(path)
                    else:
                        warn(f"No item at {idx}")

                if result_files:
                    return result_files
                elif enter_dir:
                    current_path = enter_dir
                    continue
                else:
                    warn("Nothing selected")

        valid_files = browse_folder("/sdcard") or []

    else:
        # ── Manual input ──
        user_input = prompt("File path / multiple (,) / folder:")
        if os.path.isdir(user_input):
            MEDIA_EXT = (".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png")
            raw = [os.path.join(user_input, f) for f in os.listdir(user_input)
                   if f.lower().endswith(MEDIA_EXT)]
            valid_files = [f for f in raw if os.path.exists(f)]
            info(f"Found {len(valid_files)} files in folder")
        else:
            paths = [f.strip() for f in user_input.split(",") if f.strip()]
            valid_files = [f for f in paths if os.path.exists(f)]

    if not valid_files:
        err("No valid files selected!")
        exit(1)
    ok(f"{len(valid_files)} file(s) selected:")
    for f in valid_files:
        print(color(f"    + {os.path.basename(f)}", C.GREEN))

    # ── Device Selection ──
    section("Device Selection")
    categories = {
        "Auto":         ["1"],
        "Samsung":      ["2","3","4","5","6","7","8"],
        "Apple":        ["9","10","11","12","13"],
        "Xiaomi/POCO":  ["14","15","16","17","18"],
        "OPPO/OnePlus": ["19","20","21","22"],
        "Vivo/iQOO":    ["23","24"],
        "Google":       ["25","26","27"],
        "Huawei":       ["28","29"],
        "Realme":       ["30","31"],
        "Custom":       ["32"],
    }
    # Table header
    line = "─" * 62
    print(color(f"\n  ┌{line}┐", C.YELLOW))
    print(color(f"  │ {'No':<4} {'Device':<27} │ {'No':<4} {'Device':<27}│", C.WHITE, C.BOLD))
    print(color(f"  ├{line}┤", C.YELLOW))

    for cat, keys in categories.items():
        print(color(f"  │ {cat:<60} │", C.YELLOW, C.BOLD))
        pairs = [keys[i:i+2] for i in range(0, len(keys), 2)]
        for pair in pairs:
            left_k = pair[0]
            left_l = DEVICES[left_k][0]
            if len(pair) > 1:
                right_k = pair[1]
                right_l = DEVICES[right_k][0]
            else:
                right_k = ""
                right_l = ""
            left_cell  = color(f"[{left_k:>2}]",  C.CYAN, C.BOLD) + color(f" {left_l:<25}", C.WHITE)
            right_cell = (color(f"[{right_k:>2}]", C.CYAN, C.BOLD) + color(f" {right_l:<25}", C.WHITE)) if right_k else color(f"{'':30}", C.WHITE)
            print(f"  │ {left_cell} │ {right_cell}│")
        print(color(f"  ├{line}┤", C.YELLOW))

    print(color(f"  └{line}┘", C.YELLOW))
    choice = prompt("Select device number:")
    if choice not in DEVICES:
        err("Invalid device choice"); exit(1)

    if choice == "1":
        try:
            brand = subprocess.check_output("getprop ro.product.brand", shell=True).decode().strip()
            model = subprocess.check_output("getprop ro.product.model", shell=True).decode().strip()
            ok(f"Detected: {brand} {model}")
        except:
            brand, model = "Android", "Device"
    elif DEVICES[choice][1] == "CUSTOM":
        brand = prompt("Enter Brand (e.g. Samsung):", "Samsung")
        model = prompt("Enter Model (e.g. SM-A546E):", "SM-A546E")
    else:
        brand, model = DEVICES[choice][1]
        ok(f"Selected: {brand} {model}")

    # ── GPS Selection ──
    GPS_OPTS = {
        "1": "Auto GPS (termux-location)",
        "2": "Random City",
        "3": "Choose from City List",
        "4": "Manual Coordinates",
    }
    gps_choice = menu("GPS / Location", GPS_OPTS)

    city_name = ""
    if gps_choice == "1":
        info("Trying GPS (termux-location)...")
        lat, lon, city_name = get_auto_gps()
        if lat and lon:
            ok(f"GPS detected: {lat}, {lon}")
        else:
            warn("GPS failed → trying network location (IP-based)...")
            lat, lon, city_name = get_network_location()
            if lat and lon:
                ok(f"Network location: {city_name} ({lat}, {lon})")
            else:
                warn("Network failed → using random city")
                lat, lon, city_name = random_city()
    elif gps_choice == "2":
        lat, lon, city_name = random_city()
    elif gps_choice == "3":
        section("City List")
        regions = {
            "🌏 Asia":      list(range(1, 27)),
            "🌍 Africa":    list(range(27, 33)),
            "🌎 Europe":    list(range(33, 41)),
            "🌎 Americas":  list(range(41, 49)),
            "🌏 Oceania":   list(range(49, 51)),
        }
        city_list = list(CITIES.keys())
        idx = 1
        for region, nums in regions.items():
            print(color(f"\n  {region}", C.YELLOW))
            for n in nums:
                if n-1 < len(city_list):
                    c = city_list[n-1]
                    lat_c, lon_c = CITIES[c]
                    print(color(f"    [{n:>2}]", C.CYAN, C.BOLD) +
                          color(f"  {c:30s}", C.WHITE) +
                          color(f"({lat_c}, {lon_c})", C.DIM))
        cidx = prompt("Enter city number:")
        try:
            city_name = city_list[int(cidx) - 1]
            lat, lon = CITIES[city_name]
            ok(f"Selected: {city_name}")
        except:
            warn("Invalid → random city")
            lat, lon, city_name = random_city()
    else:
        lat = prompt("Latitude  (e.g. 23.685):", "23.685")
        lon = prompt("Longitude (e.g. 90.356):", "90.356")
        city_name = "Custom"

    # ── Output folder ──
    section("Output Settings")

    def detect_output():
        if os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", ""):
            return "/sdcard/meta", "Termux"
        return "./meta_output", "Linux"

    final_dir, platform_name = detect_output()

    info(f"Platform   : {platform_name}")
    info(f"Output dir : {final_dir}")

    try:
        os.makedirs(final_dir, exist_ok=True)
        ok(f"Output ready → {final_dir}")
    except PermissionError:
        warn("Permission denied! Run: termux-setup-storage")
        final_dir = "./meta_output"
        os.makedirs(final_dir, exist_ok=True)
        ok(f"Fallback → {final_dir}")
    except Exception as e:
        err(f"Folder error: {e}"); exit(1)

    # GPS location timezone → video creation_time
    _loc_now, _tz_str, _tz_name = get_timezone_offset(float(lat), float(lon))
    now = _loc_now.strftime("%Y-%m-%dT%H:%M:%S") + _tz_str
    info(f"Video TZ : {_tz_name} ({_tz_str})")

    # ── Process Files ──
    section("Processing")
    success, fail = 0, 0
    output_files = []

    for file_path in valid_files:
        ext = os.path.splitext(file_path)[1].lower()
        now_dt = datetime.now()
        date_str = now_dt.strftime("%Y%m%d")
        time_str = now_dt.strftime("%H%M%S")

        if ext in (".mp4", ".mov", ".mkv"):
            out_name = f"VID{date_str}{time_str}{ext}"
        elif ext in (".jpg", ".jpeg", ".png"):
            out_name = f"IMG{date_str}{time_str}{ext}"
        else:
            out_name = f"FILE{date_str}{time_str}{ext}"

        final_path = os.path.join(final_dir, out_name)

        print()
        info(f"Output name : {color(out_name, C.GREEN, C.BOLD)}")

        if ext in (".mp4", ".mov", ".mkv"):
            r = process_video(file_path, brand, model, lat, lon, final_path, tools, now)
        elif ext in (".jpg", ".jpeg", ".png"):
            r = process_image(file_path, brand, model, lat, lon, final_path, tools, now)
        else:
            warn(f"Unsupported: {file_path}"); fail += 1; continue

        if r:
            success += 1
            output_files.append(out_name)
            verify_metadata(final_path, tools)
        else:
            if os.path.exists(final_path):
                os.remove(final_path)
            fail += 1

    # ── Media Scanner (Gallery refresh) ──
    if output_files and os.path.exists("/data/data/com.termux"):
        info("Scanning files to Gallery...")
        for fname in output_files:
            fpath = os.path.join(final_dir, fname)
            subprocess.run([
                "am", "broadcast",
                "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d", f"file://{fpath}"
            ], capture_output=True)
        ok("Gallery updated!")

    # ── Summary ──
    section("Summary")
    files_str = "\n".join([f"    ✔  {f}" for f in output_files]) if output_files else "    —"
    print(color(f"""
  Device    :  {brand} {model}
  Location  :  {city_name} ({lat}, {lon})
  Output    :  {final_dir}
  Success   :  {success} file(s)
  Failed    :  {fail} file(s)
""", C.WHITE))
    print(color("  Output Files:", C.YELLOW, C.BOLD))
    print(color(files_str, C.GREEN))
    print(color("\n  ✦ META FORGE COMPLETE ✦\n", C.CYAN, C.BOLD))

if __name__ == "__main__":
    main()