"""
Configuration for soobway.
Values are read from environment variables (see .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MTA BusTime API key — get one at https://bt.mta.info/wiki/Developers/Index
# Subway GTFS-RT feeds require no API key.
BUSTIME_API_KEY = os.environ["BUSTIME_API_KEY"]

# Display mode: 'terminal' (dev) or 'matrix' (Raspberry Pi + LED panel)
DISPLAY_MODE = os.getenv("DISPLAY_MODE", "terminal")

# Matrix hardware settings (only used when DISPLAY_MODE=matrix)
MATRIX_ROWS = int(os.getenv("MATRIX_ROWS", "32"))
MATRIX_COLS = int(os.getenv("MATRIX_COLS", "64"))
MATRIX_CHAIN = int(os.getenv("MATRIX_CHAIN", "1"))
MATRIX_BRIGHTNESS = int(os.getenv("MATRIX_BRIGHTNESS", "50"))

# Refresh interval in seconds
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))

# ---------------------------------------------------------------------------
# Subway feeds
# Each entry is a GTFS-RT feed that may contain trains stopping at our station.
# url: MTA GTFS-RT feed endpoint (no API key needed)
# stop_id: GTFS stop ID + direction suffix — 'S' = southbound = towards Manhattan
#   To find your stop ID: download stops.txt from https://api.mta.info/#/subwayRealTimeFeeds
#   and search for your station name. Append 'S' for Manhattan-bound.
# All trains stopping at the given stop_id are returned (no route filter).
# ---------------------------------------------------------------------------
SUBWAY_FEEDS = [
    {
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "stop_id": "G10S",  # 63 Dr-Rego Park — covers B, D, F, M
    },
    {
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "stop_id": "G10S",  # 63 Dr-Rego Park — covers N, Q, R, W
    },
    {
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "stop_id": "G10S",  # 63 Dr-Rego Park — covers A, C, E
    },
]

# ---------------------------------------------------------------------------
# Bus stops (MTA BusTime SIRI API)
# stop_ref: numeric stop ID — find at https://bustime.mta.info (search your stop, copy ID from URL)
# line: route number without prefix, e.g. 'Q98'
# direction_ref: '0' or '1' — visit bustime.mta.info and check which direction goes towards Flushing
# ---------------------------------------------------------------------------
BUS_STOPS = [
    {
        "stop_ref": "502872",  # Horace Harding Expy/99 St
        "line": "Q98",
        "direction_ref": "0",  # towards Flushing
        "name": "Q98 to Flushing",
    },
]
