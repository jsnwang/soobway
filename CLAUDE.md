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
- `feed.py` — wraps the `nyct-gtfs` library to fetch and parse GTFS-RT protobuf feeds from the MTA API. `get_arrivals()` is the main entry point; it filters trips by stop ID and returns sorted arrival dicts.

**Display layer** (`display/`)
- `renderer.py` — `TerminalRenderer` for development; `get_renderer(mode)` factory.
- `matrix.py` — `MatrixRenderer` wraps `rpi-rgb-led-matrix` for physical LED panels. Only works on Raspberry Pi; raises `RuntimeError` otherwise.

**Configuration** (`config.py`)
- All runtime settings come from environment variables loaded via `python-dotenv`. `STOPS` is a list of dicts that defines which stop/line/direction combos to display. Copy `.env.example` to `.env` and set `MTA_API_KEY`.

**Entry point** (`main.py`)
- Loops every `REFRESH_INTERVAL` seconds: fetches arrivals for each stop in `config.STOPS`, merges results, renders.

## MTA API Notes

- Feeds are protobuf GTFS-RT; `nyct-gtfs` handles decoding.
- Feed IDs: `1`=1/2/3/4/5/6, `2`=A/C/E, `11`=B/D/F/M, `16`=N/Q/R/W, `21`=G, `26`=J/Z, `31`=7, `36`=L.
- Stop IDs follow GTFS format: numeric ID + `N`/`S` direction suffix (e.g. `127N`).
- API key registration: https://api.mta.info/

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
