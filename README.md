# soobway

NYC subway arrival time display for RGB LED matrix boards.

Fetches real-time train arrivals from the MTA GTFS-RT API and renders them on an RGB LED matrix panel. Supports physical RGB LED panels (Raspberry Pi + Adafruit Triple Matrix Bonnet) and a terminal renderer for development on any machine.

## Hardware

### Parts List

| Qty | Part |
|-----|------|
| 1 | Raspberry Pi 4 Model B (2 GB RAM) |
| 1 | Adafruit Triple LED Matrix Bonnet for Raspberry Pi – HUB75 ([#6358](https://www.adafruit.com/product/6358)) |
| 1 | P4 Indoor RGB LED Panel, 64×32 pixels, 256×128 mm, 1/16 scan, HUB75E |
| 1 | 5V 4A DC power supply with 2.1mm barrel jack (powers the LED panel) |
| 1 | Female DC Power Adapter – 2.1mm jack to screw terminal ([#368](https://www.adafruit.com/product/368)) |
| 1 | Official Raspberry Pi USB-C Power Supply 5.1V 3A (powers the Pi) |

### Wiring

1. **Stack the Bonnet** onto the Pi's 40-pin GPIO header.
2. **LED panel data cable** — connect the HUB75 ribbon cable from the panel's input port to the Bonnet's HUB75 connector (labeled on the board). Ensure pin 1 aligns (usually indicated by a notch or arrow on the connector).
3. **Panel power** — connect the 5V 4A power supply to the screw terminals on the DC power adapter, then plug the 2.1mm barrel into the Bonnet's power jack (labeled `5V PWR IN`). The panel draws power through the Bonnet.
4. **Pi power** — plug the USB-C supply into the Pi separately.

> **Important:** Never power the LED panel from the Pi's GPIO 5V pins. Always use the dedicated 5V 4A supply via the Bonnet's power jack.

### Raspberry Pi OS Setup

```bash
# On the Pi, enable SPI and disable audio (conflicts with PWM on the Bonnet)
sudo raspi-config
# → Interface Options → SPI → Enable
# → Advanced Options → GL Driver → Legacy (required for rpi-rgb-led-matrix)

# Disable onboard audio in /boot/firmware/config.txt (add this line):
# dtparam=audio=off
```

### Install rpi-rgb-led-matrix

The `pip install rpi-rgb-led-matrix` package is a pre-built wheel. If it fails on your Pi OS version, build from source:

```bash
git clone https://github.com/hzeller/rpi-rgb-led-matrix
cd rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

## Software Requirements

- Python 3.11+
- MTA API key — register at https://api.mta.info/

## Setup

### Development (any machine, terminal output)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set MTA_API_KEY at minimum
python main.py
```

### Raspberry Pi (LED matrix)

```bash
# Clone the repo on your Pi
git clone https://github.com/jsnwang/soobway.git
cd soobway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Install rpi-rgb-led-matrix (see Hardware section above if pip wheel fails)
pip install rpi-rgb-led-matrix

cp .env.example .env
# Edit .env: set MTA_API_KEY and DISPLAY_MODE=matrix

# Must run as root for GPIO access
sudo .venv/bin/python main.py
```

## Configuration

Edit `config.py` to set which stops/lines to display. The `STOPS` list controls what is shown.

### MTA Feed IDs

| Feed ID | Lines |
|---------|-------|
| 1 | 1, 2, 3, 4, 5, 6, S |
| 2 | A, C, E |
| 11 | B, D, F, M |
| 16 | N, Q, R, W |
| 21 | G |
| 26 | J, Z |
| 31 | 7 |
| 36 | L |
| 51 | SIR |

### Stop IDs

Stop IDs use the GTFS format: numeric stop ID + direction suffix `N` or `S`.
Example: `127N` = Times Square (42 St) northbound on the 1/2/3.

MTA stop IDs can be looked up in the [MTA GTFS static data](https://api.mta.info/#/subwayRealTimeFeeds).

