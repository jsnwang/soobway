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
TIME_X = 18

# Delay color
RED = (255, 40, 40)


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


def _draw_filled_circle(canvas, cx, cy, radius, r, g, b):
    """Draw a filled circle by setting individual pixels."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                canvas.SetPixel(cx + dx, cy + dy, r, g, b)


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
        self._draw_subway_row(subway_arrivals, y_offset=0)
        self._draw_bus_row(bus_arrivals, y_offset=14)
        self._draw_clock()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _draw_subway_row(self, arrivals: list[dict], y_offset: int):
        """Draw subway row: [●R] 6m          12m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(100, 100, 100)

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_sm, 2, y_offset + 10, dim, "No trains")
            return

        first = arrivals[0]
        line = first["line"]
        r, g, b = LINE_COLORS.get(line, (255, 255, 255))

        # Filled circle — radius 6, center at (8, y+8)
        cx, cy = 8, y_offset + 8
        _draw_filled_circle(self.canvas, cx, cy, 6, r, g, b)

        # White letter centered inside circle (4x6 font — smaller for better centering)
        letter_x = cx - 2
        letter_y = cy + 3
        graphics.DrawText(self.canvas, self.font_sm, letter_x, letter_y, white, line)

        # Primary time in 6x10, vertically centered with circle (baseline y=13)
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_lg, TIME_X, y_offset + 13, time_color, time_str)

        # Next train — right-aligned in 6x10, same baseline
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 6
            nxt_x = self.cols - nxt_width
            if nxt.get("delayed"):
                nxt_color = graphics.Color(*RED)
            else:
                nxt_r, nxt_g, nxt_b = LINE_COLORS.get(nxt["line"], (100, 100, 100))
                nxt_color = graphics.Color(nxt_r, nxt_g, nxt_b)
            graphics.DrawText(self.canvas, self.font_lg, nxt_x, y_offset + 13, nxt_color, nxt_str)

    def _draw_bus_row(self, arrivals: list[dict], y_offset: int):
        """Draw bus row: Q98 15m          8m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(160, 160, 160)
        bus_color = graphics.Color(0, 119, 187)

        # "Q98" label in 5x8
        graphics.DrawText(self.canvas, self.font_md, 2, y_offset + 10, bus_color, "Q98")

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_sm, TIME_X, y_offset + 8, dim, "No buses")
            return

        first = arrivals[0]
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_md, TIME_X, y_offset + 10, time_color, time_str)

        # Next bus — right-aligned in 5x8, same baseline
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 5
            nxt_x = self.cols - nxt_width
            nxt_color = graphics.Color(*RED) if nxt.get("delayed") else dim
            graphics.DrawText(self.canvas, self.font_md, nxt_x, y_offset + 10, nxt_color, nxt_str)

    def _draw_clock(self):
        """Draw tiny clock in bottom-right corner."""
        dim = graphics.Color(100, 100, 100)
        clock_str = _time.strftime("%H:%M")
        clock_width = len(clock_str) * 5
        graphics.DrawText(self.canvas, self.font_sm, self.cols - clock_width, 31, dim, clock_str)
