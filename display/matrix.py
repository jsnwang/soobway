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


def _draw_caution(canvas, x, y):
    """Draw a small 5×5 yellow caution triangle with dark '!' center."""
    yellow = (255, 200, 0)
    # Row by row (top to bottom)
    #     *        row 0: 1 pixel
    #    * *       row 1: 2 pixels
    #   * . *      row 2: 3 pixels, center dark for "!"
    #  * * * *     row 3: 4 pixels, center dot for "!"
    # * * * * *    row 4: 5 pixels (base)
    pixels = [
        [(2, 0)],
        [(1, 1), (3, 1)],
        [(0, 2), (2, 2), (4, 2)],
        [(0, 3), (1, 3), (3, 3), (4, 3)],
        [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)],
    ]
    for row in pixels:
        for dx, dy in row:
            canvas.SetPixel(x + dx, y + dy, *yellow)
    # Dark "!" dot at center of triangle
    canvas.SetPixel(x + 2, y + 2, 0, 0, 0)
    canvas.SetPixel(x + 2, y + 3, 255, 200, 0)


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
        self._draw_bus_row(bus_arrivals, y_offset=16)
        self._draw_clock()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _draw_subway_row(self, arrivals: list[dict], y_offset: int):
        """Draw subway row: [●R] 6m ⚠        12m"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(100, 100, 100)

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_sm, 1, y_offset + 10, dim, "No trains")
            return

        first = arrivals[0]
        line = first["line"]
        r, g, b = LINE_COLORS.get(line, (255, 255, 255))

        # Filled circle icon — radius 5, center at (5, y+7)
        cx, cy = 5, y_offset + 7
        _draw_filled_circle(self.canvas, cx, cy, 5, r, g, b)

        # White letter centered inside circle (5x8 font)
        letter_x = cx - 2
        letter_y = cy + 4
        graphics.DrawText(self.canvas, self.font_md, letter_x, letter_y, white, line)

        # Primary time in 6x10 font
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_x = 13
        graphics.DrawText(self.canvas, self.font_lg, time_x, y_offset + 12, white, time_str)

        # Caution triangle if delayed
        time_width = len(time_str) * 6
        if first.get("delayed"):
            _draw_caution(self.canvas, time_x + time_width + 2, y_offset + 4)

        # Next train — right-aligned in 4x6 font
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_mins = nxt["minutes_away"]
            nxt_str = f"{nxt_mins}m"
            nxt_width = len(nxt_str) * 5
            nxt_x = self.cols - nxt_width
            nxt_r, nxt_g, nxt_b = LINE_COLORS.get(nxt["line"], (100, 100, 100))
            graphics.DrawText(self.canvas, self.font_sm, nxt_x, y_offset + 10, graphics.Color(nxt_r, nxt_g, nxt_b), nxt_str)

    def _draw_bus_row(self, arrivals: list[dict], y_offset: int):
        """Draw bus row: Q98 15m ⚠        12m"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(100, 100, 100)
        bus_color = graphics.Color(0, 119, 187)

        # "Q98" label in 6x10
        graphics.DrawText(self.canvas, self.font_lg, 1, y_offset + 12, bus_color, "Q98")

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_sm, 20, y_offset + 10, dim, "No buses")
            return

        first = arrivals[0]
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_x = 20
        graphics.DrawText(self.canvas, self.font_lg, time_x, y_offset + 12, white, time_str)

        # Caution triangle if delayed
        time_width = len(time_str) * 6
        if first.get("delayed"):
            _draw_caution(self.canvas, time_x + time_width + 2, y_offset + 4)

        # Next bus — right-aligned in 4x6 font
        if len(arrivals) >= 2:
            nxt_mins = arrivals[1]["minutes_away"]
            nxt_str = f"{nxt_mins}m"
            nxt_width = len(nxt_str) * 5
            nxt_x = self.cols - nxt_width
            graphics.DrawText(self.canvas, self.font_sm, nxt_x, y_offset + 10, dim, nxt_str)

    def _draw_clock(self):
        """Draw tiny clock in bottom-right corner."""
        dim = graphics.Color(60, 60, 60)
        clock_str = _time.strftime("%H:%M")
        clock_width = len(clock_str) * 5
        graphics.DrawText(self.canvas, self.font_sm, self.cols - clock_width, 31, dim, clock_str)
