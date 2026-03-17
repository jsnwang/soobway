 # CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**soobway** — a Python application that fetches real-time NYC subway arrivals from the MTA GTFS-RT API and renders them on an RGB LED matrix board (or terminal for development).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run in terminal/simulation mode (no hardware needed)
python main.py

# Run on Raspberry Pi with LED matrix
DISPLAY_MODE=matrix python main.py

# Lint
flake8 .

# Type check
mypy .

# Tests
pytest
pytest tests/test_feed.py   # single test file
```

## Architecture

The app has two main layers:

**Data layer** (`mta/`)
- `feed.py` — fetches subway GTFS-RT protobuf directly via `requests` + `gtfs-realtime-bindings`. No API key needed. `get_arrivals(url, stop_id, route_id)` filters by route and stop, returns arrival dicts.
- `bus.py` — fetches bus arrivals from the MTA BusTime SIRI API (JSON). Requires `BUSTIME_API_KEY`. `get_arrivals(api_key, stop_ref, line, direction_ref)`.

**Display layer** (`display/`)
- `renderer.py` — `TerminalRenderer` for development; `get_renderer(mode)` factory.
- `matrix.py` — `MatrixRenderer` wraps `rpi-rgb-led-matrix` for physical LED panels. Only works on Raspberry Pi; raises `RuntimeError` otherwise.

**Configuration** (`config.py`)
- `SUBWAY_STOPS` — list of dicts with `url`, `stop_id`, `route_id`, `name`. Stop IDs use GTFS format with direction suffix (`S` = southbound = towards Manhattan).
- `BUS_STOPS` — list of dicts with `stop_ref`, `line`, `direction_ref`, `name`. Uses BusTime stop IDs.
- Only `BUSTIME_API_KEY` is required in `.env`; subway feeds are keyless.

**Entry point** (`main.py`)
- Loops every `REFRESH_INTERVAL` seconds: fetches from all subway and bus stops, merges and sorts by `minutes_away`, renders.

## MTA API Notes

- Subway GTFS-RT feeds require no API key — endpoints are public.
- Bus uses MTA BusTime SIRI API (`mta/bus.py`) with `BUSTIME_API_KEY`.
- Subway stop IDs: GTFS format, numeric ID + `N`/`S` suffix. Download `stops.txt` from https://api.mta.info to look up by station name.
- BusTime stop refs: numeric only. Find at https://bustime.mta.info — search your stop, ID is in the URL.

## Hardware (actual build)

- **Pi:** Raspberry Pi 4 Model B 2GB
- **Bonnet:** Adafruit Triple LED Matrix Bonnet (#6358) — uses `hardware_mapping = "adafruit-hat"`, requires `gpio_slowdown = 4` on RPi 4
- **Panel:** P4 64×32 pixel HUB75E, 1/16 scan — 64 cols, 32 rows
- **Panel power:** 5V 4A supply via DC barrel jack → Bonnet `5V PWR IN` screw terminal
- The Pi and panel are powered separately; never draw panel power from GPIO 5V

## Display Modes

- `DISPLAY_MODE=terminal` — renders to stdout, works on any OS including Windows for development.
- `DISPLAY_MODE=matrix` — requires `rpi-rgb-led-matrix` Python bindings and the Raspberry Pi hardware above. Must be run as root (`sudo`) for GPIO access.

## Line Colors

`display/renderer.py` contains `LINE_COLORS` — a dict mapping line letters/numbers to official MTA RGB colors. Keep this dict as the single source of truth for colors.
