#!/usr/bin/env python3

# ─────────────────────────────────────────────
CURRENT_VERSION = "2.4"
GITHUB_USER     = "X-Fm"
GITHUB_REPO     = "MetaForge"
VERSION_URL     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
SCRIPT_URL      = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/meta_forge.py"
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



# ─────────────────────────────────────────────
# 🔄 Auto Update System
# ─────────────────────────────────────────────
def check_update():
    """Check GitHub for newer version and auto update if found"""
    try:
        import urllib.request
        req = urllib.request.Request(
            VERSION_URL,
            headers={"User-Agent": "MetaForge-Updater"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            latest = resp.read().decode().strip()

        if latest == CURRENT_VERSION:
            ok(f"Already up to date (v{CURRENT_VERSION})")
            return False

        # New version available
        print(color(f"\n  ┌─── Update Available ───────────────────────────┐", C.YELLOW, C.BOLD))
        print(color(f"  │  Current : v{CURRENT_VERSION:<38}│", C.WHITE))
        print(color(f"  │  Latest  : v{latest:<38}│", C.GREEN, C.BOLD))
        print(color(f"  └────────────────────────────────────────────────┘", C.YELLOW))

        choice = prompt("Auto update now? [y/n/q(quit)]:", "y")
        if choice.lower() == "q":
            print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)
        if choice.lower() != "y":
            info("Skipping update...")
            return False

        # Download new version
        info("Downloading update...")
        import stat
        running_path = os.path.abspath(__file__)
        prefix_bin   = os.path.join(os.environ.get("PREFIX", "/usr"), "bin", "metaforge")
        usr_bin      = "/usr/local/bin/metaforge"

        # Collect all locations to update
        paths_to_update = set()
        paths_to_update.add(os.path.realpath(running_path))
        for gpath in [prefix_bin, usr_bin]:
            if os.path.exists(gpath):
                paths_to_update.add(os.path.realpath(gpath))

        script_path = running_path
        backup_path = script_path + ".backup"

        req2 = urllib.request.Request(
            SCRIPT_URL,
            headers={"User-Agent": "MetaForge-Updater"}
        )

        bar = ProgressBar()
        bar.start(label="Downloading...")

        with urllib.request.urlopen(req2, timeout=30) as resp:
            new_code = resp.read()

        bar.update(70, label="Downloaded ✔", duration=0.3)

        # Backup old version
        shutil.copy2(script_path, backup_path)
        bar.update(85, label="Backup created...", duration=0.2)

        # Write new version to ALL locations
        updated_paths = []
        for upath in paths_to_update:
            try:
                shutil.copy2(upath, upath + ".backup")
                with open(upath, 'wb') as f:
                    f.write(new_code)
                st = os.stat(upath)
                os.chmod(upath, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                updated_paths.append(upath)
            except Exception as e:
                warn(f"Could not update {upath}: {e}")

        bar.finish(label="Update complete ✔")
        ok(f"Updated to v{latest}")
        ok(f"Backup saved: {backup_path}")
        print(color("\n  Restart script to use new version\n", C.CYAN, C.BOLD))
        exit(0)

    except urllib.error.URLError:
        warn("Update check failed (no internet)")
        return False
    except Exception as e:
        warn(f"Update check error: {e}")
        return False

def banner():
    print(color("""
╔══════════════════════════════════════════════════════╗
║  ███╗   ███╗███████╗████████╗ █████╗                 ║
║  ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗                ║
║  ██╔████╔██║█████╗     ██║   ███████║                 ║
║  ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║                 ║
║  ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║                 ║
║  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝  FORGE v2.5   ║
╠══════════════════════════════════════════════════════╣
║       EXIF • GPS • Device Metadata Injector          ║
╠══════════════════════════════════════════════════════╣
║  Developer : Forrukh (FmIt)                                    ║
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
# CITIES: name -> (lat, lon, tz_offset)
# tz_offset format: "+06:00"
CITIES = {
    # Asia
    "Dhaka, Bangladesh":        ("23.8103",  "90.4125",   "+06:00"),
    "Chittagong, Bangladesh":   ("22.3569",  "91.7832",   "+06:00"),
    "Mumbai, India":            ("19.0760",  "72.8777",   "+05:30"),
    "Delhi, India":             ("28.7041",  "77.1025",   "+05:30"),
    "Kolkata, India":           ("22.5726",  "88.3639",   "+05:30"),
    "Karachi, Pakistan":        ("24.8607",  "67.0011",   "+05:00"),
    "Lahore, Pakistan":         ("31.5204",  "74.3587",   "+05:00"),
    "Colombo, Sri Lanka":       ("6.9271",   "79.8612",   "+05:30"),
    "Kathmandu, Nepal":         ("27.7172",  "85.3240",   "+05:45"),
    "Kabul, Afghanistan":       ("34.5553",  "69.2075",   "+04:30"),
    "Tehran, Iran":             ("35.6892",  "51.3890",   "+03:30"),
    "Dubai, UAE":               ("25.2048",  "55.2708",   "+04:00"),
    "Riyadh, Saudi Arabia":     ("24.7136",  "46.6753",   "+03:00"),
    "Baghdad, Iraq":            ("33.3152",  "44.3661",   "+03:00"),
    "Istanbul, Turkey":         ("41.0082",  "28.9784",   "+03:00"),
    "Beijing, China":           ("39.9042",  "116.4074",  "+08:00"),
    "Shanghai, China":          ("31.2304",  "121.4737",  "+08:00"),
    "Tokyo, Japan":             ("35.6762",  "139.6503",  "+09:00"),
    "Seoul, South Korea":       ("37.5665",  "126.9780",  "+09:00"),
    "Bangkok, Thailand":        ("13.7563",  "100.5018",  "+07:00"),
    "Jakarta, Indonesia":       ("-6.2088",  "106.8456",  "+07:00"),
    "Singapore":                ("1.3521",   "103.8198",  "+08:00"),
    "Kuala Lumpur, Malaysia":   ("3.1390",   "101.6869",  "+08:00"),
    "Manila, Philippines":      ("14.5995",  "120.9842",  "+08:00"),
    "Yangon, Myanmar":          ("16.8661",  "96.1951",   "+06:30"),
    "Tashkent, Uzbekistan":     ("41.2995",  "69.2401",   "+05:00"),
    # Africa
    "Cairo, Egypt":             ("30.0444",  "31.2357",   "+02:00"),
    "Lagos, Nigeria":           ("6.5244",   "3.3792",    "+01:00"),
    "Nairobi, Kenya":           ("-1.2921",  "36.8219",   "+03:00"),
    "Casablanca, Morocco":      ("33.5731",  "-7.5898",   "+01:00"),
    "Johannesburg, S. Africa":  ("-26.2041", "28.0473",   "+02:00"),
    "Addis Ababa, Ethiopia":    ("9.0320",   "38.7469",   "+03:00"),
    # Europe
    "London, UK":               ("51.5074",  "-0.1278",   "+01:00"),
    "Paris, France":            ("48.8566",  "2.3522",    "+02:00"),
    "Berlin, Germany":          ("52.5200",  "13.4050",   "+02:00"),
    "Rome, Italy":              ("41.9028",  "12.4964",   "+02:00"),
    "Madrid, Spain":            ("40.4168",  "-3.7038",   "+02:00"),
    "Moscow, Russia":           ("55.7558",  "37.6173",   "+03:00"),
    "Amsterdam, Netherlands":   ("52.3676",  "4.9041",    "+02:00"),
    "Stockholm, Sweden":        ("59.3293",  "18.0686",   "+02:00"),
    # Americas
    "New York, USA":            ("40.7128",  "-74.0060",  "-04:00"),
    "Los Angeles, USA":         ("34.0522",  "-118.2437", "-07:00"),
    "Chicago, USA":             ("41.8781",  "-87.6298",  "-05:00"),
    "Toronto, Canada":          ("43.6532",  "-79.3832",  "-04:00"),
    "Mexico City, Mexico":      ("19.4326",  "-99.1332",  "-06:00"),
    "Sao Paulo, Brazil":        ("-23.5505", "-46.6333",  "-03:00"),
    "Buenos Aires, Argentina":  ("-34.6037", "-58.3816",  "-03:00"),
    "Bogota, Colombia":         ("4.7110",   "-74.0721",  "-05:00"),
    # Oceania
    "Sydney, Australia":        ("-33.8688", "151.2093",  "+10:00"),
    "Melbourne, Australia":     ("-37.8136", "144.9631",  "+10:00"),
}

def random_city():
    city = random.choice(list(CITIES.keys()))
    lat, lon, tz = CITIES[city]
    info(f"Random city → {city} ({lat}, {lon})")
    return lat, lon, city

def city_timezone(city_name):
    """Return tz_offset string for a city, e.g. '+06:00'"""
    entry = CITIES.get(city_name)
    if entry and len(entry) == 3:
        return entry[2]
    # fallback device tz
    now_local = datetime.now().astimezone()
    raw = now_local.strftime('%z')
    return raw[:3] + ":" + raw[3:]

def _run_with_spinner(label, cmd, timeout_s):
    """Run subprocess with animated spinner. Returns (returncode, stdout, stderr)"""
    stop_evt = threading.Event()

    def spin_thread():
        spin  = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        i     = 0
        start = time.time()
        while not stop_evt.is_set():
            elapsed = time.time() - start
            pct     = min(99, int(elapsed / timeout_s * 100))
            filled  = int(30 * pct / 100)
            bar     = C.GREEN + "█" * filled + C.DIM + "░" * (30 - filled) + C.RESET
            sys.stdout.write(
                f"\r  {color(spin[i%len(spin)], C.CYAN, C.BOLD)}  "
                f"{color(label, C.WHITE):<30} "
                f"[{bar}] {color(f'{pct:3d}%', C.GREEN, C.BOLD)}"
            )
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 72 + "\r")
        sys.stdout.flush()

    t = threading.Thread(target=spin_thread, daemon=True)
    t.start()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        stop_evt.set(); t.join()
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        stop_evt.set(); t.join()
        return -1, "", "timeout"
    except Exception as e:
        stop_evt.set(); t.join()
        return -1, "", str(e)


def check_internet():
    """Quick internet check"""
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
            capture_output=True, timeout=3
        )
        if r.returncode == 0:
            return True
    except:
        pass
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "3", "-o", "/dev/null",
             "-w", "%{http_code}", "http://connectivitycheck.gstatic.com/generate_204"],
            capture_output=True, text=True, timeout=4
        )
        if r.stdout.strip() in ("204", "200"):
            return True
    except:
        pass
    return False


def check_termux_api():
    """Check if termux-location is available"""
    if not shutil.which("termux-location"):
        warn("termux-location not found!")
        warn("Fix: pkg install termux-api")
        warn("Fix: Install Termux:API app from F-Droid")
        return False
    return True



def get_location_wifi_tower():
    """
    Get location via WiFi + mobile tower using Google Geolocation API (free tier).
    No API key needed for basic requests.
    """
    try:
        # Get WiFi info via termux-wifi-scaninfo
        wifi_data = []
        rc_w, out_w, _ = _run_with_spinner("Scanning WiFi...", [
            "termux-wifi-scaninfo"
        ], 4)
        if rc_w == 0 and out_w.strip():
            try:
                wlist = json.loads(out_w)
                for ap in wlist[:5]:
                    bssid = ap.get("bssid", "")
                    rssi  = ap.get("level", -70)
                    if bssid:
                        wifi_data.append({
                            "macAddress": bssid,
                            "signalStrength": rssi
                        })
            except:
                pass

        if not wifi_data:
            return None, None, None

        payload = json.dumps({"wifiAccessPoints": wifi_data})
        import urllib.request
        req = urllib.request.Request(
            "https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY",
            data=payload.encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            loc  = data.get("location", {})
            lat  = str(loc.get("lat", ""))
            lon  = str(loc.get("lng", ""))
            if lat and lon:
                return lat, lon, "WiFi/Tower"
    except:
        pass
    return None, None, None

def get_location_by_ip():
    """IP-based location - curl + urllib fallback"""
    apis = [
        ("http://ip-api.com/json/",   "lat",       "lon",       "city", "country"),
        ("https://ipapi.co/json/",    "latitude",  "longitude", "city", "country_name"),
        ("https://ipinfo.io/json",    None,         None,        "city", "country"),
    ]
    for url, lat_key, lon_key, city_key, country_key in apis:
        out = None
        rc, curl_out, _ = _run_with_spinner("IP location...", [
            "curl", "-s", "--max-time", "3", "-A",
            "Mozilla/5.0 (Linux; Android 13)", url
        ], 4)
        if rc == 0 and curl_out.strip():
            out = curl_out
        if not out:
            try:
                import urllib.request
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13)"}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    out = resp.read().decode()
            except:
                pass
        if not out:
            continue
        try:
            data = json.loads(out)
            if data.get("status") == "fail":
                continue
            if lat_key is None and "loc" in data:
                parts = data["loc"].split(",")
                if len(parts) != 2: continue
                lat, lon = parts[0].strip(), parts[1].strip()
            else:
                lat = str(data.get(lat_key, ""))
                lon = str(data.get(lon_key, ""))
            city    = data.get(city_key,    "")
            country = data.get(country_key, "")
            if lat and lon and lat not in ("", "0", "0.0"):
                label = f"{city}, {country}".strip(", ")
                return lat, lon, label
        except:
            pass
    return None, None, None


def get_location_by_timezone():
    """Pick city matching device timezone offset"""
    try:
        now_local  = datetime.now().astimezone()
        dev_offset = now_local.strftime('%z')          # e.g. +0600
        dev_tz_str = dev_offset[:3] + ":" + dev_offset[3:]  # +06:00

        matches = [
            (name, lat, lon, tz)
            for name, (lat, lon, tz) in CITIES.items()
            if tz == dev_tz_str
        ]
        if matches:
            name, lat, lon, tz = random.choice(matches)
            info(f"Timezone {dev_tz_str} -> {name}")
            return lat, lon, name
    except:
        pass
    return random_city()


def get_auto_gps():
    """Smart GPS detection with diagnostics"""
    online = check_internet()
    info(f"Internet: {'Online' if online else 'Offline'}")

    has_api = check_termux_api()

    if has_api:
        if online:
            providers    = [("gps", 8), ("network", 4)]
            total_budget = 12
        else:
            providers    = [("gps", 8), ("passive", 4)]
            total_budget = 12

        start = time.time()
        for provider, budget in providers:
            if time.time() - start >= total_budget:
                break
            remaining = min(budget, total_budget - (time.time() - start))
            rc, out, stderr = _run_with_spinner(
                f"GPS ({provider})...",
                ["termux-location", "-p", provider, "-r", "once"],
                remaining
            )
            if rc == 0 and out.strip():
                try:
                    data = json.loads(out)
                    lat  = str(data.get("latitude",  ""))
                    lon  = str(data.get("longitude", ""))
                    acc  = data.get("accuracy", "?")
                    if lat and lon and float(lat) != 0.0:
                        ok(f"GPS ({provider}): {lat}, {lon}  acc={acc}m")
                        return lat, lon, "GPS Auto"
                    else:
                        warn(f"GPS ({provider}): coordinates are 0.0")
                except Exception as e:
                    warn(f"GPS ({provider}): parse error - {e}")
            else:
                diag = stderr.strip()[:100] if stderr.strip() else "no output / timeout"
                warn(f"GPS ({provider}): {diag}")

    if online:
        # Try WiFi + tower location first (faster than IP)
        info("Trying WiFi/Tower location...")
        lat, lon, label = get_location_wifi_tower()
        if lat:
            ok(f"WiFi/Tower: {label} ({lat}, {lon})")
            return lat, lon, label

        info("Trying IP-based location...")
        lat, lon, label = get_location_by_ip()
        if lat:
            ok(f"IP location: {label} ({lat}, {lon})")
            return lat, lon, label
        warn("IP location failed")

    warn("Using timezone-based location...")
    return get_location_by_timezone()



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


def get_timezone_offset(lat_f=None, lon_f=None):
    """
    Get timezone from GPS coordinates via online API.
    Falls back to device timezone if offline or API fails.
    """
    if lat_f is not None and lon_f is not None:
        # Try TimeZoneDB API (free, no key needed for basic)
        apis = [
            f"http://api.timezonedb.com/v2.1/get-time-zone?key=VGSWLNI6Y62E&format=json&by=position&lat={lat_f}&lng={lon_f}",
            f"https://timeapi.io/api/timezone/coordinate?latitude={lat_f}&longitude={lon_f}",
        ]
        for url in apis:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())

                    # TimeZoneDB response
                    if "gmtOffset" in data:
                        total_s = int(data["gmtOffset"])
                        h, m    = divmod(abs(total_s) // 60, 60)
                        sign    = "+" if total_s >= 0 else "-"
                        tz_str  = f"{sign}{h:02d}:{m:02d}"
                        tz_name = data.get("zoneName", tz_str)
                        from datetime import timezone as _tz, timedelta
                        tz      = _tz(timedelta(seconds=total_s))
                        loc_now = datetime.now(tz)
                        ok(f"Timezone: {tz_name} ({tz_str})")
                        return loc_now, tz_str, tz_name

                    # timeapi.io response
                    if "utcOffset" in data:
                        tz_str  = data["utcOffset"]    # e.g. "+06:00"
                        tz_name = data.get("timeZone", tz_str)
                        try:
                            sign = 1 if tz_str[0] == "+" else -1
                            h, m = map(int, tz_str[1:].split(":"))
                            from datetime import timezone as _tz, timedelta
                            tz      = _tz(timedelta(hours=h, minutes=m) * sign)
                            loc_now = datetime.now(tz)
                            ok(f"Timezone: {tz_name} ({tz_str})")
                            return loc_now, tz_str, tz_name
                        except:
                            pass
            except:
                pass

    # Fallback: device timezone
    now_local = datetime.now().astimezone()
    raw    = now_local.strftime('%z')
    tz_str = raw[:3] + ":" + raw[3:]
    return now_local, tz_str, tz_str

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

    # GPS timestamp always UTC (timezone-aware, no deprecation warning)
    from datetime import timezone as _tz_utc
    utc_now = datetime.now(_tz_utc.utc)

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
def main(skip_update=False):
    os.system("clear")
    banner()

    # ── Auto Update Check (only on first run) ──
    if not skip_update:
        section("Update Check")
        check_update()

    tools = check_tools()

    # ── File Selection ──
    section("File Selection")
    print(color("  [1]", C.CYAN, C.BOLD) + color("  Browse /sdcard (folder navigator)", C.WHITE))
    print(color("  [2]", C.CYAN, C.BOLD) + color("  Manual path input", C.WHITE))
    print(color("  [0]", C.CYAN, C.BOLD) + color("  Exit", C.WHITE))
    file_mode = prompt("Select option [1/2/0]:", "1")
    if file_mode == "0":
        print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)

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
    print(color("\n  [0]  Exit", C.YELLOW))
    choice = prompt("Select device number [0=Exit]:")
    if choice == "0":
        print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)
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
        "0": "Exit",
    }
    gps_choice = menu("GPS / Location", GPS_OPTS)
    if gps_choice == "0":
        print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)

    city_name = ""
    if gps_choice == "1":
        lat, lon, city_name = get_auto_gps()
        ok(f"Location: {city_name} ({lat}, {lon})")
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
                    lat_c, lon_c, _tz_c = CITIES[c]
                    print(color(f"    [{n:>2}]", C.CYAN, C.BOLD) +
                          color(f"  {c:30s}", C.WHITE) +
                          color(f"({lat_c}, {lon_c})", C.DIM))
        cidx = prompt("Enter city number:")
        try:
            city_name = city_list[int(cidx) - 1]
            lat, lon, _tz_sel = CITIES[city_name]
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

    # Run again or exit
    again = prompt("Process more files? [y/n]:", "n")
    if again.lower() == "y":
        main(skip_update=True)

if __name__ == "__main__":
    main()