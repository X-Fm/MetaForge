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
║  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝  FORGE v2.0   ║
╠══════════════════════════════════════════════════════╣
║       EXIF • GPS • Device Metadata Injector          ║
╠══════════════════════════════════════════════════════╣
║  Developer : FmIt                                    ║
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
    try:
        result = subprocess.run(["termux-location"], capture_output=True, text=True, timeout=8)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return str(data["latitude"]), str(data["longitude"]), "Auto"
    except:
        pass
    return None, None, None

def get_network_location():
    """Fallback: detect country via public IP geolocation API"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "https://ipapi.co/json/"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            lat  = str(data.get("latitude", ""))
            lon  = str(data.get("longitude", ""))
            city = data.get("city", "")
            country = data.get("country_name", "")
            if lat and lon:
                label = f"{city}, {country}" if city else country
                return lat, lon, label
    except:
        pass
    # second fallback
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "https://ip-api.com/json/"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                lat = str(data.get("lat", ""))
                lon = str(data.get("lon", ""))
                city = data.get("city", "")
                country = data.get("country", "")
                if lat and lon:
                    label = f"{city}, {country}" if city else country
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
        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-map_metadata", "-1",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-metadata", f"make={brand}",
            "-metadata", f"model={model}",
            "-metadata", f"creation_time={now}",
            "-metadata", f"encoder={brand} {model}",
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
def process_image(file_path, brand, model, lat, lon, output_path, tools, now):
    fname = os.path.basename(file_path)
    info(f"Image → {fname}")

    bar = ProgressBar()
    bar.start(label="Preparing ...")
    bar.update(8, duration=0.2)

    shutil.copy2(file_path, output_path)
    bar.update(20, label="File copied ✔", duration=0.2)

    lat_f, lon_f = float(lat), float(lon)

    if tools["exiftool"]:
        lat_ref = "N" if lat_f >= 0 else "S"
        lon_ref = "E" if lon_f >= 0 else "W"
        cmd = [
            "exiftool", "-overwrite_original",
            f"-Make={brand}",
            f"-Model={model}",
            f"-LensInfo={brand} Lens",
            f"-Software={brand} Camera App",
            f"-DateTimeOriginal={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-CreateDate={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-GPSLatitude={abs(lat_f)}",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon_f)}",
            f"-GPSLongitudeRef={lon_ref}",
            f"-GPSAltitude=10",
            f"-GPSAltitudeRef=0",
            f"-ImageDescription=Shot on {brand} {model}",
            f"-Comment=Shot on {brand} {model}",
            output_path
        ]
        rc, stderr = run_with_progress("Injecting EXIF ...", cmd, bar, 25, 90)
        if rc == 0:
            bar.finish(label="EXIF injected ✔")
            ok("exiftool: all metadata injected")
            return True
        else:
            bar.update(90, label="exiftool error ⚠", duration=0.2)
            warn(f"\nexiftool error: {stderr[:200]}")

    # PIL fallback
    bar.update(92, label="PIL fallback ...", duration=0.2)
    try:
        from PIL import Image
        import piexif
        from piexif.helper import deg_to_dms_rational

        img = Image.open(file_path)
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make]  = brand.encode()
        exif_dict["0th"][piexif.ImageIFD.Model] = model.encode()
        exif_dict["0th"][piexif.ImageIFD.XPComment] = f"Shot on {brand} {model}".encode("utf-16le")
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude]     = deg_to_dms_rational(lat_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef]  = "N" if lat_f >= 0 else "S"
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude]    = deg_to_dms_rational(lon_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" if lon_f >= 0 else "W"
        exif_bytes = piexif.dump(exif_dict)
        img.save(output_path, exif=exif_bytes)
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
    user_input = prompt("File path / multiple (,) / folder:")
    if os.path.isdir(user_input):
        files = [os.path.join(user_input, f) for f in os.listdir(user_input)
                 if f.lower().endswith((".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png"))]
        info(f"Found {len(files)} files in folder")
    else:
        files = [f.strip() for f in user_input.split(",") if f.strip()]

    valid_files = [f for f in files if os.path.exists(f)]
    if not valid_files:
        err("No valid files found!")
        exit(1)
    ok(f"{len(valid_files)} file(s) ready")

    # ── Device Selection ──
    section("Device Selection")
    categories = {
        "── Auto":         ["1"],
        "── Samsung":      ["2","3","4","5","6","7","8"],
        "── Apple":        ["9","10","11","12","13"],
        "── Xiaomi/POCO":  ["14","15","16","17","18"],
        "── OPPO/OnePlus": ["19","20","21","22"],
        "── Vivo/iQOO":    ["23","24"],
        "── Google":       ["25","26","27"],
        "── Huawei":       ["28","29"],
        "── Realme":       ["30","31"],
        "── Custom":       ["32"],
    }
    for cat, keys in categories.items():
        print(color(f"\n  {cat}", C.YELLOW))
        for k in keys:
            label = DEVICES[k][0]
            print(color(f"    [{k:>2}]", C.CYAN, C.BOLD) + color(f"  {label}", C.WHITE))
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
    out_dir = prompt("Output folder [default: ./meta_output]:", "./meta_output")
    os.makedirs(out_dir, exist_ok=True)
    ok(f"Output → {out_dir}")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # ── Process Files ──
    section("Processing")
    success, fail = 0, 0
    output_files = []

    for file_path in valid_files:
        ext = os.path.splitext(file_path)[1].lower()
        now_dt = datetime.now()
        date_str = now_dt.strftime("%d%m%Y")
        time_str = now_dt.strftime("%H%M%S")

        if ext in (".mp4", ".mov", ".mkv"):
            out_name = f"VID{date_str}{time_str}{ext}"
        elif ext in (".jpg", ".jpeg", ".png"):
            out_name = f"IMG{date_str}{time_str}{ext}"
        else:
            out_name = f"FILE{date_str}{time_str}{ext}"

        output_path = os.path.join(out_dir, out_name)

        print()
        info(f"Output name: {color(out_name, C.GREEN, C.BOLD)}")
        if ext in (".mp4", ".mov", ".mkv"):
            r = process_video(file_path, brand, model, lat, lon, output_path, tools, now)
        elif ext in (".jpg", ".jpeg", ".png"):
            r = process_image(file_path, brand, model, lat, lon, output_path, tools, now)
        else:
            warn(f"Unsupported: {file_path}"); fail += 1; continue

        if r:
            success += 1
            output_files.append(out_name)
            verify_metadata(output_path, tools)
        else:
            fail += 1

    # ── Summary ──
    section("Summary")
    files_str = "\n".join([f"    ✔  {f}" for f in output_files]) if output_files else "    —"
    print(color(f"""
  Device    :  {brand} {model}
  Location  :  {city_name} ({lat}, {lon})
  Output    :  {out_dir}
  Success   :  {success} file(s)
  Failed    :  {fail} file(s)
""", C.WHITE))
    print(color("  Output Files:", C.YELLOW, C.BOLD))
    print(color(files_str, C.GREEN))
    print(color("\n  ✦ META FORGE COMPLETE ✦\n", C.CYAN, C.BOLD))

if __name__ == "__main__":
    main()