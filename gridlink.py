import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import re
import tkintermapview
from maidenhead import to_location
from PIL import Image, ImageDraw, ImageTk
import datetime
from pathlib import Path
import sqlite3
import subprocess
import shutil
import time
import zipfile
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

# -------------------------
# PATHS
# -------------------------

BASE_DIR = Path(__file__).resolve().parent
ICON_DIR = BASE_DIR / "icons"
DATA_DIR = BASE_DIR / "data"
MAPS_DIR = BASE_DIR / "maps"

CONFIG_FILE = BASE_DIR / "config.json"
ICON_FILE = ICON_DIR / "varalert_icon.png"
SAMPLE_FILE = DATA_DIR / "sample_messages.txt"
USA_MAP_FILE = MAPS_DIR / "usa_full.png"
CALLSIGN_DB_FILE = DATA_DIR / "callsigns.db"
ZIPCODE_DB_FILE = DATA_DIR / "zipcodes.db"
VARAC_DB_FILE = Path.home() / ".wine-vara" / "drive_c" / "VarAC" / "VarAC.db"
JS8CALL_DIRECTED_FILE = Path.home() / ".local" / "share" / "JS8Call" / "DIRECTED.TXT"

FCC_AMATEUR_LICENSE_URL = "https://data.fcc.gov/download/pub/uls/complete/l_amat.zip"
FCC_AMATEUR_ZIP_FILE = DATA_DIR / "l_amat.zip"
FCC_AMATEUR_EXTRACT_DIR = DATA_DIR / "fcc_amat"

ICON_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
MAPS_DIR.mkdir(exist_ok=True)

# -------------------------
# CONSTANTS
# -------------------------

APP_VERSION = "v1.4.7 - Beta"

EMERGENCY_FREQUENCIES = [
    {
        "category": "Time / Propagation",
        "frequency": "2.500 MHz",
        "mode": "AM",
        "name": "WWV / WWVH",
        "description": "Lower-band propagation reference.",
        "details": (
            "WWV / WWVH 2.5 MHz\n\n"
            "• Atomic time reference\n"
            "• Lower-band HF propagation check\n"
            "• Often more useful at night\n\n"
            "WWV geophysical report: :18 after the hour\n"
            "WWVH geophysical report: :45 after the hour"
        )
    },
    {
        "category": "Time / Propagation",
        "frequency": "5.000 MHz",
        "mode": "AM",
        "name": "WWV / WWVH",
        "description": "Nighttime HF propagation reference.",
        "details": (
            "WWV / WWVH 5 MHz\n\n"
            "• HF propagation beacon\n"
            "• Good lower-band/NVIS indicator\n\n"
            "WWV geophysical report: :18 after the hour\n"
            "WWVH geophysical report: :45 after the hour"
        )
    },
    {
        "category": "Time / Propagation",
        "frequency": "10.000 MHz",
        "mode": "AM",
        "name": "WWV / WWVH",
        "description": "Best all-around WWV monitoring frequency.",
        "details": (
            "WWV / WWVH 10 MHz\n\n"
            "• General HF propagation reference\n"
            "• Useful day or night\n"
            "• Good first propagation check"
        )
    },
    {
        "category": "Time / Propagation",
        "frequency": "15.000 MHz",
        "mode": "AM",
        "name": "WWV / WWVH",
        "description": "Daytime upper-HF propagation indicator.",
        "details": (
            "WWV / WWVH 15 MHz\n\n"
            "Strong signal often indicates higher HF bands are open."
        )
    },
    {
        "category": "Time / Propagation",
        "frequency": "20.000 MHz",
        "mode": "AM",
        "name": "WWV",
        "description": "Upper-HF daytime propagation indicator.",
        "details": (
            "WWV 20 MHz\n\n"
            "• Upper-HF propagation reference\n"
            "• Most useful during strong daytime propagation\n"
            "• If clearly heard, 15m/12m/10m may also be usable\n\n"
            "WWV geophysical report: :18 after the hour"
        )
    },
    {
        "category": "Weather",
        "frequency": "162.400-162.550 MHz",
        "mode": "FM",
        "name": "NOAA Weather Radio",
        "description": "Weather alerts and emergency information.",
        "details": (
            "NOAA Weather Radio Frequencies\n\n"
            "Channel 1: 162.400 MHz\n"
            "Channel 2: 162.425 MHz\n"
            "Channel 3: 162.450 MHz\n"
            "Channel 4: 162.475 MHz\n"
            "Channel 5: 162.500 MHz\n"
            "Channel 6: 162.525 MHz\n"
            "Channel 7: 162.550 MHz\n\n"
            "Purpose:\n"
            "• Severe weather alerts\n"
            "• Tornado warnings\n"
            "• Watches and advisories\n"
            "• Emergency Alert System information\n\n"
            "Operational Note:\n"
            "NOAA Weather Radio is local/regional VHF FM, not HF. "
            "Program all seven frequencies and use whichever one is strongest in your area."
        )
    },
    {
        "category": "Aviation Emergency",
        "frequency": "121.500 MHz",
        "mode": "AM",
        "name": "Aviation Guard",
        "description": "International aviation emergency frequency.",
        "details": (
            "121.5 MHz Aviation Guard\n\n"
            "• Aircraft distress\n"
            "• ELT monitoring\n"
            "• Search and rescue"
        )
    },
    {
        "category": "Marine Emergency",
        "frequency": "156.800 MHz",
        "mode": "FM",
        "name": "Marine Ch 16",
        "description": "Marine distress and calling frequency.",
        "details": (
            "Marine Channel 16\n\n"
            "• Maritime distress\n"
            "• Calling channel\n"
            "• Coast Guard activity"
        )
    },
    {
        "category": "HF Emergency Nets",
        "frequency": "14.300 MHz",
        "mode": "USB",
        "name": "Maritime Mobile Net",
        "description": "HF maritime emergency assistance net.",
        "details": (
            "Maritime Mobile Service Net\n\n"
            "• Emergency assistance\n"
            "• Welfare traffic\n"
            "• Maritime support"
        )
    },
    {
        "category": "Digital HF",
        "frequency": "7.078 MHz",
        "mode": "USB",
        "name": "JS8Call",
        "description": "JS8Call 40m calling frequency.",
        "details": (
            "JS8Call Calling Frequencies\n\n"
            "160m: 1.842 MHz USB\n"
            "80m: 3.578 MHz USB\n"
            "40m: 7.078 MHz USB\n"
            "30m: 10.130 MHz USB\n"
            "20m: 14.078 MHz USB\n"
            "17m: 18.104 MHz USB\n"
            "15m: 21.078 MHz USB\n"
            "12m: 24.922 MHz USB\n"
            "10m: 28.078 MHz USB\n\n"
            "Operational Note:\n"
            "The top reference uses 40m because it is often useful for regional/emergency-style monitoring."
        )
    },
    {
        "category": "Digital HF",
        "frequency": "7.105 MHz",
        "mode": "USB",
        "name": "VarAC",
        "description": "VarAC 40m calling frequency.",
        "details": (
            "VarAC Calling Frequencies\n\n"
            "80m: 3.595 MHz USB\n"
            "40m: 7.105 MHz USB\n"
            "30m: 10.133 MHz USB\n"
            "20m: 14.105 MHz USB\n"
            "17m: 18.105 MHz USB\n"
            "15m: 21.105 MHz USB\n"
            "12m: 24.925 MHz USB\n"
            "10m: 28.105 MHz USB\n\n"
            "Operational Note:\n"
            "The top reference uses 40m because it is often useful for regional/emergency-style monitoring."
        )
    },
]

GEOMAGNETIC_REFERENCE_TEXT = """K-INDEX REFERENCE

0-2  Quiet conditions
3    Unsettled
4    Active
5    Minor geomagnetic storm
6-7  Strong geomagnetic storm
8-9  Severe geomagnetic storm

SOLAR FLUX INDEX (SFI)

70-90     Poor HF conditions
90-120    Moderate HF conditions
120-160   Good HF conditions
160+      Excellent upper-HF propagation

A-INDEX

0-7       Quiet
8-15      Unsettled
16-29     Active
30-49     Minor storm
50+       Major disturbance

OPERATIONAL GUIDANCE

High K-Index:
• More HF noise
• More fading
• Weaker digital decode
• Poor long-distance HF
• Try lower HF bands or NVIS

High Solar Flux:
• Better 20m / 15m / 10m propagation
• Longer daytime openings
• Improved DX potential

WWV / WWVH:
• WWV geophysical report: :18 after the hour
• WWVH geophysical report: :45 after the hour
"""


MAP_MODE = "Internet"
SIDE_PANEL_WIDTH = 520

BASE_MAP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
BASE_MBTILES_FILE = os.path.join(BASE_MAP_DIR, "north_america_z2_z6.mbtiles")

TILE_CACHE_DIR = os.path.join(BASE_MAP_DIR, "tile_cache")
os.makedirs(TILE_CACHE_DIR, exist_ok=True)

EXTERNAL_MAP_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps", "external"),
]

MBTILES_SERVER = None
MBTILES_SERVER_PORT = None
MBTILES_SERVER_THREAD = None

def mbtiles_file_exists(path):
    try:
        return bool(path and os.path.exists(path) and path.lower().endswith(".mbtiles"))
    except Exception:
        return False


def find_available_mbtiles_files():
    found = []

    if mbtiles_file_exists(BASE_MBTILES_FILE):
        found.append(BASE_MBTILES_FILE)

    for base_dir in EXTERNAL_MAP_DIRS:
        if not os.path.exists(base_dir):
            continue

        try:
            for root_dir, dirs, files in os.walk(base_dir):
                for filename in files:
                    if filename.lower().endswith(".mbtiles"):
                        full_path = os.path.join(root_dir, filename)
                        if full_path not in found:
                            found.append(full_path)
        except Exception as e:
            print(f"MBTiles scan error in {base_dir}: {e}")

    return found


def inspect_mbtiles_file(path):
    info = {
        "path": path,
        "name": os.path.basename(path),
        "exists": False,
        "min_zoom": None,
        "max_zoom": None,
        "tile_count": 0,
        "format": None,
        "valid": False,
        "error": None,
    }

    if not mbtiles_file_exists(path):
        info["error"] = "File does not exist or is not an .mbtiles file"
        return info

    info["exists"] = True

    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        try:
            cur.execute("SELECT value FROM metadata WHERE name='format'")
            fmt_row = cur.fetchone()
            if fmt_row:
                info["format"] = fmt_row[0]
        except Exception:
            pass

        cur.execute("SELECT MIN(zoom_level), MAX(zoom_level), COUNT(*) FROM tiles")
        row = cur.fetchone()

        if row:
            info["min_zoom"] = row[0]
            info["max_zoom"] = row[1]
            info["tile_count"] = row[2] or 0

        if not info.get("format"):
            try:
                cur.execute("SELECT tile_data FROM tiles LIMIT 1")
                tile_row = cur.fetchone()
                if tile_row and tile_row[0]:
                    data = tile_row[0]
                    if data.startswith(b"\x89PNG"):
                        info["format"] = "png"
                    elif data.startswith(b"\xff\xd8"):
                        info["format"] = "jpg"
                    elif data.startswith(b"RIFF") and b"WEBP" in data[:20]:
                        info["format"] = "webp"
                    else:
                        info["format"] = "unknown"
            except Exception:
                pass

        conn.close()

        info["valid"] = info["tile_count"] > 0

    except Exception as e:
        info["error"] = str(e)

    return info


def print_mbtiles_status():
    files = find_available_mbtiles_files()

    if not files:
        print("No MBTiles files found.")
        return

    print("Available MBTiles files:")

    for path in files:
        info = inspect_mbtiles_file(path)

        if info["valid"]:
            print(
                f"  {info['name']} | format {info.get('format')} | "
                f"zoom {info['min_zoom']}–{info['max_zoom']} | "
                f"{info['tile_count']} tiles | {info['path']}"
            )
        else:
            print(f"  INVALID: {info['path']} | {info['error']}")

def get_free_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_mbtiles_server(mbtiles_path):
    global MBTILES_SERVER, MBTILES_SERVER_PORT, MBTILES_SERVER_THREAD

    if MBTILES_SERVER is not None:
        return MBTILES_SERVER_PORT

    if not mbtiles_file_exists(mbtiles_path):
        print(f"MBTiles server error: file not found: {mbtiles_path}")
        return None

    print(f"DEBUG MBTiles path being served: {mbtiles_path}")

    class MBTilesRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                parts = self.path.strip("/").split("/")

                if len(parts) != 3:
                    self.send_error(404)
                    return

                z = int(parts[0])
                x = int(parts[1])
                y_part = parts[2]
                y = int(os.path.splitext(y_part)[0])

                # GDAL-generated GridLink Natural Earth tiles are XYZ
                tile_row = y
                print(f"Tile request: z={z}, x={x}, y={y}, tile_row={tile_row}")

                conn = sqlite3.connect(mbtiles_path)
                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT tile_data
                    FROM tiles
                    WHERE zoom_level = ?
                      AND tile_column = ?
                      AND tile_row = ?
                    """,
                    (z, x, tile_row)
                )

                row = cur.fetchone()
                conn.close()

                if not row:
                    self.send_error(404)
                    return

                tile_data = row[0]

                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(tile_data)

            except Exception as e:
                print(f"MBTiles tile server error: {e}")
                self.send_error(500)

        def log_message(self, format, *args):
            return

    try:
        MBTILES_SERVER_PORT = get_free_local_port()
        MBTILES_SERVER = HTTPServer(("127.0.0.1", MBTILES_SERVER_PORT), MBTilesRequestHandler)

        MBTILES_SERVER_THREAD = threading.Thread(
            target=MBTILES_SERVER.serve_forever,
            daemon=True
        )
        MBTILES_SERVER_THREAD.start()

        print(f"MBTiles tile server running on port {MBTILES_SERVER_PORT}")
        return MBTILES_SERVER_PORT

    except Exception as e:
        print(f"Could not start MBTiles server: {e}")
        MBTILES_SERVER = None
        MBTILES_SERVER_PORT = None
        MBTILES_SERVER_THREAD = None
        return None

BROADCAST_FEED_LIMIT = 30
BROADCAST_MEMORY_LIMIT = 150
RELAY_LOG_HISTORY_LIMIT = 60

color_map = {"grn": "green", "yel": "yellow", "red": "red"}

priority_map = {
    "Routine": "routine",
    "Priority": "priority",
    "Immediate": "immediate",
    "Flash": "flash"
}

priority_name_map = {
    "routine": "Routine",
    "priority": "Priority",
    "immediate": "Immediate",
    "flash": "Flash"
}

status_name_map = {
    "grn": "Green",
    "yel": "Yellow",
    "red": "Red"
}

STATUS_COLOR_MAP = {
    "grn": "green",
    "yel": "yellow",
    "red": "red",
}

CATEGORY_LABELS = [
    "Commercial Power",
    "Public Water",
    "Medical",
    "Over-Air Comms",
    "Travel",
    "Internet",
    "Fuel",
    "Food",
    "Criminal Activity",
    "Civil Stability",
    "Political Stability"
]

# Geographic bounds for the continental U.S.
US_LAT_MIN = 24.0
US_LAT_MAX = 50.0
US_LON_MIN = -125.0
US_LON_MAX = -66.0

# -------------------------
# OFFLINE MAP CALIBRATION
# -------------------------

SHOW_CALIBRATION_GUIDES = True

# Native PNG size
USA_MAP_WIDTH = 1100
USA_MAP_HEIGHT = 814

# Image-relative calibration points collected from your map
CALIBRATION_POINTS = [
    {"name": "Seattle",        "lat": 47.6062, "lon": -122.3321, "x": 244, "y": 211},
    {"name": "Los Angeles",    "lat": 34.0522, "lon": -118.2437, "x": 302, "y": 462},
    {"name": "Salt Lake City", "lat": 40.7608, "lon": -111.8910, "x": 386, "y": 347},
    {"name": "Phoenix",        "lat": 33.4484, "lon": -112.0740, "x": 386, "y": 470},
    {"name": "Memphis",        "lat": 35.1495, "lon": -90.0490,  "x": 685, "y": 442},
    {"name": "New Orleans",    "lat": 29.9511, "lon": -90.0715,  "x": 685, "y": 529},
    {"name": "Toronto",        "lat": 43.6532, "lon": -79.3832,  "x": 826, "y": 297},
    {"name": "Ottawa",         "lat": 45.4215, "lon": -75.6972,  "x": 876, "y": 261},
    {"name": "Washington DC",  "lat": 38.9072, "lon": -77.0369,  "x": 858, "y": 380},
    {"name": "New York",       "lat": 40.7128, "lon": -74.0060,  "x": 900, "y": 348},
]


# -------------------------
# THEMES
# -------------------------

LIGHT_THEME = {
    "name": "light",
    "bg": "#E7E0D0",
    "panel_bg": "#D4CAB3",
    "map_bg": "#B8AD94",
    "fg": "#172330",
    "muted_fg": "#4F5360",

    "list_bg": "#F3EDE0",
    "list_fg": "#172330",
    "list_select_bg": "#B88A3B",
    "list_select_fg": "#101820",

    "entry_bg": "#F7F2E8",
    "entry_fg": "#172330",

    "text_bg": "#F3EDE0",
    "text_fg": "#172330",

    "button_bg": "#24384D",
    "button_fg": "#F6F0E4",

    "status_bg": "#D4CAB3",
    "status_fg": "#172330",

    "labelframe_bg": "#E7E0D0",
    "labelframe_fg": "#24384D",

    "canvas_title_fg": "#172330",
    "highlight_outline": "#B88A3B",

    "calibration_outline": "#24384D",
    "calibration_point_fill": "#B88A3B",
    "calibration_point_outline": "#172330",

    "statrep_font": ("Courier", 16,),
}
    

DARK_THEME = {
    "name": "dark",
    "bg": "#1e1e1e",
    "panel_bg": "#252526",
    "map_bg": "#2d2d30",
    "fg": "#f3f3f3",
    "muted_fg": "#d0d0d0",
    "list_bg": "#252526",
    "list_fg": "#7CFC00",
    "list_select_bg": "#3a7bd5",
    "list_select_fg": "#7CFC00",
    "entry_bg": "#2d2d30",
    "entry_fg": "#f3f3f3",
    "text_bg": "#252526",
    "text_fg": "#f3f3f3",
    "button_bg": "#3a3d41",
    "button_fg": "#f3f3f3",
    "status_bg": "#333333",
    "status_fg": "#f3f3f3",
    "labelframe_bg": "#1e1e1e",
    "labelframe_fg": "#f3f3f3",
    "canvas_title_fg": "#f3f3f3",
    "highlight_outline": "#4ea1ff",
    "calibration_outline": "#b07cff",
    "calibration_point_fill": "#66d9ef",
    "calibration_point_outline": "#111111",
    "statrep_font": ("Courier", 16,),
}


OUTER_SPACE_THEME = {
    "name": "high_flight",
    "bg": "#0a0f1c",
    "panel_bg": "#121a2b",
    "map_bg": "#0f1624",
    "fg": "#e6edf3",
    "muted_fg": "#9aa4b2",
    "list_bg": "#000000",
    "list_fg": "#e6edf3",
    "list_select_bg": "#1a2740",
    "list_select_fg": "#ffffff",
    "entry_bg": "#162033",
    "entry_fg": "#e6edf3",
    "text_bg": "#121a2b",
    "text_fg": "#e6edf3",
    "button_bg": "#1a2740",
    "button_fg": "#e6edf3",
    "status_bg": "#162033",
    "status_fg": "#e6edf3",
    "labelframe_bg": "#0a0f1c",
    "labelframe_fg": "#e6edf3",
    "canvas_title_fg": "#e6edf3",
    "highlight_outline": "#3da9fc",
    "calibration_outline": "#7f5af0",
    "calibration_point_fill": "#00ffaa",
    "calibration_point_outline": "#0a0f1c",
    "statrep_font": ("Courier", 16,),
}


WOODLANDS_THEME = {
    "name": "woodlands",
    "bg": "#1a241a",                 
    "panel_bg": "#3a4a36",           
    "map_bg": "#2a3326",             
    "fg": "#cbbfa2",                 
    "muted_fg": "#9f957d",           
    "list_bg": "#000000",            
    "list_fg": "#ffd166",            
    "list_select_bg": "#3a4435",     
    "list_select_fg": "#ffffff",
    "entry_bg": "#2a3326",
    "entry_fg": "#cbbfa2",
    "text_bg": "#1f281d",
    "text_fg": "#fff2cc",
    "button_bg": "#4a3b2a",          
    "button_fg": "#cbbfa2",
    "status_bg": "#2a3326",
    "status_fg": "#cbbfa2",
    "labelframe_bg": "#1a241a",
    "labelframe_fg": "#cbbfa2",
    "canvas_title_fg": "#cbbfa2",
    "highlight_outline": "#bfa67a",  
    "calibration_outline": "#5a4630",
    "calibration_point_fill": "#cbbfa2",
    "calibration_point_outline": "#1a241a",
    "statrep_font": ("Courier", 16,),
}


LEATHERNECK_THEME = {
    "name": "leatherneck",
    "bg": "#2a3a2a",                 
    "panel_bg": "#526a4f",           
    "map_bg": "#3a4a36",             
    "fg": "#cbbfa2",                 
    "muted_fg": "#b5aa90",           
    "list_bg": "#5a1f1f",            
    "list_fg": "#f4c542",            
    "list_select_bg": "#6b2a2a",     
    "list_select_fg": "#fff8dc",
    "entry_bg": "#3a4a36",
    "entry_fg": "#cbbfa2",
    "text_bg": "#324230",
    "text_fg": "#fff2cc",
    "button_bg": "#6a5a44",          
    "button_fg": "#cbbfa2",
    "status_bg": "#3a4a36",
    "status_fg": "#cbbfa2",
    "labelframe_bg": "#2a3a2a",
    "labelframe_fg": "#cbbfa2",
    "canvas_title_fg": "#cbbfa2",
    "highlight_outline": "#d4af37",  
    "calibration_outline": "#7a644c",
    "calibration_point_fill": "#cbbfa2",
    "calibration_point_outline": "#2a3a2a",
    "statrep_font": ("Courier", 16,),
}


MIDWATCH_THEME = {
    "name": "midwatch",
    "bg": "#050d18",
    "panel_bg": "#0b1726",
    "map_bg": "#08121f",
    "fg": "#d6e2f0",
    "muted_fg": "#7f96ad",
    "list_bg": "#040b14",
    "list_fg": "#f4c542",
    "list_select_bg": "#132a44",
    "list_select_fg": "#fff8dc",
    "entry_bg": "#08121f",
    "entry_fg": "#d6e2f0",
    "text_bg": "#040b14",
    "text_fg": "#d6e2f0",
    "button_bg": "#10233a",
    "button_fg": "#d6e2f0",
    "status_bg": "#08121f",
    "status_fg": "#d6e2f0",
    "labelframe_bg": "#050d18",
    "labelframe_fg": "#d6e2f0",
    "canvas_title_fg": "#d6e2f0",
    "highlight_outline": "#d4af37",
    "calibration_outline": "#4f6a88",
    "calibration_point_fill": "#d6e2f0",
    "calibration_point_outline": "#050d18",
    "statrep_font": ("Courier", 16,),
}

# ============================================================
# PHASE 2 - TEMPORARY TEST DATA - TRUSTED GATEWAYS
# ============================================================

trusted_gateways = []

# ============================================================
# PHASE 4 - REPLY WORKFLOW
# ============================================================

pending_replies = []
last_reply_ids = set()
active_gateway_callsigns = []


def get_theme():
    theme_name = config.get("theme", "light").lower() if "config" in globals() else "light"

    if theme_name == "dark":
        return DARK_THEME
    elif theme_name in ("outer_space", "high_flight"):
        return OUTER_SPACE_THEME
    elif theme_name == "woodlands":
        return WOODLANDS_THEME
    elif theme_name == "leatherneck":
        return LEATHERNECK_THEME
    elif theme_name == "midwatch":
        return MIDWATCH_THEME
    else:
        return LIGHT_THEME


def copy_text_to_clipboard(text, widget=None):
    """
    Hardened clipboard copy helper for GridLink.

    Uses xclip/xsel when available because Wine apps like VarAC can
    sometimes hold stale Tk clipboard contents under Linux/X11.
    Falls back to Tk clipboard ownership if system clipboard tools
    are unavailable.
    """
    text = "" if text is None else str(text)

    if shutil.which("xclip"):
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=True
        )
        return

    if shutil.which("xsel"):
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode(),
            check=True
        )
        return

    clip_widget = widget if widget is not None else globals().get("root")

    if clip_widget is None:
        raise RuntimeError("No Tk widget available for clipboard fallback.")

    clip_widget.clipboard_clear()
    clip_widget.clipboard_append(text)
    clip_widget.update()


# ============================================================
# PHASE 2 - TELEGRAM DASHBOARD HELPERS
# ============================================================

current_gateway_band = "20m"


def format_gateway_row(status, callsign, source, band, snr, activity):
    snr_display = f"{snr:+03}" if snr is not None else "---"
    return f"{status:<6} {callsign:<7}{source:<4} {band:<4} {snr_display:<3} {activity}"


def build_trusted_gateway_rows():
    gateway_entries = []

    recent_beacons = get_recent_beacons(hours=3)
    recent_js8 = get_recent_js8_activity(hours=3)
    active_calls = {c.strip().upper() for c in active_gateway_callsigns if c.strip()}
    now = datetime.datetime.now(datetime.UTC)

    current_band_normalized = (current_gateway_band or "").strip().lower()

    trusted_lookup = {}
    for gateway in trusted_gateways:
        callsign = (gateway.get("callsign", "") or "").strip().upper()
        bands = [(b or "").strip().lower() for b in gateway.get("bands", [])]
        if callsign:
            trusted_lookup[callsign] = set(bands)

    all_callsigns = set(trusted_lookup.keys()) | set(active_calls)

    for callsign in sorted(all_callsigns):
        beacon = recent_beacons.get(callsign)
        js8_timestamp = recent_js8.get(callsign)
        is_detected = callsign in active_calls
        is_trusted = callsign in trusted_lookup

        trusted_on_band = current_band_normalized in trusted_lookup.get(callsign, set())

        beacon_on_current_band = False
        if beacon:
            beacon_band = (beacon.get("band") or "").strip().lower()
            beacon_on_current_band = (beacon_band == current_band_normalized)

        is_js8_active = js8_timestamp is not None
        is_active = beacon_on_current_band or is_js8_active

        if is_trusted:
            if is_active:
                status = "[T][A]"
            elif is_detected:
                status = "[T][D]"
            else:
                status = "[T]   "
        else:
            if is_active:
                status = "   [A]"
            elif is_detected:
                status = "   [D]"
            else:
                continue

        if is_trusted and not trusted_on_band and not beacon_on_current_band and not is_detected:
            continue

        if beacon_on_current_band:
            delta = now - beacon["timestamp"]
            minutes = int(delta.total_seconds() // 60)
            hours = minutes // 60
            minutes = minutes % 60
            activity = f"{hours:02}:{minutes:02}"
            snr = beacon.get("snr")
            band_display = beacon.get("band", current_gateway_band)
            last_heard_dt = beacon["timestamp"]
        else:
            if js8_timestamp:
                js8_data = js8_timestamp

                delta = now - js8_data["timestamp"]
                minutes = int(delta.total_seconds() // 60)
                hours = minutes // 60
                minutes = minutes % 60
                activity = f"{hours:02}:{minutes:02}"

                snr = js8_data.get("snr")

                try:
                    freq = float(js8_data.get("frequency", 0))
                    if 14.0 <= freq < 15.0:
                        band_display = "20m"
                    elif 7.0 <= freq < 8.0:
                        band_display = "40m"
                    else:
                        band_display = "---"
                except Exception:
                    band_display = "---"

                last_heard_dt = js8_data["timestamp"]
            else:
                activity = "Detected" if is_detected else "No Beacon"
                snr = None
                band_display = "?" if is_detected else (current_gateway_band if current_gateway_band else "?")
                last_heard_dt = None
            
        source = "VAC" if beacon_on_current_band else (
            "JS8" if js8_timestamp else "---"
        )

        row = format_gateway_row(
            status=status,
            callsign=callsign,
            source=source,
            band=band_display,
            snr=snr,
            activity=activity
        )

        gateway_entries.append({
            "row": row,
            "trusted": is_trusted,
            "active": beacon_on_current_band,
            "detected": is_detected,
            "last_heard": last_heard_dt,
            "callsign": callsign
        })

    gateway_entries.sort(
        key=lambda entry: (
            0 if entry["trusted"] else 1,
            0 if entry["active"] else 1,
            0 if entry["detected"] else 1,
            -(entry["last_heard"].timestamp()) if entry["last_heard"] else float("inf"),
            entry["callsign"]
        )
    )

    return [entry["row"] for entry in gateway_entries]

def parse_beacon_line(message_text):
    """
    Example:
    <SENDING ADVANCED BEACON ON 20m - 14.105.000> DE KG5VPF
    """
    message_text = (message_text or "").strip()

    pattern = re.compile(
        r"<SENDING ADVANCED BEACON ON\s+(.+?)\s+-\s+([0-9.]+)>\s+DE\s+([A-Z0-9/]+)",
        re.IGNORECASE
    )

    match = pattern.search(message_text)
    if not match:
        return None

    band = match.group(1).strip()
    frequency = match.group(2).strip()
    callsign = match.group(3).strip().upper()

    return {
        "callsign": callsign,
        "band": band,
        "frequency": frequency
    }

def get_recent_beacons(hours=3):
    """
    Use cqframe table to detect active gateways.
    Returns dict keyed by callsign.
    """
    recent = {}

    rows = get_recent_cqframe_rows(hours=hours)

    for row in rows:
        callsign = (row["from_callsign"] or "").strip().upper()
        band = (row["band"] or "").strip()
        frequency = row["frequency"]
        snr = row["snr"]
        locator = (row["locator"] or "").strip().upper()

        if not callsign:
            continue

        # Convert timestamp
        timestamp = datetime.datetime.now(datetime.UTC)
        try:
            ts = str(row["cqframe_time"]).replace("Z", "")
            if "." in ts:
                main_part, frac_part = ts.split(".", 1)
                frac_part = (frac_part + "000000")[:6]
                ts = f"{main_part}.{frac_part}"
                timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
            else:
                timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
        except Exception:
            pass

        existing = recent.get(callsign)
        if existing is None or timestamp > existing["timestamp"]:
            recent[callsign] = {
                "band": band,
                "frequency": frequency,
                "snr": snr,
                "locator": locator,
                "timestamp": timestamp
            }

    return recent

def get_js8call_rows_for_callsign(callsign, lookback_days):
    path = config.get("js8call_directed_path", "").strip()

    if not path:
        return []

    file_path = Path(path)

    if not file_path.exists():
        return []

    target = callsign.strip().upper()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)
    rows = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) < 5:
                    continue

                timestamp_str = parts[0].strip()
                freq_str = parts[1].strip()
                snr_str = parts[3].strip()
                text = parts[4].strip()

                if ":" not in text:
                    continue

                from_call = text.split(":", 1)[0].strip().upper()
                message_text = text.split(":", 1)[1].strip().upper()

                if target not in message_text and from_call != target:
                    continue

                try:
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    continue

                if timestamp < cutoff:
                    continue

                try:
                    frequency = float(freq_str)
                except Exception:
                    frequency = 0.0

                try:
                    snr = int(snr_str)
                except Exception:
                    snr = None

                band = "?"
                if 14.0 <= frequency < 14.35:
                    band = "20m"
                elif 7.0 <= frequency < 7.3:
                    band = "40m"
                elif 21.0 <= frequency < 21.45:
                    band = "15m"
                elif 28.0 <= frequency < 29.7:
                    band = "10m"
                elif 3.5 <= frequency < 4.0:
                    band = "80m"
                elif 1.8 <= frequency < 2.0:
                    band = "160m"
                elif 18.068 <= frequency < 18.168:
                    band = "17m"
                elif 24.89 <= frequency < 24.99:
                    band = "12m"
                elif 50.0 <= frequency < 54.0:
                    band = "6m"

                rows.append({
                    "timestamp": timestamp,
                    "callsign": from_call,
                    "target_callsign": target,
                    "frequency": frequency,
                    "band": band,
                    "snr": snr,
                    "text": text
                })

    except Exception as e:
        print(f"JS8 callsign propagation read error: {e}")
        return []

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows

def analyze_js8call_activity(js8_rows):
    if not js8_rows:
        return None

    band_counts = {}
    time_counts = {
        "00:00-05:59": 0,
        "06:00-11:59": 0,
        "12:00-17:59": 0,
        "18:00-23:59": 0
    }
    hour_counts = {}
    snr_values = []

    for row in js8_rows:
        band = row.get("band", "?")
        hour = row["timestamp"].hour
        snr = row.get("snr")

        band_counts[band] = band_counts.get(band, 0) + 1
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if 0 <= hour <= 5:
            time_counts["00:00-05:59"] += 1
        elif 6 <= hour <= 11:
            time_counts["06:00-11:59"] += 1
        elif 12 <= hour <= 17:
            time_counts["12:00-17:59"] += 1
        else:
            time_counts["18:00-23:59"] += 1

        if snr is not None:
            snr_values.append(snr)

    most_common_band = max(band_counts, key=band_counts.get) if band_counts else "?"
    most_active_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
    most_active_window = max(time_counts, key=time_counts.get) if time_counts else None

    avg_snr = None
    if snr_values:
        avg_snr = sum(snr_values) / len(snr_values)

    return {
        "count": len(js8_rows),
        "most_common_band": most_common_band,
        "most_active_hour": most_active_hour,
        "most_active_window": most_active_window,
        "avg_snr": avg_snr,
        "snr_sample_count": len(snr_values),
        "band_counts": band_counts,
        "time_counts": time_counts
    }

def get_recent_js8_activity(hours=3):
    """
    Read recent JS8Call activity from DIRECTED.TXT.
    Returns dict keyed by callsign with the most recent timestamp seen.
    """
    recent = {}
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=hours)

    lines = read_js8call_directed_lines()
    if not lines:
        return recent

    for line in lines:
        try:
            parts = line.split("\t")
            if len(parts) < 5:
                continue

            timestamp_text = parts[0].strip()
            frequency = parts[1].strip()
            snr_text = parts[3].strip()
            payload = parts[4].strip()

            if ":" not in payload:
                continue

            from_call, raw_message = payload.split(":", 1)
            callsign = from_call.strip().upper()

            if not callsign:
                continue

            try:
                timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
            except Exception:
                continue

            if timestamp < cutoff:
                continue

            try:
                snr_value = int(snr_text)
            except Exception:
                snr_value = None

            existing = recent.get(callsign)
            if existing is None or timestamp > existing["timestamp"]:
                recent[callsign] = {
                    "timestamp": timestamp,
                    "frequency": frequency,
                    "snr": snr_value
                }

        except Exception:
            continue

    return recent

def get_latest_gateway_band(hours=3):
    rows = get_recent_cqframe_rows(hours=hours)

    latest_band = None
    latest_timestamp = None

    for row in rows:
        band = (row["band"] or "").strip()
        if not band:
            continue

        timestamp = datetime.datetime.now(datetime.UTC)
        try:
            ts = str(row["cqframe_time"]).replace("Z", "")
            if "." in ts:
                main_part, frac_part = ts.split(".", 1)
                frac_part = (frac_part + "000000")[:6]
                ts = f"{main_part}.{frac_part}"
                timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
            else:
                timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
        except Exception:
            pass

        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_band = band

    return latest_band

def refresh_gateway_dashboard():
    if "gateway_text" not in globals():
        return

    global current_gateway_band

    latest_band = get_latest_gateway_band(hours=3)
    if latest_band:
        current_gateway_band = latest_band

    rows = build_trusted_gateway_rows()

    gateway_text.config(state="normal")
    gateway_text.delete("1.0", tk.END)

    gateway_text.insert(tk.END, f"{'Status':<6} {'Call':<6} {'SRC':<4} {'Band':<4} {'SNR':<3} Activity\n")
    gateway_text.insert(tk.END, "-" * 48 + "\n")

    for row in rows:
        gateway_text.insert(tk.END, row + "\n")

    gateway_text.config(state="disabled")


def style_ttk_widgets():
    theme = get_theme()

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "TCombobox",
        fieldbackground=theme["entry_bg"],
        background=theme["button_bg"],
        foreground=theme["entry_fg"],
        arrowcolor=theme["fg"],
        insertcolor=theme["entry_fg"]
    )

    style.map(
        "TCombobox",
        fieldbackground=[("readonly", theme["entry_bg"])],
        background=[("readonly", theme["button_bg"])],
        foreground=[("readonly", theme["entry_fg"])],
        selectbackground=[("readonly", theme["list_select_bg"])],
        selectforeground=[("readonly", theme["list_select_fg"])]
    )

    style.configure(
        "TLabel",
        background=theme["bg"],
        foreground=theme["fg"]
    )

def style_menus():
    theme = get_theme()

    menu_bg = theme["panel_bg"]
    menu_fg = theme["fg"]
    active_bg = theme["list_select_bg"]
    active_fg = theme["list_select_fg"]

    menus_to_style = [
        menu,
        setup_menu,
        theme_menu,
        filter_menu,
        dashboard_menu,
        map_menu,
        propagation_menu,
        contacts_menu,
    ]

    for m in menus_to_style:
        try:
            m.configure(
                bg=menu_bg,
                fg=menu_fg,
                activebackground=active_bg,
                activeforeground=active_fg,
                relief="flat",
                bd=0
            )
        except Exception as e:
            print(f"Menu styling error: {e}")

def apply_widget_colors(widget, bg, fg=None, button_bg=None, entry_bg=None, text_bg=None):
    try:
        cls = widget.winfo_class()

        if cls == "Frame":
            widget.configure(bg=bg)

        elif cls == "LabelFrame":
            theme = get_theme()
            widget.configure(
                bg=theme["labelframe_bg"],
                fg=theme["labelframe_fg"]
            )

        elif cls == "Label":
            theme = get_theme()
            widget.configure(
                bg=bg,
                fg=fg if fg else theme["fg"]
            )

        elif cls == "Button":
            theme = get_theme()

            if "reply_button" in globals() and widget is reply_button:
                pass
            else:
                widget.configure(
                    bg=button_bg if button_bg else theme["button_bg"],
                    fg=theme["button_fg"],
                    activebackground=theme["button_bg"],
                    activeforeground=theme["button_fg"]
                )

        elif cls == "Listbox":
            theme = get_theme()

            if theme["name"] == "outer_space":
                list_fg = "#00e5ff"
            else:
                list_fg = theme["list_fg"]

            widget.configure(
                bg=theme["list_bg"],
                fg=list_fg,
                selectbackground=theme["list_select_bg"],
                selectforeground=theme["list_select_fg"]
            )

        elif cls == "Text":
            widget.configure(
                bg=text_bg if text_bg else bg,
                fg=fg if fg else "black",
                insertbackground=fg if fg else "black"
            )

        elif cls == "Entry":
            widget.configure(
                bg=entry_bg if entry_bg else bg,
                fg=fg if fg else "black",
                insertbackground=fg if fg else "black"
            )

        elif cls == "Canvas":
            widget.configure(bg=get_theme()["map_bg"], highlightthickness=0)

    except Exception:
        pass

    for child in widget.winfo_children():
        apply_widget_colors(
            child,
            bg=bg,
            fg=fg,
            button_bg=button_bg,
            entry_bg=entry_bg,
            text_bg=text_bg
        )


def apply_theme_to_toplevel(win):
    theme = get_theme()

    try:
        win.configure(bg=theme["bg"])
    except Exception:
        pass

    apply_widget_colors(
        win,
        bg=theme["bg"],
        fg=theme["fg"],
        button_bg=theme["button_bg"],
        entry_bg=theme["entry_bg"],
        text_bg=theme["text_bg"]
    )


def apply_theme():
    theme = get_theme()
    font_sizes = get_font_sizes()

    try:
        root.configure(bg=theme["bg"])
    except Exception:
        pass

    style_ttk_widgets()
    style_menus()

    try:
        top_frame.configure(bg=theme["labelframe_bg"], fg=theme["labelframe_fg"])
        feed_inner_frame.configure(bg=theme["map_bg"], highlightthickness=0)
        list_button_frame.configure(bg=theme["map_bg"])

        left_dashboard_frame.configure(bg=theme["labelframe_bg"], fg=theme["labelframe_fg"])
        left_dashboard_inner.configure(bg=theme["map_bg"], highlightthickness=0)

        right_dashboard_frame.configure(bg=theme["labelframe_bg"], fg=theme["labelframe_fg"])
        right_dashboard_inner.configure(bg=theme["map_bg"], highlightthickness=0)

        map_frame.configure(bg=theme["labelframe_bg"], fg=theme["labelframe_fg"])
        map_inner_frame.configure(bg=theme["map_bg"], highlightthickness=0)

        lower_frame.configure(bg=theme["bg"])
        status_frame.configure(bg=theme["bg"])
    except Exception:
        pass

    try:
        if theme["name"] == "outer_space":
            list_fg = "#38bdf8"
        else:
            list_fg = theme["list_fg"]

        main_feed_list.configure(
            bg=theme["list_bg"],
            fg=list_fg,
            selectbackground=theme["list_select_bg"],
            selectforeground=theme["list_select_fg"],
            font=("Courier", font_sizes["varalert"])
        )

        broadcast_feed_text.configure(
            bg=theme["text_bg"],
            fg=theme["text_fg"],
            insertbackground=theme["text_fg"],
            font=("Arial", font_sizes["broadcast"])
        )

        gateway_text.configure(
            bg=theme["text_bg"],
            fg=theme["text_fg"],
            insertbackground=theme["text_fg"],
            font=("Courier", font_sizes["telegram"])
        )
    except Exception:
        pass

    try:
        offline_canvas.configure(bg=theme["map_bg"], highlightthickness=0)
    except Exception:
        pass

    try:
        click_status_label.configure(
            bg=theme["status_bg"],
            fg=theme["status_fg"]
        )
    except Exception:
        pass

    apply_widget_colors(
        root,
        bg=theme["bg"],
        fg=theme["fg"],
        button_bg=theme["button_bg"],
        entry_bg=theme["entry_bg"],
        text_bg=theme["text_bg"]
    )

    refresh_active_map()
    update_reply_button_state()


def set_theme(theme_name):
    config["theme"] = theme_name
    save_config()
    apply_theme()
    click_status_var.set(f"Theme set to {theme_name.title()} mode")


def force_entry_uppercase(entry_widget):
    def _convert(event=None):
        current = entry_widget.get()
        upper = current.upper()
        if current != upper:
            cursor_pos = entry_widget.index(tk.INSERT)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, upper)
            try:
                entry_widget.icursor(cursor_pos)
            except Exception:
                pass

    entry_widget.bind("<KeyRelease>", _convert)


def configure_toplevel_window(win, width, height, min_width=None, min_height=None, center=True):
    """
    Phase 5A helper:
    - makes pop-up windows resizable
    - gives them a safe minimum size
    - keeps them on screen
    - prevents windows from opening too short on small displays
    """
    win.update_idletasks()

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    usable_width = max(320, screen_width - 40)
    usable_height = max(320, screen_height - 80)

    requested_width = max(width, win.winfo_reqwidth())
    requested_height = max(height, win.winfo_reqheight())

    final_width = min(requested_width, usable_width)
    final_height = min(requested_height, usable_height)

    if min_width is None:
        min_width = min(final_width, 320)
    if min_height is None:
        min_height = min(final_height, 240)

    min_width = min(min_width, usable_width)
    min_height = min(min_height, usable_height)

    win.minsize(min_width, min_height)
    win.resizable(True, True)

    if center:
        x = max(0, (screen_width // 2) - (final_width // 2))
        y = max(0, (screen_height // 2) - (final_height // 2))
        win.geometry(f"{final_width}x{final_height}+{x}+{y}")
    else:
        win.geometry(f"{final_width}x{final_height}")


messages = []
broadcast_messages = []
filtered_messages = []
visible_main_feed_items = []
visible_broadcast_feed_items = []
selected_broadcast_feed_index = None
selection_clear_after_id = None
SELECTION_TIMEOUT_MS = 15000
offline_station_items = []
offline_map_image = None

internet_station_markers = []
selected_station_label_marker = None

click_status_var = None
relay_log_messages = []
relay_log_text = None
current_filter_days = 24
log_watcher = None
seen_message_keys = set()

last_broadcast_id = 0
last_cqframe_id = 0
sqlite_poll_interval_ms = 5000
sqlite_monitor_enabled = False

marker_icons = {}

def create_dot_icon(color, size=6, center_dot=False):
    key = f"{color}_{size}_{'center' if center_dot else 'solid'}"
    if key in marker_icons:
        return marker_icons[key]

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Main station marker dot
    draw.ellipse((0, 0, size - 1, size - 1), fill=color)

    # Optional black center dot means heard-only / no proof they hear us
    if center_dot:
        dot_size = max(4, size // 3)
        pad = (size - dot_size) // 2
        draw.ellipse(
            (pad, pad, pad + dot_size - 1, pad + dot_size - 1),
            fill="black"
        )

    tk_img = ImageTk.PhotoImage(img)
    marker_icons[key] = tk_img
    return tk_img


# ============================================================
# BETA READINESS - VMAIL TRIGGER MONITOR
# ============================================================

LAST_VMAIL_ID_FILE = BASE_DIR / "last_vmail_id.txt"
VMAIL_TRIGGER_POLL_INTERVAL_MS = 5000

highest_processed_vmail_id = 0
trigger_polling_enabled = False


# -------------------------
# CONFIG
# -------------------------

def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            loaded.setdefault("callsign", "")
            loaded.setdefault("grid", "")
            loaded.setdefault("group", "")
            loaded.setdefault("traffic_log_path", "")
            loaded.setdefault("varac_db_path", str(VARAC_DB_FILE))
            loaded.setdefault("js8call_directed_path", str(JS8CALL_DIRECTED_FILE))
            loaded.setdefault("relay_url", "https://relay.varalert.net")
            loaded.setdefault("theme", "light")
            loaded.setdefault("show_broadcast_feed", False)
            loaded.setdefault("show_beacon_feed", False)
            loaded.setdefault("trusted_gateways", [])
            loaded.setdefault("telegram_contacts", [])

            # Phase 5B - per-feed font sizes
            loaded.setdefault("varalert_feed_font_size", 14)
            loaded.setdefault("broadcast_feed_font_size", 11)
            loaded.setdefault("telegram_dashboard_font_size", 13)
            loaded.setdefault("js8_activity_filter_hours", 24)

            # 🔥 NEW: mark first-run setup, but still return config
            if not loaded.get("callsign", "").strip() or not loaded.get("grid", "").strip():
                loaded["show_setup_on_start"] = True

            return loaded

        return setup_config()
    except Exception as e:
        print(f"Config load error: {e}")
        return setup_config()


def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")
        messagebox.showerror("Error", f"Could not save config:\n{e}")


def get_font_sizes():
    return {
        "varalert": config.get("varalert_feed_font_size", 14),
        "broadcast": config.get("broadcast_feed_font_size", 11),
        "telegram": config.get("telegram_dashboard_font_size", 13),
    }


def setup_config():
    global config

    theme = get_theme()

    existing_callsign = config.get("callsign", "")
    existing_grid = config.get("grid", "")
    existing_group = config.get("group", "")
    existing_traffic_log_path = config.get("traffic_log_path", "")
    existing_varac_db_path = config.get("varac_db_path", str(VARAC_DB_FILE))
    existing_js8call_directed_path = config.get("js8call_directed_path", str(JS8CALL_DIRECTED_FILE))
    existing_relay_url = config.get("relay_url", "https://relay.varalert.net")
    existing_theme = config.get("theme", "light")
    existing_show_broadcast = config.get("show_broadcast_feed", False)
    existing_show_beacon = config.get("show_beacon_feed", False)
    existing_trusted_gateways = config.get("trusted_gateways", [])
    existing_telegram_contacts = config.get("telegram_contacts", [])

    win = tk.Toplevel(root)
    win.withdraw()
    win.title("Station Setup")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=12, pady=12)

    form_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=12,
        pady=12
    )
    form_frame.pack(fill="both", expand=True)

    # -------------------------
    # BASIC FIELDS
    # -------------------------

    tk.Label(form_frame, text="Callsign", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=0, column=0, sticky="w", pady=6)
    callsign_entry = tk.Entry(form_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
    callsign_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6)
    callsign_entry.insert(0, existing_callsign)

    tk.Label(form_frame, text="Grid", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="w", pady=6)
    grid_entry = tk.Entry(form_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
    grid_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
    grid_entry.insert(0, existing_grid)

    tk.Label(form_frame, text="Group", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=2, column=0, sticky="w", pady=6)
    group_entry = tk.Entry(form_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
    group_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)
    group_entry.insert(0, existing_group)

    tk.Label(
        form_frame,
        text="Optional: Enter your EmComm group (e.g. HRMS).\nIf left blank, messages will use @No Group.",
        bg=theme["panel_bg"],
        fg=theme["muted_fg"],
        justify="left"
    ).grid(row=3, column=1, columnspan=2, sticky="w", pady=(0, 8))

    # -------------------------
    # VARAC DB
    # -------------------------

    tk.Label(form_frame, text="VarAC DB", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=4, column=0, sticky="w", pady=6)

    varac_db_entry = tk.Entry(form_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
    varac_db_entry.grid(row=4, column=1, sticky="ew", pady=6)
    varac_db_entry.insert(0, existing_varac_db_path)

    def browse_varac_db():
        initial_dir = str(Path(varac_db_entry.get()).parent) if Path(varac_db_entry.get()).exists() else str(Path.home())

        path = filedialog.askopenfilename(
            title="Select VarAC SQLite Database",
            initialdir=initial_dir,
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
        )

        if path:
            varac_db_entry.delete(0, tk.END)
            varac_db_entry.insert(0, path)

    tk.Button(form_frame, text="Browse...", command=browse_varac_db).grid(row=4, column=2, pady=6)

    # -------------------------
    # JS8CALL DIRECTED
    # -------------------------

    tk.Label(form_frame, text="JS8Call DIRECTED.TXT", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=5, column=0, sticky="w", pady=6)

    js8call_entry = tk.Entry(form_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
    js8call_entry.grid(row=5, column=1, sticky="ew", pady=6)
    js8call_entry.insert(0, existing_js8call_directed_path)

    def browse_js8call_directed():
        initial_path = js8call_entry.get().strip()

        if initial_path:
            path_obj = Path(initial_path)
            initial_dir = str(path_obj.parent) if path_obj.exists() else str(Path.home())
        else:
            initial_dir = str(Path.home() / ".local" / "share" / "JS8Call")

        if not Path(initial_dir).exists():
            initial_dir = str(Path.home())

        path = filedialog.askopenfilename(
            title="Select JS8Call DIRECTED.TXT",
            initialdir=initial_dir,
            initialfile="DIRECTED.TXT"
        )

        if path:
            js8call_entry.delete(0, tk.END)
            js8call_entry.insert(0, path)

    tk.Button(form_frame, text="Browse...", command=browse_js8call_directed).grid(row=5, column=2, pady=6)

    tk.Label(
        form_frame,
        text="Leave blank to disable JS8Call ingest.",
        bg=theme["panel_bg"],
        fg=theme["muted_fg"]
    ).grid(row=6, column=1, columnspan=2, sticky="w")

    # -------------------------
    # THEME
    # -------------------------

    tk.Label(form_frame, text="Theme", bg=theme["panel_bg"], fg=theme["fg"]).grid(row=7, column=0, sticky="w", pady=6)

    theme_var = tk.StringVar(value=existing_theme.title())

    ttk.Combobox(
        form_frame,
        textvariable=theme_var,
        values=["Light", "Dark", "High Flight", "Woodlands", "Leatherneck", "Midwatch"],
        state="readonly"
    ).grid(row=7, column=1, columnspan=2, sticky="ew")

    form_frame.columnconfigure(1, weight=1)

    # -------------------------
    # SAVE
    # -------------------------

    def save_setup():
        global config

        config.update({
            "callsign": callsign_entry.get().strip().upper(),
            "grid": grid_entry.get().strip().upper(),
            "group": group_entry.get().strip().lstrip("@"),
            "varac_db_path": varac_db_entry.get().strip(),
            "js8call_directed_path": js8call_entry.get().strip(),
            "theme": theme_var.get().lower(),
            "show_setup_on_start": False,
        })

        save_config()
        apply_theme()
        click_status_var.set("Station setup saved")

        win.destroy()

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Font Sizes",
        command=open_font_sizes_window,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Cancel",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    tk.Button(
        button_frame,
        text="Save",
        command=save_setup,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right", padx=6)

    win.deiconify()
    callsign_entry.focus_set()


def open_font_sizes_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Font Sizes")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=12, pady=12)

    form_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=12,
        pady=12
    )
    form_frame.pack(fill="both", expand=True)

    tk.Label(
        form_frame,
        text="Adjust feed font sizes",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 10, "bold")
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

    tk.Label(
        form_frame,
        text="JS8Call Activity Feed",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))

    tk.Label(
        form_frame,
        text="VarAC Activity Feed",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=2, column=0, sticky="w", pady=6, padx=(0, 10))

    tk.Label(
        form_frame,
        text="Gateway Dashboard",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=3, column=0, sticky="w", pady=6, padx=(0, 10))

    varalert_var = tk.IntVar(value=int(config.get("varalert_feed_font_size", 14)))
    broadcast_var = tk.IntVar(value=int(config.get("broadcast_feed_font_size", 11)))
    telegram_var = tk.IntVar(value=int(config.get("telegram_dashboard_font_size", 13)))

    varalert_spin = tk.Spinbox(
        form_frame,
        from_=8,
        to=24,
        width=6,
        textvariable=varalert_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    varalert_spin.grid(row=1, column=1, sticky="w", pady=6)

    broadcast_spin = tk.Spinbox(
        form_frame,
        from_=8,
        to=24,
        width=6,
        textvariable=broadcast_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    broadcast_spin.grid(row=2, column=1, sticky="w", pady=6)

    telegram_spin = tk.Spinbox(
        form_frame,
        from_=8,
        to=24,
        width=6,
        textvariable=telegram_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    telegram_spin.grid(row=3, column=1, sticky="w", pady=6)

    sample_frame = tk.Frame(
        form_frame,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=10,
        pady=10
    )
    sample_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(14, 0))

    preview_label = tk.Label(
        sample_frame,
        text="Preview",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 10, "bold")
    )
    preview_label.pack(anchor="w")

    varalert_preview = tk.Label(
        sample_frame,
        text="03-29 18:42 KG5VPF  SNR:+08  20m  HRMS  EM54ML  Priority  All Good",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        anchor="w",
        justify="left"
    )
    varalert_preview.pack(anchor="w", pady=(8, 6), fill="x")

    broadcast_preview = tk.Label(
        sample_frame,
        text="03-29 18:42  KG5VPF     +08  20m   Test broadcast traffic line",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        anchor="w",
        justify="left"
    )
    broadcast_preview.pack(anchor="w", pady=6, fill="x")

    telegram_preview = tk.Label(
        sample_frame,
        text="[T][A] KG5VPF 20m +08 00:14",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        anchor="w",
        justify="left"
    )
    telegram_preview.pack(anchor="w", pady=6, fill="x")

    note_label = tk.Label(
        form_frame,
        text="Defaults: GridLink 14, Broadcast 11, Telegram 13",
        bg=theme["panel_bg"],
        fg=theme["muted_fg"],
        anchor="w",
        justify="left"
    )
    note_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))

    form_frame.columnconfigure(2, weight=1)
    form_frame.rowconfigure(4, weight=1)

    def refresh_preview():
        varalert_preview.config(font=("Courier", int(varalert_var.get())))
        broadcast_preview.config(font=("Arial", int(broadcast_var.get())))
        telegram_preview.config(font=("Courier", int(telegram_var.get())))

    def close_font_window():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    def apply_changes():
        try:
            config["varalert_feed_font_size"] = int(varalert_var.get())
            config["broadcast_feed_font_size"] = int(broadcast_var.get())
            config["telegram_dashboard_font_size"] = int(telegram_var.get())
        except Exception:
            messagebox.showwarning("Font Sizes", "Please enter valid whole-number font sizes.")
            return

        save_config()

        try:
            statrep_list.config(font=("Courier", config["varalert_feed_font_size"]))
        except Exception:
            pass

        try:
            broadcast_feed_text.config(font=("Arial", config["broadcast_feed_font_size"]))
        except Exception:
            pass

        try:
            gateway_text.config(font=("Courier", config["telegram_dashboard_font_size"]))
        except Exception:
            pass

        try:
            click_status_var.set("Font sizes updated")
        except Exception:
            pass

    def save_and_close():
        apply_changes()
        close_font_window()

    def restore_defaults():
        varalert_var.set(14)
        broadcast_var.set(11)
        telegram_var.set(13)
        refresh_preview()

    varalert_spin.configure(command=refresh_preview)
    broadcast_spin.configure(command=refresh_preview)
    telegram_spin.configure(command=refresh_preview)

    varalert_spin.bind("<KeyRelease>", lambda e: refresh_preview())
    broadcast_spin.bind("<KeyRelease>", lambda e: refresh_preview())
    telegram_spin.bind("<KeyRelease>", lambda e: refresh_preview())

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Defaults",
        command=restore_defaults,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Apply",
        command=apply_changes,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=(6, 0))

    tk.Button(
        button_frame,
        text="Save",
        command=save_and_close,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    tk.Button(
        button_frame,
        text="Cancel",
        command=close_font_window,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right", padx=(0, 6))

    win.protocol("WM_DELETE_WINDOW", close_font_window)

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 620, 430, min_width=560, min_height=390)
    refresh_preview()


def choose_log_file():
    
    global config, log_watcher

    initial_dir = config.get("traffic_log_path", "")
    if initial_dir:
        initial_dir = str(Path(initial_dir).parent) if Path(initial_dir).exists() else str(Path.home())
    else:
        initial_dir = str(Path.home())

    path = filedialog.askopenfilename(
        title="Select VarAC Traffic Log",
        initialdir=initial_dir,
        filetypes=[("Log files", "*.log"), ("All files", "*.*")]
    )

    if not path:
        return

    config["traffic_log_path"] = path
    save_config()

    log_watcher = VarACLogWatcher(path, start_at_end=True)

    messagebox.showinfo(
        "Traffic Log Selected",
        f"VarAC traffic log set to:\n\n{path}\n\nLive monitoring will use this file."
    )

def choose_varac_db_file():
    global config

    initial_dir = config.get("varac_db_path", "")
    if initial_dir:
        initial_dir = str(Path(initial_dir).parent) if Path(initial_dir).exists() else str(Path.home())
    else:
        initial_dir = str(Path.home())

    path = filedialog.askopenfilename(
        title="Select VarAC SQLite Database",
        initialdir=initial_dir,
        filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
    )

    if not path:
        return

    config["varac_db_path"] = path
    save_config()

    messagebox.showinfo(
        "VarAC Database Selected",
        f"VarAC SQLite database set to:\n\n{path}"
    )


def choose_js8call_directed_file():
    global config

    initial_dir = config.get("js8call_directed_path", "")
    if initial_dir:
        initial_dir = str(Path(initial_dir).parent) if Path(initial_dir).exists() else str(Path.home())
    else:
        initial_dir = str(Path.home())

    path = filedialog.askopenfilename(
        title="Select JS8Call DIRECTED.TXT",
        initialdir=initial_dir,
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not path:
        return

    config["js8call_directed_path"] = path
    save_config()

    messagebox.showinfo(
        "JS8Call DIRECTED.TXT Selected",
        f"JS8Call DIRECTED.TXT set to:\n\n{path}"
    )  


# ============================================================
# PHASE 4 - REPLY WORKFLOW (POLLING)
# ============================================================

import requests

def poll_relay_for_replies():
    global pending_replies, last_reply_ids, active_gateway_callsigns

    gateway_callsign = (config.get("callsign", "") or "").strip().upper()

    if not gateway_callsign:
        add_relay_log("Reply polling skipped: callsign not configured")
        return

    relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")

    # Persistent state for logging / offline behavior
    if not hasattr(poll_relay_for_replies, "_last_logged_active_gateways"):
        poll_relay_for_replies._last_logged_active_gateways = None

    if not hasattr(poll_relay_for_replies, "_relay_online"):
        poll_relay_for_replies._relay_online = True

    # -------------------------
    # FETCH ACTIVE GATEWAYS
    # -------------------------
    active_result = fetch_active_gateways()

    relay_online_now = active_result["ok"]

    if relay_online_now:
        active_gateway_callsigns = active_result["gateways"]

        if not poll_relay_for_replies._relay_online:
            add_relay_log("Relay connection restored. Returning to hybrid RF + Internet gateway view.")

        current_active_tuple = tuple(active_gateway_callsigns)

        if current_active_tuple != poll_relay_for_replies._last_logged_active_gateways:
            if active_gateway_callsigns:
                add_relay_log(
                    f"Active Gateways ({len(active_gateway_callsigns)}): "
                    + ", ".join(active_gateway_callsigns)
                )
            else:
                add_relay_log("Active Gateways (0): none")

            poll_relay_for_replies._last_logged_active_gateways = current_active_tuple

    else:
        # Relay offline: force RF-only logic
        active_gateway_callsigns = []

        if poll_relay_for_replies._relay_online:
            add_relay_log("Relay unreachable. Switching Telegram Dashboard to RF-only mode.")
            try:
                click_status_var.set("Relay offline: RF-only gateway view active")
            except Exception:
                pass

        # Reset so a fresh gateway summary is logged when relay returns
        poll_relay_for_replies._last_logged_active_gateways = None

    poll_relay_for_replies._relay_online = relay_online_now

    # Dashboard should refresh either way
    refresh_gateway_dashboard()

    # If relay is offline, skip reply polling but keep app functional
    if not relay_online_now:
        update_reply_button_state()
        return

    # -------------------------
    # FETCH PENDING REPLIES
    # -------------------------
    try:
        add_relay_log(f"Polling relay for replies for gateway {gateway_callsign}...")

        response = requests.get(
            f"{relay_url}/pending_replies",
            params={"gateway": gateway_callsign},
            timeout=10
        )

        if response.status_code != 200:
            add_relay_log(f"Reply polling failed: HTTP {response.status_code}")
            return

        data = response.json()

        if not data.get("ok", False):
            add_relay_log("Relay returned non-OK status for pending replies")
            return

        replies = data.get("replies", [])

        for r in replies:
            add_relay_log(
                "Reply debug: "
                f"id={r.get('reply_id')} "
                f"alias={r.get('telegram_alias')} "
                f"transport={r.get('reply_transport')} "
                f"from={r.get('original_rf_callsign')} "
                f"relay_call={r.get('relay_call')} "
                f"is_relayed={r.get('is_relayed')}"
            )

            add_relay_log(
                "Reply fields: "
                f"original_subject={repr(r.get('original_subject'))} "
                f"| original_body={repr(r.get('original_body'))} "
                f"| reply_subject={repr(r.get('reply_subject'))} "
                f"| gateway_callsign={repr(r.get('gateway_callsign'))}"
            )   

        new_replies = []
        for r in replies:
            reply_id = r.get("reply_id")

            if reply_id not in last_reply_ids:
                last_reply_ids.add(reply_id)
                new_replies.append(r)

        if new_replies:
            add_relay_log(f"Received {len(new_replies)} new reply message(s)")

        pending_replies[:] = replies
        update_reply_button_state()

    except Exception as e:
        add_relay_log(f"Reply polling error: {e}")

def test_relay_connection():
    try:
        relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")

        response = requests.get(f"{relay_url}/status", timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                add_relay_log("Relay connection test successful")
                return True, "Relay reachable"
            
            add_relay_log("Relay responded but not OK")
            return False, "Relay responded but not OK"
        
        add_relay_log(f"Relay HTTP error: {response.status_code}")
        return False, f"HTTP {response.status_code}"

    except Exception as e:
        add_relay_log(f"Relay connection exception: {e}")
        return False, str(e)

def fetch_active_gateways():
    relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")

    try:
        response = requests.get(
            f"{relay_url}/active_gateways",
            timeout=5
        )

        if response.status_code != 200:
            add_relay_log(f"Active gateway fetch failed: HTTP {response.status_code}")
            return {
                "ok": False,
                "gateways": []
            }

        data = response.json()

        if not data.get("ok", False):
            add_relay_log("Relay returned non-OK status while fetching active gateways")
            return {
                "ok": False,
                "gateways": []
            }

        gateways = data.get("gateways", [])
        active_callsigns = []

        for item in gateways:
            callsign = (item.get("gateway_callsign", "") or "").strip().upper()
            if callsign:
                active_callsigns.append(callsign)

        active_callsigns = sorted(set(active_callsigns))

        return {
            "ok": True,
            "gateways": active_callsigns
        }

    except Exception as e:
        add_relay_log(f"Active gateway fetch exception: {e}")
        return {
            "ok": False,
            "gateways": []
        }

def update_reply_button_state():
    try:
        theme = get_theme()
        count = len(pending_replies)

        if count > 0:
            reply_button.config(
                text=f"Gateway\nRelay ({count})",
                bg="red",
                fg="white",
                activebackground="red",
                activeforeground="white"
            )
        else:
            reply_button.config(
                text="Gateway\nRelay",
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_bg"],
                activeforeground=theme["button_fg"]
            )
    except Exception:
        pass

def mark_reply_handled_on_relay(reply_id):
    try:
        relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")

        response = requests.post(
            f"{relay_url}/mark_reply_handled",
            json={"reply_id": reply_id},
            timeout=5
        )

        if response.status_code != 200:
            add_relay_log(f"Mark handled HTTP error: {response.status_code}")
            return False, f"HTTP {response.status_code}"

        data = response.json()

        if data.get("ok"):
            add_relay_log(f"Reply {reply_id} marked handled on relay")
            return True, "Handled"

        error_message = data.get("error", "Unknown relay error")
        add_relay_log(f"Mark handled failed: {error_message}")
        return False, error_message

    except Exception as e:
        add_relay_log(f"Mark handled exception: {e}")
        return False, str(e)
    
def send_telegram_message(telegram_alias, message_text):
    try:
        gateway = config.get("callsign", "").strip().upper()
        relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")

        telegram_alias = (telegram_alias or "").strip()
        message_text = (message_text or "").strip()

        if not gateway:
            add_relay_log("Send failed: callsign not configured")
            return False, "Callsign not configured"

        if not telegram_alias:
            add_relay_log("Send failed: Telegram alias missing")
            return False, "Telegram alias missing"

        if not message_text:
            add_relay_log("Send failed: message text is empty")
            return False, "Message text is empty"

        payload = {
            "source": "GridLink",
            "callsign": gateway,
            "telegram_alias": telegram_alias,
            "message": message_text,
            "client_version": APP_VERSION
        }

        add_relay_log(f"Sending Telegram message to {telegram_alias}...")

        response = requests.post(
            f"{relay_url}/send_message",
            json=payload,
            timeout=8
        )

        if response.status_code != 200:
            add_relay_log(f"Send HTTP error: {response.status_code}")
            return False, f"HTTP {response.status_code}"

        data = response.json()

        if data.get("ok"):
            add_relay_log(f"Telegram send successful to {telegram_alias}")
            return True, data.get("status", "sent")

        error_message = data.get("error", "Unknown relay error")
        add_relay_log(f"Telegram send failed: {error_message}")
        return False, error_message

    except Exception as e:
        add_relay_log(f"Telegram send exception: {e}")
        return False, str(e)


# -------------------------
# SQLITE ACCESS
# ------------------------- 

def get_varac_db_path():
    path = config.get("varac_db_path", "").strip() if "config" in globals() else ""
    if path:
        return Path(path)
    return VARAC_DB_FILE

def test_sqlite_connection():
    """
    Simple test: read a few rows from the VarAC broadcast table.
    This does not change program behavior yet.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        print(f"VarAC database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, broadcast_time, from_callsign, broadcast_message
            FROM broadcast
            ORDER BY id DESC
            LIMIT 5
        """)

        rows = cursor.fetchall()

        print("\nLatest broadcasts from SQLite database:")
        for row in rows:
            print(row)

        conn.close()

    except Exception as e:
        print(f"SQLite test error: {e}")


def load_messages_from_db():
    """
    Load existing VarAC broadcast history from the VarAC SQLite database
    as generic RF activity.
    """
    global messages

    db_path = get_varac_db_path()

    if not db_path.exists():
        print(f"VarAC database not found: {db_path}")
        return False

    messages.clear()
    seen_message_keys.clear()

    loaded_count = 0

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, broadcast_time, from_callsign, to_callsign, band, broadcast_message, snr
            FROM broadcast
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            raw = (row["broadcast_message"] or "").strip()
            if not raw:
                continue

            try:
                timestamp = datetime.datetime.now()
                try:
                    ts = row["broadcast_time"].replace("Z", "")
                    if "." in ts:
                        main_part, frac_part = ts.split(".", 1)
                        frac_part = (frac_part + "000000")[:6]
                        ts = f"{main_part}.{frac_part}"
                        timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

                item = make_message_record(
                    raw=raw,
                    timestamp=timestamp,
                    from_call=(row["from_callsign"] or "").strip(),
                    to_call=(row["to_callsign"] or "").strip(),
                    band=(row["band"] or "").strip(),
                    snr=row["snr"],
                    log_timestamp_text=str(row["broadcast_time"]),
                    message_timestamp_text=str(row["broadcast_time"]),
                    raw_line=f"SQLITE::{row['id']}::{raw}",
                    source="varac"
                )

                # Try to enrich map placement from any grid found in the text.
                grid = find_grid_in_js8_text(raw)
                if grid:
                    item["parsed"]["grid"] = grid
                    try:
                        item["lat"], item["lon"] = to_location(grid)
                    except Exception:
                        pass

                if register_message_if_new(item):
                    loaded_count += 1

            except Exception as e:
                print(f"SQLite row load error: {e} | message={raw}")

        apply_filter(current_filter_days)
        print(f"Loaded {loaded_count} VarAC broadcast message(s) from SQLite database.")
        click_status_var.set(
            f"Loaded {loaded_count} VarAC broadcast message(s) from database: {db_path}"
        )
        return True

    except Exception as e:
        print(f"SQLite load error: {e}")
        click_status_var.set(f"SQLite load error: {e}")
        return False


def find_grid_in_js8_text(text):
    """
    Try to find a Maidenhead grid square in JS8Call text.
    Accepts 4 or 6 character grids such as EM54 or EM54ML.
    """
    text = (text or "").upper()

    matches = re.findall(r"\b[A-R]{2}[0-9]{2}(?:[A-X]{2})?\b", text)

    for match in matches:
        if looks_like_grid(match):
            return match

    return ""

def resolve_grid_for_js8_station(callsign, raw_message):
    """
    Resolve station grid for JS8 map plotting.

    Order:
    1. Grid found in JS8 message text
    2. Callsign database grid
    3. Local activity enrichment
    """
    callsign = (callsign or "").strip().upper()

    grid = find_grid_in_js8_text(raw_message)
    if grid:
        return grid, "JS8 message"

    record = lookup_callsign_in_db(callsign)
    if record:
        db_grid = (record.get("grid") or "").strip().upper()
        if looks_like_grid(db_grid):
            return db_grid, "Callsign database"

        zipcode = (record.get("zipcode") or "").strip()
        zip_grid, zip_source = find_grid_from_zipcode(zipcode)
        if zip_grid and looks_like_grid(zip_grid):
            return zip_grid, zip_source or "ZIP code estimate"

    found_grid, found_source = find_grid_from_local_activity(callsign)
    if found_grid and looks_like_grid(found_grid):
        return found_grid, found_source or "Local activity"

    return "", ""

def load_messages_from_js8call():
    """
    Load all heard JS8Call activity lines from DIRECTED.TXT into the main feed.
    """
    loaded_count = 0

    lines = read_js8call_directed_lines()
    if not lines:
        return 0

    # Load enough startup history to support all filter menu choices.
    # The visible filter is applied separately by apply_filter(current_filter_days).
    filter_hours = 48
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=filter_hours)

    for line in lines:
        try:
            parts = line.split("\t")
            if len(parts) < 5:
                continue

            timestamp_text = parts[0].strip()
            frequency_text = parts[1].strip()
            snr_text = parts[3].strip()
            payload = parts[4].strip()

            if ":" not in payload:
                continue

            from_call, raw_message = payload.split(":", 1)
            from_call = from_call.strip().upper()
            raw_message = raw_message.strip()

            if raw_message.endswith("♢"):
                raw_message = raw_message[:-1].rstrip()

            try:
                timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            # Skip old lines (huge performance boost)
            if timestamp < cutoff:
                continue

            try:
                snr_value = int(snr_text)
            except Exception:
                snr_value = snr_text

            try:
                frequency = float(frequency_text)
            except Exception:
                frequency = 0.0

            band = "?"
            if 14.0 <= frequency < 14.35:
                band = "20m"
            elif 7.0 <= frequency < 7.3:
                band = "40m"
            elif 21.0 <= frequency < 21.45:
                band = "15m"
            elif 28.0 <= frequency < 29.7:
                band = "10m"
            elif 3.5 <= frequency < 4.0:
                band = "80m"
            elif 1.8 <= frequency < 2.0:
                band = "160m"
            elif 18.068 <= frequency < 18.168:
                band = "17m"
            elif 24.89 <= frequency < 24.99:
                band = "12m"
            elif 50.0 <= frequency < 54.0:
                band = "6m"

            # --- NEW: resolve grid using fallback chain ---
            grid, grid_source = resolve_grid_for_js8_station(from_call, raw_message)

            lat, lon = None, None

            if grid:
                try:
                    lat, lon = maidenhead_to_latlon(grid)
                except Exception:
                    lat, lon = None, None

            item = {
                "source": "js8call",
                "timestamp": timestamp,
                "from_call": from_call,
                "to_call": "",
                "band": band,
                "snr": snr_value,
                "raw": raw_message,
                "raw_line": line,
                "grid": grid,
                "grid_source": grid_source,
                "lat": lat,
                "lon": lon,
            }

            if register_message_if_new(item):
                loaded_count += 1

        except Exception as e:
            print(f"JS8Call startup parse error: {e} | line={line}")

    if loaded_count:
        print(f"Loaded {loaded_count} JS8Call activity line(s) from DIRECTED.TXT.")

    return loaded_count


def load_broadcast_feed_from_db():
    """
    Load existing VarAC broadcast history from the VarAC SQLite database
    into the left dashboard feed.
    """
    global broadcast_messages

    db_path = get_varac_db_path()

    if not db_path.exists():
        print(f"VarAC database not found: {db_path}")
        return False

    broadcast_messages.clear()

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, broadcast_time, from_callsign, broadcast_message, snr, band
            FROM broadcast
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        loaded_count = 0

        for row in rows:
            raw = (row["broadcast_message"] or "").strip()

            timestamp = datetime.datetime.now()
            try:
                ts = str(row["broadcast_time"]).replace("Z", "")
                if "." in ts:
                    main_part, frac_part = ts.split(".", 1)
                    frac_part = (frac_part + "000000")[:6]
                    ts = f"{main_part}.{frac_part}"
                    timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

            broadcast_messages.append({
                "timestamp": timestamp,
                "from_call": (row["from_callsign"] or "").strip(),
                "message": raw,
                "snr": row["snr"],
                "band": (row["band"] or "").strip()
            })

            if len(broadcast_messages) > BROADCAST_MEMORY_LIMIT:
                broadcast_messages = broadcast_messages[-BROADCAST_MEMORY_LIMIT:]

            loaded_count += 1

        refresh_broadcast_feed()
        print(f"Loaded {loaded_count} broadcast message(s) from SQLite database.")
        return True

    except Exception as e:
        print(f"Broadcast feed load error: {e}")
        return False
    

def get_max_broadcast_id():
    """
    Return the highest broadcast.id currently in the VarAC database.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(id) FROM broadcast")
        row = cursor.fetchone()
        conn.close()

        if not row or row[0] is None:
            return 0

        return int(row[0])

    except Exception as e:
        print(f"SQLite max-id error: {e}")
        return 0


def get_new_broadcast_rows(after_id):
    """
    Return broadcast rows with id greater than after_id.
    Rows are returned in ascending order.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, broadcast_time, from_callsign, to_callsign, band, broadcast_message, snr
            FROM broadcast
            WHERE id > ?
            ORDER BY id ASC
        """, (after_id,))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"SQLite incremental read error: {e}")
        return []


def initialize_cqframe_last_id():
    """
    Load recent VarAC cqframe rows at startup using the
    currently selected filter window.

    This allows GridLink to restore recent VarAC beacon/heard
    markers after restart while still preventing huge historical
    database loads.
    """
    global last_cqframe_id

    try:
        hours = max(1, int(current_filter_days * 24))

        rows = get_recent_cqframe_rows(hours=hours)

        if rows:
            process_new_cqframe_rows(rows)

            try:
                last_cqframe_id = max(int(r["id"]) for r in rows)
            except Exception:
                pass

        print(
            f"Initialized VarAC cqframe monitor with "
            f"{len(rows)} recent rows"
        )

    except Exception as e:
        print(f"CQ frame startup initialization error: {e}")


def get_new_cqframe_rows(after_id):
    """
    Return cqframe rows with id greater than after_id.
    Rows are returned in ascending order.
    Used to add VarAC heard/beacon stations to the map.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, cqframe_time, cqframe_type_id, from_callsign, band, frequency, snr,
                   locator, is_email_gateway, is_ai_gateway, is_bbs
            FROM cqframe
            WHERE id > ?
            ORDER BY id ASC
        """, (after_id,))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"CQ frame incremental read error: {e}")
        return []


def get_recent_datastream_rows(hours=3):
    """
    Return datastream rows from the last X hours.
    Used for beacon detection.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, creation_time, entry
            FROM datastream
            WHERE creation_time >= datetime('now', ?)
              AND is_deleted = 0
            ORDER BY creation_time ASC
        """, (f"-{hours} hours",))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"Datastream query error: {e}")
        return []

def debug_recent_datastream_rows(hours=3, limit=20):
    """
    Print recent datastream rows so we can confirm field names/content.
    """
    rows = get_recent_datastream_rows(hours=hours)

    print("\n===== RECENT DATASTREAM ROWS =====")
    print(f"Row count: {len(rows)}")

    for row in rows[-limit:]:
        try:
            print(dict(row))
        except Exception:
            print(row)

    print("===== END DATASTREAM ROWS =====\n")

def debug_datastream_schema():
    """
    Print datastream table schema so we can see actual column names.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        print("VarAC database not found for schema debug.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(datastream)")
        rows = cursor.fetchall()
        conn.close()

        print("\n===== DATASTREAM SCHEMA =====")
        for row in rows:
            print(row)
        print("===== END DATASTREAM SCHEMA =====\n")

    except Exception as e:
        print(f"Datastream schema debug error: {e}")

def get_qso_rows_for_callsign(callsign, lookback_days):
    """
    Return QSO rows for a callsign using clean_callsign,
    limited to the requested lookback window.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, starttime, endtime, callsign, clean_callsign,
                   band, frequency, snr_received, snr_sent, locator
            FROM qso
            WHERE UPPER(TRIM(clean_callsign)) = ?
              AND starttime >= datetime('now', ?)
            ORDER BY starttime ASC
        """, (callsign, f"-{lookback_days} days"))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"QSO query error: {e}")
        return []

def get_cqframe_rows_for_callsign(callsign, lookback_days):
    """
    Return heard/beacon rows for a callsign from cqframe,
    limited to the requested lookback window.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, cqframe_time, from_callsign, band, frequency, snr, locator
            FROM cqframe
            WHERE UPPER(TRIM(from_callsign)) = ?
              AND cqframe_time >= datetime('now', ?)
            ORDER BY cqframe_time ASC
        """, (callsign, f"-{lookback_days} days"))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"CQ frame callsign query error: {e}")
        return []

def get_broadcast_rows_for_callsign(callsign):
    """
    Return broadcast rows where the target callsign appears as either
    the sender or recipient. Rows are returned in ascending time order.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, broadcast_time, from_callsign, to_callsign, band, broadcast_message, snr
            FROM broadcast
            WHERE UPPER(TRIM(from_callsign)) = ?
               OR UPPER(TRIM(to_callsign)) = ?
            ORDER BY id ASC
        """, (callsign, callsign))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"Callsign broadcast query error: {e}")
        return []
    
def get_recent_cqframe_rows(hours=3):
    """
    Return recent heard-station rows from cqframe.
    Used for gateway activity detection.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, cqframe_time, from_callsign, band, frequency, snr,
                   locator, is_email_gateway, is_ai_gateway, is_bbs
            FROM cqframe
            WHERE cqframe_time >= datetime('now', ?)
            ORDER BY cqframe_time ASC
        """, (f"-{hours} hours",))

        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        print(f"CQ frame query error: {e}")
        return []


# ============================================================
# BETA READINESS - VMAIL TRIGGER HELPERS
# ============================================================

def load_last_processed_vmail_id():
    """
    Load the last processed vmail id from disk.
    Returns 0 if the file does not exist or is invalid.
    """
    try:
        if LAST_VMAIL_ID_FILE.exists():
            text = LAST_VMAIL_ID_FILE.read_text(encoding="utf-8").strip()
            return int(text) if text else 0
    except Exception as e:
        add_relay_log(f"Warning: could not read {LAST_VMAIL_ID_FILE}: {e}")

    return 0


def save_last_processed_vmail_id(vmail_id):
    """
    Save the last processed vmail id to disk.
    """
    try:
        LAST_VMAIL_ID_FILE.write_text(str(int(vmail_id)), encoding="utf-8")
    except Exception as e:
        add_relay_log(f"Warning: could not write {LAST_VMAIL_ID_FILE}: {e}")


def get_starting_highest_vmail_id():
    db_path = get_varac_db_path()

    if not db_path.exists():
        raise FileNotFoundError(f"VarAC database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM vmail")
        row = cur.fetchone()
        return int(row["max_id"]) if row else 0
    finally:
        conn.close()


def fetch_new_trigger_messages(last_id):
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    gateway_callsign = (config.get("callsign", "") or "").strip().upper()
    if not gateway_callsign:
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                received_time,
                folder_id,
                vmail_to,
                vmail_from,
                subject,
                msg,
                delivery_snr
            FROM vmail
            WHERE id > ?
              AND folder_id = 1
              AND UPPER(TRIM(vmail_to)) = UPPER(TRIM(?))
              AND subject LIKE 'TG:%'
            ORDER BY id ASC
            """,
            (last_id, gateway_callsign)
        )
        return cur.fetchall()
    finally:
        conn.close()


def fetch_recent_trigger_messages(hours=2, after_id=0):
    """
    Return recent Inbox TG: vMail rows for startup recovery.

    This is the VarAC equivalent of JS8Call's 120-minute recovery scan.
    It only returns rows newer than after_id so previously processed vMail
    messages are not sent twice after GridLink restarts.
    """
    db_path = get_varac_db_path()

    if not db_path.exists():
        return []

    gateway_callsign = (config.get("callsign", "") or "").strip().upper()
    if not gateway_callsign:
        return []

    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=hours)
    cutoff_text = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                received_time,
                folder_id,
                vmail_to,
                vmail_from,
                subject,
                msg,
                delivery_snr
            FROM vmail
            WHERE id > ?
              AND folder_id = 1
              AND UPPER(TRIM(vmail_to)) = UPPER(TRIM(?))
              AND subject LIKE 'TG:%'
              AND received_time >= ?
            ORDER BY id ASC
            """,
            (after_id, gateway_callsign, cutoff_text)
        )
        return cur.fetchall()
    finally:
        conn.close()


def recover_recent_varac_telegram_triggers():
    """
    On GridLink startup, scan recent VarAC Inbox TG: vMail messages
    from the last 120 minutes.

    Duplicate protection is based on the stable VarAC vMail id saved in
    last_vmail_id.txt. This prevents duplicate Telegram sends after restart.
    """
    global highest_processed_vmail_id

    try:
        saved_last_id = load_last_processed_vmail_id()

        # First run safety: do not back-send old messages if there is no saved state yet.
        if saved_last_id <= 0:
            try:
                current_db_max_id = get_starting_highest_vmail_id()
                highest_processed_vmail_id = current_db_max_id
                save_last_processed_vmail_id(highest_processed_vmail_id)
                add_relay_log(
                    f"VarAC startup recovery initialized at vMail id {highest_processed_vmail_id}"
                )
            except Exception as e:
                add_relay_log(f"VarAC startup recovery init skipped: {e}")
            return

        highest_processed_vmail_id = saved_last_id

        rows = fetch_recent_trigger_messages(hours=2, after_id=saved_last_id)

        if not rows:
            add_relay_log("VarAC startup recovery found no new recent TG: messages.")
            return

        add_relay_log(
            f"VarAC startup recovery found {len(rows)} recent TG: message(s)."
        )

        recovered_count = 0

        for row in rows:
            parsed = parse_trigger_message(row)

            add_relay_log(
                f"VarAC recovery match: id={parsed['id']} "
                f"from={parsed['from_call']} "
                f"alias={parsed['alias']} "
                f"snr={parsed['snr']}"
            )

            if not parsed["alias"]:
                add_relay_log(
                    f"Skipping recovery id={parsed['id']}: subject missing alias after TG:"
                )
                highest_processed_vmail_id = max(highest_processed_vmail_id, parsed["id"])
                save_last_processed_vmail_id(highest_processed_vmail_id)
                continue

            payload = build_relay_trigger_payload(parsed)

            add_relay_log(
                f"Sending recovered VarAC trigger id={parsed['id']} "
                f"to relay for alias '{parsed['alias']}'..."
            )

            success, result = send_trigger_to_relay(payload)

            if success:
                recovered_count += 1
                add_relay_log(f"SUCCESS recovery id={parsed['id']}: {result}")
                try:
                    click_status_var.set(
                        f"Recovered VarAC TG trigger sent for alias {parsed['alias']} "
                        f"(vMail {parsed['id']})"
                    )
                except Exception:
                    pass
            else:
                add_relay_log(f"FAILED recovery id={parsed['id']}: {result}")
                try:
                    click_status_var.set(
                        f"Recovered VarAC TG trigger failed for alias {parsed['alias']} "
                        f"(vMail {parsed['id']})"
                    )
                except Exception:
                    pass

            # Match existing VarAC live workflow: advance/save processed id
            # after the row has been handled so restart does not duplicate it.
            highest_processed_vmail_id = max(highest_processed_vmail_id, parsed["id"])
            save_last_processed_vmail_id(highest_processed_vmail_id)

        add_relay_log(
            f"VarAC startup recovery processed {recovered_count} TG: trigger(s)."
        )

    except Exception as e:
        add_relay_log(f"VarAC startup recovery error: {e}")


def parse_trigger_message(row):
    subject = (row["subject"] or "").strip()
    alias = ""

    if ":" in subject:
        alias = subject.split(":", 1)[1].strip()

    return {
        "id": row["id"],
        "received_time": (row["received_time"] or "").strip(),
        "to_call": (row["vmail_to"] or "").strip(),
        "from_call": (row["vmail_from"] or "").strip(),
        "subject": subject,
        "alias": alias,
        "body": (row["msg"] or "").strip(),
        "snr": "" if row["delivery_snr"] is None else str(row["delivery_snr"]).strip(),
    }


def build_telegram_text(parsed):
    return "\n".join([
        "GridLink Gateway Trigger",
        "",
        f"Alias: {parsed['alias']}",
        f"From: {parsed['from_call']}",
        f"To Gateway: {parsed['to_call']}",
        f"Received: {parsed['received_time']}",
        f"SNR: {parsed['snr']}",
        "",
        "Message:",
        parsed["body"] or "(no body text)"
    ])


def build_relay_trigger_payload(parsed):
    return {
        "alias": parsed["alias"],
        "message": build_telegram_text(parsed),
        "from_callsign": parsed["from_call"],
        "gateway_callsign": parsed["to_call"],
        "original_rf_callsign": parsed["from_call"],
        "original_subject": parsed["subject"],
        "original_body": parsed["body"],
        "original_vmail_id": parsed["id"],
        "received_time": parsed["received_time"],
        "delivery_snr": parsed["snr"],
    }


def send_trigger_to_relay(payload):
    try:
        relay_url = config.get("relay_url", "https://relay.varalert.net").rstrip("/")
        trigger_url = f"{relay_url}/trigger"

        response = requests.post(trigger_url, json=payload, timeout=10)
        response.raise_for_status()

        try:
            return True, str(response.json())
        except Exception:
            return True, response.text

    except Exception as e:
        return False, str(e)


def build_js8_trigger_payload(parsed):
    """
    Build relay payload from a parsed JS8Call TG: trigger message.
    Includes relay metadata when the JS8 message arrived through a relay station.
    """
    relay_call = parsed.get("relay_call", "")
    is_relayed = parsed.get("is_relayed", False)

    relay_lines = []
    if is_relayed and relay_call:
        relay_lines = [
            f"Relay Station: {relay_call}",
            "Relay Path: Yes",
        ]
    else:
        relay_lines = [
            "Relay Path: No",
        ]

    return {
        "alias": parsed["telegram_alias"],
        "reply_transport": "js8call",
        "message": "\n".join([
            "GridLink JS8Call Trigger",
            "",
            f"Alias: {parsed['telegram_alias']}",
            f"From: {parsed['from_call']}",
            f"To Gateway: {parsed['to_call']}",
            *relay_lines,
            f"Received: {parsed['timestamp_text']}",
            f"SNR: {parsed['snr_text']}",
            f"Frequency: {parsed['frequency']}",
            f"Offset: {parsed['offset']}",
            "",
            "Message:",
            parsed["message_text"] or "(no body text)"
        ]),
        "from_callsign": parsed["from_call"],
        "gateway_callsign": parsed["to_call"],
        "original_rf_callsign": parsed["from_call"],
        "relay_call": relay_call,
        "is_relayed": is_relayed,
        "original_subject": f"TG:{parsed['telegram_alias']}",
        "original_body": parsed["message_text"],
        "original_vmail_id": 0,
        "received_time": parsed["timestamp_text"],
        "delivery_snr": parsed["snr_text"],
    }


# -------------------------
# PARSING HELPERS
# -------------------------

def looks_like_grid(grid: str) -> bool:
    if not isinstance(grid, str):
        return False

    grid = grid.strip().upper()
    return bool(re.fullmatch(r"[A-R]{2}[0-9]{2}([A-X]{2})?", grid))


def parse_status_string(status_string):
    """
    Accepts either:
    - comma-separated status fields: grn,yel,red,...
    - a list/tuple of status values

    Returns a normalized structure for the current 11-field STATREP format.
    """
    if isinstance(status_string, (list, tuple)):
        values = [str(v).strip().lower() for v in status_string if str(v).strip()]
    else:
        text = (status_string or "").strip().lower()
        values = [part.strip() for part in text.split(",") if part.strip()] if text else []

    color_lookup = {
        "grn": "green",
        "yel": "yellow",
        "red": "red",
    }

    colors = [color_lookup.get(v, "gray") for v in values]

    if "red" in values:
        overall_color = "red"
    elif "yel" in values:
        overall_color = "yellow"
    elif "grn" in values:
        overall_color = "green"
    else:
        overall_color = "gray"

    return {
        "raw": ",".join(values),
        "values": values,
        "colors": colors,
        "overall_color": overall_color,
    }



# Removed unused JS8Call STATREP status decoder.

def read_js8call_directed_lines():
    path = config.get("js8call_directed_path", "").strip()

    if not path:
        return []

    file_path = Path(path)

    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines if line.strip()]
    except Exception as e:
        print(f"JS8Call read error: {e}")
        return []



# Removed duplicate unused JS8Call STATREP status decoder.

# -------------------------
# CALLSIGN DATABASE HELPERS
# -------------------------

def get_callsign_db_connection():
    """
    Open SQLite connection to the offline callsign database.
    Returns None if DB does not exist.
    """
    try:
        if not CALLSIGN_DB_FILE.exists():
            return None

        conn = sqlite3.connect(str(CALLSIGN_DB_FILE))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Callsign DB connection error: {e}")
        return None


def lookup_callsign_in_db(callsign):
    """
    Look up a callsign in the local SQLite database.

    Returns:
        dict with callsign info, or None if not found
    """
    callsign = (callsign or "").strip().upper()
    if not callsign:
        return None

    conn = get_callsign_db_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM callsigns
            WHERE callsign = ?
            LIMIT 1
            """,
            (callsign,)
        )

        row = cur.fetchone()

        if not row:
            return None

        # Convert row to dictionary safely
        result = dict(row)

        return result

    except Exception as e:
        print(f"Callsign lookup error: {e}")
        return None

    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_grid_to_callsign_db(callsign, grid):
    """
    Save a validated grid to callsigns.db for the given callsign.
    """
    callsign = (callsign or "").strip().upper()
    grid = (grid or "").strip().upper()

    if not callsign or not grid:
        return False

    if not looks_like_grid(grid):
        return False

    conn = get_callsign_db_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE callsigns
            SET grid = ?
            WHERE callsign = ?
        """, (grid, callsign))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"Save grid error: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def find_grid_from_local_activity(callsign):
    """
    Try to find a callsign's grid from local GridLink/VarAC/JS8 activity.

    Search order:
    1. Loaded STATREP messages in memory
    2. VarAC qso.locator
    3. VarAC cqframe.locator

    Returns:
        (grid, source_text) or (None, None)
    """
    callsign = (callsign or "").strip().upper()
    if not callsign:
        return None, None

    # 1. Loaded STATREP messages already in memory
    try:
        for item in reversed(messages):
            from_call = (item.get("from_call") or "").strip().upper()
            if from_call != callsign:
                continue

            parsed = item.get("parsed", {})
            grid = (parsed.get("grid") or "").strip().upper()
            if looks_like_grid(grid):
                return grid, "STATREP activity"
    except Exception as e:
        print(f"Message grid lookup error: {e}")

    db_path = get_varac_db_path()
    if not db_path.exists():
        return None, None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 2. QSO table locator
        cur.execute("""
            SELECT locator, starttime
            FROM qso
            WHERE UPPER(TRIM(clean_callsign)) = ?
              AND locator IS NOT NULL
              AND TRIM(locator) != ''
            ORDER BY starttime DESC
            LIMIT 20
        """, (callsign,))

        rows = cur.fetchall()
        for row in rows:
            grid = (row["locator"] or "").strip().upper()
            if looks_like_grid(grid):
                conn.close()
                return grid, "VarAC QSO locator"

        # 3. CQ frame locator
        cur.execute("""
            SELECT locator, cqframe_time
            FROM cqframe
            WHERE UPPER(TRIM(from_callsign)) = ?
              AND locator IS NOT NULL
              AND TRIM(locator) != ''
            ORDER BY cqframe_time DESC
            LIMIT 20
        """, (callsign,))

        rows = cur.fetchall()
        for row in rows:
            grid = (row["locator"] or "").strip().upper()
            if looks_like_grid(grid):
                conn.close()
                return grid, "VarAC CQ locator"

        conn.close()

    except Exception as e:
        print(f"Local activity grid lookup error: {e}")

    return None, None


def open_callsign_update_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Update Callsign Database")
    win.geometry("600x400")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(
        outer,
        text="Callsign Database Tools",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 12, "bold")
    ).pack(anchor="w", pady=(0, 8))

    # -------------------------
    # BUTTON FRAME
    # -------------------------
    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(0, 10))

    def download_data():
        log("Starting FCC data download...")

        try:
            DATA_DIR.mkdir(exist_ok=True)
            FCC_AMATEUR_EXTRACT_DIR.mkdir(exist_ok=True)

            log(f"Source: {FCC_AMATEUR_LICENSE_URL}")
            log(f"Saving ZIP to: {FCC_AMATEUR_ZIP_FILE}")

            response = requests.get(FCC_AMATEUR_LICENSE_URL, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_logged_mb = -1

            with open(FCC_AMATEUR_ZIP_FILE, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    downloaded_mb = downloaded // (1024 * 1024)
                    if downloaded_mb != last_logged_mb:
                        last_logged_mb = downloaded_mb
                        if total_size > 0:
                            total_mb = total_size / (1024 * 1024)
                            log(f"Downloaded {downloaded_mb} MB of {total_mb:.1f} MB...")
                        else:
                            log(f"Downloaded {downloaded_mb} MB...")

                    try:
                        win.update_idletasks()
                    except Exception:
                        pass

            log("Download complete.")
            log(f"Extracting ZIP into: {FCC_AMATEUR_EXTRACT_DIR}")

            with zipfile.ZipFile(FCC_AMATEUR_ZIP_FILE, "r") as zf:
                zf.extractall(FCC_AMATEUR_EXTRACT_DIR)
                names = zf.namelist()

            log(f"Extracted {len(names)} file(s).")

            important_files = ["HD.dat", "EN.dat", "AM.dat"]
            found = [name for name in important_files if (FCC_AMATEUR_EXTRACT_DIR / name).exists()]

            if found:
                log("Found key FCC files: " + ", ".join(found))
            else:
                log("Warning: key FCC files not found after extraction.")

            log("FCC data download step finished successfully.")

        except Exception as e:
            log(f"Download failed: {e}")

    def build_database():
        log("Building callsign database...")

        try:
            hd_file = FCC_AMATEUR_EXTRACT_DIR / "HD.dat"
            en_file = FCC_AMATEUR_EXTRACT_DIR / "EN.dat"

            if not hd_file.exists():
                log(f"Missing file: {hd_file}")
                return

            if not en_file.exists():
                log(f"Missing file: {en_file}")
                return

            log(f"Reading: {hd_file.name}")
            log(f"Reading: {en_file.name}")
            log(f"Writing database: {CALLSIGN_DB_FILE}")

            # -------------------------
            # PASS 1: Read EN.dat
            # -------------------------
            en_map = {}
            en_count = 0

            with open(en_file, "r", encoding="latin-1", errors="ignore") as f:
                for line in f:
                    parts = line.rstrip("\n").split("|")

                    if len(parts) < 20:
                        continue

                    unique_id = parts[1].strip()

                    entity_name = parts[7].strip()
                    first_name = parts[8].strip()
                    mi = parts[9].strip()
                    last_name = parts[10].strip()
                    suffix = parts[11].strip()

                    address = parts[15].strip()
                    city = parts[16].strip()
                    state = parts[17].strip()
                    zipcode = parts[18].strip()
                    country = parts[19].strip()

                    if entity_name:
                        name = entity_name
                    else:
                        name_parts = [first_name, mi, last_name, suffix]
                        name = " ".join(p for p in name_parts if p).strip()

                    en_map[unique_id] = {
                        "name": name,
                        "address": address,
                        "city": city,
                        "state": state,
                        "zipcode": zipcode,
                        "country": country if country else "USA"
                    }

                    en_count += 1
                    if en_count % 500000 == 0:
                        log(f"Loaded {en_count:,} EN records...")

                    try:
                        win.update_idletasks()
                    except Exception:
                        pass

            log(f"Finished EN.dat: {en_count:,} records indexed.")

            # -------------------------
            # PASS 2: Rebuild callsigns.db
            # -------------------------
            conn = sqlite3.connect(str(CALLSIGN_DB_FILE))
            cur = conn.cursor()

            cur.execute("DROP TABLE IF EXISTS callsigns")

            cur.execute("""
                CREATE TABLE callsigns (
                    callsign TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zipcode TEXT,
                    country TEXT,
                    grid TEXT,
                    license_class TEXT,
                    status TEXT
                )
            """)

            cur.execute("DROP TABLE IF EXISTS metadata")
            cur.execute("""
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            log("Reading HD.dat and building callsign records...")

            inserted = 0
            skipped_blank = 0
            batch = []

            with open(hd_file, "r", encoding="latin-1", errors="ignore") as f:
                for line in f:
                    parts = line.rstrip("\n").split("|")

                    if len(parts) < 9:
                        continue

                    unique_id = parts[1].strip()
                    callsign = parts[4].strip().upper()
                    operator_class = parts[5].strip()
                    lic_status = parts[6].strip()

                    if not callsign:
                        skipped_blank += 1
                        continue

                    en_info = en_map.get(unique_id, {})

                    row = (
                        callsign,
                        en_info.get("name", ""),
                        en_info.get("address", ""),
                        en_info.get("city", ""),
                        en_info.get("state", ""),
                        en_info.get("zipcode", ""),
                        en_info.get("country", "USA"),
                        "",  # grid blank for now
                        operator_class,
                        lic_status
                    )

                    batch.append(row)

                    if len(batch) >= 5000:
                        cur.executemany("""
                            INSERT OR REPLACE INTO callsigns
                            (callsign, name, address, city, state, zipcode, country, grid, license_class, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        conn.commit()
                        inserted += len(batch)
                        batch.clear()

                        if inserted % 50000 == 0:
                            log(f"Inserted {inserted:,} callsign records...")
                            try:
                                win.update_idletasks()
                            except Exception:
                                pass

                if batch:
                    cur.executemany("""
                        INSERT OR REPLACE INTO callsigns
                        (callsign, name, address, city, state, zipcode, country, grid, license_class, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    inserted += len(batch)
                    batch.clear()

            timestamp_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES (?, ?)
            """, ("fcc_last_build", timestamp_text))
            conn.commit()

            cur.execute("CREATE INDEX IF NOT EXISTS idx_callsigns_name ON callsigns(name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_callsigns_state ON callsigns(state)")
            conn.commit()
            conn.close()

            log("Build complete.")
            log(f"Inserted records: {inserted:,}")
            log(f"Skipped blank callsigns: {skipped_blank:,}")
            log(f"Last build time saved: {timestamp_text}")

        except Exception as e:
            log(f"Build failed: {e}")

    tk.Button(
        button_frame,
        text="Download FCC Data",
        command=download_data,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Build / Rebuild Database",
        command=build_database,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=(6, 0))

    # -------------------------
    # LOG OUTPUT
    # -------------------------
    log_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=6,
        pady=6
    )
    log_frame.pack(fill="both", expand=True)

    log_text = tk.Text(
        log_frame,
        wrap="word",
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"]
    )
    log_text.pack(fill="both", expand=True)

    def log(message):
        try:
            log_text.config(state="normal")
            log_text.insert("end", message + "\n")
            log_text.config(state="disabled")
            log_text.see("end")
        except Exception:
            pass

    # -------------------------
    # CLOSE BUTTON
    # -------------------------
    bottom_frame = tk.Frame(outer, bg=theme["bg"])
    bottom_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        bottom_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(win)


def build_zipcode_database(csv_path):
    """
    Build zipcodes.db from a CSV file with:
    zipcode,lat,lon
    """
    if not csv_path or not Path(csv_path).exists():
        print("ZIP CSV file not found.")
        return False

    try:
        conn = sqlite3.connect(str(ZIPCODE_DB_FILE))
        cur = conn.cursor()

        # Create table
        cur.execute("DROP TABLE IF EXISTS zipcodes")
        cur.execute("""
            CREATE TABLE zipcodes (
                zipcode TEXT PRIMARY KEY,
                lat REAL,
                lon REAL
            )
        """)

        inserted = 0
        batch = []

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split(",")

                if len(parts) < 3:
                    continue

                zipcode = parts[0].strip()
                lat = parts[1].strip()
                lon = parts[2].strip()

                if not zipcode or not lat or not lon:
                    continue

                try:
                    lat = float(lat)
                    lon = float(lon)
                except Exception:
                    continue

                batch.append((zipcode, lat, lon))

                if len(batch) >= 5000:
                    cur.executemany("""
                        INSERT OR REPLACE INTO zipcodes (zipcode, lat, lon)
                        VALUES (?, ?, ?)
                    """, batch)
                    conn.commit()
                    inserted += len(batch)
                    batch.clear()

        if batch:
            cur.executemany("""
                INSERT OR REPLACE INTO zipcodes (zipcode, lat, lon)
                VALUES (?, ?, ?)
            """, batch)
            conn.commit()
            inserted += len(batch)

        conn.close()

        print(f"ZIP database built: {inserted:,} records")
        return True

    except Exception as e:
        print(f"ZIP DB build error: {e}")
        return False


# -------------------------
# GRID / DISTANCE HELPERS
# -------------------------

import math


def normalize_zipcode(zipcode):
    zipcode = (zipcode or "").strip()
    if not zipcode:
        return ""

    match = re.match(r"^(\d{5})", zipcode)
    if match:
        return match.group(1)

    return ""


def latlon_to_maidenhead(lat, lon):
    """
    Convert lat/lon to a 6-character Maidenhead grid.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return ""

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return ""

    lon += 180.0
    lat += 90.0

    field_lon = int(lon // 20)
    field_lat = int(lat // 10)

    square_lon = int((lon % 20) // 2)
    square_lat = int(lat % 10)

    subsquare_lon = int(((lon % 2) * 60) // 5)
    subsquare_lat = int((((lat % 1) * 60) // 2.5))

    return (
        chr(ord("A") + field_lon) +
        chr(ord("A") + field_lat) +
        str(square_lon) +
        str(square_lat) +
        chr(ord("A") + subsquare_lon) +
        chr(ord("A") + subsquare_lat)
    )


def get_zipcode_latlon(zipcode):
    """
    Look up ZIP centroid lat/lon from local zipcodes.db
    """
    zipcode = normalize_zipcode(zipcode)
    if not zipcode:
        return None, None

    if not ZIPCODE_DB_FILE.exists():
        return None, None

    try:
        conn = sqlite3.connect(str(ZIPCODE_DB_FILE))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT lat, lon
            FROM zipcodes
            WHERE zipcode = ?
            LIMIT 1
        """, (zipcode,))

        row = cur.fetchone()
        conn.close()

        if not row:
            return None, None

        return row["lat"], row["lon"]

    except Exception as e:
        print(f"ZIP centroid lookup error: {e}")
        return None, None


def find_grid_from_zipcode(zipcode):
    """
    Convert ZIP centroid lat/lon into a 6-character Maidenhead grid.
    Returns (grid, source_text) or (None, None)
    """
    zipcode = normalize_zipcode(zipcode)
    if not zipcode:
        return None, None

    lat, lon = get_zipcode_latlon(zipcode)
    if lat is None or lon is None:
        return None, None

    grid = latlon_to_maidenhead(lat, lon).upper()
    if not looks_like_grid(grid):
        return None, None

    return grid, "ZIP code estimate"


def maidenhead_to_latlon(grid):
    """
    Convert Maidenhead grid (e.g., EM54ML) to lat/lon (center of grid square).
    """
    grid = (grid or "").strip().upper()

    if len(grid) < 4:
        return None, None

    try:
        lon = (ord(grid[0]) - ord('A')) * 20 - 180
        lat = (ord(grid[1]) - ord('A')) * 10 - 90

        lon += int(grid[2]) * 2
        lat += int(grid[3]) * 1

        if len(grid) >= 6:
            lon += (ord(grid[4]) - ord('A')) * (5 / 60)
            lat += (ord(grid[5]) - ord('A')) * (2.5 / 60)

            lon += (5 / 60) / 2
            lat += (2.5 / 60) / 2
        else:
            lon += 1
            lat += 0.5

        return lat, lon

    except Exception:
        return None, None


def decimal_to_dm(lat, lon):
    """
    Convert decimal lat/lon to degrees + decimal minutes.
    Example: 34°07.404'N 088°34.068'W
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return ""

    def one(value, is_lat=True):
        hemi = "N" if is_lat and value >= 0 else "S" if is_lat else "E" if value >= 0 else "W"
        value = abs(value)
        deg = int(value)
        minutes = (value - deg) * 60
        width = 2 if is_lat else 3
        return f"{deg:0{width}d}°{minutes:06.3f}'{hemi}"

    return f"{one(lat, True)} {one(lon, False)}"


def decimal_to_dms(lat, lon):
    """
    Convert decimal lat/lon to degrees, minutes, seconds.
    Example: 34°07'24.2"N 088°34'04.1"W
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return ""

    def one(value, is_lat=True):
        hemi = "N" if is_lat and value >= 0 else "S" if is_lat else "E" if value >= 0 else "W"
        value = abs(value)
        deg = int(value)
        minutes_full = (value - deg) * 60
        minutes = int(minutes_full)
        seconds = (minutes_full - minutes) * 60

        # Handle rounding rollover, such as 59.96 seconds -> 60.0 seconds.
        seconds = round(seconds, 1)
        if seconds >= 60:
            seconds = 0.0
            minutes += 1
        if minutes >= 60:
            minutes = 0
            deg += 1

        width = 2 if is_lat else 3
        return f'{deg:0{width}d}°{minutes:02d}\'{seconds:04.1f}"{hemi}'

    return f"{one(lat, True)} {one(lon, False)}"


def decimal_to_dm_radio_safe(lat, lon):
    """
    Convert decimal lat/lon to radio-safe degrees + decimal minutes.
    Example: 34 07.404 N 088 34.068 W
    """
    pretty = decimal_to_dm(lat, lon)
    return (
        pretty.replace("°", " ")
        .replace("'", " ")
        .replace('"', " ")
        .replace("  ", " ")
        .strip()
    )


def decimal_to_dms_radio_safe(lat, lon):
    """
    Convert decimal lat/lon to radio-safe degrees, minutes, seconds.
    Example: 34 07 24.2 N 088 34 04.1 W
    """
    pretty = decimal_to_dms(lat, lon)
    return (
        pretty.replace("°", " ")
        .replace("'", " ")
        .replace('"', " ")
        .replace("  ", " ")
        .strip()
    )



def decimal_to_clean_decimal(lat, lon):
    """
    Format decimal lat/lon consistently.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return ""

    return f"{lat:.6f}, {lon:.6f}"


def decimal_to_utm(lat, lon):
    """
    Convert decimal lat/lon to full UTM.
    Example: 16S 323456E 3776543N
    """
    try:
        lat = float(lat)
        lon = float(lon)
        easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)
        return f"{zone_number}{zone_letter} {int(round(easting / 10))}E {int(round(northing / 10))}N"
    except Exception:
        return ""


def decimal_to_mgrs(lat, lon, precision=4):
    """
    Convert decimal lat/lon to MGRS.
    precision=3 gives 100m, precision=4 gives 10m.
    """
    try:
        lat = float(lat)
        lon = float(lon)
        m = mgrs.MGRS()
        raw = m.toMGRS(lat, lon, MGRSPrecision=precision)

        # Pretty print common format:
        # 16SEG23457654 -> 16S EG 2345 7654
        if len(raw) >= 5 + (precision * 2):
            zone = raw[:3]
            square = raw[3:5]
            digits = raw[5:]
            east = digits[:precision]
            north = digits[precision:]
            return f"{zone} {square} {east} {north}"

        return raw
    except Exception:
        return ""


def mgrs_to_decimal(value):
    """
    Convert MGRS to decimal lat/lon.
    """
    try:
        m = mgrs.MGRS()
        lat, lon = m.toLatLon(value.replace(" ", "").upper())
        return lat, lon
    except Exception:
        return None, None


def utm_to_decimal(value):
    """
    Convert simple UTM text to decimal lat/lon.
    Expected examples:
      16S 323456 3776543
      16S 323456E 3776543N
    """
    try:
        raw = (value or "").strip().upper()
        raw = raw.replace(",", " ")
        raw = raw.replace("E", " ")
        raw = raw.replace("N", " ")
        parts = [p for p in raw.split() if p]

        if len(parts) < 3:
            return None, None

        zone_text = parts[0]
        match = re.match(r"^(\d{1,2})([C-HJ-NP-X])$", zone_text)
        if not match:
            return None, None

        zone_number = int(match.group(1))
        zone_letter = match.group(2)
        easting = float(parts[1])
        northing = float(parts[2])

        lat, lon = utm.to_latlon(easting, northing, zone_number, zone_letter)
        return lat, lon
    except Exception:
        return None, None


def parse_decimal_latlon(text):
    """
    Parse decimal latitude/longitude.
    Examples:
      34.1234 -88.5678
      34.1234, -88.5678
    """
    try:
        raw = (text or "").strip()
        raw = raw.replace(",", " ")

        parts = [p for p in raw.split() if p]

        if len(parts) != 2:
            return None, None

        lat = float(parts[0])
        lon = float(parts[1])

        if not (-90 <= lat <= 90):
            return None, None

        if not (-180 <= lon <= 180):
            return None, None

        return lat, lon

    except Exception:
        return None, None


def parse_maidenhead(text):
    """
    Parse Maidenhead grid locator.
    """
    try:
        grid = (text or "").strip().upper()

        if not re.match(r"^[A-R]{2}[0-9]{2}([A-X]{2})?([0-9]{2})?$", grid):
            return None, None

        return maidenhead_to_latlon(grid)

    except Exception:
        return None, None


def parse_utm(text):
    """
    Parse UTM text.
    """
    return utm_to_decimal(text)


def parse_mgrs(text):
    """
    Parse MGRS text.
    """
    return mgrs_to_decimal(text)


def parse_any_coordinate(text):
    """
    Attempt to auto-detect coordinate format.

    Returns:
        (lat, lon, format_name)
    """
    text = (text or "").strip()

    if not text:
        return None, None, None

    parsers = [
        ("Decimal Degrees", parse_decimal_latlon),
        ("Maidenhead Grid", parse_maidenhead),
        ("UTM", parse_utm),
        ("MGRS", parse_mgrs),
    ]

    for format_name, parser in parsers:
        try:
            lat, lon = parser(text)

            if lat is not None and lon is not None:
                return lat, lon, format_name

        except Exception:
            continue

    return None, None, None




def build_coordinate_outputs(lat, lon, original_text="", radio_safe=False):
    """
    Build the standard GridLink coordinate output list.
    Returns a list of (label, value) tuples.
    """
    maiden = latlon_to_maidenhead(lat, lon).upper()

    if radio_safe:
        dm_value = decimal_to_dm_radio_safe(lat, lon)
        dms_value = decimal_to_dms_radio_safe(lat, lon)
        original_value = dm_value
    else:
        dm_value = decimal_to_dm(lat, lon)
        dms_value = decimal_to_dms(lat, lon)
        original_value = dm_value

    return [
        ("Original / Cleaned", original_value),
        ("Decimal Degrees", decimal_to_clean_decimal(lat, lon)),
        ("Degrees Decimal Minutes", dm_value),
        ("Degrees Minutes Seconds", dms_value),
        ("Maidenhead Grid", maiden),
        ("UTM", decimal_to_utm(lat, lon)),
        ("MGRS 100m", decimal_to_mgrs(lat, lon, precision=3)),
        ("MGRS 10m", decimal_to_mgrs(lat, lon, precision=4)),
    ]



def calculate_distance_and_bearing(grid1, grid2):
    """
    Returns:
        (distance_km, distance_miles, bearing_deg, reciprocal_deg)
    """
    lat1, lon1 = maidenhead_to_latlon(grid1)
    lat2, lon2 = maidenhead_to_latlon(grid2)

    if None in (lat1, lon1, lat2, lon2):
        return None

    # Convert to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Haversine distance
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    earth_km = 6371.0
    distance_km = earth_km * c
    distance_miles = distance_km * 0.621371

    # Bearing
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    bearing = math.degrees(math.atan2(y, x))
    bearing = (bearing + 360) % 360

    reciprocal = (bearing + 180) % 360

    return (
        round(distance_km, 1),
        round(distance_miles, 1),
        round(bearing, 1),
        round(reciprocal, 1),
    )



# Legacy standard STATREP parser removed.
# GridLink now treats VarAC/JS8 messages as generic RF activity.


# JS8Call STATREP parser functions removed.
# JS8 Telegram startup recovery remains below.


# -------------------------
# JS8CALL STARTUP RECOVERY
# -------------------------

import hashlib
import utm
import mgrs

JS8_RECOVERY_WINDOW_MINUTES = 120
PROCESSED_JS8_HASHES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "processed_js8_triggers.txt"
)


def make_js8_trigger_hash(line):
    """
    Create a stable hash for a JS8Call trigger.

    Uses parsed trigger fields when possible so duplicates are detected even
    if whitespace or DIRECTED.TXT formatting changes slightly.
    """
    clean_line = (line or "").strip()

    try:
        parsed = parse_js8call_trigger_line(clean_line)

        if parsed:
            timestamp = parsed.get("timestamp")
            if timestamp:
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_text = ""

            key = "|".join([
                timestamp_text,
                (parsed.get("from_call") or "").strip().upper(),
                (parsed.get("relay_call") or "").strip().upper(),
                (parsed.get("to_call") or "").strip().upper(),
                (parsed.get("telegram_alias") or "").strip().upper(),
                (parsed.get("message_text") or "").strip(),
            ])
        else:
            key = clean_line

    except Exception:
        key = clean_line

    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def load_processed_js8_hashes():
    """
    Load previously processed JS8 trigger hashes from disk.
    This survives GridLink restarts.
    """
    if not os.path.exists(PROCESSED_JS8_HASHES_FILE):
        return set()

    try:
        with open(PROCESSED_JS8_HASHES_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"Could not load processed JS8 hashes: {e}")
        return set()


def save_processed_js8_hash(trigger_hash):
    """
    Save one processed JS8 trigger hash to disk.
    """
    try:
        with open(PROCESSED_JS8_HASHES_FILE, "a", encoding="utf-8") as f:
            f.write(trigger_hash + "\n")
    except Exception as e:
        print(f"Could not save processed JS8 hash: {e}")

def recover_recent_js8_telegram_triggers():
    """
    On GridLink startup, scan recent JS8Call DIRECTED.TXT lines and process
    valid TG: messages from the last 120 minutes.

    This allows a gateway operator to open GridLink after noticing a JS8
    Telegram message and still forward it, as long as it is not older than
    the recovery window.
    """
    try:
        directed_path = config.get(
            "js8call_directed_txt",
            os.path.expanduser("~/.local/share/JS8Call/DIRECTED.TXT")
        )

        if not directed_path or not os.path.exists(directed_path):
            print("JS8 startup recovery skipped: DIRECTED.TXT not found.")
            return

        processed_hashes = load_processed_js8_hashes()
        recovered_count = 0
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=JS8_RECOVERY_WINDOW_MINUTES)

        with open(directed_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            trigger_hash = make_js8_trigger_hash(line)
            if trigger_hash in processed_hashes:
                continue

            parsed = parse_js8call_trigger_line(line)
            if not parsed:
                continue

            timestamp = parsed.get("timestamp")
            if not timestamp:
                continue

            if timestamp < cutoff_time:
                continue

            # Reuse the existing live trigger processor so recovery behaves
            # exactly like live JS8 trigger handling.
            process_js8call_trigger_lines([line])

            save_processed_js8_hash(trigger_hash)
            processed_hashes.add(trigger_hash)
            recovered_count += 1

        if recovered_count:
            print(f"JS8 startup recovery processed {recovered_count} recent Telegram trigger(s).")
        else:
            print("JS8 startup recovery found no new recent Telegram triggers.")

    except Exception as e:
        print(f"JS8 startup recovery error: {e}")

def parse_js8call_trigger_line(line):
    """
    Parse a JS8Call DIRECTED.TXT line carrying a Telegram trigger.

    Supports direct and JS8Call relay-style TG messages.

    Reply messages using [ALIAS] are intentionally ignored here.
    """
    line = (line or "").strip()
    if not line:
        return None

    parts = line.split("\t")
    if len(parts) < 5:
        return None

    timestamp_text = parts[0].strip()
    frequency = parts[1].strip()
    offset = parts[2].strip()
    snr_text = parts[3].strip()
    payload = parts[4].strip()

    # Only TG: messages are Telegram triggers.
    # Reply messages like KW3KW [SCOTT] MSG RECEIVED must not trigger Telegram.
    if "TG:" not in payload.upper():
        return None

    from_call = ""
    relay_call = ""
    to_call = ""
    is_relayed = False

    # -------------------------------------------------
    # Relay format A:
    # K4EXA>KW3KW: KG5VPF TG:SCOTT MESSAGE
    #
    # Interpreted as:
    # from_call  = K4EXA
    # relay_call = KW3KW
    # to_call    = KG5VPF
    # -------------------------------------------------
    match = re.match(
        r"^(?P<from_call>[A-Z0-9/]+)>\s*(?P<relay_call>[A-Z0-9/]+):\s*(?P<to_call>[A-Z0-9/]+)\s+TG:(?P<alias>[A-Z0-9_@.-]+)\s*(?P<body>.*)$",
        payload,
        re.IGNORECASE
    )

    if match:
        from_call = match.group("from_call").strip().upper()
        relay_call = match.group("relay_call").strip().upper()
        to_call = match.group("to_call").strip().upper()
        is_relayed = True
    else:
        # -------------------------------------------------
        # Relay format B:
        # KW3KW: K4EXA>KG5VPF TG:SCOTT MESSAGE
        # KW3KW: K4EXA> KG5VPF TG:SCOTT MESSAGE
        #
        # Interpreted as:
        # from_call  = KW3KW
        # relay_call = K4EXA
        # to_call    = KG5VPF
        # -------------------------------------------------
        match = re.match(
            r"^(?P<from_call>[A-Z0-9/]+):\s*(?P<relay_call>[A-Z0-9/]+)>\s*(?P<to_call>[A-Z0-9/]+)\s+TG:(?P<alias>[A-Z0-9_@.-]+)\s*(?P<body>.*)$",
            payload,
            re.IGNORECASE
        )

        if match:
            from_call = match.group("from_call").strip().upper()
            relay_call = match.group("relay_call").strip().upper()
            to_call = match.group("to_call").strip().upper()
            is_relayed = True
        else:
            # -------------------------------------------------
            # Direct format:
            # FROMCALL: TOCALL TG:SCOTT MESSAGE
            # -------------------------------------------------
            match = re.match(
                r"^(?P<from_call>[A-Z0-9/]+):\s+(?P<to_call>[A-Z0-9/]+)\s+TG:(?P<alias>[A-Z0-9_@.-]+)\s*(?P<body>.*)$",
                payload,
                re.IGNORECASE
            )

            if not match:
                return None

            from_call = match.group("from_call").strip().upper()
            to_call = match.group("to_call").strip().upper()

    alias = normalize_js8_alias(match.group("alias"))
    body = normalize_js8_message_text(match.group("body"))

    try:
        timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
    except Exception:
        print(f"JS8 timestamp parse failed: {timestamp_text}")
        return None

    try:
        snr_value = int(snr_text)
    except Exception:
        snr_value = snr_text

    return {
        "source": "js8call",
        "timestamp": timestamp,
        "timestamp_text": timestamp_text,
        "frequency": frequency,
        "offset": offset,
        "snr": snr_value,
        "snr_text": snr_text,
        "from_call": from_call,
        "to_call": to_call,
        "relay_call": relay_call,
        "is_relayed": is_relayed,
        "telegram_alias": alias,
        "message_text": body,
        "raw_payload": payload,
        "raw_line": line,
    }


def parse_js8call_directed_line(line):
    """
    Example:
    2026-02-28 14:42:17\t7.110000\t2200\t-11\tW6MZT: @AMRRON,EM78DH,1,131,111111111111,IN-WARM HIGH NEAR 70 SUNNY,{&%} ♢
    """
    line = (line or "").strip()
    if not line:
        return None

    parts = line.split("\t")
    if len(parts) < 5:
        return None

    timestamp_text = parts[0].strip()
    frequency = parts[1].strip()
    offset = parts[2].strip()
    snr_text = parts[3].strip()
    payload = parts[4].strip()

    if ":" not in payload:
        return None

    from_call, raw_message = payload.split(":", 1)
    from_call = from_call.strip().upper()
    raw_message = raw_message.strip()

    if not raw_message.startswith("@"):
        return None

    try:
        timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
    except Exception:
        timestamp = datetime.datetime.now()

    try:
        snr_value = int(snr_text)
    except Exception:
        snr_value = snr_text

    try:
        return make_message_record(
            raw=raw_message,
            timestamp=timestamp,
            from_call=from_call,
            to_call="ALL",
            band="JS8",
            snr=snr_value,
            log_timestamp_text=timestamp_text,
            message_timestamp_text=timestamp_text,
            raw_line=line,
            source="js8call",
            extra_metadata={
                "frequency": frequency,
                "offset": offset,
                "js8call_snr_text": snr_text,
            }
        )
    except Exception as e:
        print(f"JS8Call directed parse error: {e} | line={line}")
        return None


def get_worst_status(status_string):
    """
    Accepts either:
    - comma-separated new format: grn,yel,red,...
    - a list/tuple of status values
    - legacy numeric strings, for backward tolerance

    Returns one of:
    - "grn"
    - "yel"
    - "red"
    """
    if isinstance(status_string, (list, tuple)):
        values = [str(v).strip().lower() for v in status_string]
    else:
        text = (status_string or "").strip().lower()

        if "," in text:
            values = [part.strip() for part in text.split(",") if part.strip()]
        else:
            # Backward tolerance for legacy numeric strings
            digits = [ch for ch in text if ch in ("1", "2", "3")]
            if digits:
                if "3" in digits:
                    return "red"
                elif "2" in digits:
                    return "yel"
                else:
                    return "grn"

            values = [text] if text else []

    if "red" in values:
        return "red"
    elif "yel" in values:
        return "yel"
    elif "grn" in values:
        return "grn"

    return "grn"



def make_message_record(
    raw,
    timestamp=None,
    from_call="",
    to_call="",
    band="",
    snr=None,
    log_timestamp_text="",
    message_timestamp_text="",
    raw_line="",
    source="varac",
    extra_metadata=None
):
    """
    Build a generic RF activity record.

    GridLink treats VarAC/JS8 traffic as general RF activity first.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()

    if extra_metadata is None:
        extra_metadata = {}

    source_normalized = (source or "varac").strip().lower()

    parsed = {
        "source": source_normalized,
        "grid": "",
        "comment": raw or "",
        "group_display": "",
        "priority": "",
        "status": "",
        "message_type": "RF Activity",
    }

    lat, lon = None, None

    return {
        "source": source_normalized,
        "raw": raw,
        "raw_line": raw_line if raw_line else raw,
        "timestamp": timestamp,
        "log_timestamp_text": log_timestamp_text,
        "message_timestamp_text": message_timestamp_text,
        "from_call": from_call,
        "to_call": to_call,
        "band": band,
        "snr": snr,
        "parsed": parsed,
        "lat": lat,
        "lon": lon,
        "extra_metadata": dict(extra_metadata),
    }


def parse_log_datetime(dt_text):
    try:
        return datetime.datetime.strptime(dt_text.strip(), "%d/%m/%Y %H:%M:%S")
    except Exception:
        return datetime.datetime.now()


def parse_varac_broadcast_line(line):
    """
    Example:
    13/03/2026 16:53:02 - BROADCAST - (20m) - 3/13/2026 4:53:01 PM - FROM: KG5VPF - TO: ALL - @HRMS,EM54ML,1,999,111111111111,All Good (Test Only),{&%} -
    """

    line = (line or "").strip()
    if "BROADCAST -" not in line:
        return None

    pattern = re.compile(
        r"^(?P<log_ts>\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+-\s+"
        r"BROADCAST\s+-\s+"
        r"\((?P<band>[^)]+)\)\s+-\s+"
        r"(?P<msg_ts>.+?)\s+-\s+"
        r"FROM:\s+(?P<from_call>.*?)\s+-\s+"
        r"TO:\s+(?P<to_call>.*?)\s+-\s+"
        r"(?P<payload>.*?)\s*-\s*$"
    )

    match = pattern.match(line)
    if not match:
        return None

    data = match.groupdict()
    payload = data["payload"].strip()

    if not payload.startswith("@"):
        return None

    timestamp = parse_log_datetime(data["log_ts"])

    try:
        return make_message_record(
            raw=payload,
            timestamp=timestamp,
            from_call=data["from_call"].strip(),
            to_call=data["to_call"].strip(),
            band=data["band"].strip(),
            log_timestamp_text=data["log_ts"].strip(),
            message_timestamp_text=data["msg_ts"].strip(),
            raw_line=line
        )
    except Exception as e:
        print(f"Broadcast parse error: {e} | line={line}")
        return None


def parse_js8call_directed_line(line):
    """
    Example:
    2026-02-28 14:42:17\t7.110000\t2200\t-11\tW6MZT: @AMRRON,EM78DH,1,131,111111111111,IN-WARM HIGH NEAR 70 SUNNY,{&%} ♢
    """
    line = (line or "").strip()
    if not line:
        return None

    parts = line.split("\t")
    if len(parts) < 5:
        return None

    timestamp_text = parts[0].strip()
    frequency = parts[1].strip()
    offset = parts[2].strip()
    snr_text = parts[3].strip()
    payload = parts[4].strip()

    if ":" not in payload:
        return None

    from_call, raw_message = payload.split(":", 1)
    from_call = from_call.strip().upper()
    raw_message = raw_message.strip()

    if not raw_message.startswith("@"):
        return None

    try:
        timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
    except Exception:
        timestamp = datetime.datetime.now()

    try:
        snr_value = int(snr_text)
    except Exception:
        snr_value = snr_text

    try:
        return make_message_record(
            raw=raw_message,
            timestamp=timestamp,
            from_call=from_call,
            to_call="ALL",
            band="JS8",
            snr=snr_value,
            log_timestamp_text=timestamp_text,
            message_timestamp_text=timestamp_text,
            raw_line=line,
            source="js8call",
            extra_metadata={
                "frequency": frequency,
                "offset": offset,
                "js8call_snr_text": snr_text,
            }
        )
    except Exception as e:
        print(f"JS8Call directed parse error: {e} | line={line}")
        return None


def get_map_item_summary(item):
    parsed = item["parsed"]
    callsign = (item.get("from_call", "") or "Unknown").strip()
    group_name = parsed.get("group_display", "")
    grid = parsed.get("grid", "")
    priority = priority_name_map.get(parsed.get("priority", ""), parsed.get("priority", ""))
    comment = parsed.get("comment", "")

    summary = f"{callsign} | {group_name} | {grid} | {priority}"
    if comment:
        summary += f" | {comment}"

    return summary


def show_map_item_basic_info(item):
    try:
        click_status_var.set(get_map_item_summary(item))
    except Exception:
        pass


def schedule_map_item_single_click(item):
    # Cancel any pending click
    if hasattr(schedule_map_item_single_click, "_after_id"):
        try:
            root.after_cancel(schedule_map_item_single_click._after_id)
        except Exception:
            pass

    schedule_map_item_single_click._pending_item = item

    def fire_single_click():
        pending_item = getattr(schedule_map_item_single_click, "_pending_item", None)
        schedule_map_item_single_click._after_id = None
        schedule_map_item_single_click._pending_item = None

        if pending_item is not None:
            show_map_item_basic_info(pending_item)

    schedule_map_item_single_click._after_id = root.after(250, fire_single_click)


def trigger_map_item_double_click(item):
    # Cancel pending single-click
    if hasattr(schedule_map_item_single_click, "_after_id"):
        after_id = getattr(schedule_map_item_single_click, "_after_id", None)
        if after_id:
            try:
                root.after_cancel(after_id)
            except Exception:
                pass

        schedule_map_item_single_click._after_id = None
        schedule_map_item_single_click._pending_item = None

    open_details_window(item)


def on_internet_polygon_click(polygon):
    item = getattr(polygon, "data", None)
    if item is None:
        return

    last_item = getattr(on_internet_polygon_click, "_last_item", None)
    last_time = getattr(on_internet_polygon_click, "_last_time", None)
    now = datetime.datetime.now()

    is_double = (
        last_item is item
        and last_time is not None
        and (now - last_time).total_seconds() <= 0.60
    )

    on_internet_polygon_click._last_item = item
    on_internet_polygon_click._last_time = now

    if is_double:
        trigger_map_item_double_click(item)
    else:
        schedule_map_item_single_click(item)


def find_offline_item_at_xy(x, y, max_distance=12):
    best_item = None
    best_distance_sq = None

    for entry in offline_station_items:
        dx = x - entry["x"]
        dy = y - entry["y"]
        distance_sq = dx * dx + dy * dy

        if distance_sq <= (max_distance * max_distance):
            if best_distance_sq is None or distance_sq < best_distance_sq:
                best_distance_sq = distance_sq
                best_item = entry["item"]

    return best_item

MAP_CLICK_DELAY_MS = 250


def schedule_map_item_single_click(item):
    global _last_map_click_time, _last_map_click_item

    _last_map_click_time = int(time.time() * 1000)
    _last_map_click_item = item

    def handle_single():
        now = int(time.time() * 1000)

        # If no newer click replaced this one, treat as single-click
        if now - _last_map_click_time >= MAP_CLICK_DELAY_MS:
            show_map_item_summary(item)

    root.after(MAP_CLICK_DELAY_MS, handle_single)


def trigger_map_item_double_click(item):
    global _last_map_click_time

    _last_map_click_time = int(time.time() * 1000)
    open_details_window(item)


def show_map_item_summary(item):
    try:
        parsed = item["parsed"]
        callsign = item.get("from_call", "Unknown")
        grid = parsed.get("grid", "")
        priority = parsed.get("priority", "")
        comment = parsed.get("comment", "")

        summary = f"{callsign} | {grid} | {priority.upper()} | {comment}"
        click_status_var.set(summary)

    except Exception as e:
        print(f"Map summary error: {e}")


# -------------------------
# INTERNET MAP
# -------------------------------

def clear_internet_map():
    global internet_station_markers, selected_station_label_marker

    # Remove existing markers
    for marker in internet_station_markers:
        try:
            marker.delete()
        except Exception:
            pass

    internet_station_markers = []

    # Remove selected label marker (if any)
    if selected_station_label_marker:
        try:
            selected_station_label_marker.delete()
        except Exception:
            pass
        selected_station_label_marker = None

def get_station_marker_color(item):
    source = (item.get("source") or "").strip().lower()
    callsign = (item.get("from_call") or "").strip().upper()
    my_call = (config.get("callsign") or "").strip().upper()

    # My station (from Station Setup)
    if source == "my_station":
        return "green"

    # Fallback if callsign matches but source not set correctly
    if callsign and callsign == my_call:
        return "green"

    if source == "js8call":
        return "blue"

    if source == "varac":
        return "red"

    if source == "gateway":
        return "green"

    return "gray"

def station_has_heard_us(item):
    """
    Return True if we have evidence this station has heard / addressed us.

    Evidence examples:
    - station sent a directed message to our callsign
    - station's raw traffic contains our callsign

    If no evidence is found, the marker can be shown as heard-only.
    """
    source = (item.get("source") or "").strip().lower()
    station_call = (item.get("from_call") or "").strip().upper()
    my_call = (config.get("callsign") or "").strip().upper()

    if source not in ("js8call", "varac"):
        return True

    if not station_call or not my_call:
        return True

    if station_call == my_call:
        return True

    for msg in messages:
        msg_from = (msg.get("from_call") or "").strip().upper()
        msg_to = (msg.get("to_call") or "").strip().upper()
        msg_raw = (msg.get("raw") or "").upper()

        if msg_from != station_call:
            continue

        if msg_to == my_call:
            return True

        if my_call in msg_raw:
            return True

    return False


def is_heard_only_station(item):
    source = (item.get("source") or "").strip().lower()

    if source not in ("js8call", "varac"):
        return False

    return not station_has_heard_us(item)


def draw_station_marker(item):
    global internet_station_markers, selected_station_label_marker

    lat = item.get("lat")
    lon = item.get("lon")

    if lat is None or lon is None:
        return

    color = get_station_marker_color(item)
    callsign = (item.get("from_call") or "UNKNOWN").strip()

    def show_marker_summary():
        global selected_station_label_marker

        if selected_station_label_marker:
            try:
                selected_station_label_marker.delete()
            except Exception:
                pass
            selected_station_label_marker = None

        try:
            selected_station_label_marker = map_widget.set_marker(
                lat,
                lon,
                text=callsign,
                marker_color_outside=color
            )

            def remove_label():
                global selected_station_label_marker
                try:
                    if selected_station_label_marker:
                        selected_station_label_marker.delete()
                except Exception:
                    pass
                selected_station_label_marker = None

            root.after(3000, remove_label)
        except Exception:
            pass

        try:
            snr = item.get("snr", "--")
            band = item.get("band", "?")
            raw = (item.get("raw") or "").strip()
            click_status_var.set(
                f"{callsign} | {band} | SNR {snr} | {raw[:80]}"
            )
        except Exception:
            pass

    def on_marker_click(marker=None):
        now = time.time()

        last_click_time = getattr(on_marker_click, "_last_click_time", 0)
        pending_after_id = getattr(on_marker_click, "_pending_after_id", None)

        is_double_click = (now - last_click_time) <= 0.70

        on_marker_click._last_click_time = now

        if is_double_click:
            if pending_after_id:
                try:
                    root.after_cancel(pending_after_id)
                except Exception:
                    pass
                on_marker_click._pending_after_id = None

            open_details_window(item)
            return

        def delayed_single_click():
            on_marker_click._pending_after_id = None
            show_marker_summary()

        on_marker_click._pending_after_id = root.after(300, delayed_single_click)

    try:
        icon = create_dot_icon(
            color,
            size=16,
            center_dot=is_heard_only_station(item)
        )

        marker = map_widget.set_marker(
            lat,
            lon,
            text="",
            icon=icon,
            command=on_marker_click
        )

        try:
            marker.data = item
        except Exception:
            pass

        internet_station_markers.append(marker)

    except Exception as e:
        print(f"Draw marker error: {e}")

def draw_square(item, color):
    lat = item["lat"]
    lon = item["lon"]
    size = 0.3

    try:
        polygon = map_widget.set_polygon(
            [
                (lat + size, lon + size),
                (lat - size, lon + size),
                (lat - size, lon - size),
                (lat + size, lon - size)
            ],
            fill_color=color,
            outline_color=color,
            command=on_internet_polygon_click
        )

        try:
            polygon.data = item
        except Exception:
            pass

    except Exception as e:
        print(f"Draw square error: {e}")

def auto_fit_map(message_items):
    """
    Auto-fit disabled to preserve user's current map view during live updates.
    """
    return

def draw_my_station_marker():
    my_call = (config.get("callsign") or "").strip().upper()
    my_grid = (config.get("grid") or "").strip().upper()

    if not my_call or not my_grid:
        return

    try:
        lat, lon = maidenhead_to_latlon(my_grid)
    except Exception:
        return

    item = {
        "source": "my_station",
        "from_call": my_call,
        "grid": my_grid,
        "grid_source": "Station Setup",
        "lat": lat,
        "lon": lon,
        "band": "Home",
        "snr": "--",
        "raw": "My station location",
    }

    draw_station_marker(item)

def update_internet_map(message_items):
    clear_internet_map()

    # Always plot my station from Station Setup
    draw_my_station_marker()

    # message_items are already filtered/prepared by refresh_active_map()
    map_items = list(message_items)

    for item in map_items:
        draw_station_marker(item)

    auto_fit_map(map_items)


# -------------------------
# OFFLINE MAP
# -------------------------

def load_offline_map_image():
    global offline_map_image

    try:
        if USA_MAP_FILE.exists():
            offline_map_image = tk.PhotoImage(file=str(USA_MAP_FILE))
        else:
            offline_map_image = None
            print(f"Offline map image not found: {USA_MAP_FILE}")
    except Exception as e:
        print(f"Offline map image load error: {e}")
        offline_map_image = None


def get_offline_image_bounds(canvas_width, canvas_height):
    if offline_map_image is not None:
        img_w = offline_map_image.width()
        img_h = offline_map_image.height()
    else:
        img_w = USA_MAP_WIDTH
        img_h = USA_MAP_HEIGHT

    image_left = (canvas_width - img_w) / 2
    image_top = (canvas_height - img_h) / 2
    image_right = image_left + img_w
    image_bottom = image_top + img_h

    return image_left, image_top, image_right, image_bottom


def interpolate(value, src1, dst1, src2, dst2):
    if src2 == src1:
        return dst1
    ratio = (value - src1) / (src2 - src1)
    return dst1 + ratio * (dst2 - dst1)


def interpolate_from_points(value, points, src_key, dst_key):
    """
    Piecewise linear interpolation from calibration points.
    Points are sorted by src_key.
    """
    pts = sorted(points, key=lambda p: p[src_key])

    if not pts:
        return 0

    if len(pts) == 1:
        return pts[0][dst_key]

    if value <= pts[0][src_key]:
        return interpolate(
            value,
            pts[0][src_key], pts[0][dst_key],
            pts[1][src_key], pts[1][dst_key]
        )

    if value >= pts[-1][src_key]:
        return interpolate(
            value,
            pts[-2][src_key], pts[-2][dst_key],
            pts[-1][src_key], pts[-1][dst_key]
        )

    for i in range(len(pts) - 1):
        a = pts[i]
        b = pts[i + 1]
        if a[src_key] <= value <= b[src_key]:
            return interpolate(
                value,
                a[src_key], a[dst_key],
                b[src_key], b[dst_key]
            )

    return pts[-1][dst_key]


def image_xy_from_latlon(lat, lon):
    """
    Convert lat/lon to pixel coordinates on the original PNG image
    using calibration city anchors.
    """
    x = interpolate_from_points(lon, CALIBRATION_POINTS, "lon", "x")
    y = interpolate_from_points(lat, CALIBRATION_POINTS, "lat", "y")
    return x, y


def canvas_xy_from_latlon(lat, lon, canvas_width, canvas_height):
    image_left, image_top, image_right, image_bottom = get_offline_image_bounds(
        canvas_width, canvas_height
    )

    img_w = image_right - image_left
    img_h = image_bottom - image_top

    img_x, img_y = image_xy_from_latlon(lat, lon)

    x = image_left + (img_x / USA_MAP_WIDTH) * img_w
    y = image_top + (img_y / USA_MAP_HEIGHT) * img_h

    return x, y


def clear_offline_map():
    offline_canvas.delete("all")
    offline_station_items.clear()


def draw_offline_background():
    width = max(offline_canvas.winfo_width(), 900)
    height = max(offline_canvas.winfo_height(), 600)

    theme = get_theme()

    offline_canvas.create_rectangle(
        0, 0, width, height,
        fill=theme["map_bg"],
        outline=""
    )

    if offline_map_image is not None:
        offline_canvas.create_image(
            width // 2,
            height // 2,
            image=offline_map_image
        )
    else:
        offline_canvas.create_text(
            width // 2,
            height // 2 - 20,
            text="Offline map image not found",
            font=("TkDefaultFont", 14, "bold")
        )
        offline_canvas.create_text(
            width // 2,
            height // 2 + 10,
            text=f"Place a PNG file here:\n{USA_MAP_FILE}",
            font=("TkDefaultFont", 10),
            justify="center"
        )

    offline_canvas.create_text(
        width // 2,
        18,
        text="Offline Emergency Map",
        font=("TkDefaultFont", 12, "bold"),
        fill=theme["canvas_title_fg"]
    )


def draw_calibration_guides():
    if not SHOW_CALIBRATION_GUIDES:
        return

    width = max(offline_canvas.winfo_width(), 900)
    height = max(offline_canvas.winfo_height(), 600)

    image_left, image_top, image_right, image_bottom = get_offline_image_bounds(width, height)
    img_w = image_right - image_left
    img_h = image_bottom - image_top

    theme = get_theme()

    offline_canvas.create_rectangle(
        image_left, image_top, image_right, image_bottom,
        outline=theme["calibration_outline"],
        width=1,
        dash=(2, 2)
    )

    for pt in CALIBRATION_POINTS:
        cx = image_left + (pt["x"] / USA_MAP_WIDTH) * img_w
        cy = image_top + (pt["y"] / USA_MAP_HEIGHT) * img_h

        offline_canvas.create_oval(
            cx - 4, cy - 4, cx + 4, cy + 4,
            fill=theme["calibration_point_fill"],
            outline=theme["calibration_point_outline"]
        )


def draw_offline_station(item, highlight=False):
    width = max(offline_canvas.winfo_width(), 900)
    height = max(offline_canvas.winfo_height(), 600)

    worst = get_worst_status(item["parsed"]["status"])
    color = color_map.get(worst, "green")

    x, y = canvas_xy_from_latlon(item["lat"], item["lon"], width, height)
    size = 6

    if highlight:
        offline_canvas.create_oval(
            x - 12, y - 12, x + 12, y + 12,
            outline=get_theme()["highlight_outline"], width=2
        )

    offline_canvas.create_rectangle(
        x - size, y - size, x + size, y + size,
        fill=color,
        outline=color
    )

    offline_station_items.append({
        "item": item,
        "x": x,
        "y": y
    })


def update_offline_map(message_items, selected_item=None):
    clear_offline_map()
    draw_offline_background()
    draw_calibration_guides()

    for item in message_items:
        try:
            if not item.get("parsed"):
                continue

            if not item["parsed"].get("grid"):
                continue

            highlight = (
                selected_item is not None
                and item.get("raw_line") == selected_item.get("raw_line")
            )

            draw_offline_station(item, highlight=highlight)

        except Exception as e:
            print(f"Offline map update error for '{item.get('raw', 'unknown')}': {e}")

def on_offline_map_click(event):
    width = max(offline_canvas.winfo_width(), 900)
    height = max(offline_canvas.winfo_height(), 600)

    image_left, image_top, image_right, image_bottom = get_offline_image_bounds(width, height)

    rel_x = event.x - image_left
    rel_y = event.y - image_top

    click_text = (
        f"Canvas x,y = ({event.x}, {event.y})    "
        f"Image x,y = ({int(round(rel_x))}, {int(round(rel_y))})"
    )

    print(click_text)
    click_status_var.set(click_text)


def refresh_active_map(selected_item=None):
    # Build map from the main filtered message list PLUS any mappable
    # VarAC Activity Feed items. This keeps VarAC CQ/BEACON markers
    # synchronized with the VarAC Activity Feed.
    combined_items = list(filtered_messages)

    existing_keys = set()
    for item in combined_items:
        existing_keys.add(get_message_unique_key(item))

    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    cutoff_time = now - datetime.timedelta(hours=current_filter_days)

    for item in broadcast_messages:
        if item.get("lat") is None or item.get("lon") is None:
            continue

        timestamp = item.get("timestamp")
        if not timestamp or timestamp < cutoff_time:
            continue

        key = get_message_unique_key(item)
        if key in existing_keys:
            continue

        combined_items.append(item)
        existing_keys.add(key)

    map_items = get_latest_messages_for_map(combined_items)

    # Both Internet and MBTiles Offline modes use map_widget.
    # Offline mode simply changes the tile server to local MBTiles.
    update_internet_map(map_items)

    if MAP_MODE == "Internet":
        click_status_var.set("Internet map mode")
    else:
        click_status_var.set("Offline MBTiles map mode")


def set_map_mode(mode):
    global MAP_MODE
    MAP_MODE = mode

    if mode == "Internet":
        offline_canvas.pack_forget()
        map_widget.pack(fill="both", expand=True)

        # Default online tiles
        map_widget.set_tile_server(
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        )

        refresh_active_map()

    elif mode == "Offline":
        offline_canvas.pack_forget()
        map_widget.pack(fill="both", expand=True)

        port = start_mbtiles_server(BASE_MBTILES_FILE)

        if port:
            map_widget.set_tile_server(
                f"http://127.0.0.1:{port}/{{z}}/{{x}}/{{y}}.png"
            )
            map_widget.set_position(34.5, -88.0)
            map_widget.set_zoom(6)
            print("Offline MBTiles map enabled.")
        else:
            print("Offline MBTiles map unavailable; falling back to internet map.")
            map_widget.set_tile_server(
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
            )

        refresh_active_map()


def on_offline_canvas_resize(event):
    if MAP_MODE == "Offline":
        selected_item = get_selected_item()
        update_offline_map(filtered_messages, selected_item=selected_item)


# -------------------------
# LIST / FILTERS
# -------------------------


def get_message_unique_key(item):
    """
    Use raw log line as the primary unique key for real VarAC messages.
    Fall back to a synthetic key for sample messages.
    """
    raw_line = item.get("raw_line", "").strip()
    if raw_line and raw_line != item.get("raw", ""):
        return raw_line

    return (
        f"{item.get('timestamp', '')}|"
        f"{item.get('from_call', '')}|"
        f"{item.get('raw', '')}"
    )


def register_message_if_new(item):
    """
    Add message only if we have not already seen it.
    Returns True if added, False if duplicate.
    """
    key = get_message_unique_key(item)

    if key in seen_message_keys:
        return False

    seen_message_keys.add(key)
    messages.append(item)
    return True

def get_latest_messages_for_map(message_items):
    """
    Keep only the newest mappable item per station,
    respecting the current time filter window.
    """
    latest_by_station = {}

    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    cutoff_time = None
    try:
        if current_filter_days is not None:
            cutoff_time = now - datetime.timedelta(hours=current_filter_days)
    except Exception:
        cutoff_time = None

    for item in message_items:
        lat = item.get("lat")
        lon = item.get("lon")

        if lat is None or lon is None:
            continue

        timestamp = item.get("timestamp")

        
        # 🔥 CRITICAL FIX: Apply time filter HERE
        if cutoff_time and timestamp:
            if timestamp < cutoff_time:
                continue

        from_call = (item.get("from_call", "") or "").strip().upper()
        if not from_call:
            from_call = "UNKNOWN"

        existing = latest_by_station.get(from_call)

        if existing is None or item["timestamp"] > existing["timestamp"]:
            latest_by_station[from_call] = item

    latest_items = list(latest_by_station.values())
    latest_items.sort(key=lambda x: x["timestamp"])
    return latest_items

def format_record_for_list(item):
    timestamp = item.get("timestamp")

    if timestamp:
        time_text = timestamp.strftime("%m-%d %H:%M")
    else:
        time_text = "??-?? ??:??"

    from_call = (item.get("from_call", "") or config.get("callsign", "")).strip()
    if not from_call:
        from_call = "UNKNOWN"

    snr = item.get("snr", "")
    if snr in (None, ""):
        snr_text = "SNR:--"
    else:
        try:
            snr_text = f"SNR:{int(snr):+03d}"
        except Exception:
            snr_text = f"SNR:{snr}"

    band = (item.get("band") or "").strip()
    band_text = band if band else "?"

    payload = (item.get("raw") or "").strip()

    return (
        f"{time_text} "
        f"{from_call:8} "
        f"{snr_text:7} "
        f"{band_text:4} "
        f"{payload}"
    )


def refresh_listbox(message_items):
    global visible_main_feed_items

    main_feed_list.delete(0, tk.END)
    visible_main_feed_items = []

    for item in message_items:
        source = (item.get("source") or "").strip().lower()
        raw = (item.get("raw") or "").strip().upper()

        # Keep VarAC cqframe/beacon activity out of the JS8/main feed.
        # These still plot on the map and can appear in the VarAC Activity Feed.
        if source == "varac" and raw.startswith("CQFRAME"):
            continue

        main_feed_list.insert(tk.END, format_record_for_list(item))
        visible_main_feed_items.append(item)

    if main_feed_list.size() > 0:
        main_feed_list.see(tk.END)


def format_broadcast_message_for_display(raw_message):
    raw_message = (raw_message or "").strip()

    if not raw_message:
        return ""

    if raw_message == "^ALL":
        return "Path Finder Request: ALL"

    if raw_message.startswith("^") and len(raw_message) > 1:
        return f"Path Finder Request: {raw_message[1:]}"

    return raw_message


def format_broadcast_feed_line(item):
    timestamp = item.get("timestamp")
    from_call = item.get("from_call", "").strip()
    snr = item.get("snr")
    band = (item.get("band", "") or "").strip()
    message = format_broadcast_message_for_display(item.get("message", ""))

    if timestamp:
        time_str = timestamp.strftime("%m-%d %H:%M")
    else:
        time_str = "??-?? ??:??"

    if snr is None:
        snr_str = "---"
    else:
        snr_str = f"{snr}"

    if not band:
        band = "?"

    return f"{time_str}  {from_call:<8}  {snr_str:>4}  {band:<4}  {message}\n\n"


def refresh_broadcast_feed():
    global visible_broadcast_feed_items, selected_broadcast_feed_index

    if not hasattr(refresh_broadcast_feed, "_initialized"):
        refresh_broadcast_feed._initialized = False
        refresh_broadcast_feed._last_visible_key = None
        refresh_broadcast_feed._last_visible_count = 0

    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    cutoff_time = now - datetime.timedelta(hours=current_filter_days)

    filtered_items = []

    for item in broadcast_messages:
        timestamp = item.get("timestamp")

        if not timestamp:
            continue

        if timestamp >= cutoff_time:
            filtered_items.append(item)

    current_items = filtered_items[-BROADCAST_FEED_LIMIT:]

    visible_broadcast_feed_items = list(current_items)

    if selected_broadcast_feed_index is not None and selected_broadcast_feed_index >= len(visible_broadcast_feed_items):
        selected_broadcast_feed_index = None

    # Build a unique key from the last visible item
    if current_items:
        last_item = current_items[-1]
        current_last_key = (
            last_item.get("timestamp"),
            last_item.get("from_call", "").strip(),
            last_item.get("message", "").strip(),
        )
    else:
        current_last_key = None

    current_count = len(current_items)

    try:
        top_fraction, bottom_fraction = broadcast_feed_text.yview()
        was_at_bottom = bottom_fraction >= 0.999
    except Exception:
        was_at_bottom = True

    # First load or empty/reset case: rebuild once
    if (not refresh_broadcast_feed._initialized) or (refresh_broadcast_feed._last_visible_key is None):
        broadcast_feed_text.config(state="normal")
        broadcast_feed_text.delete("1.0", tk.END)

        for item in current_items:
            line = format_broadcast_feed_line(item)
            broadcast_feed_text.insert(tk.END, line)

        broadcast_feed_text.config(state="disabled")
        broadcast_feed_text.see(tk.END)

        refresh_broadcast_feed._initialized = True
        refresh_broadcast_feed._last_visible_key = current_last_key
        return

    # If newest visible item changed, rebuild the visible feed slice
    if (
        current_last_key != refresh_broadcast_feed._last_visible_key
        or current_count != refresh_broadcast_feed._last_visible_count
    ):
        broadcast_feed_text.config(state="normal")
        broadcast_feed_text.delete("1.0", tk.END)

        for item in current_items:
            line = format_broadcast_feed_line(item)
            broadcast_feed_text.insert(tk.END, line)

        if was_at_bottom:
            broadcast_feed_text.see(tk.END)

        broadcast_feed_text.config(state="disabled")

    refresh_broadcast_feed._initialized = True
    refresh_broadcast_feed._last_visible_key = current_last_key
    refresh_broadcast_feed._last_visible_count = current_count



def clear_feed_selections():
    global selected_broadcast_feed_index, selection_clear_after_id

    selected_broadcast_feed_index = None
    selection_clear_after_id = None

    try:
        main_feed_list.selection_clear(0, tk.END)
    except Exception:
        pass

    try:
        broadcast_feed_text.config(state="normal")
        broadcast_feed_text.tag_remove("selected_broadcast_line", "1.0", tk.END)
        broadcast_feed_text.config(state="disabled")
    except Exception:
        pass


def schedule_selection_clear():
    global selection_clear_after_id

    try:
        if selection_clear_after_id is not None:
            root.after_cancel(selection_clear_after_id)

        selection_clear_after_id = root.after(SELECTION_TIMEOUT_MS, clear_feed_selections)

    except Exception as e:
        print(f"Selection timeout schedule error: {e}")


def on_broadcast_feed_click(event):
    global selected_broadcast_feed_index

    try:
        index_text = broadcast_feed_text.index(f"@{event.x},{event.y}")
        line_number = int(index_text.split(".")[0])
        item_index = (line_number - 1) // 2

        if item_index < 0 or item_index >= len(visible_broadcast_feed_items):
            selected_broadcast_feed_index = None
            return

        selected_broadcast_feed_index = item_index

        broadcast_feed_text.config(state="normal")
        broadcast_feed_text.tag_remove("selected_broadcast_line", "1.0", tk.END)

        start = f"{line_number}.0"
        end = f"{line_number}.end"
        broadcast_feed_text.tag_add("selected_broadcast_line", start, end)

        broadcast_feed_text.config(state="disabled")
        main_feed_list.selection_clear(0, tk.END)
        schedule_selection_clear()

    except Exception as e:
        print(f"Broadcast feed click error: {e}")


def apply_filter(hours=24):
    global filtered_messages, current_filter_days

    if hours is None:
        filtered_messages = list(messages)
    else:
        current_filter_days = hours
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        filtered_messages = [item for item in messages if item["timestamp"] > cutoff]

    filtered_messages.sort(key=lambda item: item.get("timestamp", datetime.datetime.min))

    refresh_listbox(filtered_messages)

    # Force VarAC Activity Feed to rebuild whenever the time filter changes.
    try:
        refresh_broadcast_feed._initialized = False
        refresh_broadcast_feed._last_visible_key = None
        refresh_broadcast_feed._last_visible_count = 0
    except Exception:
        pass

    refresh_broadcast_feed()
    refresh_active_map()

def filter_messages_hours(hours):
    config["js8_activity_filter_hours"] = hours
    save_config()
    apply_filter(hours)

# -------------------------
# SAMPLE DATA
# -------------------------

def create_sample_file_if_missing():
    if SAMPLE_FILE.exists():
        return

    sample_lines = [
    "KW3KW|@HRMS,FM05SE,1,801,111111111111,All Good,{&%}",
    "W3BFO|@HRMS,FN20GG,1,802,111111111111,All Good,{&%}"
]

    try:
        with open(SAMPLE_FILE, "w", encoding="utf-8") as f:
            for line in sample_lines:
                f.write(line + "\n")
    except Exception as e:
        print(f"Sample file creation error: {e}")


def load_sample_messages():
    global messages

    messages.clear()
    seen_message_keys.clear()

    create_sample_file_if_missing()
    now = datetime.datetime.now(datetime.UTC)

    try:
        with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    callsign, raw = line.split("|", 1)
                    callsign = callsign.strip().upper()
                    raw = raw.strip()

                    sample_time = now + datetime.timedelta(seconds=idx)

                    item = make_message_record(
                        raw=raw,
                        timestamp=sample_time,
                        from_call=callsign,
                        to_call="ALL",
                        band="TEST",
                        log_timestamp_text=sample_time.strftime("%d/%m/%Y %H:%M:%S"),
                        message_timestamp_text=sample_time.strftime("%-m/%-d/%Y %-I:%M:%S %p") if os.name != "nt" else sample_time.strftime("%m/%d/%Y %I:%M:%S %p"),
                        raw_line=f"SAMPLE::{idx}::{callsign}::{raw}"
                    )
                    register_message_if_new(item)

                except Exception as e:
                    print(f"Sample parse error for '{line}': {e}")

    except Exception as e:
        print(f"Sample load error: {e}")
        messagebox.showerror("Error", f"Could not load sample messages:\n{e}")

    show_standard_messages()
    
    
def process_new_broadcast_rows(rows):
    global last_broadcast_id, broadcast_messages

    added_count = 0

    for row in rows:
        try:
            row_id = int(row["id"])
            if row_id > last_broadcast_id:
                last_broadcast_id = row_id

            raw = (row["broadcast_message"] or "").strip()

            timestamp = datetime.datetime.now()
            try:
                ts = str(row["broadcast_time"]).replace("Z", "")
                if "." in ts:
                    main_part, frac_part = ts.split(".", 1)
                    frac_part = (frac_part + "000000")[:6]
                    ts = f"{main_part}.{frac_part}"
                    timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    timestamp = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

            broadcast_messages.append({
                "timestamp": timestamp,
                "from_call": (row["from_callsign"] or "").strip(),
                "message": raw,
                "snr": row["snr"],
                "band": (row["band"] or "").strip()
            })

            if len(broadcast_messages) > BROADCAST_MEMORY_LIMIT:
                broadcast_messages = broadcast_messages[-BROADCAST_MEMORY_LIMIT:]

            added_count += 1

        except Exception as e:
            print(f"SQLite live row parse error: {e}")

    if added_count:
        refresh_broadcast_feed()
        click_status_var.set(
            f"SQLite live monitor: added {added_count} new VarAC broadcast message(s)"
        )


def process_new_cqframe_rows(rows):
    global last_cqframe_id

    added_count = 0

    for row in rows:
        try:
            row_id = int(row["id"])

            if row_id > last_cqframe_id:
                last_cqframe_id = row_id

            callsign = (row["from_callsign"] or "").strip().upper()
            locator = (row["locator"] or "").strip().upper()

            if not callsign:
                continue

            timestamp = datetime.datetime.now()

            try:
                ts = str(row["cqframe_time"]).replace("Z", "")

                if "." in ts:
                    main_part, frac_part = ts.split(".", 1)
                    frac_part = (frac_part + "000000")[:6]
                    ts = f"{main_part}.{frac_part}"

                    timestamp = datetime.datetime.strptime(
                        ts,
                        "%Y-%m-%d %H:%M:%S.%f"
                    )
                else:
                    timestamp = datetime.datetime.strptime(
                        ts,
                        "%Y-%m-%d %H:%M:%S"
                    )

            except Exception:
                pass

            grid_source = "cqframe"

            if not locator or not looks_like_grid(locator):
                try:
                    resolved_grid, resolved_source = resolve_grid_for_js8_station(
                        callsign,
                        ""
                    )
                    locator = (resolved_grid or "").strip().upper()
                    grid_source = resolved_source or "callsign lookup"
                except Exception:
                    locator = ""
                    grid_source = ""

            if not locator or not looks_like_grid(locator):
                continue

            try:
                lat, lon = maidenhead_to_latlon(locator)
            except Exception:
                continue

            item = {
                "source": "varac",
                "timestamp": timestamp,
                "from_call": callsign,
                "to_call": "",
                "band": (row["band"] or "").strip(),
                "snr": row["snr"],
                "raw": f"CQFRAME {locator}",
                "raw_line": f"CQFRAME::{row_id}",
                "grid": locator,
                "grid_source": grid_source,
                "lat": lat,
                "lon": lon,
            }

            is_new_map_item = register_message_if_new(item)

            if is_new_map_item:
                added_count += 1

            try:
                cqframe_type_id = int(row["cqframe_type_id"])
            except Exception:
                cqframe_type_id = 0

            if cqframe_type_id == 1:
                activity_label = "CQ"
                activity_type = "cq"
            else:
                activity_label = "BEACON"
                activity_type = "beacon"

            feed_item = dict(item)
            feed_item["message"] = f"{activity_label} {locator}"
            feed_item["activity_type"] = activity_type

            broadcast_messages.append(feed_item)

            if len(broadcast_messages) > BROADCAST_MEMORY_LIMIT:
                broadcast_messages[:] = broadcast_messages[-BROADCAST_MEMORY_LIMIT:]

        except Exception as e:
            print(f"CQ frame live row parse error: {e}")

    if added_count:
        apply_filter(current_filter_days)
        refresh_broadcast_feed()

        click_status_var.set(
            f"VarAC activity monitor: added {added_count} beacon/heard station(s)"
        )


def poll_sqlite_database():
    global sqlite_monitor_enabled

    try:
        if not sqlite_monitor_enabled:
            root.after(sqlite_poll_interval_ms, poll_sqlite_database)
            return

        db_path = get_varac_db_path()

        if not db_path.exists():
            click_status_var.set(
                "VarAC SQLite database not found. Use Setup > Select VarAC Database."
            )
            root.after(sqlite_poll_interval_ms, poll_sqlite_database)
            return

        rows = get_new_broadcast_rows(last_broadcast_id)
        process_new_broadcast_rows(rows)

        cq_rows = get_new_cqframe_rows(last_cqframe_id)
        process_new_cqframe_rows(cq_rows)

        refresh_gateway_dashboard()

    except Exception as e:
        print(f"SQLite polling error: {e}")
        click_status_var.set(f"SQLite polling error: {e}")

    root.after(sqlite_poll_interval_ms, poll_sqlite_database)       


def start_sqlite_monitor():
    global last_broadcast_id, sqlite_monitor_enabled

    db_path = get_varac_db_path()

    if not db_path.exists():
        sqlite_monitor_enabled = False
        click_status_var.set(
            "VarAC SQLite database not found. Use Setup > Select VarAC Database."
        )
        return

    try:
        last_broadcast_id = get_max_broadcast_id()
        sqlite_monitor_enabled = True

        click_status_var.set(
            f"SQLite live monitor started at broadcast ID {last_broadcast_id}"
        )

    except Exception as e:
        sqlite_monitor_enabled = False
        print(f"SQLite monitor start error: {e}")
        click_status_var.set(f"SQLite monitor start error: {e}")


def show_standard_messages():
    """
    Reload real STATREP messages from the VarAC SQLite database
    and display them again after sample mode was used.
    """
    global last_broadcast_id

    success = load_messages_from_db()
    load_broadcast_feed_from_db()

    if success:
        last_broadcast_id = get_max_broadcast_id()
        apply_filter(current_filter_days)
        click_status_var.set("Showing standard SQLite data from VarAC database")
    else:
        messagebox.showwarning(
            "Standard STATREPs",
            "Could not reload standard STATREPs from the VarAC SQLite database."
        )


# -------------------------
# DETAILS WINDOW
# -------------------------

def calculate_distance_and_bearing_latlon(lat1, lon1, lat2, lon2):
    """
    Returns distance in miles and initial bearing/azimuth in degrees.
    """
    try:
        r_miles = 3958.8

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad)
            * math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = r_miles * c

        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (
            math.cos(lat1_rad) * math.sin(lat2_rad)
            - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        )

        bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

        return distance, bearing

    except Exception:
        return None, None


def get_distance_bearing_from_my_station(item):
    """
    Calculates distance and azimuth from my Station Setup grid to this item.
    """
    try:
        my_grid = (config.get("grid") or "").strip().upper()
        lat2 = item.get("lat")
        lon2 = item.get("lon")

        if not my_grid or lat2 is None or lon2 is None:
            return None, None

        lat1, lon1 = maidenhead_to_latlon(my_grid)

        return calculate_distance_and_bearing_latlon(lat1, lon1, lat2, lon2)

    except Exception:
        return None, None


def format_message_details(item):
    parsed = item.get("parsed") or {}

    timestamp = item.get("timestamp")
    if timestamp:
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp_str = ""

    lat = item.get("lat")
    lon = item.get("lon")

    distance, bearing = get_distance_bearing_from_my_station(item)

    lines = [
        "RF Activity:",
        "",
        f"Source:      {item.get('source', '')}",
        f"From:        {item.get('from_call', '')}",
        f"To:          {item.get('to_call', '')}",
        f"Band:        {item.get('band', '')}",
        f"SNR:         {item.get('snr', '')}",
        f"Grid:        {item.get('grid') or parsed.get('grid', '')}",
        f"Grid Source: {item.get('grid_source', '')}",
    ]

    if lat is not None and lon is not None:
        lines.extend([
            f"Latitude:    {lat:.4f}",
            f"Longitude:   {lon:.4f}",
        ])
    else:
        lines.extend([
            "Latitude:    Not available",
            "Longitude:   Not available",
        ])

    if distance is not None and bearing is not None:
        lines.extend([
            f"Distance:    {distance:.1f} miles",
            f"Azimuth:     {bearing:.0f}°",
        ])
    else:
        lines.extend([
            "Distance:    Not available",
            "Azimuth:     Not available",
        ])

    lines.append(f"Timestamp:   {timestamp_str}")

    comment = parsed.get("comment") or item.get("raw", "")
    if comment:
        lines.extend([
            "",
            "Message:",
            comment
        ])

    if item.get("log_timestamp_text"):
        lines.append(f"Log Time:    {item['log_timestamp_text']}")

    if item.get("message_timestamp_text"):
        lines.append(f"Msg Time:    {item['message_timestamp_text']}")

    lines.extend([
        "",
        "Raw Message:",
        item.get("raw", "")
    ])

    if item.get("raw_line") and item.get("raw_line") != item.get("raw"):
        lines.extend([
            "",
            "Raw Log Line:",
            item.get("raw_line", "")
        ])

    return "\n".join(lines)


def open_details_window(item):
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("STATION Details")
    win.geometry("700x460")

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    text = tk.Text(
        outer,
        wrap="word",
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"],
        relief="solid",
        bd=1
    )
    text.pack(fill="both", expand=True)

    button_frame = tk.Frame(win, bg=theme["bg"])
    button_frame.pack(fill="x", padx=10, pady=(0, 10))

    tk.Button(
        button_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"],
        width=10
    ).pack(side="right")

    text.insert("1.0", format_message_details(item))
    text.config(state="disabled")

    apply_theme_to_toplevel(win)


def get_selected_item():
    selection = main_feed_list.curselection()

    if selection:
        index = selection[0]

        if 0 <= index < len(visible_main_feed_items):
            return visible_main_feed_items[index]

    if (
        selected_broadcast_feed_index is not None
        and 0 <= selected_broadcast_feed_index < len(visible_broadcast_feed_items)
    ):
        return visible_broadcast_feed_items[selected_broadcast_feed_index]

    return None


def on_main_feed_select(event=None):
    global selected_broadcast_feed_index

    selected_broadcast_feed_index = None

    try:
        broadcast_feed_text.config(state="normal")
        broadcast_feed_text.tag_remove("selected_broadcast_line", "1.0", tk.END)
        broadcast_feed_text.config(state="disabled")
    except Exception:
        pass

    schedule_selection_clear()


def open_selected_details():
    item = get_selected_item()
    if item is None:
        messagebox.showwarning("Selection", "Please select a message first.")
        return

    open_details_window(item)

def center_selected_on_map():
    item = get_selected_item()
    if item is None:
        messagebox.showwarning("Selection", "Please select a message first.")
        return

    try:
        lat = item.get("lat")
        lon = item.get("lon")
        callsign = (item.get("from_call") or "UNKNOWN").strip().upper()

        if lat is None or lon is None:
            click_status_var.set(f"No map location available for {callsign}.")
            messagebox.showinfo(
                "No Map Location",
                f"No grid/location data is available for {callsign}."
            )
            return

        map_widget.set_position(lat, lon)
        map_widget.set_zoom(7)
        refresh_active_map(selected_item=item)
        click_status_var.set(f"Centered map on {callsign}.")

    except Exception as e:
        print(f"Map center/highlight error: {e}")
        messagebox.showerror("Map Error", f"Unable to center map:\n{e}")

def show_selected_message(event=None):
    item = get_selected_item()
    if item is None:
        messagebox.showwarning("Selection", "Please select a message first.")
        return

    try:
        if MAP_MODE == "Internet":
            map_widget.set_position(item["lat"], item["lon"])
            map_widget.set_zoom(7)
        else:
            update_offline_map(filtered_messages, selected_item=item)
    except Exception as e:
        print(f"Map center/highlight error: {e}")

    open_details_window(item)


# -------------------------
# STATREP generator removed.
# Legacy STATREP parsing/loading cleanup will be handled separately.

def open_callsign_propagation_report():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Callsign Propagation Report")
    configure_toplevel_window(win, 760, 560, min_width=680, min_height=500)

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    form_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=10,
        pady=10
    )
    form_frame.pack(fill="x", expand=False)

    tk.Label(
        form_frame,
        text="Callsign",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=0, column=0, padx=6, pady=6, sticky="w")

    callsign_entry = tk.Entry(
        form_frame,
        width=20,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"],
        relief="solid"
    )
    callsign_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

    def uppercase_callsign_entry(event=None):
        current = callsign_entry.get()
        upper = current.upper()

        if current != upper:
            pos = callsign_entry.index(tk.INSERT)

            callsign_entry.delete(0, tk.END)
            callsign_entry.insert(0, upper)

            callsign_entry.icursor(pos)

    callsign_entry.bind("<KeyRelease>", uppercase_callsign_entry)
    
    tk.Label(
        form_frame,
        text="Lookback Days",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=0, column=2, padx=6, pady=6, sticky="w")

    lookback_entry = tk.Entry(
        form_frame,
        width=8,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"],
        relief="solid"
    )
    lookback_entry.grid(row=0, column=3, padx=6, pady=6, sticky="w")
    lookback_entry.insert(0, "90")

    def generate_report():
        callsign = callsign_entry.get().strip().upper()
        lookback_text = lookback_entry.get().strip()

        if not callsign:
            messagebox.showwarning("Callsign Required", "Please enter a callsign.")
            return

        if not lookback_text.isdigit():
            messagebox.showwarning("Invalid Lookback", "Lookback Days must be a whole number.")
            return

        lookback_days = int(lookback_text)
        js8_rows = get_js8call_rows_for_callsign(callsign, lookback_days)

        if lookback_days <= 0:
            messagebox.showwarning("Invalid Lookback", "Lookback Days must be greater than zero.")
            return

        rows = get_qso_rows_for_callsign(callsign, lookback_days)
        heard_rows = get_cqframe_rows_for_callsign(callsign, lookback_days)
        js8_stats = analyze_js8call_activity(js8_rows)

        output.config(state="normal")
        output.delete("1.0", tk.END)

        if not rows and not heard_rows and not js8_rows:
            output.insert(
                "1.0",
                f"Callsign Propagation Report\n\n"
                f"Time Reference: UTC (Zulu)\n\n"
                f"Target Callsign: {callsign}\n"
                f"Lookback Days: {lookback_days}\n\n"
                f"No matching QSO, Beacon/Heard, or JS8Call records found.\n"
            )
            output.config(state="disabled")
            return

        output.insert(
            "1.0",
            f"Callsign Propagation Report\n\n"
            f"Time Reference: UTC (Zulu)\n\n"
            f"Target Callsign: {callsign}\n"
            f"Lookback Days: {lookback_days}\n\n"
        )

        if js8_stats:
            avg_snr = js8_stats.get("avg_snr")
            window_str = js8_stats.get("most_active_window", "N/A")
            snr_str = f"{avg_snr:.1f} dB" if avg_snr is not None else "N/A"

            output.insert(
                tk.END,
                "========================================\n"
                "JS8CALL ACTIVITY\n"
                "========================================\n\n"
                f"Matching JS8 records: {js8_stats['count']}\n\n"
                "JS8 Activity Estimate:\n"
                f"- Most active band: {js8_stats['most_common_band']}\n"
                f"- Most active window: {window_str} UTC\n"
                f"- Average JS8 SNR Received: {snr_str}\n\n"
            )

            output.insert(tk.END, "Bands active:\n")
            for band, count in sorted(js8_stats["band_counts"].items()):
                output.insert(tk.END, f"- {band}: {count} hits\n")

            output.insert(tk.END, "\nTime-of-day activity:\n")
            for window in ["00:00-05:59", "06:00-11:59", "12:00-17:59", "18:00-23:59"]:
                output.insert(
                    tk.END,
                    f"- {window}: {js8_stats['time_counts'].get(window, 0)} hits\n"
                )

            output.insert(
                tk.END,
                "\nSNR summary:\n"
                f"- Average JS8 SNR Received: {snr_str} ({js8_stats['snr_sample_count']} samples)\n\n"
            )

        # ============================================================
        # VARAC QSO ACTIVITY
        # ============================================================
        best_band = None
        best_time_bucket = None
        best_snr_bucket = None
        best_snr_value = None

        if rows:
            band_counts = {}

            for row in rows:
                band = (row["band"] or "Unknown").strip()
                if not band:
                    band = "Unknown"
                band_counts[band] = band_counts.get(band, 0) + 1

            sorted_bands = sorted(
                band_counts.items(),
                key=lambda item: (-item[1], item[0])
            )

            time_buckets = {
                "00:00-05:59": 0,
                "06:00-11:59": 0,
                "12:00-17:59": 0,
                "18:00-23:59": 0
            }

            bucket_snr_received = {
                "00:00-05:59": [],
                "06:00-11:59": [],
                "12:00-17:59": [],
                "18:00-23:59": []
            }

            for row in rows:
                starttime = (row["starttime"] or "").strip()

                try:
                    hour = int(starttime[11:13])
                except Exception:
                    continue

                if 0 <= hour <= 5:
                    time_buckets["00:00-05:59"] += 1
                elif 6 <= hour <= 11:
                    time_buckets["06:00-11:59"] += 1
                elif 12 <= hour <= 17:
                    time_buckets["12:00-17:59"] += 1
                elif 18 <= hour <= 23:
                    time_buckets["18:00-23:59"] += 1

            snr_received_values = []
            snr_sent_values = []

            for row in rows:
                snr_received = row["snr_received"]
                snr_sent = row["snr_sent"]

                starttime = (row["starttime"] or "").strip()

                try:
                    hour = int(starttime[11:13])
                except Exception:
                    hour = None

                if hour is not None:
                    if 0 <= hour <= 5:
                        bucket_label = "00:00-05:59"
                    elif 6 <= hour <= 11:
                        bucket_label = "06:00-11:59"
                    elif 12 <= hour <= 17:
                        bucket_label = "12:00-17:59"
                    elif 18 <= hour <= 23:
                        bucket_label = "18:00-23:59"
                    else:
                        bucket_label = None
                else:
                    bucket_label = None

                try:
                    if snr_received is not None and str(snr_received).strip() != "":
                        value = float(snr_received)
                        snr_received_values.append(value)

                        if bucket_label is not None:
                            bucket_snr_received[bucket_label].append(value)
                except Exception:
                    pass

                try:
                    if snr_sent is not None and str(snr_sent).strip() != "":
                        snr_sent_values.append(float(snr_sent))
                except Exception:
                    pass

            avg_snr_received = (
                sum(snr_received_values) / len(snr_received_values)
                if snr_received_values else None
            )

            avg_snr_sent = (
                sum(snr_sent_values) / len(snr_sent_values)
                if snr_sent_values else None
            )

            if band_counts:
                best_band = max(band_counts, key=band_counts.get)

            if time_buckets:
                best_time_bucket = max(time_buckets, key=time_buckets.get)

            for label, values in bucket_snr_received.items():
                if values:
                    avg_bucket_snr = sum(values) / len(values)
                    if best_snr_value is None or avg_bucket_snr > best_snr_value:
                        best_snr_value = avg_bucket_snr
                        best_snr_bucket = label

            output.insert(tk.END, "========================================\n")
            output.insert(tk.END, "VARAC QSO ACTIVITY\n")
            output.insert(tk.END, "========================================\n\n")

            output.insert(tk.END, f"Matching QSO records: {len(rows)}\n\n")

            output.insert(tk.END, "Best Contact Window Estimate:\n")

            if best_band is not None:
                output.insert(tk.END, f"- Best band: {best_band}\n")
            else:
                output.insert(tk.END, "- Best band: No data\n")

            if best_time_bucket is not None:
                output.insert(tk.END, f"- Best time window: {best_time_bucket} UTC\n")
            else:
                output.insert(tk.END, "- Best time window: No data\n")

            if best_snr_bucket is not None and best_snr_value is not None:
                output.insert(
                    tk.END,
                    f"- Strongest average received SNR window: "
                    f"{best_snr_bucket} UTC ({best_snr_value:.1f} dB)\n"
                )
            else:
                output.insert(tk.END, "- Strongest average received SNR window: No data\n")

            if best_band is not None and best_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- Best contact window estimate: Try {best_band} during "
                    f"{best_time_bucket} UTC\n\n"
                )
            else:
                output.insert(tk.END, "- Best contact window estimate: No data\n\n")

            output.insert(tk.END, "Bands worked:\n")

            for band, count in sorted_bands:
                output.insert(tk.END, f"- {band}: {count} QSOs\n")

            output.insert(tk.END, "\nTime-of-day activity:\n")

            for label, count in time_buckets.items():
                output.insert(tk.END, f"- {label}: {count} QSOs\n")

            output.insert(tk.END, "\nSNR summary:\n")

            if avg_snr_received is not None:
                output.insert(
                    tk.END,
                    f"- Average SNR received: {avg_snr_received:.1f} dB "
                    f"({len(snr_received_values)} samples)\n"
                )
            else:
                output.insert(tk.END, "- Average SNR received: No data\n")

            if avg_snr_sent is not None:
                output.insert(
                    tk.END,
                    f"- Average SNR sent: {avg_snr_sent:.1f} dB "
                    f"({len(snr_sent_values)} samples)\n"
                )
            else:
                output.insert(tk.END, "- Average SNR sent: No data\n")

            output.insert(tk.END, "\n")

        # ============================================================
        # VARAC BEACON / HEARD ACTIVITY
        # ============================================================
        best_heard_band = None
        best_heard_time_bucket = None
        best_heard_snr_bucket = None
        best_heard_snr_value = None

        if heard_rows:
            heard_band_counts = {}
            heard_time_buckets = {
                "00:00-05:59": 0,
                "06:00-11:59": 0,
                "12:00-17:59": 0,
                "18:00-23:59": 0
            }

            heard_bucket_snr = {
                "00:00-05:59": [],
                "06:00-11:59": [],
                "12:00-17:59": [],
                "18:00-23:59": []
            }

            heard_snr_values = []

            for row in heard_rows:
                band = (row["band"] or "Unknown").strip()
                if not band:
                    band = "Unknown"
                heard_band_counts[band] = heard_band_counts.get(band, 0) + 1

                ts = (row["cqframe_time"] or "").strip()

                try:
                    ts_clean = ts.replace("Z", "")
                    if "." in ts_clean:
                        main_part, frac_part = ts_clean.split(".", 1)
                        frac_part = (frac_part + "000000")[:6]
                        ts_clean = f"{main_part}.{frac_part}"
                        dt = datetime.datetime.strptime(ts_clean, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = datetime.datetime.strptime(ts_clean, "%Y-%m-%d %H:%M:%S")

                    hour = dt.hour
                except Exception:
                    hour = None

                if hour is not None:
                    if 0 <= hour <= 5:
                        bucket_label = "00:00-05:59"
                    elif 6 <= hour <= 11:
                        bucket_label = "06:00-11:59"
                    elif 12 <= hour <= 17:
                        bucket_label = "12:00-17:59"
                    elif 18 <= hour <= 23:
                        bucket_label = "18:00-23:59"
                    else:
                        bucket_label = None

                    if bucket_label is not None:
                        heard_time_buckets[bucket_label] += 1
                else:
                    bucket_label = None

                try:
                    snr = row["snr"]
                    if snr is not None and str(snr).strip() != "":
                        snr_value = float(snr)
                        heard_snr_values.append(snr_value)

                        if bucket_label is not None:
                            heard_bucket_snr[bucket_label].append(snr_value)
                except Exception:
                    pass

            sorted_heard_bands = sorted(
                heard_band_counts.items(),
                key=lambda item: (-item[1], item[0])
            )

            avg_heard_snr = (
                sum(heard_snr_values) / len(heard_snr_values)
                if heard_snr_values else None
            )

            if heard_band_counts:
                best_heard_band = max(heard_band_counts, key=heard_band_counts.get)

            if heard_time_buckets:
                best_heard_time_bucket = max(heard_time_buckets, key=heard_time_buckets.get)

            for label, values in heard_bucket_snr.items():
                if values:
                    avg_bucket_snr = sum(values) / len(values)
                    if best_heard_snr_value is None or avg_bucket_snr > best_heard_snr_value:
                        best_heard_snr_value = avg_bucket_snr
                        best_heard_snr_bucket = label

            output.insert(tk.END, "========================================\n")
            output.insert(tk.END, "VARAC BEACON / HEARD ACTIVITY\n")
            output.insert(tk.END, "========================================\n\n")

            output.insert(tk.END, f"Matching heard records: {len(heard_rows)}\n\n")

            output.insert(tk.END, "Heard Activity Estimate:\n")

            if best_heard_band is not None:
                output.insert(tk.END, f"- Most-heard band: {best_heard_band}\n")
            else:
                output.insert(tk.END, "- Most-heard band: No data\n")

            if best_heard_time_bucket is not None:
                output.insert(tk.END, f"- Most active heard window: {best_heard_time_bucket} UTC\n")
            else:
                output.insert(tk.END, "- Most active heard window: No data\n")

            if best_heard_snr_bucket is not None and best_heard_snr_value is not None:
                output.insert(
                    tk.END,
                    f"- Strongest average heard SNR window: "
                    f"{best_heard_snr_bucket} UTC ({best_heard_snr_value:.1f} dB)\n"
                )
            else:
                output.insert(tk.END, "- Strongest average heard SNR window: No data\n")

            if best_heard_band is not None and best_heard_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- Best heard window estimate: Station most often heard on "
                    f"{best_heard_band} during {best_heard_time_bucket} UTC\n\n"
                )
            else:
                output.insert(tk.END, "- Best heard window estimate: No data\n\n")

            output.insert(tk.END, "Bands heard:\n")
            for band, count in sorted_heard_bands:
                output.insert(tk.END, f"- {band}: {count} hits\n")

            output.insert(tk.END, "\nTime-of-day heard activity:\n")
            for label, count in heard_time_buckets.items():
                output.insert(tk.END, f"- {label}: {count} hits\n")

            output.insert(tk.END, "\nHeard SNR summary:\n")
            if avg_heard_snr is not None:
                output.insert(
                    tk.END,
                    f"- Average heard SNR: {avg_heard_snr:.1f} dB "
                    f"({len(heard_snr_values)} samples)\n"
                )
            else:
                output.insert(tk.END, "- Average heard SNR: No data\n")

            output.insert(tk.END, "\n")

        # ============================================================
        # OPERATOR SUMMARY
        # ============================================================
        output.insert(tk.END, "========================================\n")
        output.insert(tk.END, "OPERATOR SUMMARY\n")
        output.insert(tk.END, "========================================\n")

        if rows and heard_rows:
            output.insert(tk.END, "- VarAC QSO history exists for this station.\n")
            output.insert(tk.END, "- VarAC Beacon/heard data provides more frequent propagation sampling.\n")

            if best_band is not None and best_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- VarAC QSO data suggests trying {best_band} during {best_time_bucket} UTC.\n"
                )

            if best_heard_band is not None and best_heard_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- VarAC Heard data suggests the station is most often present on "
                    f"{best_heard_band} during {best_heard_time_bucket} UTC.\n"
                )

        elif rows and not heard_rows:
            output.insert(tk.END, "- VarAC QSO history exists for this station.\n")
            output.insert(tk.END, "- No VarAC Beacon/Heard records were found in cqframe for this period.\n")

            if best_band is not None and best_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- Best contact window estimate: {best_band} during {best_time_bucket} UTC.\n"
                )

        elif heard_rows and not rows:
            output.insert(tk.END, "- No VarAC QSO history found for this station in the selected period.\n")
            output.insert(tk.END, "- VarAC Beacon/heard data shows this station has been present on the air.\n")

            if best_heard_band is not None and best_heard_time_bucket is not None:
                output.insert(
                    tk.END,
                    f"- Best heard window estimate: {best_heard_band} during {best_heard_time_bucket} UTC.\n"
                )

        if js8_stats:
            avg_snr = js8_stats.get("avg_snr")
            snr_str = f"{avg_snr:.1f} dB" if avg_snr is not None else "N/A"

            output.insert(
                tk.END,
                f"- JS8Call: {js8_stats['most_common_band']} during {js8_stats['most_active_window']} UTC (Avg SNR {snr_str})\n"
            )
        output.config(state="disabled")

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Generate Report",
        command=generate_report,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"]
    ).pack(side="right")

    win.bind("<Return>", lambda event: generate_report())

    output_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=8,
        pady=8
    )
    output_frame.pack(fill="both", expand=True, pady=(10, 0))

    output = tk.Text(
        output_frame,
        wrap="word",
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"],
        relief="solid",
        bd=1
    )
    output.pack(fill="both", expand=True)
    output.config(state="disabled")

    form_frame.columnconfigure(1, weight=1)
    form_frame.columnconfigure(3, weight=0)

    apply_theme_to_toplevel(win)
    callsign_entry.focus_set()




def open_zulu_time_reference():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Zulu / UTC Time Reference")
    configure_toplevel_window(win, 620, 500, min_width=500, min_height=350)
    win.configure(bg=theme["bg"])

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=8, pady=8)

    title = tk.Label(
        outer,
        text="Add these hours to local time to get Zulu / UTC",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 10, "bold")
    )
    title.pack(anchor="w", pady=(0, 8))

    columns = ("zone", "standard", "daylight")

    style_name = "Zulu.Treeview"

    style = ttk.Style()
    style.configure(
        style_name,
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        fieldbackground=theme["entry_bg"],
        rowheight=24
    )
    style.configure(
        f"{style_name}.Heading",
        background=theme["button_bg"],
        foreground=theme["button_fg"]
    )

    tree = ttk.Treeview(
        outer,
        columns=columns,
        show="headings",
        height=16,
        style=style_name
    )

    tree.heading("zone", text="US Time Zone")
    tree.heading("standard", text="Standard Time")
    tree.heading("daylight", text="Daylight Time")

    tree.column("zone", width=220, anchor="w", stretch=True)
    tree.column("standard", width=160, anchor="center", stretch=False)
    tree.column("daylight", width=160, anchor="center", stretch=False)

    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    zulu_offsets = [
        ("Eastern", "+5 hrs", "+4 hrs"),
        ("Central", "+6 hrs", "+5 hrs"),
        ("Mountain", "+7 hrs", "+6 hrs"),
        ("Pacific", "+8 hrs", "+7 hrs"),
        ("Alaska", "+9 hrs", "+8 hrs"),
        ("Hawaii", "+10 hrs", "No DST"),
        ("Arizona", "+7 hrs", "No DST"),
    ]

    for zone, standard, daylight in zulu_offsets:
        tree.insert("", "end", values=(zone, standard, daylight))


def open_grid_coordinate_converter():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Grid Coordinate Converter")
    configure_toplevel_window(win, 680, 560, min_width=560, min_height=440)
    win.configure(bg=theme["bg"])

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    title = tk.Label(
        outer,
        text="Grid Coordinate Converter",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 12, "bold")
    )
    title.pack(anchor="w", pady=(0, 8))

    input_frame = tk.LabelFrame(
        outer,
        text="Coordinate Input",
        bg=theme["bg"],
        fg=theme["fg"],
        padx=8,
        pady=8
    )
    input_frame.pack(fill="x", pady=(0, 8))

    tk.Label(
        input_frame,
        text="Enter coordinates in any supported format:",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w")

    coord_var = tk.StringVar()

    entry = tk.Entry(
        input_frame,
        textvariable=coord_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    entry.pack(fill="x", pady=(4, 6))
    entry.focus_set()

    examples = tk.Label(
        input_frame,
        text="Examples: 34.1234 -88.5678   |   34 07.407 N 088 59.259 W   |   16S 323456 3776543   |   EM54",
        bg=theme["bg"],
        fg=theme["fg"],
        wraplength=620,
        justify="left"
    )
    examples.pack(anchor="w")

    button_frame = tk.Frame(input_frame, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(8, 0))

    output_mode_var = tk.StringVar(value="VarAC")

    mode_frame = tk.Frame(button_frame, bg=theme["bg"])
    mode_frame.pack(side="right")

    tk.Label(
        mode_frame,
        text="Output:",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(side="left", padx=(0, 6))

    ttk.Radiobutton(
        mode_frame,
        text="VarAC",
        variable=output_mode_var,
        value="VarAC"
    ).pack(side="left")

    ttk.Radiobutton(
        mode_frame,
        text="JS8Call",
        variable=output_mode_var,
        value="JS8Call"
    ).pack(side="left", padx=(6, 0))

    results_frame = tk.LabelFrame(
        outer,
        text="Conversion Results",
        bg=theme["bg"],
        fg=theme["fg"],
        padx=8,
        pady=8
    )
    results_frame.pack(fill="both", expand=True, pady=(0, 8))

    result_canvas = tk.Canvas(
        results_frame,
        bg=theme["bg"],
        highlightthickness=0
    )
    result_scrollbar = ttk.Scrollbar(
        results_frame,
        orient="vertical",
        command=result_canvas.yview
    )
    result_rows_frame = tk.Frame(result_canvas, bg=theme["bg"])

    result_rows_window = result_canvas.create_window(
        (0, 0),
        window=result_rows_frame,
        anchor="nw"
    )

    result_canvas.configure(yscrollcommand=result_scrollbar.set)

    result_canvas.pack(side="left", fill="both", expand=True)
    result_scrollbar.pack(side="right", fill="y")

    def update_result_scrollregion(event=None):
        result_canvas.configure(scrollregion=result_canvas.bbox("all"))

    def resize_result_rows(event=None):
        result_canvas.itemconfigure(result_rows_window, width=event.width)

    def scroll_results(event):
        if hasattr(event, "delta") and event.delta:
            result_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_results_up(event):
        result_canvas.yview_scroll(-1, "units")

    def scroll_results_down(event):
        result_canvas.yview_scroll(1, "units")

    result_rows_frame.bind("<Configure>", update_result_scrollregion)
    result_canvas.bind("<Configure>", resize_result_rows)

    # Mouse wheel / touchpad support across platforms.
    result_canvas.bind("<MouseWheel>", scroll_results)
    result_rows_frame.bind("<MouseWheel>", scroll_results)
    result_canvas.bind("<Button-4>", scroll_results_up)
    result_canvas.bind("<Button-5>", scroll_results_down)
    result_rows_frame.bind("<Button-4>", scroll_results_up)
    result_rows_frame.bind("<Button-5>", scroll_results_down)

    def enable_result_mousewheel(event=None):
        win.bind_all("<MouseWheel>", scroll_results)
        win.bind_all("<Button-4>", scroll_results_up)
        win.bind_all("<Button-5>", scroll_results_down)

    def disable_result_mousewheel(event=None):
        win.unbind_all("<MouseWheel>")
        win.unbind_all("<Button-4>")
        win.unbind_all("<Button-5>")

    result_canvas.bind("<Enter>", enable_result_mousewheel)
    result_rows_frame.bind("<Enter>", enable_result_mousewheel)
    results_frame.bind("<Enter>", enable_result_mousewheel)

    result_canvas.bind("<Leave>", disable_result_mousewheel)
    results_frame.bind("<Leave>", disable_result_mousewheel)

    result_vars = {}

    status_var = tk.StringVar(value="Ready.")

    def copy_to_clipboard(value, label="Coordinate"):
        value = (value or "").strip()

        if not value:
            status_var.set(f"{label} is empty.")
            return

        prefix_map = {
            "Decimal Degrees": "DD",
            "Degrees Decimal Minutes": "DDM",
            "Degrees Minutes Seconds": "DMS",
            "Maidenhead Grid": "GRID",
            "UTM": "UTM",
            "MGRS 100m": "MGRS",
            "MGRS 10m": "MGRS",
        }

        prefix = prefix_map.get(label)
        clipboard_text = f"{prefix}: {value}" if prefix else value

        try:
            copy_text_to_clipboard(clipboard_text, widget=win)
            status_var.set(f"Copied {label}.")
        except Exception as e:
            status_var.set(f"Copy failed: {e}")

    def make_result_row(parent, label):
        row = tk.Frame(parent, bg=theme["bg"])
        row.pack(fill="x", pady=2)

        tk.Label(
            row,
            text=label,
            width=24,
            anchor="w",
            bg=theme["bg"],
            fg=theme["fg"]
        ).pack(side="left")

        var = tk.StringVar()

        value_entry = tk.Entry(
            row,
            textvariable=var,
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            insertbackground=theme["entry_fg"],
            relief="sunken"
        )
        value_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ttk.Button(
            row,
            text="Copy",
            command=lambda v=var, l=label: copy_to_clipboard(v.get(), l)
        ).pack(side="right")

        result_vars[label] = var

    for row_label in [
        "Detected Format",
        "Original / Cleaned",
        "Decimal Degrees",
        "Degrees Decimal Minutes",
        "Degrees Minutes Seconds",
        "Maidenhead Grid",
        "UTM",
        "MGRS 100m",
        "MGRS 10m",
    ]:
        make_result_row(result_rows_frame, row_label)


    status_label = tk.Label(
        outer,
        textvariable=status_var,
        bg=theme["bg"],
        fg=theme["fg"],
        anchor="w"
    )
    status_label.pack(fill="x")

    def clear_results():
        coord_var.set("")
        for var in result_vars.values():
            var.set("")
        status_var.set("Ready.")
        entry.focus_set()

    def convert_coordinates():
        raw = coord_var.get().strip()

        for var in result_vars.values():
            var.set("")

        if not raw:
            status_var.set("Enter coordinates first.")
            return

        lat, lon, format_name = parse_any_coordinate(raw)

        if lat is None or lon is None:
            status_var.set(
                "Unable to convert. Try decimal lat/lon, Maidenhead, UTM, or MGRS."
            )
            return

        result_vars["Detected Format"].set(format_name)

        radio_safe = output_mode_var.get() == "JS8Call"

        for label, value in build_coordinate_outputs(lat, lon, raw, radio_safe=radio_safe):
            if label in result_vars and value:
                result_vars[label].set(value)

        status_var.set("Conversion complete.")

    output_mode_var.trace_add("write", lambda *args: convert_coordinates())

    ttk.Button(
        button_frame,
        text="Convert",
        command=convert_coordinates
    ).pack(side="left", padx=(0, 6))

    ttk.Button(
        button_frame,
        text="Clear",
        command=clear_results
    ).pack(side="left")

    entry.bind("<Return>", lambda event: convert_coordinates())






def get_custom_nets_file():
    """
    Return the JSON file used for operator-entered scheduled nets.
    """
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "custom_nets.json"


def load_custom_nets():
    """
    Load operator-entered scheduled nets from JSON.
    """
    global CUSTOM_NETS

    path = get_custom_nets_file()

    if not path.exists():
        CUSTOM_NETS = []
        return

    try:
        import json
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            CUSTOM_NETS = data
        else:
            CUSTOM_NETS = []

    except Exception as e:
        print(f"Could not load custom nets: {e}")
        CUSTOM_NETS = []


def save_custom_nets():
    """
    Save operator-entered scheduled nets to JSON.
    """
    try:
        import json
        path = get_custom_nets_file()
        with path.open("w", encoding="utf-8") as f:
            json.dump(CUSTOM_NETS, f, indent=2)
    except Exception as e:
        print(f"Could not save custom nets: {e}")





def open_enter_scheduled_net_window():
    """
    Simple scheduled net entry dialog.
    """
    from tkinter import simpledialog, messagebox

    name = simpledialog.askstring(
        "Scheduled Net",
        "Net Name:"
    )

    if not name:
        return

    frequency = simpledialog.askstring(
        "Scheduled Net",
        "Frequency:"
    )

    if not frequency:
        return

    mode = simpledialog.askstring(
        "Scheduled Net",
        "Mode:"
    ) or "---"

    schedule = simpledialog.askstring(
        "Scheduled Net",
        "Schedule:"
    ) or "Not specified"

    description = simpledialog.askstring(
        "Scheduled Net",
        "Description:"
    ) or "Operator scheduled net"

    comments = simpledialog.askstring(
        "Scheduled Net",
        "Comments / Details:"
    ) or "No comments entered."

    entry = {
        "category": "Scheduled Net",
        "frequency": frequency,
        "mode": mode,
        "name": name,
        "description": description,
        "details": (
            f"{name}\n\n"
            f"Frequency: {frequency}\n"
            f"Mode: {mode}\n"
            f"Schedule: {schedule}\n"
            f"Description: {description}\n\n"
            f"Comments:\n{comments}"
        )
    }

    load_custom_nets()
    CUSTOM_NETS.insert(0, entry)
    save_custom_nets()

    messagebox.showinfo(
        "Scheduled Net",
        "Scheduled net saved successfully."
    )



def open_manage_scheduled_nets_window():
    """
    Manage saved operator scheduled nets.
    Allows edit/delete without manually editing JSON.
    """
    from tkinter import simpledialog, messagebox

    load_custom_nets()

    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Manage Scheduled Nets")
    win.geometry("760x420")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"], padx=10, pady=10)
    outer.pack(fill="both", expand=True)

    title = tk.Label(
        outer,
        text="Manage Scheduled Nets",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 12, "bold")
    )
    title.pack(anchor="w", pady=(0, 8))

    list_frame = tk.Frame(outer, bg=theme["bg"])
    list_frame.pack(fill="both", expand=True, pady=(0, 8))

    scrollbar = tk.Scrollbar(list_frame, orient="vertical")
    net_list = tk.Listbox(
        list_frame,
        height=10,
        bg=theme["list_bg"],
        fg=theme["list_fg"],
        selectbackground=theme["list_select_bg"],
        selectforeground=theme["list_select_fg"],
        yscrollcommand=scrollbar.set
    )
    scrollbar.config(command=net_list.yview)

    net_list.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    status_var = tk.StringVar(value="")

    def refresh_list():
        net_list.delete(0, "end")
        load_custom_nets()

        for idx, net in enumerate(CUSTOM_NETS):
            name = net.get("name", "Unnamed Net")
            freq = net.get("frequency", "")
            mode = net.get("mode", "")
            schedule = net.get("description", "")
            net_list.insert("end", f"{idx + 1}. {name} | {freq} | {mode} | {schedule}")

    def get_selected_index():
        selection = net_list.curselection()
        if not selection:
            messagebox.showwarning("Manage Scheduled Nets", "Select a scheduled net first.")
            return None
        return selection[0]

    def edit_selected():
        idx = get_selected_index()
        if idx is None:
            return

        load_custom_nets()

        if idx >= len(CUSTOM_NETS):
            refresh_list()
            return

        net = CUSTOM_NETS[idx]

        old_name = net.get("name", "")
        old_frequency = net.get("frequency", "")
        old_mode = net.get("mode", "---")
        old_description = net.get("description", "")
        old_details = net.get("details", "")

        name = simpledialog.askstring("Edit Scheduled Net", "Net Name:", initialvalue=old_name)
        if name is None:
            return

        frequency = simpledialog.askstring("Edit Scheduled Net", "Frequency:", initialvalue=old_frequency)
        if frequency is None:
            return

        mode = simpledialog.askstring("Edit Scheduled Net", "Mode:", initialvalue=old_mode)
        if mode is None:
            return

        schedule = simpledialog.askstring("Edit Scheduled Net", "Schedule:", initialvalue=old_description)
        if schedule is None:
            return

        comments = simpledialog.askstring("Edit Scheduled Net", "Comments / Details:", initialvalue=old_details)
        if comments is None:
            return

        name = name.strip()
        frequency = frequency.strip()

        if not name or not frequency:
            messagebox.showwarning("Edit Scheduled Net", "Name and frequency are required.")
            return

        mode = (mode or "---").strip() or "---"
        schedule = (schedule or "Operator scheduled net").strip() or "Operator scheduled net"
        comments = (comments or "No comments entered.").strip() or "No comments entered."

        CUSTOM_NETS[idx] = {
            "category": "Scheduled Net",
            "frequency": frequency,
            "mode": mode,
            "name": name,
            "description": schedule,
            "details": (
                f"{name}\n\n"
                f"Frequency: {frequency}\n"
                f"Mode: {mode}\n"
                f"Schedule: {schedule}\n\n"
                f"Comments:\n{comments}"
            )
        }

        save_custom_nets()
        refresh_list()
        status_var.set("Scheduled net updated.")

    def delete_selected():
        idx = get_selected_index()
        if idx is None:
            return

        load_custom_nets()

        if idx >= len(CUSTOM_NETS):
            refresh_list()
            return

        net = CUSTOM_NETS[idx]
        name = net.get("name", "selected net")

        if not messagebox.askyesno(
            "Delete Scheduled Net",
            f"Delete scheduled net:\n\n{name}?"
        ):
            return

        del CUSTOM_NETS[idx]
        save_custom_nets()
        refresh_list()
        status_var.set("Scheduled net deleted.")

    button_row = tk.Frame(outer, bg=theme["bg"])
    button_row.pack(fill="x", pady=(4, 0))

    tk.Button(
        button_row,
        text="Edit Selected",
        command=edit_selected,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=14
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        button_row,
        text="Delete Selected",
        command=delete_selected,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=14
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        button_row,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=12
    ).pack(side="right")

    status_label = tk.Label(
        outer,
        textvariable=status_var,
        bg=theme["bg"],
        fg=theme["fg"],
        anchor="w"
    )
    status_label.pack(fill="x", pady=(8, 0))

    refresh_list()
    apply_theme_to_toplevel(win)


def open_emergency_frequency_reference():
    """
    Net and frequency reference window.
    """
    load_custom_nets()

    win = tk.Toplevel(root)
    win.title("Net/Frequency Reference")

    configure_toplevel_window(win, 1040, 700, min_width=820, min_height=560)
    apply_theme_to_toplevel(win)

    theme = get_theme()

    main_frame = tk.Frame(win, bg=theme["bg"], padx=10, pady=10)
    main_frame.pack(fill="both", expand=True)

    header = ttk.Label(
        main_frame,
        text="Net/Frequency Reference",
        font=("TkDefaultFont", 12, "bold")
    )
    header.pack(anchor="w", pady=(0, 8))

    columns = ("Category", "Frequency", "Mode", "Name", "Description")

    tree_frame = tk.Frame(main_frame, bg=theme["bg"])
    tree_frame.pack(fill="both", expand=True)

    style_ttk_widgets()
    theme = get_theme()

    tree_style_name = "NetFrequencyReference.Treeview"
    heading_style_name = "NetFrequencyReference.Treeview.Heading"

    style = ttk.Style()
    style.configure(
        tree_style_name,
        background=theme["list_bg"],
        foreground=theme["list_fg"],
        fieldbackground=theme["list_bg"],
        rowheight=24
    )
    style.map(
        tree_style_name,
        background=[("selected", theme["list_select_bg"])],
        foreground=[("selected", theme["list_select_fg"])]
    )
    if theme["name"] == "light":
        heading_fg = "#ffffff"
    else:
        heading_fg = theme["fg"]

    style.configure(
        heading_style_name,
        background=theme["button_bg"],
        foreground=heading_fg
    )

    tree = ttk.Treeview(
        tree_frame,
        columns=columns,
        show="headings",
        height=14,
        style=tree_style_name
    )
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    for col in columns:
        tree.heading(col, text=col)

    tree.column("Category", width=170, anchor="w")
    tree.column("Frequency", width=140, anchor="center")
    tree.column("Mode", width=80, anchor="center")
    tree.column("Name", width=170, anchor="w")
    tree.column("Description", width=420, anchor="w")

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    all_frequency_items = CUSTOM_NETS + EMERGENCY_FREQUENCIES

    for item in all_frequency_items:
        tree.insert(
            "",
            "end",
            values=(
                item["category"],
                item["frequency"],
                item["mode"],
                item["name"],
                item["description"],
            )
        )

    details_label = ttk.Label(
        main_frame,
        text="Frequency Details / Propagation Guide",
        font=("TkDefaultFont", 10, "bold")
    )
    details_label.pack(anchor="w", pady=(10, 4))

    theme = get_theme()

    details_text = tk.Text(
        main_frame,
        wrap="word",
        height=16,
        relief="solid",
        borderwidth=1,
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"]
    )
    details_text.pack(fill="both", expand=False)
    details_text.insert("1.0", GEOMAGNETIC_REFERENCE_TEXT)

    selection_clear_after_id = None

    def clear_frequency_selection():
        tree.selection_remove(tree.selection())

    def on_select(event=None):
        nonlocal selection_clear_after_id

        selection = tree.selection()
        if not selection:
            return

        if selection_clear_after_id is not None:
            win.after_cancel(selection_clear_after_id)

        selection_clear_after_id = win.after(10000, clear_frequency_selection)

        values = tree.item(selection[0], "values")
        freq = values[1]
        name = values[3]

        for entry in all_frequency_items:
            if entry["frequency"] == freq and entry["name"] == name:
                details_text.delete("1.0", "end")
                if "WWV" in entry["name"]:
                    details = entry["details"] + "\n\n" + GEOMAGNETIC_REFERENCE_TEXT
                else:
                    details = entry["details"]

                details_text.insert("1.0", details)
                break

    tree.bind("<<TreeviewSelect>>", on_select)

    def _on_mousewheel(event):
        tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    tree.bind("<MouseWheel>", _on_mousewheel)
    tree.bind("<Button-4>", lambda e: tree.yview_scroll(-1, "units"))
    tree.bind("<Button-5>", lambda e: tree.yview_scroll(1, "units"))


def open_qcode_reference():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Q-Code Reference")
    configure_toplevel_window(win, 620, 500, min_width=500, min_height=350)
    win.configure(bg=theme["bg"])

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=8, pady=8)

    columns = ("code", "meaning")

    style_name = "QCode.Treeview"

    style = ttk.Style()
    style.configure(
        style_name,
        background=theme["entry_bg"],
        foreground=theme["entry_fg"],
        fieldbackground=theme["entry_bg"],
        rowheight=24
    )
    style.configure(
        f"{style_name}.Heading",
        background=theme["button_bg"],
        foreground=theme["button_fg"]
    )

    tree = ttk.Treeview(
        outer,
        columns=columns,
        show="headings",
        height=18,
        style=style_name
    )

    tree.heading("code", text="Q-Code")
    tree.heading("meaning", text="Meaning")

    tree.column("code", width=90, anchor="center", stretch=False)
    tree.column("meaning", width=480, anchor="w", stretch=True)

    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    qcodes = [
        ("QRA", "What is the name of your station?"),
        ("QRB", "How far approximately are you from my station?"),
        ("QRG", "What is my exact frequency?"),
        ("QRH", "Does my frequency vary?"),
        ("QRI", "How is the tone of my transmission?"),
        ("QRK", "What is the intelligibility of my signals?"),
        ("QRL", "Are you busy? / I am busy."),
        ("QRM", "Are you being interfered with? / I am being interfered with."),
        ("QRN", "Are you troubled by static? / I am troubled by static."),
        ("QRO", "Shall I increase power? / Increase power."),
        ("QRP", "Shall I decrease power? / Decrease power."),
        ("QRQ", "Shall I send faster? / Send faster."),
        ("QRR", "Are you ready for automatic operation?"),
        ("QRS", "Shall I send more slowly? / Send more slowly."),
        ("QRT", "Shall I stop sending? / Stop sending."),
        ("QRU", "Do you have anything for me? / I have nothing for you."),
        ("QRV", "Are you ready? / I am ready."),
        ("QRW", "Shall I inform that you are calling?"),
        ("QRX", "When will you call me again? / Stand by."),
        ("QRY", "What is my turn?"),
        ("QRZ", "Who is calling me? / You are being called by."),
        ("QSA", "What is the strength of my signals?"),
        ("QSB", "Are my signals fading?"),
        ("QSD", "Is my keying defective?"),
        ("QSG", "Shall I send messages at a fixed number?"),
        ("QSK", "Can you hear me between your signals?"),
        ("QSL", "Can you acknowledge receipt? / I acknowledge receipt."),
        ("QSM", "Shall I repeat the last message?"),
        ("QSN", "Did you hear me?"),
        ("QSO", "Can you communicate with my station directly? / I can communicate directly."),
        ("QSP", "Will you relay a message? / I will relay the message."),
        ("QSQ", "Have you a doctor onboard?"),
        ("QSR", "Shall I repeat the call on the calling frequency?"),
        ("QSS", "What working frequency will you use?"),
        ("QSU", "Shall I send on this frequency?"),
        ("QSV", "Shall I send a series of V's?"),
        ("QSW", "Will you send on this frequency?"),
        ("QSX", "Will you listen on another frequency?"),
        ("QSY", "Shall I change frequency? / Change frequency."),
        ("QSZ", "Shall I send each word/group more than once?"),
        ("QTA", "Shall I cancel message number?"),
        ("QTB", "Do you agree with my word count?"),
        ("QTC", "How many messages have you to send?"),
        ("QTH", "What is your location? / My location is."),
        ("QTI", "What is your true track?"),
        ("QTJ", "What is your speed?"),
        ("QTK", "What is your position?"),
        ("QTL", "What is your true heading?"),
        ("QTM", "What is your magnetic heading?"),
        ("QTN", "At what time did you depart?"),
        ("QTO", "Have you left dock/port?"),
        ("QTP", "Are you going to enter dock/port?"),
        ("QTQ", "Can you communicate with my station by signal lamp?"),
        ("QTR", "What is the correct time? / The correct time is."),
        ("QTS", "Will you send your call sign for tuning?"),
        ("QTU", "At what hours is your station open?"),
        ("QTV", "Shall I stand guard for you?"),
        ("QTW", "What is the condition of survivors?"),
        ("QTX", "Will you keep your station open?"),
        ("QTY", "Are you proceeding to the accident scene?"),
        ("QTZ", "Are you continuing the search?"),
        ("QUA", "Have you news of?"),
        ("QUB", "Can you give me information on visibility/weather?"),
        ("QUC", "What is the last message received?"),
        ("QUD", "Have you received urgency signal?"),
        ("QUE", "Can you use telephony in language?"),
        ("QUF", "Have you received distress signal?")
    ]

    for code, meaning in qcodes:
        tree.insert("", "end", values=(code, meaning))


def open_offline_callsign_lookup_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Offline Callsign Lookup")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    form_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=10,
        pady=10
    )
    form_frame.pack(fill="x", expand=False)

    tk.Label(
        form_frame,
        text="Callsign",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).grid(row=0, column=0, padx=6, pady=6, sticky="w")

    callsign_entry = tk.Entry(
        form_frame,
        width=20,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"],
        relief="solid"
    )
    callsign_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

    force_entry_uppercase(callsign_entry)

    output_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=8,
        pady=8
    )
    output_frame.pack(fill="both", expand=True, pady=(10, 0))

    output = tk.Text(
        output_frame,
        wrap="word",
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"],
        relief="solid",
        bd=1
    )
    output.pack(fill="both", expand=True)
    output.config(state="disabled")

    def generate_lookup(event=None):
        callsign = callsign_entry.get().strip().upper()

        output.config(state="normal")
        output.delete("1.0", tk.END)

        if not callsign:
            output.insert("1.0", "Please enter a callsign.\n")
            output.config(state="disabled")
            return

        if not CALLSIGN_DB_FILE.exists():
            output.insert(
                "1.0",
                f"Offline callsign database not found.\n\nExpected file:\n{CALLSIGN_DB_FILE}\n"
            )
            output.config(state="disabled")
            return

        record = lookup_callsign_in_db(callsign)

        if not record:
            output.insert(
                "1.0",
                f"No local record found for {callsign}.\n"
            )
            output.config(state="disabled")
            return

        station_grid = (record.get("grid") or "").strip().upper()
        grid_source = "Callsign database" if station_grid else ""

        lookup_callsign = (record.get("callsign") or "").strip().upper()
        my_callsign = (config.get("callsign") or "").strip().upper()
        my_grid = (config.get("grid") or "").strip().upper()

        # If this is the operator's own callsign, fall back to configured grid
        if not station_grid and lookup_callsign == my_callsign:
            station_grid = my_grid
            if station_grid:
                grid_source = "Station setup"

        # If still missing, try local activity enrichment
        if not station_grid:
            found_grid, found_source = find_grid_from_local_activity(lookup_callsign)
            if found_grid:
                station_grid = found_grid
                grid_source = found_source or "Local activity"
                save_grid_to_callsign_db(lookup_callsign, station_grid)

        # If still missing, try ZIP code estimate
        if not station_grid:
            zipcode = (record.get("zipcode") or "").strip()

            found_grid, found_source = find_grid_from_zipcode(zipcode)
            if found_grid:
                station_grid = found_grid
                grid_source = found_source or "ZIP code estimate"
                save_grid_to_callsign_db(lookup_callsign, station_grid)

        lines = [
            "Offline Callsign Lookup",
            "",
            f"Callsign:      {record.get('callsign', '')}",
            f"Name:          {record.get('name', '')}",
            f"Address:       {record.get('address', '')}",
            f"City:          {record.get('city', '')}",
            f"State:         {record.get('state', '')}",
            f"Zipcode:       {record.get('zipcode', '')}",
            f"Country:       {record.get('country', '')}",
            f"Grid:          {station_grid}",
            f"Grid Source:   {grid_source}",
            f"License Class: {record.get('license_class', '')}",
            f"Status:        {record.get('status', '')}",
        ]

        if my_grid and station_grid:
            calc = calculate_distance_and_bearing(my_grid, station_grid)

            if calc is not None:
                distance_km, distance_miles, bearing_deg, reciprocal_deg = calc
                lines.extend([
                    "",
                    f"Your Grid:     {my_grid}",
                    f"Distance:      {distance_miles} miles / {distance_km} km",
                    f"Azimuth:       {bearing_deg}°",
                    f"Reciprocal:    {reciprocal_deg}°",
                ])
            else:
                lines.extend([
                    "",
                    f"Your Grid:     {my_grid}",
                    "Distance:      Not available",
                    "Azimuth:       Not available",
                    "Reciprocal:    Not available",
                ])
        else:
            lines.extend([
                "",
                f"Your Grid:     {my_grid if my_grid else '(not set)'}",
                "Distance:      Not available",
                "Azimuth:       Not available",
                "Reciprocal:    Not available",
            ])

        output.insert("1.0", "\n".join(lines) + "\n")
        output.config(state="disabled")

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Lookup",
        command=generate_lookup,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Update Callsign Database",
        command=open_callsign_update_window,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"]
    ).pack(side="left", padx=(6, 0))

    tk.Button(
        button_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["list_select_bg"],
        activeforeground=theme["list_select_fg"]
    ).pack(side="right")

    callsign_entry.bind("<Return>", generate_lookup)

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 760, 520, min_width=620, min_height=420)
    callsign_entry.focus_set()


# -------------------------
# MAIN WINDOW
# -------------------------


def refresh_dashboard_layout():
    show_left = show_broadcast_feed_var.get()
    show_right = show_telegram_dashboard_var.get()

    # LEFT PANEL
    if show_left:
        left_dashboard_frame.grid()
        lower_frame.columnconfigure(0, weight=0, minsize=SIDE_PANEL_WIDTH)
    else:
        left_dashboard_frame.grid_remove()
        lower_frame.columnconfigure(0, weight=0, minsize=0)

    # RIGHT PANEL
    if show_right:
        right_dashboard_frame.grid()
        lower_frame.columnconfigure(2, weight=0, minsize=SIDE_PANEL_WIDTH)
    else:
        right_dashboard_frame.grid_remove()
        lower_frame.columnconfigure(2, weight=0, minsize=0)

    # CENTER MAP always expands
    lower_frame.columnconfigure(1, weight=1)


def update_dashboard_config():
    config["show_broadcast_feed"] = show_broadcast_feed_var.get()
    config["show_beacon_feed"] = show_telegram_dashboard_var.get()
    save_config()


def on_dashboard_toggle():
    update_dashboard_config()
    refresh_dashboard_layout()

def open_telegram_contacts_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Telegram Contacts")
    win.geometry("500x400")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(
        outer,
        text="Telegram Contacts",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 6))

    contact_list = tk.Listbox(
        outer,
        bg=theme["list_bg"],
        fg=theme["list_fg"],
        selectbackground=theme["list_select_bg"],
        selectforeground=theme["list_select_fg"]
    )
    contact_list.pack(fill="both", expand=True)

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    def normalize_alias(alias_text):
        return (alias_text or "").strip().upper()

    def refresh_contact_list():
        contact_list.delete(0, tk.END)

        contacts = config.get("telegram_contacts", [])
        for c in contacts:
            name = (c.get("name", "") or "").strip()
            alias = (c.get("alias", "") or "").strip()
            contact_list.insert(tk.END, f"{name} → {alias}")

    def alias_exists(alias_text, exclude_index=None):
        normalized = normalize_alias(alias_text)
        if not normalized:
            return False

        contacts = config.get("telegram_contacts", [])

        for idx, contact in enumerate(contacts):
            if exclude_index is not None and idx == exclude_index:
                continue

            existing_alias = normalize_alias(contact.get("alias", ""))
            if existing_alias == normalized:
                return True

        return False

    def add_contact():
        name = tk.simpledialog.askstring("Contact Name", "Enter contact name:")
        if not name:
            return

        alias = tk.simpledialog.askstring("Telegram Alias", "Enter Telegram alias:")
        if not alias:
            return

        name = name.strip()
        alias = alias.strip()

        if not name:
            messagebox.showwarning("Add Contact", "Contact name cannot be blank.")
            return

        if not alias:
            messagebox.showwarning("Add Contact", "Telegram alias cannot be blank.")
            return

        if alias_exists(alias):
            messagebox.showwarning(
                "Duplicate Alias",
                f"The alias '{alias}' is already in use.\n\n"
                "Aliases must be unique regardless of capitalization."
            )
            return

        contact = {
            "name": name,
            "alias": alias
        }

        config.setdefault("telegram_contacts", []).append(contact)
        save_config()
        refresh_contact_list()

    def delete_contact():
        selection = contact_list.curselection()
        if not selection:
            messagebox.showwarning("Delete Contact", "Select a contact first.")
            return

        index = selection[0]

        contacts = config.get("telegram_contacts", [])
        if index < len(contacts):
            contacts.pop(index)
            config["telegram_contacts"] = contacts
            save_config()

        refresh_contact_list()

        if contact_list.size() > 0:
            new_index = min(index, contact_list.size() - 1)
            contact_list.selection_set(new_index)
            contact_list.see(new_index)

    def edit_contact():
        selection = contact_list.curselection()
        if not selection:
            messagebox.showwarning("Edit Contact", "Select a contact first.")
            return

        index = selection[0]

        contacts = config.get("telegram_contacts", [])
        if index >= len(contacts):
            return

        contact = contacts[index]

        new_name = tk.simpledialog.askstring(
            "Edit Name",
            "Edit contact name:",
            initialvalue=contact.get("name", "")
        )
        if not new_name:
            return

        new_alias = tk.simpledialog.askstring(
            "Edit Alias",
            "Edit Telegram alias:",
            initialvalue=contact.get("alias", "")
        )
        if not new_alias:
            return

        new_name = new_name.strip()
        new_alias = new_alias.strip()

        if not new_name:
            messagebox.showwarning("Edit Contact", "Contact name cannot be blank.")
            return

        if not new_alias:
            messagebox.showwarning("Edit Contact", "Telegram alias cannot be blank.")
            return

        if alias_exists(new_alias, exclude_index=index):
            messagebox.showwarning(
                "Duplicate Alias",
                f"The alias '{new_alias}' is already in use.\n\n"
                "Aliases must be unique regardless of capitalization."
            )
            return

        contacts[index] = {
            "name": new_name,
            "alias": new_alias
        }

        config["telegram_contacts"] = contacts
        save_config()
        refresh_contact_list()

        if contact_list.size() > index:
            contact_list.selection_set(index)
            contact_list.see(index)

    tk.Button(
        button_frame,
        text="Add",
        command=add_contact,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Edit",
        command=edit_contact,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left", padx=(6, 0))

    tk.Button(
        button_frame,
        text="Delete",
        command=delete_contact,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left", padx=(6, 0))

    tk.Button(
        outer,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(pady=(10, 0))

    refresh_contact_list()
    apply_theme_to_toplevel(win)

def open_gateway_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Trusted Gateway Manager")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    list_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=8,
        pady=8
    )
    list_frame.pack(fill="both", expand=True)

    tk.Label(
        list_frame,
        text="Callsign     Bands",
        bg=theme["panel_bg"],
        fg=theme["fg"],
        font=("Courier", 12, "bold")
    ).pack(anchor="w", pady=(0, 2))

    tk.Label(
        list_frame,
        text="---------------------------",
        bg=theme["panel_bg"],
        fg=theme["muted_fg"],
        font=("Courier", 10)
    ).pack(anchor="w", pady=(0, 6))

    list_container = tk.Frame(list_frame, bg=theme["panel_bg"])
    list_container.pack(fill="both", expand=True)

    gateway_scroll = tk.Scrollbar(list_container, orient="vertical")

    gateway_list = tk.Listbox(
        list_container,
        bg=theme["list_bg"],
        fg=theme["list_fg"],
        selectbackground=theme["list_select_bg"],
        selectforeground=theme["list_select_fg"],
        yscrollcommand=gateway_scroll.set,
        font=("Courier", 14),
    )

    gateway_scroll.config(command=gateway_list.yview)

    gateway_list.pack(side="left", fill="both", expand=True)
    gateway_scroll.pack(side="right", fill="y")

    for gateway in trusted_gateways:
        bands = ",".join(gateway.get("bands", []))
        gateway_list.insert(tk.END, f"{gateway['callsign']}  ({bands})")

    def get_selected_gateway():
        selection = gateway_list.curselection()
        if not selection:
            return None

        index = selection[0]

        if index >= len(trusted_gateways):
            return None

        return trusted_gateways[index]

    def delete_gateway():
        selection = gateway_list.curselection()
        if not selection:
            messagebox.showwarning("Delete Gateway", "Please select a gateway first.")
            return

        index = selection[0]
        gateway_list.delete(index)

        if index < len(trusted_gateways):
            trusted_gateways.pop(index)

        config["trusted_gateways"] = trusted_gateways
        save_config()
        refresh_gateway_dashboard()

        size = gateway_list.size()
        if size > 0:
            new_index = min(index, size - 1)
            gateway_list.selection_set(new_index)
            gateway_list.see(new_index)

    def add_gateway():
        new_call = tk.simpledialog.askstring("Add Gateway", "Enter callsign:")
        if not new_call:
            return

        new_call = new_call.strip().upper()
        if not new_call:
            return

        band_input = tk.simpledialog.askstring(
            "Gateway Bands",
            "Enter bands (comma separated, e.g. 20m,40m):"
        )
        if not band_input:
            return

        bands = [b.strip().lower() for b in band_input.split(",") if b.strip()]

        trusted_gateways.append({"callsign": new_call, "bands": bands})

        band_str = ",".join(bands)
        gateway_list.insert(tk.END, f"{new_call}  ({band_str})")

        last_index = gateway_list.size() - 1
        gateway_list.selection_clear(0, tk.END)
        gateway_list.selection_set(last_index)
        gateway_list.see(last_index)

        config["trusted_gateways"] = trusted_gateways
        save_config()
        refresh_gateway_dashboard()

    def edit_gateway():
        gateway = get_selected_gateway()

        if gateway is None:
            messagebox.showwarning("Edit Gateway", "Please select a gateway first.")
            return

        callsign = gateway.get("callsign", "")

        new_call = tk.simpledialog.askstring(
            "Edit Gateway",
            "Edit callsign:",
            initialvalue=callsign
        )
        if not new_call:
            return

        new_call = new_call.strip().upper()

        current_bands = ",".join(gateway.get("bands", []))

        band_input = tk.simpledialog.askstring(
            "Edit Gateway Bands",
            "Edit bands (comma separated):",
            initialvalue=current_bands
        )
        if not band_input:
            return

        bands = [b.strip().lower() for b in band_input.split(",") if b.strip()]

        index = trusted_gateways.index(gateway)

        if index < len(trusted_gateways):
            trusted_gateways[index]["callsign"] = new_call
            trusted_gateways[index]["bands"] = bands

        config["trusted_gateways"] = trusted_gateways
        save_config()
        refresh_gateway_dashboard()

        gateway_list.delete(index)
        band_str = ",".join(bands)
        gateway_list.insert(index, f"{new_call}  ({band_str})")
        gateway_list.selection_set(index)
        gateway_list.see(index)

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Add",
        command=add_gateway,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left", padx=(0, 6))

    tk.Button(
        button_frame,
        text="Edit",
        command=edit_gateway,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left", padx=(0, 6))

    tk.Button(
        button_frame,
        text="Delete",
        command=delete_gateway,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=8
    ).pack(side="left", padx=(0, 6))

    tk.Button(
        button_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 600, 420, min_width=520, min_height=360)


def normalize_js8_alias(alias_text):
    """
    Normalize Telegram alias for JS8Call use.
    JS8 traffic is effectively uppercase, so aliases should be treated
    case-insensitively and transmitted in uppercase.
    """
    return (alias_text or "").strip().upper()


def normalize_js8_message_text(message_text):
    """
    Normalize free-text body for JS8Call output.
    - trims leading/trailing whitespace
    - collapses repeated internal whitespace
    - converts to uppercase
    """
    text = (message_text or "").strip()
    text = " ".join(text.split())
    return text.upper()


def build_js8_telegram_payload(target_call, alias_text, message_text):
    """
    Build Phase 1 JS8Call Telegram payload.

    Output format:
        <TARGET_CALL> TG:<ALIAS> <MESSAGE>

    Example:
        KW3KW TG:SCOTT RUNNING LATE
    """
    target_normalized = (target_call or "").strip().upper()
    alias_normalized = normalize_js8_alias(alias_text)
    message_normalized = normalize_js8_message_text(message_text)

    if not target_normalized or not alias_normalized:
        return ""

    if not message_normalized:
        return f"{target_normalized} TG:{alias_normalized}"

    return f"{target_normalized} TG:{alias_normalized} {message_normalized}"


def estimate_js8_frames(my_call, target_call, payload):
    """
    Estimate number of JS8Call transmit frames.

    This is an approximation based on:
    - sender callsign
    - target callsign
    - payload text
    - small overhead for separators and EOM

    JS8 uses variable encoding, so this is only an estimate.
    """

    my_call = (my_call or "").strip().upper()
    target_call = (target_call or "").strip().upper()
    payload = (payload or "").strip()

    # Build approximate transmitted string (what actually goes over the air)
    # Format resembles:
    # KG5VPF: W3BFO TG:SCOTT SEND FUEL TO SHELTER 2
    effective = f"{my_call}: {target_call} {payload}"

    # Add small fixed overhead for EOM + spacing
    effective_length = len(effective) + 2

    # Rough estimate: ~13–15 characters per JS8 frame
    # Using 14 as a middle-ground estimate
    CHARS_PER_FRAME = 14

    frames = (effective_length + CHARS_PER_FRAME - 1) // CHARS_PER_FRAME

    return max(frames, 1)


def open_send_telegram_transport_choice():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Send Telegram")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=14, pady=14)

    tk.Label(
        outer,
        text="Choose transport",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 11, "bold")
    ).pack(anchor="w", pady=(0, 10))

    tk.Label(
        outer,
        text="How would you like to send this Telegram message?",
        bg=theme["bg"],
        fg=theme["muted_fg"],
        justify="left"
    ).pack(anchor="w", pady=(0, 12))

    def choose_varac():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()
        open_send_telegram_dialog()

    def choose_js8call():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()
        open_js8_compose_window()

    def close_window():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(4, 0))

    tk.Button(
        button_frame,
        text="VarAC",
        command=choose_varac,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=12
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="JS8Call",
        command=choose_js8call,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=12
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        button_frame,
        text="Cancel",
        command=close_window,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=12
    ).pack(side="right")

    win.protocol("WM_DELETE_WINDOW", close_window)

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 420, 170, min_width=360, min_height=150)


def open_send_telegram_dialog():
    theme = get_theme()

    send_win = tk.Toplevel(root)
    send_win.title("Send Telegram via VarAC")
    send_win.geometry("820x560")
    send_win.transient(root)
    send_win.grab_set()

    send_outer = tk.Frame(send_win, bg=theme["bg"])
    send_outer.pack(fill="both", expand=True, padx=10, pady=10)

    contacts = config.get("telegram_contacts", [])
    contact_display_values = [
        f"{c.get('name', '').strip()} → {c.get('alias', '').strip()}"
        for c in contacts
        if c.get("name") or c.get("alias")
    ]

    address_var = tk.StringVar()
    contact_var = tk.StringVar()
    subject_var = tk.StringVar()
    char_count_var = tk.StringVar()

    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Custom.TCombobox",
        fieldbackground=theme["entry_bg"],
        background=theme["entry_bg"],
        foreground=theme["entry_fg"]
    )

    style.map(
        "Custom.TCombobox",
        fieldbackground=[("readonly", theme["entry_bg"])],
        foreground=[("readonly", theme["entry_fg"])]
    )

    tk.Label(
        send_outer,
        text="Address (Gateway Callsign)",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 4))

    address_entry = tk.Entry(
        send_outer,
        textvariable=address_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    address_entry.pack(fill="x", pady=(0, 10))
    
    tk.Label(
        send_outer,
        text="Telegram Contact",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 4))

    contact_combo = ttk.Combobox(
        send_outer,
        textvariable=contact_var,
        values=contact_display_values,
        state="readonly",
        style="Custom.TCombobox"
    )
    contact_combo.pack(fill="x", pady=(0, 10))

    tk.Label(
        send_outer,
        text="Subject",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 4))

    subject_entry = tk.Entry(
        send_outer,
        textvariable=subject_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    subject_entry.pack(fill="x", pady=(0, 10))

    tk.Label(
        send_outer,
        text="Message",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 4))

    message_text = tk.Text(
        send_outer,
        height=10,
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"],
        relief="solid",
        bd=1
    )
    message_text.pack(fill="both", expand=True, pady=(0, 4))

    char_count_label = tk.Label(
        send_outer,
        textvariable=char_count_var,
        bg=theme["bg"],
        fg=theme["fg"],
        font=("Courier", 10, "bold")
    )
    char_count_label.pack(anchor="e", pady=(0, 8))

    status_label = tk.Label(
        send_outer,
        text="Select a contact to build TG:alias in Subject.",
        bg=theme["bg"],
        fg=theme["muted_fg"]
    )
    status_label.pack(anchor="w", pady=(0, 8))

    def update_char_count(event=None):
        msg = message_text.get("1.0", "end-1c")
        count = len(msg)
        char_count_var.set(f"{count} / 500")

        if count > 500:
            char_count_label.config(fg="red")
        else:
            char_count_label.config(fg=theme["fg"])

    def on_contact_selected(event=None):
        selection = contact_var.get().strip()

        if "→" in selection:
            alias = selection.split("→", 1)[1].strip()
        else:
            alias = selection

        if alias:
            subject_var.set(f"TG:{alias}")
            status_label.config(
                text=f"Subject prepared for Telegram alias: {alias}",
                fg=theme["muted_fg"]
            )
            subject_entry.focus_set()
            subject_entry.icursor(tk.END)

    def copy_value(label, value):
        value = (value or "").strip()

        if not value:
            messagebox.showwarning("Copy", f"{label} is empty.")
            return

        try:
            copy_text_to_clipboard(value, widget=send_win)
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))
            return

        status_label.config(
            text=f"{label} copied to clipboard.",
            fg=theme["muted_fg"]
        )

    def copy_callsign():
        copy_value("Callsign", address_var.get().strip().upper())

    def copy_subject():
        copy_value("Subject", subject_var.get())

    def copy_message():
        copy_value("Message", message_text.get("1.0", "end-1c"))

    contact_combo.bind("<<ComboboxSelected>>", on_contact_selected)
    message_text.bind("<KeyRelease>", update_char_count)

    update_char_count()

    button_frame = tk.Frame(send_outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(4, 0))

    tk.Button(
        button_frame,
        text="Copy Callsign",
        command=copy_callsign,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Copy Subject",
        command=copy_subject,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=6)

    tk.Button(
        button_frame,
        text="Copy Message",
        command=copy_message,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=6)

    tk.Button(
        button_frame,
        text="Close",
        command=send_win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(send_win)
    address_entry.focus_set()


def open_js8_compose_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Send Telegram via JS8Call")
    win.geometry("700x520")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    contacts = config.get("telegram_contacts", [])
    contact_values = [
        f"{c.get('name','').strip()} → {c.get('alias','').strip()}"
        for c in contacts
    ]

    target_var = tk.StringVar()
    contact_var = tk.StringVar()
    payload_var = tk.StringVar()
    stats_var = tk.StringVar()

    # -------------------------
    # TARGET CALLSIGN
    # -------------------------
    tk.Label(outer, text="Gateway Callsign", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
    target_entry = tk.Entry(
        outer,
        textvariable=target_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    target_entry.pack(fill="x", pady=(0, 10))

    # -------------------------
    # CONTACT SELECT
    # -------------------------
    tk.Label(outer, text="Telegram Contact", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")

    contact_combo = ttk.Combobox(
        outer,
        textvariable=contact_var,
        values=contact_values,
        state="readonly"
    )
    contact_combo.pack(fill="x", pady=(0, 10))

    # -------------------------
    # MESSAGE TEXT
    # -------------------------
    tk.Label(outer, text="Message", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")

    message_text = tk.Text(
        outer,
        height=6,
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"]
    )
    message_text.pack(fill="both", expand=True, pady=(0, 10))

    # -------------------------
    # OUTPUT PAYLOAD
    # -------------------------
    tk.Label(outer, text="JS8 Payload (copy into JS8Call)", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")

    output = tk.Entry(
        outer,
        textvariable=payload_var,
        state="readonly",
        readonlybackground=theme["entry_bg"],
        fg=theme["entry_fg"]
    )
    output.pack(fill="x", pady=(0, 6))

    # -------------------------
    # STATS (chars + frames)
    # -------------------------
    stats_label = tk.Label(
        outer,
        textvariable=stats_var,
        bg=theme["bg"],
        fg=theme["fg"],
        font=("Courier", 10, "bold")
    )
    stats_label.pack(anchor="e", pady=(0, 10))

    # -------------------------
    # UPDATE LOGIC
    # -------------------------
    def update_payload(event=None):
        selection = contact_var.get().strip()

        if "→" in selection:
            alias = selection.split("→", 1)[1].strip()
        else:
            alias = selection

        msg = message_text.get("1.0", "end-1c")

        payload = build_js8_telegram_payload(target_var.get(), alias, msg)
        payload_var.set(payload)

        my_call = (config.get("callsign") or "").strip().upper()
        target_call = target_var.get().strip().upper()

        frames = estimate_js8_frames(my_call, target_call, payload)
        char_count = len(payload)

        stats_var.set(f"{char_count} chars | ~{frames} frames")

    contact_combo.bind("<<ComboboxSelected>>", update_payload)
    message_text.bind("<KeyRelease>", update_payload)
    target_entry.bind("<KeyRelease>", update_payload)

    # -------------------------
    # COPY BUTTON
    # -------------------------
    def copy_payload():
        text = payload_var.get().strip()
        if not text:
            return

        try:
            copy_text_to_clipboard(text, widget=win)
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))
            return

        messagebox.showinfo("Copied", "JS8 payload copied to clipboard.")

    # -------------------------
    # BUTTONS
    # -------------------------
    btn_frame = tk.Frame(outer, bg=theme["bg"])
    btn_frame.pack(fill="x")

    tk.Button(
        btn_frame,
        text="Copy Payload",
        command=copy_payload,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        btn_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(win)
    target_entry.focus_set()

def get_reply_transport(reply_record):
    """
    Classify a pending reply by transport.

    Priority:
    1. explicit reply_transport from relay
    2. fallback detection from original message content
    3. default to VarAC
    """
    transport = (reply_record.get("reply_transport", "") or "").strip().lower()

    if transport == "js8call":
        return "js8call"

    original_body = (reply_record.get("original_body", "") or "").strip()
    original_subject = (reply_record.get("original_subject", "") or "").strip()
    reply_subject = (reply_record.get("reply_subject", "") or "").strip()
    gateway_callsign = (reply_record.get("gateway_callsign", "") or "").strip().upper()

    message_blob = "\n".join([
        original_body,
        original_subject,
        reply_subject,
        gateway_callsign
    ]).upper()

    if "VARALERT JS8CALL TRIGGER" in message_blob:
        return "js8call"

    return "varac"


def split_pending_replies_by_transport():
    """
    Split pending replies into VarAC and JS8Call buckets.
    Returns:
        (varac_replies, js8call_replies)
    """
    varac_replies = []
    js8call_replies = []

    for reply in pending_replies:
        if get_reply_transport(reply) == "js8call":
            js8call_replies.append(reply)
        else:
            varac_replies.append(reply)

    return varac_replies, js8call_replies


def open_reply_transport_choice():
    theme = get_theme()

    varac_replies, js8_replies = split_pending_replies_by_transport()

    varac_count = len(varac_replies)
    js8_count = len(js8_replies)

    win = tk.Toplevel(root)
    win.title("Reply")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=14, pady=14)

    tk.Label(
        outer,
        text="Choose reply transport",
        bg=theme["bg"],
        fg=theme["fg"],
        font=("TkDefaultFont", 11, "bold")
    ).pack(anchor="w", pady=(0, 10))

    tk.Label(
        outer,
        text="Select how you want to send your reply:",
        bg=theme["bg"],
        fg=theme["muted_fg"]
    ).pack(anchor="w", pady=(0, 12))

    def choose_varac():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()
        open_reply_window()

    def choose_js8():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()
        open_js8_reply_window()

    def close_window():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x")

    tk.Button(
        button_frame,
        text=f"VarAC ({varac_count})",
        command=choose_varac,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=14
    ).pack(side="left")

    tk.Button(
        button_frame,
        text=f"JS8Call ({js8_count})",
        command=choose_js8,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=14
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        button_frame,
        text="Cancel",
        command=close_window,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        width=14
    ).pack(side="right")

    win.protocol("WM_DELETE_WINDOW", close_window)

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 420, 180, min_width=360, min_height=150)

def open_reply_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Telegram Reply Workflow")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    list_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=8,
        pady=8
    )
    list_frame.pack(fill="both", expand=True)

    tk.Label(
        list_frame,
        text="Pending VarAC Replies",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 6))

    reply_list = tk.Listbox(
        list_frame,
        bg=theme["list_bg"],
        fg=theme["list_fg"],
        selectbackground=theme["list_select_bg"],
        selectforeground=theme["list_select_fg"],
        font=("Courier", 12),
        height=4
    )
    reply_list.pack(fill="both", expand=True)

    details_frame = tk.Frame(
        outer,
        bg=theme["panel_bg"],
        bd=1,
        relief="solid",
        padx=8,
        pady=8
    )
    details_frame.pack(fill="both", expand=True, pady=(10, 0))

    tk.Label(
        details_frame,
        text="Callsign",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).pack(anchor="w")

    callsign_var = tk.StringVar()
    callsign_entry = tk.Entry(
        details_frame,
        textvariable=callsign_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    callsign_entry.pack(fill="x", pady=(0, 6))

    tk.Label(
        details_frame,
        text="Subject",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).pack(anchor="w")

    subject_var = tk.StringVar()
    subject_entry = tk.Entry(
        details_frame,
        textvariable=subject_var,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    subject_entry.pack(fill="x", pady=(0, 6))

    tk.Label(
        details_frame,
        text="Message",
        bg=theme["panel_bg"],
        fg=theme["fg"]
    ).pack(anchor="w")

    message_text = tk.Text(
        details_frame,
        height=10,
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"]
    )
    message_text.pack(fill="both", expand=True)

    status_label = tk.Label(
        details_frame,
        text="",
        bg=theme["panel_bg"],
        fg=theme["muted_fg"]
    )
    status_label.pack(anchor="w", pady=(6, 0))

    def get_varac_replies():
        varac_replies, _ = split_pending_replies_by_transport()
        return varac_replies

    def refresh_list():
        reply_list.delete(0, tk.END)

        varac_replies = get_varac_replies()

        for r in varac_replies:
            alias = r.get("telegram_alias", "Unknown")
            rf = r.get("original_rf_callsign", "Unknown")
            preview = (r.get("reply_text", "") or "")[:40]
            reply_list.insert(tk.END, f"{alias} → {rf} : {preview}")

    def load_selected():
        sel = reply_list.curselection()
        if not sel:
            return

        idx = sel[0]
        varac_replies = get_varac_replies()

        if idx >= len(varac_replies):
            return

        r = varac_replies[idx]

        callsign_var.set(r.get("original_rf_callsign", ""))
        subject_var.set(r.get("reply_subject", ""))

        message_text.delete("1.0", tk.END)
        message_text.insert(
            "1.0",
            f"TG Reply from {r.get('telegram_alias', '')}:\n{r.get('reply_text', '')}"
        )

        status_label.config(
            text=f"Reply ID: {r.get('reply_id')}  |  {r.get('created_at', '')}",
            fg=theme["muted_fg"]
        )

    reply_list.bind("<<ListboxSelect>>", lambda e: load_selected())

    def copy_value(label, value):
        value = (value or "").strip()

        if not value:
            messagebox.showwarning("Copy", f"{label} is empty.")
            return

        try:
            copy_text_to_clipboard(value, widget=win)
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))
            return

        status_label.config(
            text=f"{label} copied to clipboard.",
            fg=theme["muted_fg"]
        )

    def copy_callsign():
        copy_value("Callsign", callsign_var.get())

    def copy_subject():
        copy_value("Subject", subject_var.get())

    def copy_message():
        copy_value("Message", message_text.get("1.0", "end-1c"))

    def mark_handled():
        sel = reply_list.curselection()
        if not sel:
            messagebox.showwarning("Handled", "Select a reply first")
            return

        idx = sel[0]
        varac_replies = get_varac_replies()

        if idx >= len(varac_replies):
            return

        r = varac_replies[idx]
        reply_id = r.get("reply_id")

        ok, msg = mark_reply_handled_on_relay(reply_id)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        if r in pending_replies:
            pending_replies.remove(r)

        last_reply_ids.discard(reply_id)

        update_reply_button_state()
        refresh_list()

        message_text.delete("1.0", tk.END)
        callsign_var.set("")
        subject_var.set("")
        status_label.config(
            text="Reply marked handled.",
            fg=theme["muted_fg"]
        )

        if reply_list.size() > 0:
            new_index = min(idx, reply_list.size() - 1)
            reply_list.selection_set(new_index)
            reply_list.see(new_index)
            load_selected()

    btn_frame = tk.Frame(outer, bg=theme["bg"])
    btn_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        btn_frame,
        text="Copy Callsign",
        command=copy_callsign,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        btn_frame,
        text="Copy Subject",
        command=copy_subject,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=6)

    tk.Button(
        btn_frame,
        text="Copy Message",
        command=copy_message,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=6)

    tk.Button(
        btn_frame,
        text="Mark Handled",
        command=mark_handled,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=12)

    tk.Button(
        btn_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    refresh_list()
    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 820, 560, min_width=680, min_height=500)

def open_js8_reply_window():
    theme = get_theme()

    _, js8_replies = split_pending_replies_by_transport()

    win = tk.Toplevel(root)
    win.title("JS8 Reply Workflow")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(
        outer,
        text="JS8 Pending Replies",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 6))

    reply_list = tk.Listbox(
        outer,
        bg=theme["list_bg"],
        fg=theme["list_fg"],
        selectbackground=theme["list_select_bg"],
        selectforeground=theme["list_select_fg"],
        font=("Courier", 12)
    )
    reply_list.pack(fill="both", expand=True)

    for r in js8_replies:
        alias = r.get("telegram_alias", "Unknown")
        rf = r.get("original_rf_callsign", "Unknown")
        relay_call = (r.get("relay_call") or "").strip().upper()
        is_relayed = bool(r.get("is_relayed"))

        preview = (r.get("reply_text", "") or "")[:40]

        if is_relayed and relay_call:
            reply_list.insert(tk.END, f"{alias} → {rf} via {relay_call} : {preview}")
        else:
            reply_list.insert(tk.END, f"{alias} → {rf} : {preview}")

    tk.Label(
        outer,
        text="JS8 Payload (copy into JS8Call)",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(10, 4))

    payload_var = tk.StringVar()

    payload_entry = tk.Entry(
        outer,
        textvariable=payload_var,
        state="readonly",
        readonlybackground=theme["entry_bg"],
        fg=theme["entry_fg"]
    )
    payload_entry.pack(fill="x", pady=(0, 10))

    def update_payload(event=None):
        sel = reply_list.curselection()
        if not sel:
            payload_var.set("")
            return

        idx = sel[0]
        if idx >= len(js8_replies):
            payload_var.set("")
            return

        r = js8_replies[idx]

        target_call = (r.get("original_rf_callsign") or "").strip().upper()
        relay_call = (r.get("relay_call") or "").strip().upper()
        is_relayed = bool(r.get("is_relayed"))

        reply_text = (r.get("reply_text") or "").strip().upper()
        alias = (r.get("telegram_alias") or "").strip().upper()

        if not target_call:
            payload_var.set("")
            return

        if is_relayed and relay_call:
            js8_target = f"{relay_call}>{target_call}"
        else:
            js8_target = target_call

        if alias and reply_text:
            payload_var.set(f"{js8_target} [{alias}] {reply_text}")
        elif alias:
            payload_var.set(f"{js8_target} [{alias}]")
        elif reply_text:
            payload_var.set(f"{js8_target} {reply_text}")
        else:
            payload_var.set(js8_target)

    reply_list.bind("<<ListboxSelect>>", update_payload)

    def copy_payload():
        text = payload_var.get().strip()
        if not text:
            messagebox.showwarning("Copy Payload", "No JS8 payload to copy.")
            return

        try:
            copy_text_to_clipboard(text, widget=win)
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))
            return

        messagebox.showinfo("Copied", "JS8 reply copied to clipboard.")

    def mark_handled():
        sel = reply_list.curselection()
        if not sel:
            messagebox.showwarning("Handled", "Select a reply first.")
            return

        idx = sel[0]
        if idx >= len(js8_replies):
            return

        r = js8_replies[idx]
        reply_id = r.get("reply_id")

        ok, msg = mark_reply_handled_on_relay(reply_id)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        if r in pending_replies:
            pending_replies.remove(r)

        update_reply_button_state()

        try:
            last_reply_ids.discard(reply_id)
        except Exception:
            pass

        reply_list.delete(idx)
        payload_var.set("")

        if reply_list.size() > 0:
            new_index = min(idx, reply_list.size() - 1)
            reply_list.selection_set(new_index)
            reply_list.see(new_index)
            update_payload()
        else:
            payload_var.set("")

    btn_frame = tk.Frame(outer, bg=theme["bg"])
    btn_frame.pack(fill="x")

    tk.Button(
        btn_frame,
        text="Copy Payload",
        command=copy_payload,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        btn_frame,
        text="Mark Handled",
        command=mark_handled,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left", padx=(6, 0))

    tk.Button(
        btn_frame,
        text="Close",
        command=win.destroy,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(win)
    configure_toplevel_window(win, 600, 420, min_width=500, min_height=350)


def open_relay_settings_window():
    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Relay Settings")
    win.geometry("420x180")
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(
        outer,
        text="Relay URL",
        bg=theme["bg"],
        fg=theme["fg"]
    ).pack(anchor="w", pady=(0, 4))

    relay_entry = tk.Entry(
        outer,
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    relay_entry.pack(fill="x", pady=(0, 10))

    relay_entry.insert(0, config.get("relay_url", "https://relay.varalert.net"))

    status_label = tk.Label(
        outer,
        text="",
        bg=theme["bg"],
        fg=theme["muted_fg"]
    )
    status_label.pack(anchor="w", pady=(0, 10))

    def test_connection():
        ok, msg = test_relay_connection()

        if ok:
            status_label.config(text="✔ " + msg, fg="green")
        else:
            status_label.config(text="✖ " + msg, fg="red")

    def save_settings():
        url = relay_entry.get().strip()

        if not url:
            messagebox.showwarning("Relay Settings", "Relay URL cannot be empty.")
            return

        config["relay_url"] = url
        save_config()

        click_status_var.set("Relay settings saved")
        win.destroy()

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x")

    tk.Button(
        button_frame,
        text="Test",
        command=test_connection,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    tk.Button(
        button_frame,
        text="Save",
        command=save_settings,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    apply_theme_to_toplevel(win)

def open_relay_log_window():
    global relay_log_text

    try:
        if relay_log_text is not None and relay_log_text.winfo_exists():
            existing_win = relay_log_text.winfo_toplevel()
            existing_win.lift()
            existing_win.focus_force()
            return
    except Exception:
        relay_log_text = None

    theme = get_theme()

    win = tk.Toplevel(root)
    win.title("Relay Log")
    win.geometry("700x400")
    win.transient(root)
    win.grab_set()

    outer = tk.Frame(win, bg=theme["bg"])
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    relay_log_text = tk.Text(
        outer,
        wrap="word",
        bg=theme["text_bg"],
        fg=theme["text_fg"],
        insertbackground=theme["text_fg"],
        relief="solid",
        bd=1
    )
    relay_log_text.pack(fill="both", expand=True)

    relay_log_text.config(state="normal")
    relay_log_text.delete("1.0", "end")

    for line in relay_log_messages:
        relay_log_text.insert("end", line + "\n")

    relay_log_text.config(state="disabled")
    relay_log_text.see("end")

    button_frame = tk.Frame(outer, bg=theme["bg"])
    button_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        button_frame,
        text="Clear",
        command=clear_relay_log,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="left")

    def close_relay_log():
        global relay_log_text
        relay_log_text = None
        win.destroy()

    tk.Button(
        button_frame,
        text="Close",
        command=close_relay_log,
        bg=theme["button_bg"],
        fg=theme["button_fg"]
    ).pack(side="right")

    win.protocol("WM_DELETE_WINDOW", close_relay_log)

    apply_theme_to_toplevel(win)

def add_relay_log(message):
    global relay_log_messages, relay_log_text

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"

    relay_log_messages.append(line)

    if len(relay_log_messages) > RELAY_LOG_HISTORY_LIMIT:
        relay_log_messages = relay_log_messages[-RELAY_LOG_HISTORY_LIMIT:]

    if relay_log_text is not None:
        try:
            if relay_log_text.winfo_exists():
                at_bottom = relay_log_text.yview()[1] >= 0.999

                relay_log_text.config(state="normal")
                relay_log_text.insert("end", line + "\n")
                relay_log_text.config(state="disabled")

                if at_bottom:
                    relay_log_text.see("end")
        except Exception:
            relay_log_text = None

def clear_relay_log():
    global relay_log_messages, relay_log_text

    relay_log_messages.clear()

    if relay_log_text is not None:
        try:
            if relay_log_text.winfo_exists():
                relay_log_text.config(state="normal")
                relay_log_text.delete("1.0", "end")
                relay_log_text.config(state="disabled")
        except Exception:
            relay_log_text = None 

root = tk.Tk()
root.title(f"GridLink {APP_VERSION}")
root.geometry("1500x900")

try:
    if ICON_FILE.exists():
        icon = tk.PhotoImage(file=str(ICON_FILE))
        root.iconphoto(True, icon)
except Exception as e:
    print(f"Icon load error: {e}")

load_offline_map_image()

config = {"callsign": "", "grid": "", "group": "", "traffic_log_path": ""}
config = load_config()

# Restore operator's last selected activity/map filter window.
current_filter_days = config.get("js8_activity_filter_hours", current_filter_days)

js8_grid_cache = {}

if config.get("show_setup_on_start", False):
    config["theme"] = "light"
    config["show_broadcast_feed"] = False
    config["show_beacon_feed"] = False

trusted_gateways[:] = config.get("trusted_gateways", [])

show_broadcast_feed_var = tk.BooleanVar(value=config.get("show_broadcast_feed", False))
show_telegram_dashboard_var = tk.BooleanVar(value=config.get("show_beacon_feed", False))

test_sqlite_connection()
debug_recent_datastream_rows()
debug_datastream_schema()

menu = tk.Menu(root)
root.config(menu=menu)

setup_menu = tk.Menu(menu, tearoff=0)

setup_menu.add_command(label="Station Setup", command=setup_config)
setup_menu.add_command(label="Select VarAC Database", command=choose_varac_db_file)
setup_menu.add_command(label="Select JS8Call DIRECTED.TXT", command=choose_js8call_directed_file)

theme_menu = tk.Menu(setup_menu, tearoff=0)
theme_menu.add_command(label="Light", command=lambda: set_theme("light"))
theme_menu.add_command(label="Dark", command=lambda: set_theme("dark"))
theme_menu.add_command(label="High Flight", command=lambda: set_theme("high_flight"))
theme_menu.add_command(label="Woodlands", command=lambda: set_theme("woodlands"))
theme_menu.add_command(label="Leatherneck", command=lambda: set_theme("leatherneck"))
theme_menu.add_command(label="Midwatch", command=lambda: set_theme("midwatch"))

setup_menu.add_cascade(label="Theme", menu=theme_menu)

menu.add_cascade(label="Setup", menu=setup_menu)

filter_menu = tk.Menu(menu, tearoff=0)

filter_menu.add_command(label="Last 1 Hour", command=lambda: filter_messages_hours(1))
filter_menu.add_command(label="Last 3 Hours", command=lambda: filter_messages_hours(3))
filter_menu.add_command(label="Last 6 Hours", command=lambda: filter_messages_hours(6))
filter_menu.add_command(label="Last 12 Hours", command=lambda: filter_messages_hours(12))
filter_menu.add_command(label="Last 24 Hours", command=lambda: filter_messages_hours(24))
filter_menu.add_command(label="Last 48 Hours", command=lambda: filter_messages_hours(48))

menu.add_cascade(label="Filters", menu=filter_menu)

dashboard_menu = tk.Menu(menu, tearoff=0)
dashboard_menu.add_checkbutton(
    label="VarAC Activity Feed",
    variable=show_broadcast_feed_var,
    command=on_dashboard_toggle
)
dashboard_menu.add_checkbutton(
    label="Gateway Dashboard",
    variable=show_telegram_dashboard_var,
    command=on_dashboard_toggle
)
menu.add_cascade(label="Dashboard", menu=dashboard_menu)

map_menu = tk.Menu(menu, tearoff=0)
map_menu.add_command(label="Internet Map", command=lambda: set_map_mode("Internet"))
map_menu.add_command(label="Offline Map", command=lambda: set_map_mode("Offline"))

menu.add_cascade(label="Map", menu=map_menu)


# -------------------------
# TOOLS MENU
# -------------------------

propagation_menu = tk.Menu(menu, tearoff=0)

propagation_menu.add_command(
    label="Callsign Propagation Report",
    command=open_callsign_propagation_report
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Offline Callsign Lookup",
    command=open_offline_callsign_lookup_window
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Q-Code Reference",
    command=open_qcode_reference
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Zulu Time Reference",
    command=open_zulu_time_reference
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Grid Coordinate Converter",
    command=open_grid_coordinate_converter
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Net/Frequency Reference",
    command=open_emergency_frequency_reference
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Enter Scheduled Net",
    command=open_enter_scheduled_net_window
)

propagation_menu.add_separator()

propagation_menu.add_command(
    label="Manage Scheduled Nets",
    command=open_manage_scheduled_nets_window
)

menu.add_cascade(label="Tools", menu=propagation_menu)


# -------------------------
# CONTACTS MENU
# -------------------------

contacts_menu = tk.Menu(menu, tearoff=0)

contacts_menu.add_command(
    label="Telegram Aliases",
    command=open_telegram_contacts_window
)

menu.add_cascade(label="Contacts", menu=contacts_menu)

top_frame = tk.LabelFrame(
    root,
    text="JS8Call Activity Feed",
    bg=get_theme()["labelframe_bg"],
    fg=get_theme()["labelframe_fg"],
    bd=1,
    relief="groove"
)
top_frame.pack(fill="both", expand=False, padx=8, pady=(6, 4))

feed_inner_frame = tk.Frame(top_frame, bd=1, relief="solid")
feed_inner_frame.pack(fill="both", expand=True, padx=8, pady=8)

# Container for list + scrollbars
main_feed_container = tk.Frame(feed_inner_frame)
main_feed_container.pack(fill="both", expand=True, padx=6, pady=6)

# Scrollbars
main_feed_xscroll = tk.Scrollbar(main_feed_container, orient="horizontal")
main_feed_yscroll = tk.Scrollbar(main_feed_container, orient="vertical")

# Listbox
font_sizes = get_font_sizes()

main_feed_list = tk.Listbox(
    main_feed_container,
    height=6,
    font=("Courier", font_sizes["varalert"]),
    xscrollcommand=main_feed_xscroll.set,
    yscrollcommand=main_feed_yscroll.set
)

# Connect scrollbars
main_feed_xscroll.config(command=main_feed_list.xview)
main_feed_yscroll.config(command=main_feed_list.yview)

# Layout using grid
main_feed_list.grid(row=0, column=0, sticky="nsew")
main_feed_yscroll.grid(row=0, column=1, sticky="ns")
main_feed_xscroll.grid(row=1, column=0, sticky="ew")

# Hide scrollbars initially
main_feed_yscroll.grid_remove()
main_feed_xscroll.grid_remove()

# Make it expand properly
main_feed_container.rowconfigure(0, weight=1)
main_feed_container.columnconfigure(0, weight=1)

# Bind double-click
main_feed_list.bind("<<ListboxSelect>>", on_main_feed_select)
main_feed_list.bind("<Double-Button-1>", show_selected_message)

list_button_frame = tk.Frame(feed_inner_frame)
list_button_frame.pack(fill="x", padx=6, pady=(0, 6))

tk.Button(
    list_button_frame,
    text="Show\nDetails",
    command=open_selected_details,
    width=12,
    height=2
).pack(side="left", padx=(0, 6))

tk.Button(
    list_button_frame,
    text="Center\nMap",
    command=center_selected_on_map,
    width=12,
    height=2
).pack(side="left")

tk.Button(
    list_button_frame,
    text="Relay\nLog",
    command=open_relay_log_window,
    width=12,
    height=2
).pack(side="left", padx=(6, 0))

tk.Button(
    list_button_frame,
    text="Trusted\nGateway",
    command=open_gateway_window,
    width=12,
    height=2
).pack(side="right", padx=(6, 0))

reply_button = tk.Button(
    list_button_frame,
    text="Gateway\nRelay",
    command=open_reply_transport_choice,
    width=12,
    height=2
)
reply_button.pack(side="right", padx=(6, 0))

tk.Button(
    list_button_frame,
    text="Send\nTelegram",
    command=open_send_telegram_transport_choice,
    width=12,
    height=2
).pack(side="right")



lower_frame = tk.Frame(root)
lower_frame.pack(fill="both", expand=True, padx=8, pady=6)

lower_frame.columnconfigure(0, weight=0, minsize=SIDE_PANEL_WIDTH)
lower_frame.columnconfigure(1, weight=1)
lower_frame.columnconfigure(2, weight=0, minsize=SIDE_PANEL_WIDTH)
lower_frame.rowconfigure(0, weight=1)

left_dashboard_frame = tk.LabelFrame(lower_frame, text="VarAC Activity Feed", width=SIDE_PANEL_WIDTH)
left_dashboard_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
left_dashboard_frame.grid_propagate(False)

left_dashboard_inner = tk.Frame(left_dashboard_frame, bd=1, relief="solid")
left_dashboard_inner.pack(fill="both", expand=True, padx=4, pady=4)
left_dashboard_inner.pack_propagate(False)

font_sizes = get_font_sizes()

broadcast_feed_text = tk.Text(
    left_dashboard_inner,
    wrap="word",
    font=("Arial", font_sizes["broadcast"]),
    width=28,
    state="disabled"
)
broadcast_feed_text.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)

broadcast_feed_scrollbar = tk.Scrollbar(
    left_dashboard_inner,
    orient="vertical",
    command=broadcast_feed_text.yview
)
broadcast_feed_scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)

broadcast_feed_text.config(yscrollcommand=broadcast_feed_scrollbar.set)
broadcast_feed_text.tag_configure("selected_broadcast_line", background="#d9ecff")
broadcast_feed_text.bind("<ButtonRelease-1>", on_broadcast_feed_click)

map_frame = tk.LabelFrame(lower_frame, text="GridLink Map")
map_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

map_inner_frame = tk.Frame(map_frame, bd=1, relief="solid")
map_inner_frame.pack(fill="both", expand=True, padx=8, pady=8)

map_widget = tkintermapview.TkinterMapView(
    map_inner_frame,
    width=900,
    height=540
)
map_widget.pack(fill="both", expand=True, padx=6, pady=6)

offline_canvas = tk.Canvas(map_inner_frame, width=900, height=540, bg="#e8ecef")
offline_canvas.pack_forget()
offline_canvas.bind("<Configure>", on_offline_canvas_resize)
offline_canvas.bind("<Button-1>", on_offline_map_click)

right_dashboard_frame = tk.LabelFrame(lower_frame, text="Gateway Dashboard", width=SIDE_PANEL_WIDTH)
right_dashboard_frame.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=0)
right_dashboard_frame.grid_propagate(False)

right_dashboard_inner = tk.Frame(right_dashboard_frame, bd=1, relief="solid")
right_dashboard_inner.pack(fill="both", expand=True, padx=4, pady=4)
right_dashboard_inner.pack_propagate(False)

telegram_dashboard_container = tk.Frame(right_dashboard_inner)
telegram_dashboard_container.pack(fill="both", expand=True, padx=2, pady=2)

font_sizes = get_font_sizes()

gateway_text = tk.Text(
    telegram_dashboard_container,
    wrap="none",
    font=("Courier", font_sizes["telegram"]),
    state="disabled"
)
gateway_text.pack(fill="both", expand=True)

status_frame = tk.Frame(root)
status_frame.pack(fill="x", padx=5, pady=(0, 5))

click_status_var = tk.StringVar(value="GridLink starting...")
click_status_label = tk.Label(
    status_frame,
    textvariable=click_status_var,
    anchor="w",
    relief="sunken"
)
click_status_label.pack(fill="x")

def start_reply_polling():
    poll_relay_for_replies()
    root.after(30000, start_reply_polling)  # every 30 seconds

def process_js8call_activity_lines(lines):
    """
    Add new JS8Call DIRECTED.TXT lines to the JS8Call Activity Feed and map.

    Performance improvement:
    - Parse timestamp first
    - Skip old lines before doing message parsing, grid lookup, or map work
    """
    added_count = 0

    now = datetime.datetime.now()

    # Match the current feed/map filter window.
    # current_filter_days stores the selected filter value in HOURS.
    cutoff_time = None
    try:
        if current_filter_days:
            cutoff_time = now - datetime.timedelta(hours=current_filter_days)
    except Exception:
        cutoff_time = None

    for line in lines:
        try:
            parts = line.split("\t")
            if len(parts) < 5:
                continue

            timestamp_text = parts[0].strip()

            # Parse timestamp FIRST so old lines can be skipped early.
            try:
                timestamp = datetime.datetime.strptime(
                    timestamp_text,
                    "%Y-%m-%d %H:%M:%S"
                )
            except Exception:
                # If timestamp cannot be parsed, skip it rather than treating old
                # log lines as new/current activity.
                continue

            # Skip old JS8Call lines before expensive processing.
            if cutoff_time and timestamp < cutoff_time:
                continue

            frequency_text = parts[1].strip()
            snr_text = parts[3].strip()
            payload = parts[4].strip()

            if ":" not in payload:
                continue

            from_call, raw_message = payload.split(":", 1)
            from_call = from_call.strip().upper()
            raw_message = raw_message.strip()

            if raw_message.endswith("♢"):
                raw_message = raw_message[:-1].rstrip()

            try:
                snr_value = int(snr_text)
            except Exception:
                snr_value = snr_text

            try:
                frequency = float(frequency_text)
            except Exception:
                frequency = 0.0

            band = "?"
            if 14.0 <= frequency < 14.35:
                band = "20m"
            elif 7.0 <= frequency < 7.3:
                band = "40m"

            # Use cached grid if we already resolved this station before.
            if from_call in js8_grid_cache:
                grid, grid_source = js8_grid_cache[from_call]
            else:
                grid, grid_source = resolve_grid_for_js8_station(from_call, raw_message)

                if grid:
                    js8_grid_cache[from_call] = (grid, grid_source)

            lat, lon = None, None
            if grid:
                try:
                    lat, lon = maidenhead_to_latlon(grid)
                except Exception:
                    lat, lon = None, None

            item = {
                "source": "js8call",
                "timestamp": timestamp,
                "from_call": from_call,
                "to_call": "",
                "band": band,
                "snr": snr_value,
                "raw": raw_message,
                "raw_line": line,
                "grid": grid,
                "grid_source": grid_source,
                "lat": lat,
                "lon": lon,
            }

            if register_message_if_new(item):
                added_count += 1

        except Exception as e:
            print(f"JS8 live activity parse error: {e} | line={line}")

    if added_count:
        apply_filter(current_filter_days)
        click_status_var.set(f"JS8Call live update: added {added_count} new line(s)")

def process_js8call_trigger_lines(lines):
    """
    Process JS8Call DIRECTED.TXT lines and send TG: triggers to relay.

    Also records successfully processed JS8 trigger lines so startup
    recovery does not resend them later.
    """
    my_call = (config.get("callsign") or "").strip().upper()

    if not my_call:
        add_relay_log("JS8 trigger skipped: callsign not configured")
        return

    processed_hashes = load_processed_js8_hashes()

    for line in lines:
        line = (line or "").strip()
        if not line:
            continue

        trigger_hash = make_js8_trigger_hash(line)

        if trigger_hash in processed_hashes:
            continue

        parsed = parse_js8call_trigger_line(line)
        if not parsed:
            continue

        # Only process messages directed TO this station
        if parsed["to_call"] != my_call:
            continue

        alias = parsed["telegram_alias"]

        add_relay_log(
            f"JS8 trigger detected: from={parsed['from_call']} "
            f"alias={alias} snr={parsed['snr']}"
        )

        payload = build_js8_trigger_payload(parsed)

        add_relay_log(
            f"Sending JS8 trigger to relay for alias '{alias}'..."
        )

        success, result = send_trigger_to_relay(payload)

        if success:
            save_processed_js8_hash(trigger_hash)
            processed_hashes.add(trigger_hash)

            add_relay_log(f"JS8 SUCCESS: {result}")
            try:
                click_status_var.set(
                    f"JS8 trigger sent for alias {alias}"
                )
            except Exception:
                pass
        else:
            add_relay_log(f"JS8 FAILED: {result}")
            try:
                click_status_var.set(
                    f"JS8 trigger failed for alias {alias}"
                )
            except Exception:
                pass


def process_new_trigger_messages():
    global highest_processed_vmail_id

    if not trigger_polling_enabled:
        return

    try:
        gateway_callsign = (config.get("callsign", "") or "").strip().upper()

        if not gateway_callsign:
            add_relay_log("Trigger polling paused: callsign not configured")
            return

        rows = fetch_new_trigger_messages(highest_processed_vmail_id)

        if rows:
            add_relay_log(f"Found {len(rows)} new TG: trigger message(s)")

        for row in rows:
            parsed = parse_trigger_message(row)

            add_relay_log(
                f"Trigger match: id={parsed['id']} "
                f"from={parsed['from_call']} "
                f"alias={parsed['alias']} "
                f"snr={parsed['snr']}"
            )

            if not parsed["alias"]:
                add_relay_log(
                    f"Skipping id={parsed['id']}: subject missing alias after TG:"
                )
                highest_processed_vmail_id = max(highest_processed_vmail_id, parsed["id"])
                save_last_processed_vmail_id(highest_processed_vmail_id)
                continue

            payload = build_relay_trigger_payload(parsed)

            add_relay_log(
                f"Sending trigger message id={parsed['id']} to relay for alias '{parsed['alias']}'..."
            )
            success, result = send_trigger_to_relay(payload)

            if success:
                add_relay_log(f"SUCCESS id={parsed['id']}: {result}")
                try:
                    click_status_var.set(
                        f"Telegram trigger sent for alias {parsed['alias']} (vMail {parsed['id']})"
                    )
                except Exception:
                    pass
            else:
                add_relay_log(f"FAILED id={parsed['id']}: {result}")
                try:
                    click_status_var.set(
                        f"Telegram trigger failed for alias {parsed['alias']} (vMail {parsed['id']})"
                    )
                except Exception:
                    pass

            highest_processed_vmail_id = max(highest_processed_vmail_id, parsed["id"])
            save_last_processed_vmail_id(highest_processed_vmail_id)

    except Exception as e:
        add_relay_log(f"Trigger polling error: {e}")
        try:
            click_status_var.set(f"Trigger polling error: {e}")
        except Exception:
            pass


def poll_trigger_messages_once():
    if trigger_polling_enabled:
        process_new_trigger_messages()

    root.after(VMAIL_TRIGGER_POLL_INTERVAL_MS, poll_trigger_messages_once)

JS8CALL_TRIGGER_POLL_INTERVAL_MS = 5000  # 5 seconds

js8call_last_position = 0
js8call_polling_enabled = False


def start_trigger_polling():
    global highest_processed_vmail_id, trigger_polling_enabled

    if trigger_polling_enabled:
        return

    try:
        current_db_max_id = get_starting_highest_vmail_id()
        saved_last_id = load_last_processed_vmail_id()

        if saved_last_id > 0:
            highest_processed_vmail_id = saved_last_id
        else:
            highest_processed_vmail_id = current_db_max_id

        save_last_processed_vmail_id(highest_processed_vmail_id)

        trigger_polling_enabled = True

        add_relay_log(
            f"Trigger polling started. DB max id = {current_db_max_id}, "
            f"saved last id = {saved_last_id}"
        )
        add_relay_log(
            f"Initial highest processed vmail id = {highest_processed_vmail_id}"
        )
        add_relay_log(
            f"Watching for Inbox TG: messages to "
            f"{(config.get('callsign', '') or '').strip().upper()}"
        )

    except Exception as e:
        trigger_polling_enabled = False
        add_relay_log(f"Start trigger polling failed: {e}")
        try:
            click_status_var.set(f"Start trigger polling failed: {e}")
        except Exception:
            pass


def start_trigger_polling_loop():
    start_trigger_polling()
    poll_trigger_messages_once()

def start_js8call_trigger_monitor():
    global js8call_last_position, js8call_polling_enabled

    path = config.get("js8call_directed_path", "").strip()

    if not path:
        js8call_polling_enabled = False
        add_relay_log("JS8 trigger monitor not started: JS8Call DIRECTED.TXT path not configured")
        return

    file_path = Path(path)

    if not file_path.exists():
        js8call_polling_enabled = False
        add_relay_log(f"JS8 trigger monitor not started: file not found: {file_path}")
        return

    try:
        js8call_last_position = file_path.stat().st_size
        js8call_polling_enabled = True
        add_relay_log(f"JS8 trigger monitor started: {file_path}")
    except Exception as e:
        js8call_polling_enabled = False
        add_relay_log(f"JS8 trigger monitor start failed: {e}")

def initialize_js8call_last_position():
    """
    Set JS8Call trigger reader to the end of DIRECTED.TXT.

    This prevents the live JS8 polling loop from re-reading old lines
    after startup recovery has already scanned recent messages.
    """
    global js8call_last_position

    path = config.get("js8call_directed_path", "").strip()
    if not path:
        return

    file_path = Path(path)
    if not file_path.exists():
        return

    try:
        js8call_last_position = file_path.stat().st_size
        add_relay_log("JS8 trigger reader initialized at end of DIRECTED.TXT")
    except Exception as e:
        add_relay_log(f"JS8 trigger reader init error: {e}")

def read_new_js8call_trigger_lines():
    global js8call_last_position

    path = config.get("js8call_directed_path", "").strip()
    if not path:
        return []

    file_path = Path(path)
    if not file_path.exists():
        return []

    try:
        current_size = file_path.stat().st_size

        # File truncated or replaced
        if current_size < js8call_last_position:
            js8call_last_position = 0

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(js8call_last_position)
            new_text = f.read()
            js8call_last_position = f.tell()

        if not new_text.strip():
            return []

        return [line.strip() for line in new_text.splitlines() if line.strip()]

    except Exception as e:
        add_relay_log(f"JS8 trigger read error: {e}")
        return []


def poll_js8call_triggers_once():
    if js8call_polling_enabled:
        lines = read_new_js8call_trigger_lines()
        if lines:
            process_js8call_activity_lines(lines)
            process_js8call_trigger_lines(lines)

    root.after(JS8CALL_TRIGGER_POLL_INTERVAL_MS, poll_js8call_triggers_once)


apply_theme()
refresh_dashboard_layout()
refresh_gateway_dashboard()

if config.get("show_setup_on_start", False):
    root.after(100, setup_config)

recover_recent_js8_telegram_triggers()
recover_recent_varac_telegram_triggers()
initialize_js8call_last_position()
poll_relay_for_replies()

def initialize_map_view():
    try:
        map_widget.set_position(39.5, -98.35)
        map_widget.set_zoom(4)

        # Force tile redraw after the map widget is fully visible
        root.after(500, lambda: map_widget.set_zoom(3))
        root.after(900, lambda: map_widget.set_zoom(4))

    except Exception as e:
        print(f"Initial map view error: {e}")

root.after(500, initialize_map_view)

# print_mbtiles_status()

# Load existing data
js8_loaded_count = load_messages_from_js8call()
load_broadcast_feed_from_db()
initialize_cqframe_last_id()

if js8_loaded_count == 0:
    load_sample_messages()
    apply_filter(current_filter_days)
else:
    apply_filter(current_filter_days)
    start_sqlite_monitor()

# Start SQLite polling loop
root.after(sqlite_poll_interval_ms, poll_sqlite_database)

start_reply_polling()
start_trigger_polling_loop()

start_js8call_trigger_monitor()
poll_js8call_triggers_once()

root.mainloop()
