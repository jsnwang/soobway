"""
RGB LED matrix renderer using rpi-rgb-led-matrix.
Only functional on Raspberry Pi with the matrix hardware connected.
"""
import os
import time as _time
from display.renderer import LINE_COLORS

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False

# Default font directory — bundled in fonts/ or override with FONT_DIR env var
FONT_DIR = os.getenv("FONT_DIR", os.path.join(os.path.dirname(__file__), "..", "fonts"))

# Column where times start (both rows aligned)
TIME_X = 17

# Delay color
RED = (255, 40, 40)
YELLOW = (252, 204, 10)

# Right padding for next-time text
RIGHT_PAD = 1


def _make_options(rows: int = 32, cols: int = 64, chain: int = 1, brightness: int = 50) -> "RGBMatrixOptions":
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain
    options.brightness = brightness
    options.hardware_mapping = "regular"
    options.gpio_slowdown = 4  # RPi 4 requires slowdown of 4
    options.drop_privileges = False
    return options


def _draw_subway_icon(canvas, x, y, r, g, b):
    """Draw a 12×12 filled circle at top-left corner (x, y)."""
    # Hand-tuned 12×12 circle bitmap for clean pixel edges
    rows = [
        (3, 9),   # row 0:    ··xxx xxx··
        (2, 10),  # row 1:   ·xxxxxxxx·
        (1, 11),  # row 2:  ·xxxxxxxxxx·
        (1, 11),  # row 3:  ·xxxxxxxxxx·
        (0, 12),  # row 4: xxxxxxxxxxxx
        (0, 12),  # row 5: xxxxxxxxxxxx
        (0, 12),  # row 6: xxxxxxxxxxxx
        (0, 12),  # row 7: xxxxxxxxxxxx
        (1, 11),  # row 8:  ·xxxxxxxxxx·
        (1, 11),  # row 9:  ·xxxxxxxxxx·
        (2, 10),  # row 10:  ·xxxxxxxx·
        (3, 9),   # row 11:   ··xxx xxx··
    ]
    for dy, (x0, x1) in enumerate(rows):
        for dx in range(x0, x1):
            canvas.SetPixel(x + dx, y + dy, r, g, b)


class MatrixRenderer:
    """Renders arrivals onto an RGB LED matrix panel."""

    def __init__(self, rows: int = 32, cols: int = 64, chain: int = 1, brightness: int = 50):
        if not HAS_MATRIX:
            raise RuntimeError(
                "rpi-rgb-led-matrix is not installed or not running on a Raspberry Pi. "
                "Use TerminalRenderer for development."
            )
        self.cols = cols

        # Load fonts BEFORE creating the matrix — RGBMatrix drops privileges
        # after init, which can prevent file access.
        self.font_lg = graphics.Font()
        self.font_lg.LoadFont(os.path.join(FONT_DIR, "6x10.bdf"))

        self.font_md = graphics.Font()
        self.font_md.LoadFont(os.path.join(FONT_DIR, "5x8.bdf"))

        self.font_sm = graphics.Font()
        self.font_sm.LoadFont(os.path.join(FONT_DIR, "4x6.bdf"))

        self.matrix = RGBMatrix(options=_make_options(rows, cols, chain, brightness))
        self.canvas = self.matrix.CreateFrameCanvas()

    def render(self, subway_arrivals: list[dict], bus_arrivals: list[dict]):
        self.canvas.Clear()
        self._draw_subway_row(subway_arrivals, y_offset=-1)
        self._draw_bus_row(bus_arrivals, y_offset=10)
        self._draw_clock()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _draw_subway_row(self, arrivals: list[dict], y_offset: int):
        """Draw subway row: [●R] 6m          12m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(100, 100, 100)

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_md, 2, y_offset + 10, dim, "No trains")
            return

        first = arrivals[0]
        line = first["line"]
        r, g, b = LINE_COLORS.get(line, (255, 255, 255))

        # 12×12 circle icon at (1, y+2)
        icon_x, icon_y = 1, y_offset + 2
        _draw_subway_icon(self.canvas, icon_x, icon_y, r, g, b)

        # Letter centered in 12×12 icon: 4px wide → 4px pad each side, 6px tall → 3px pad each side
        # 5x8 font baseline = top + ascent. Glyph is 4w×6h.
        letter_x = icon_x + 4
        letter_y = icon_y + 9  # 3px top pad + 6px glyph = baseline at y+9
        graphics.DrawText(self.canvas, self.font_md, letter_x, letter_y, white, line)

        # Primary time in 6x10, vertically centered with 12×12 circle (center y+8)
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_lg, TIME_X, y_offset + 12, time_color, time_str)

        # Next train — right-aligned in 6x10, yellow (red if delayed)
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 6
            nxt_x = self.cols - nxt_width - RIGHT_PAD
            nxt_color = graphics.Color(*RED) if nxt.get("delayed") else graphics.Color(*YELLOW)
            graphics.DrawText(self.canvas, self.font_lg, nxt_x, y_offset + 12, nxt_color, nxt_str)

    def _draw_bus_row(self, arrivals: list[dict], y_offset: int):
        """Draw bus row: Q98 15m          8m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(160, 160, 160)
        bus_color = graphics.Color(0, 119, 187)

        # "Q98" label in 5x8, centered in label zone (0 to TIME_X-1)
        graphics.DrawText(self.canvas, self.font_md, 1, y_offset + 12, bus_color, "Q98")

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_md, TIME_X, y_offset + 12, dim, "No buses")
            return

        first = arrivals[0]
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_lg, TIME_X, y_offset + 12, time_color, time_str)

        # Next bus — right-aligned in 6x10, yellow (red if delayed)
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 6
            nxt_x = self.cols - nxt_width - RIGHT_PAD
            nxt_color = graphics.Color(*RED) if nxt.get("delayed") else graphics.Color(*YELLOW)
            graphics.DrawText(self.canvas, self.font_lg, nxt_x, y_offset + 12, nxt_color, nxt_str)

    def _draw_clock(self):
        """Draw clock in bottom-right corner: digits in 6x10, hand-drawn 2×2 colon."""
        r, g, b = 180, 180, 180
        dim = graphics.Color(r, g, b)

        hour = str(int(_time.strftime("%I")))  # 12-hour, no leading zero
        minute = _time.strftime("%M")

        # Layout: [hour][gap][::][gap][minute] right-aligned
        hour_w = len(hour) * 6
        colon_w = 4  # 1px gap + 2px dots + 1px gap
        minute_w = 12  # always 2 digits × 6px
        total_w = hour_w + colon_w + minute_w

        x = self.cols - total_w - RIGHT_PAD
        baseline = 31

        # Hour digits
        graphics.DrawText(self.canvas, self.font_lg, x, baseline, dim, hour)
        x += hour_w + 1  # 1px gap before dots

        # 2×2 colon dots — vertically centered in 10px font (spans y=22–31)
        for dy in (0, 1):
            for dx in (0, 1):
                self.canvas.SetPixel(x + dx, 24 + dy, r, g, b)  # upper dot
                self.canvas.SetPixel(x + dx, 28 + dy, r, g, b)  # lower dot
        x += 3  # 2px dots + 1px gap after

        # Minute digits
        graphics.DrawText(self.canvas, self.font_lg, x, baseline, dim, minute)
