#!/usr/bin/env python3

# ─────────────────────────────────────────────
CURRENT_VERSION = "2.6"
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
# 📦 Auto-install rich if missing
# ─────────────────────────────────────────────
def _ensure_rich():
    try:
        import rich
    except ImportError:
        print("[*] Installing rich...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"])

_ensure_rich()

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
# 📊 Rich Progress Bar Helper
# ─────────────────────────────────────────────
from rich.progress import (
    Progress, SpinnerColumn, BarColumn,
    TextColumn, TimeElapsedColumn, TaskProgressColumn,
    MofNCompleteColumn, ProgressColumn
)
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_console = Console()


def make_progress(description="Processing..."):
    return Progress(
        SpinnerColumn(spinner_name="moon", style="bold green"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=40,style="red", complete_style="green", finished_style="bold green"),
        TextColumn("[white]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
        transient=False,
    )


def run_with_rich_progress(label, cmd, start_pct=0, end_pct=100):
    with make_progress() as prog:
        task = prog.add_task(label, total=100)
        prog.update(task, completed=start_pct)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        span    = end_pct - start_pct
        current = start_pct

        while proc.poll() is None:
            if current < end_pct - 5:
                current += max(1, span // 20)
                prog.update(task, completed=current)
            time.sleep(0.35)

        stdout, stderr = proc.communicate()
        prog.update(task, completed=100)
        return proc.returncode, stderr.decode()


def rich_progress_steps(steps):
    results = []
    total   = len(steps)
    with make_progress() as prog:
        task = prog.add_task("", total=total)
        for i, (label, fn) in enumerate(steps):
            prog.update(task, description=f"[bold white]{label}")
            try:
                r = fn()
            except Exception as e:
                r = False
            results.append(r)
            prog.update(task, advance=1)
    return results


# ─────────────────────────────────────────────
# 🔄 Auto Update System
# ─────────────────────────────────────────────
def check_update():
    try:
        import urllib.request
        req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "MetaForge-Updater"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            latest = resp.read().decode().strip()

        if latest == CURRENT_VERSION:
            ok(f"Already up to date (v{CURRENT_VERSION})")
            return False

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

        info("Downloading update...")
        import stat
        running_path = os.path.abspath(__file__)
        prefix_bin   = os.path.join(os.environ.get("PREFIX", "/usr"), "bin", "metaforge")
        usr_bin      = "/usr/local/bin/metaforge"

        paths_to_update = set()
        paths_to_update.add(os.path.realpath(running_path))
        for gpath in [prefix_bin, usr_bin]:
            if os.path.exists(gpath):
                paths_to_update.add(os.path.realpath(gpath))

        script_path = running_path
        backup_path = script_path + ".backup"

        req2 = urllib.request.Request(SCRIPT_URL, headers={"User-Agent": "MetaForge-Updater"})

        with make_progress() as prog:
            task = prog.add_task("Downloading update...", total=100)
            with urllib.request.urlopen(req2, timeout=30) as resp:
                new_code = resp.read()
            prog.update(task, completed=70, description="Downloaded ✔")
            shutil.copy2(script_path, backup_path)
            prog.update(task, completed=85, description="Backup created...")

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
            prog.update(task, completed=100, description="Update complete ✔")

        ok(f"Updated to v{latest}")
        ok(f"Backup saved: {backup_path}")
        print(color("\n  Restart script to use new version\n", C.CYAN, C.BOLD))
        exit(0)

    except Exception as e:
        warn(f"Update check failed: {e}")
        return False


def banner():
    print(color("""
╔══════════════════════════════════════════════════════╗
║  ███╗   ███╗███████╗████████╗ █████╗                 ║
║  ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗                ║
║  ██╔████╔██║█████╗     ██║   ███████║                 ║
║  ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║                 ║
║  ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║                 ║
║  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝  FORGE v2.6   ║
╠══════════════════════════════════════════════════════╣
║       EXIF • GPS • Device Metadata Injector          ║
╠══════════════════════════════════════════════════════╣
║  Developer : Forrukh (FmIt)                          ║
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
    default_hint = color(f" [{default}]", C.DIM) if default != "" else ""
    val = input(f"{arrow}{color(msg, C.WHITE)}{default_hint} ").strip()
    return val if val else default


def menu(title, options: dict, prompt_text="Select", default_key=None):
    section(title)
    keys_list = list(options.keys())
    auto_key  = default_key if default_key else keys_list[0]

    for k, v in options.items():
        label = v[0] if isinstance(v, tuple) else v
        marker = color(" ◄ default", C.DIM) if k == auto_key else ""
        print(color(f"  [{k}]", C.CYAN, C.BOLD) + color(f"  {label}", C.WHITE) + marker)

    choice = prompt(f"{prompt_text} [1-{len(options)}] (Enter={auto_key}):", auto_key)
    return choice if choice in options else auto_key


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
    "Cairo, Egypt":             ("30.0444",  "31.2357",   "+02:00"),
    "Lagos, Nigeria":           ("6.5244",   "3.3792",    "+01:00"),
    "Nairobi, Kenya":           ("-1.2921",  "36.8219",   "+03:00"),
    "Casablanca, Morocco":      ("33.5731",  "-7.5898",   "+01:00"),
    "Johannesburg, S. Africa":  ("-26.2041", "28.0473",   "+02:00"),
    "Addis Ababa, Ethiopia":    ("9.0320",   "38.7469",   "+03:00"),
    "London, UK":               ("51.5074",  "-0.1278",   "+01:00"),
    "Paris, France":            ("48.8566",  "2.3522",    "+02:00"),
    "Berlin, Germany":          ("52.5200",  "13.4050",   "+02:00"),
    "Rome, Italy":              ("41.9028",  "12.4964",   "+02:00"),
    "Madrid, Spain":            ("40.4168",  "-3.7038",   "+02:00"),
    "Moscow, Russia":           ("55.7558",  "37.6173",   "+03:00"),
    "Amsterdam, Netherlands":   ("52.3676",  "4.9041",    "+02:00"),
    "Stockholm, Sweden":        ("59.3293",  "18.0686",   "+02:00"),
    "New York, USA":            ("40.7128",  "-74.0060",  "-04:00"),
    "Los Angeles, USA":         ("34.0522",  "-118.2437", "-07:00"),
    "Chicago, USA":             ("41.8781",  "-87.6298",  "-05:00"),
    "Toronto, Canada":          ("43.6532",  "-79.3832",  "-04:00"),
    "Mexico City, Mexico":      ("19.4326",  "-99.1332",  "-06:00"),
    "Sao Paulo, Brazil":        ("-23.5505", "-46.6333",  "-03:00"),
    "Buenos Aires, Argentina":  ("-34.6037", "-58.3816",  "-03:00"),
    "Bogota, Colombia":         ("4.7110",   "-74.0721",  "-05:00"),
    "Sydney, Australia":        ("-33.8688", "151.2093",  "+10:00"),
    "Melbourne, Australia":     ("-37.8136", "144.9631",  "+10:00"),
}


def random_city():
    city = random.choice(list(CITIES.keys()))
    lat, lon, tz = CITIES[city]
    info(f"Random city → {city} ({lat}, {lon})")
    return lat, lon, city


def get_location_by_ip():
    apis = [
        ("http://ip-api.com/json/",   "lat",       "lon",       "city", "country"),
        ("https://ipapi.co/json/",    "latitude",  "longitude", "city", "country_name"),
        ("https://ipinfo.io/json",    None,         None,        "city", "country"),
    ]

    _console.print("[cyan]  ℹ  Trying IP-based location...[/cyan]")

    for url, lat_key, lon_key, city_key, country_key in apis:
        out = None
        try:
            r = subprocess.run(
                ["curl", "-s", "--max-time", "4", "-A",
                 "Mozilla/5.0 (Linux; Android 13)", url],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                out = r.stdout
        except Exception:
            pass

        if not out:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    out = resp.read().decode()
            except Exception:
                pass

        if not out:
            continue
        try:
            data = json.loads(out)
            if data.get("status") == "fail":
                continue
            if lat_key is None and "loc" in data:
                parts = data["loc"].split(",")
                if len(parts) != 2:
                    continue
                lat, lon = parts[0].strip(), parts[1].strip()
            else:
                lat = str(data.get(lat_key, ""))
                lon = str(data.get(lon_key, ""))
            city    = data.get(city_key, "")
            country = data.get(country_key, "")
            if lat and lon and lat not in ("", "0", "0.0"):
                label = f"{city}, {country}".strip(", ")
                ok(f"IP location: {label} ({lat}, {lon})")
                return lat, lon, label
        except Exception:
            pass
    return None, None, None


def get_location_by_timezone():
    try:
        now_local  = datetime.now().astimezone()
        dev_offset = now_local.strftime('%z')
        dev_tz_str = dev_offset[:3] + ":" + dev_offset[3:]
        matches = [
            (name, lat, lon, tz)
            for name, (lat, lon, tz) in CITIES.items()
            if tz == dev_tz_str
        ]
        if matches:
            name, lat, lon, tz = random.choice(matches)
            info(f"Timezone {dev_tz_str} → {name}")
            return lat, lon, name
    except Exception:
        pass
    return random_city()


def check_internet():
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", "8.8.8.8"],
                           capture_output=True, timeout=3)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "3", "-o", "/dev/null",
             "-w", "%{http_code}", "http://connectivitycheck.gstatic.com/generate_204"],
            capture_output=True, text=True, timeout=4)
        if r.stdout.strip() in ("204", "200"):
            return True
    except Exception:
        pass
    return False


def check_termux_api():
    if not shutil.which("termux-location"):
        warn("termux-location not found!")
        warn("Fix: pkg install termux-api")
        warn("Fix: Install Termux:API app from F-Droid")
        return False
    return True


# ─────────────────────────────────────────────
# 📍 GPS: 10-second timeout with rich progress
# ─────────────────────────────────────────────
def _run_termux_location(provider, timeout_s):
    result_holder = [None]

    def _worker():
        try:
            r = subprocess.run(
                ["termux-location", "-p", provider, "-r", "once"],
                capture_output=True, text=True, timeout=timeout_s + 2
            )
            result_holder[0] = (r.returncode, r.stdout, r.stderr)
        except subprocess.TimeoutExpired:
            result_holder[0] = (-1, "", "timeout")
        except Exception as e:
            result_holder[0] = (-1, "", str(e))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    with make_progress() as prog:
        task = prog.add_task(
            f"[bold cyan]GPS ({provider}) — {timeout_s}s timeout...",
            total=timeout_s * 10
        )
        elapsed_steps = 0
        while t.is_alive() and elapsed_steps < timeout_s * 10:
            time.sleep(0.1)
            elapsed_steps += 1
            prog.update(task, advance=1)
        prog.update(task, completed=timeout_s * 10)

    t.join(timeout=2)
    if result_holder[0] is None:
        return -1, "", "no result"
    return result_holder[0]


def get_auto_gps():
    online  = check_internet()
    has_api = check_termux_api()
    info(f"Internet: {'Online' if online else 'Offline'}")

    if has_api:
        for provider in ["gps", "network"]:
            info(f"Trying GPS provider: {provider} (5s timeout)...")
            rc, out, stderr = _run_termux_location(provider, 5)

            if rc == 0 and out.strip():
                try:
                    data = json.loads(out)
                    lat  = str(data.get("latitude",  ""))
                    lon  = str(data.get("longitude", ""))
                    acc  = data.get("accuracy", "?")
                    if lat and lon and float(lat) != 0.0:
                        ok(f"GPS ({provider}): {lat}, {lon}  accuracy={acc}m")
                        return lat, lon, "GPS Auto"
                    else:
                        warn(f"GPS ({provider}): coordinates returned 0.0")
                except Exception as e:
                    warn(f"GPS ({provider}): parse error — {e}")
            else:
                diag = stderr.strip()[:80] if stderr.strip() else "no output / timeout"
                warn(f"GPS ({provider}): {diag}")

    if online:
        lat, lon, label = get_location_by_ip()
        if lat:
            return lat, lon, label
        warn("IP location failed")

    warn("Using timezone-based location fallback...")
    return get_location_by_timezone()


# ─────────────────────────────────────────────
# 🖥️ Platform Detection
# ─────────────────────────────────────────────
def is_termux():
    """Return True if running inside Termux/Android."""
    return (
        os.path.exists("/data/data/com.termux") or
        "com.termux" in os.environ.get("PREFIX", "") or
        os.path.exists("/data/data/com.termux/files/usr")
    )


def get_browse_root():
    """
    Return the starting directory for the file browser.
      Termux  → /sdcard
      Linux   → home directory
    """
    if is_termux():
        return "/sdcard"
    return os.path.expanduser("~")


def get_output_dir():
    """
    Return default output directory.
      Termux  → /sdcard/meta
      Linux   → ~/meta_output
    """
    if is_termux():
        return "/sdcard/meta"
    return os.path.join(os.path.expanduser("~"), "meta_output")


# ─────────────────────────────────────────────
# 🎬 VIDEO Processing
# ─────────────────────────────────────────────
def process_video(file_path, brand, model, lat, lon, output_path, tools, now):
    fname = os.path.basename(file_path)
    info(f"Video → {fname}")

    if tools["ffmpeg"]:
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", file_path
        ]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True)
        orig_bitrate       = "8000k"
        orig_audio_bitrate = "192k"
        try:
            pdata       = json.loads(probe.stdout)
            fmt_bitrate = int(pdata.get("format", {}).get("bit_rate", 0))
            if fmt_bitrate > 0:
                vbr = max(6000, min(20000, fmt_bitrate // 1000))
                orig_bitrate = f"{vbr}k"
            for stream in pdata.get("streams", []):
                if stream.get("codec_type") == "audio":
                    abr = int(stream.get("bit_rate", 192000)) // 1000
                    orig_audio_bitrate = f"{max(128, min(320, abr))}k"
        except Exception:
            pass

        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-map_metadata", "-1",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.2",
            "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "16",
            "-b:v", orig_bitrate, "-maxrate", orig_bitrate,
            "-bufsize", f"{int(orig_bitrate[:-1])*2}k",
            "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", orig_audio_bitrate, "-ar", "48000", "-ac", "2",
            "-metadata", f"make={brand}",
            "-metadata", f"model={model}",
            "-metadata", f"creation_time={now}",
            "-metadata", f"location={lat},{lon}",
            "-metadata", f"com.apple.quicktime.location.ISO6709=+{lat}+{lon}/",
            "-metadata:s:v:0", "handler_name=VideoHandle",
            "-metadata:s:a:0", "handler_name=SoundHandle",
            output_path
        ]
        rc, stderr = run_with_rich_progress("ffmpeg encoding...", cmd, 5, 70)
        if rc != 0:
            err(f"ffmpeg failed:\n{stderr[-300:]}")
            return False
    else:
        shutil.copy2(file_path, output_path)
        warn("ffmpeg not found — copied original")

    if tools["exiftool"]:
        lat_f, lon_f = float(lat), float(lon)
        lat_ref = "N" if lat_f >= 0 else "S"
        lon_ref = "E" if lon_f >= 0 else "W"
        et_cmd = [
            "exiftool", "-overwrite_original",
            f"-Make={brand}", f"-Model={model}",
            f"-DateTimeOriginal={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-CreateDate={datetime.now().strftime('%Y:%m:%d %H:%M:%S')}",
            f"-GPSLatitude={abs(lat_f)}", f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon_f)}", f"-GPSLongitudeRef={lon_ref}",
            f"-Software={brand} Camera",
            output_path
        ]
        rc2, se2 = run_with_rich_progress("Injecting metadata...", et_cmd, 72, 98)
        if rc2 == 0:
            ok("exiftool: metadata injected ✔")
        else:
            warn(f"exiftool: {se2[:150]}")

    return True


# ─────────────────────────────────────────────
# 🖼️ IMAGE Processing
# ─────────────────────────────────────────────
def get_timezone_offset(lat_f=None, lon_f=None):
    if lat_f is not None and lon_f is not None:
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
                if "utcOffset" in data:
                    tz_str  = data["utcOffset"]
                    tz_name = data.get("timeZone", tz_str)
                    sign    = 1 if tz_str[0] == "+" else -1
                    h, m    = map(int, tz_str[1:].split(":"))
                    from datetime import timezone as _tz, timedelta
                    tz      = _tz(timedelta(hours=h, minutes=m) * sign)
                    loc_now = datetime.now(tz)
                    ok(f"Timezone: {tz_name} ({tz_str})")
                    return loc_now, tz_str, tz_name
            except Exception:
                pass

    now_local = datetime.now().astimezone()
    raw       = now_local.strftime('%z')
    tz_str    = raw[:3] + ":" + raw[3:]
    return now_local, tz_str, tz_str


def process_image(file_path, brand, model, lat, lon, output_path, tools, now):
    fname = os.path.basename(file_path)
    info(f"Image → {fname}")

    shutil.copy2(file_path, output_path)

    lat_f, lon_f = float(lat), float(lon)
    loc_now, tz_str, tz_name = get_timezone_offset(lat_f, lon_f)
    info(f"Location TZ: {tz_name} ({tz_str})")

    dt_str    = loc_now.strftime('%Y:%m:%d %H:%M:%S')
    dt_tz_str = dt_str + tz_str

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
            f"-Make={brand}", f"-Model={model}",
            f"-LensModel={brand} {focal}mm f/{float(fstop.split('/')[0])/float(fstop.split('/')[1]):.1f}",
            f"-FocalLength={focal}", f"-FNumber={fstop}",
            f"-ISO={iso}", f"-ExposureTime={shutter}",
            f"-Software={brand} Camera",
            f"-DateTimeOriginal={dt_tz_str}",
            f"-CreateDate={dt_tz_str}",
            f"-ModifyDate={dt_tz_str}",
            f"-GPSLatitude={abs(lat_f)}", f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs(lon_f)}", f"-GPSLongitudeRef={lon_ref}",
            f"-GPSAltitude=15", f"-GPSAltitudeRef=0",
            f"-GPSTimeStamp={utc_now.strftime('%H:%M:%S')}",
            f"-GPSDateStamp={utc_now.strftime('%Y:%m:%d')}",
            f"-ImageDescription=Shot on {brand} {model}",
            f"-Comment=Shot on {brand} {model}",
            f"-Artist={brand}",
            f"-Copyright={brand} {datetime.now().year}",
            f"-ProfileDescription={brand} {model}",
            f"-XMP:DeviceManufacturer={brand}",
            f"-XMP:DeviceModel={model}",
            f"-XMP-tiff:Make={brand}", f"-XMP-tiff:Model={model}",
            "-JpegQuality=95",
            output_path
        ]
        rc, stderr = run_with_rich_progress("Injecting EXIF...", cmd, 10, 88)
        if rc == 0:
            icc_cmd = [
                "exiftool", "-overwrite_original",
                f"-ICC_Profile:DeviceManufacturer={brand[:4].ljust(4)}",
                f"-ICC_Profile:DeviceModel={model[:4].ljust(4)}",
                f"-ICC_Profile:ProfileDescription={brand} {model}",
                output_path
            ]
            subprocess.run(icc_cmd, capture_output=True)
            ok("exiftool: metadata injected ✔")
            return True
        else:
            warn(f"exiftool error: {stderr[:200]}")

    info("PIL fallback...")
    try:
        from PIL import Image
        import piexif
        from piexif.helper import deg_to_dms_rational

        img      = Image.open(file_path)
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make]              = brand.encode()
        exif_dict["0th"][piexif.ImageIFD.Model]             = model.encode()
        exif_dict["0th"][piexif.ImageIFD.Software]          = f"{brand} Camera".encode()
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal]  = dt_str.encode()
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = dt_str.encode()
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude]         = deg_to_dms_rational(lat_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef]      = ("N" if lat_f >= 0 else "S").encode()
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude]        = deg_to_dms_rational(lon_f)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef]     = ("E" if lon_f >= 0 else "W").encode()
        exif_bytes = piexif.dump(exif_dict)
        img.save(output_path, exif=exif_bytes, quality=95, optimize=False, subsampling=0)
        ok("PIL/piexif fallback: done ✔")
        return True
    except Exception as e:
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

    if not skip_update:
        section("Update Check")
        check_update()

    tools = check_tools()

    # ── Platform detect ──
    _termux = is_termux()
    _browse_root = get_browse_root()
    platform_label = "Termux/Android" if _termux else "Linux/Desktop"
    info(f"Platform: {platform_label}")

    # ── File Selection ──
    section("File Selection")
    if _termux:
        opt1_label = "Browse /sdcard (folder navigator)"
    else:
        opt1_label = f"Browse {_browse_root} (folder navigator)"

    print(color("  [1]", C.CYAN, C.BOLD) + color(f"  {opt1_label}", C.WHITE) +
          color(" ◄ default", C.DIM))
    print(color("  [2]", C.CYAN, C.BOLD) + color("  Manual path input", C.WHITE))
    print(color("  [0]", C.CYAN, C.BOLD) + color("  Exit", C.WHITE))
    file_mode = prompt("Select option [1/2/0] (Enter=1):", "1")
    if file_mode == "0":
        print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)

    valid_files = []
    MEDIA_EXT = (".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png")

    if file_mode == "1":
        def scan_folder_with_progress(path):
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
                sys.stdout.write(
                    f"\r  {color(spin[spin_i % len(spin)], C.CYAN, C.BOLD)}  "
                    f"{color('Scanning: ', C.DIM)}{color(e[:40], C.WHITE):<42}"
                )
                sys.stdout.flush()
                spin_i += 1
                if os.path.isdir(full):
                    has_media = False
                    try:
                        for root, _, fnames in os.walk(full):
                            if any(f.lower().endswith(MEDIA_EXT) for f in fnames):
                                has_media = True; break
                    except Exception:
                        pass
                    if has_media:
                        dirs_with_media.append(e)
                elif e.lower().endswith(MEDIA_EXT):
                    media_files.append(e)

            sys.stdout.write(
                f"\r  {color('✔', C.GREEN, C.BOLD)}  "
                f"{color(f'Found {len(dirs_with_media)} folder(s), {len(media_files)} file(s)', C.GREEN):<50}\n"
            )
            sys.stdout.flush()
            return dirs_with_media, media_files

        def browse_folder(current_path):
            while True:
                os.system("clear")
                banner()
                section(f"Browser: {current_path}")
                dirs_with_media, media_files = scan_folder_with_progress(current_path)

                # ── Permission / empty check ──
                if not dirs_with_media and not media_files:
                    if current_path == "/sdcard":
                        err("Permission denied! Run: termux-setup-storage")
                    else:
                        err(f"No media files found in: {current_path}")
                        warn("Supported: .mp4 .mov .mkv .jpg .jpeg .png")
                    ch = prompt("Go back? [y/n] (Enter=y):", "y")
                    if ch.lower() == "y":
                        parent = os.path.dirname(current_path)
                        if parent == current_path:
                            return []
                        current_path = parent
                        continue
                    return []

                items = []
                if current_path != _browse_root:
                    print(color("  [ 0]", C.YELLOW, C.BOLD) + color("  [..] Back", C.YELLOW))
                for d in dirs_with_media:
                    idx = len(items) + 1
                    items.append((d, os.path.join(current_path, d), True))
                    print(color(f"  [{idx:>3}]", C.CYAN, C.BOLD) + color(f"  [DIR]  {d}", C.CYAN))
                for f in media_files:
                    idx = len(items) + 1
                    ext = os.path.splitext(f)[1].upper().replace(".", "")
                    ec  = C.MAGENTA if ext in ("MP4","MOV","MKV") else C.GREEN
                    items.append((f, os.path.join(current_path, f), False))
                    print(color(f"  [{idx:>3}]", C.CYAN, C.BOLD) +
                          color(f"  [{ext}]  ", ec) + color(f"{f}", C.WHITE))

                print()
                print(color("  [*] Select ALL files in this folder", C.DIM))
                print(color("  Multi: 2,3,5  |  Range: 2-6  |  0=Back", C.DIM))
                sel = prompt("Enter number(s):")

                if sel.strip() == "0":
                    parent = os.path.dirname(current_path)
                    if parent == current_path:
                        return []
                    current_path = parent
                    continue
                if sel.strip() == "*":
                    selected = [it[1] for it in items if not it[2]]
                    if selected:
                        return selected
                    warn("No files in this folder"); continue

                chosen_idx = set()
                for part in sel.split(","):
                    part = part.strip()
                    if "-" in part:
                        try:
                            a, b = part.split("-")
                            chosen_idx.update(range(int(a), int(b)+1))
                        except Exception:
                            warn(f"Invalid range: {part}")
                    else:
                        try:
                            chosen_idx.add(int(part))
                        except Exception:
                            warn(f"Invalid: {part}")

                result_files = []
                enter_dir    = None
                for idx in sorted(chosen_idx):
                    if 1 <= idx <= len(items):
                        name, path, is_dir = items[idx-1]
                        if is_dir:
                            enter_dir = path
                        else:
                            result_files.append(path)
                    else:
                        warn(f"No item at {idx}")

                if result_files:
                    return result_files
                elif enter_dir:
                    current_path = enter_dir; continue
                else:
                    warn("Nothing selected")

        valid_files = browse_folder(_browse_root) or []

    else:
        # ── Manual path input ──
        if _termux:
            hint = "/sdcard/DCIM/photo.jpg"
        else:
            hint = f"{os.path.expanduser('~')}/Pictures/photo.jpg"
        info(f"Example: {hint}")
        user_input = prompt("File path / multiple (,) / folder:")
        if not user_input:
            err("No path entered!"); exit(1)
        if os.path.isdir(user_input):
            raw = [os.path.join(user_input, f) for f in os.listdir(user_input)
                   if f.lower().endswith(MEDIA_EXT)]
            valid_files = [f for f in raw if os.path.exists(f)]
            info(f"Found {len(valid_files)} files in folder")
        else:
            paths = [f.strip() for f in user_input.split(",") if f.strip()]
            valid_files = [f for f in paths if os.path.exists(f)]
            missing = [f for f in paths if not os.path.exists(f)]
            for m in missing:
                warn(f"File not found: {m}")

    if not valid_files:
        err("No valid files selected!"); exit(1)
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
    line = "─" * 62
    print(color(f"\n  ┌{line}┐", C.YELLOW))
    print(color(f"  │ {'No':<4} {'Device':<27} │ {'No':<4} {'Device':<27}│", C.WHITE, C.BOLD))
    print(color(f"  ├{line}┤", C.YELLOW))
    for cat, keys in categories.items():
        print(color(f"  │ {cat:<60} │", C.YELLOW, C.BOLD))
        pairs = [keys[i:i+2] for i in range(0, len(keys), 2)]
        for pair in pairs:
            left_k  = pair[0]
            left_l  = DEVICES[left_k][0]
            right_k = pair[1] if len(pair) > 1 else ""
            right_l = DEVICES[right_k][0] if right_k else ""
            left_cell  = color(f"[{left_k:>2}]",  C.CYAN, C.BOLD) + color(f" {left_l:<25}", C.WHITE)
            right_cell = (color(f"[{right_k:>2}]", C.CYAN, C.BOLD) + color(f" {right_l:<25}", C.WHITE)) if right_k else color(f"{'':30}", C.WHITE)
            print(f"  │ {left_cell} │ {right_cell}│")
        print(color(f"  ├{line}┤", C.YELLOW))
    print(color(f"  └{line}┘", C.YELLOW))

    print(color("\n  [0]  Exit", C.YELLOW))
    print(color("  (Enter = Auto-detect, option 1)", C.DIM))
    choice = prompt("Select device number [0=Exit] (Enter=1):", "1")
    if choice == "0":
        print(color("\n  Goodbye!\n", C.CYAN, C.BOLD)); exit(0)
    if choice not in DEVICES:
        err("Invalid device choice"); exit(1)

    if choice == "1":
        if _termux:
            try:
                brand = subprocess.check_output("getprop ro.product.brand", shell=True).decode().strip()
                model = subprocess.check_output("getprop ro.product.model", shell=True).decode().strip()
                ok(f"Detected: {brand} {model}")
            except Exception:
                brand, model = "Android", "Device"
        else:
            warn("Auto-detect not available on Linux → using default")
            brand, model = "Samsung", "SM-S938B"
            info(f"Default: {brand} {model}  (choose Custom [32] to override)")
    elif DEVICES[choice][1] == "CUSTOM":
        brand = prompt("Enter Brand (e.g. Samsung):", "Samsung")
        model = prompt("Enter Model (e.g. SM-A546E):", "SM-A546E")
    else:
        brand, model = DEVICES[choice][1]
        ok(f"Selected: {brand} {model}")

    # ── GPS Selection ──
    GPS_OPTS = {
        "1": "Auto GPS (termux-location + IP fallback)",
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
            "🌏 Asia":     list(range(1, 27)),
            "🌍 Africa":   list(range(27, 33)),
            "🌎 Europe":   list(range(33, 41)),
            "🌎 Americas": list(range(41, 49)),
            "🌏 Oceania":  list(range(49, 51)),
        }
        city_list = list(CITIES.keys())
        for region, nums in regions.items():
            print(color(f"\n  {region}", C.YELLOW))
            for n in nums:
                if n-1 < len(city_list):
                    c = city_list[n-1]
                    lat_c, lon_c, _tz_c = CITIES[c]
                    print(color(f"    [{n:>2}]", C.CYAN, C.BOLD) +
                          color(f"  {c:30s}", C.WHITE) +
                          color(f"({lat_c}, {lon_c})", C.DIM))
        cidx = prompt("Enter city number (Enter=1):", "1")
        try:
            city_name = city_list[int(cidx) - 1]
            lat, lon, _ = CITIES[city_name]
            ok(f"Selected: {city_name}")
        except Exception:
            warn("Invalid → random city")
            lat, lon, city_name = random_city()
    else:
        lat = prompt("Latitude  (e.g. 23.685):", "23.685")
        lon = prompt("Longitude (e.g. 90.356):", "90.356")
        city_name = "Custom"

    # ── Output folder ──
    section("Output Settings")
    final_dir = get_output_dir()
    info(f"Platform   : {platform_label}")
    info(f"Output dir : {final_dir}")

    try:
        os.makedirs(final_dir, exist_ok=True)
        ok(f"Output ready → {final_dir}")
    except PermissionError:
        if _termux:
            warn("Permission denied! Run: termux-setup-storage")
        else:
            warn(f"Permission denied for {final_dir}")
        final_dir = os.path.join(os.path.expanduser("~"), "meta_output")
        os.makedirs(final_dir, exist_ok=True)
        ok(f"Fallback → {final_dir}")
    except Exception as e:
        err(f"Folder error: {e}"); exit(1)

    _loc_now, _tz_str, _tz_name = get_timezone_offset(float(lat), float(lon))
    now = _loc_now.strftime("%Y-%m-%dT%H:%M:%S") + _tz_str
    info(f"Video TZ : {_tz_name} ({_tz_str})")

    # ── Process Files ──
    section("Processing")
    success, fail = 0, 0
    output_files  = []

    for file_path in valid_files:
        ext      = os.path.splitext(file_path)[1].lower()
        now_dt   = datetime.now()
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

    # ── Gallery scan (Termux only) ──
    if output_files and _termux:
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
    print(color("\n  ✦ META FORGE v2.6 COMPLETE ✦\n", C.CYAN, C.BOLD))

    again = prompt("Process more files? [y/n] (Enter=n):", "n")
    if again.lower() == "y":
        main(skip_update=True)


if __name__ == "__main__":
    main()