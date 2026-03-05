"""
Configuration for soobway.
Values are read from environment variables (see .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MTA API key — get one at https://api.mta.info/
MTA_API_KEY = os.environ["MTA_API_KEY"]

# Display mode: 'terminal' (dev) or 'matrix' (Raspberry Pi + LED panel)
DISPLAY_MODE = os.getenv("DISPLAY_MODE", "terminal")

# Matrix hardware settings (only used when DISPLAY_MODE=matrix)
MATRIX_ROWS = int(os.getenv("MATRIX_ROWS", "32"))
MATRIX_COLS = int(os.getenv("MATRIX_COLS", "64"))
MATRIX_CHAIN = int(os.getenv("MATRIX_CHAIN", "1"))
MATRIX_BRIGHTNESS = int(os.getenv("MATRIX_BRIGHTNESS", "50"))

# Refresh interval in seconds
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))

# Stops to display: list of dicts with keys: feed_id, stop_id, line, direction, name
# feed_id maps to MTA GTFS-RT feed numbers (see README for full list)
STOPS = [
    {
        "feed_id": "1",
        "stop_id": "127N",
        "line": "1",
        "direction": "N",
        "name": "Times Sq Uptown",
    },
]
