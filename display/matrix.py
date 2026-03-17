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
RIGHT_PAD = 2


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

        self.font_clock = graphics.Font()
        self.font_clock.LoadFont(os.path.join(FONT_DIR, "6x9.bdf"))

        self.font_sm = graphics.Font()
        self.font_sm.LoadFont(os.path.join(FONT_DIR, "4x6.bdf"))

        self.matrix = RGBMatrix(options=_make_options(rows, cols, chain, brightness))
        self.canvas = self.matrix.CreateFrameCanvas()

    def render(self, subway_arrivals: list[dict], bus_arrivals: list[dict], notice: str = ""):
        self.canvas.Clear()

        hour = int(_time.strftime("%H"))
        weekday = int(_time.strftime("%w"))  # 0=Sun, 1=Mon...6=Sat

        # Night mode: blank display 12am-8am
        if hour < 8:
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            return

        # Brightness schedule: dim during workday hours and evenings
        is_workday = 1 <= weekday <= 5 and 9 <= hour < 17
        is_evening = hour >= 20
        self.matrix.brightness = 20 if (is_workday or is_evening) else 50

        # Pixel shift: toggle 0/1px every 4 hours to reduce LED aging
        sx = (hour // 4) % 2
        sy = (hour // 4) % 2

        self._draw_subway_row(subway_arrivals, y_offset=-1, sx=sx, sy=sy)
        self._draw_bus_row(bus_arrivals, y_offset=10, sx=sx, sy=sy)
        if notice:
            self._draw_notice(notice, sx=sx, sy=sy)
        self._draw_clock(sx=sx, sy=sy)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _draw_subway_row(self, arrivals: list[dict], y_offset: int, sx: int = 0, sy: int = 0):
        """Draw subway row: [●R] 6m          12m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(100, 100, 100)

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_md, 2 + sx, y_offset + 10 + sy, dim, "No trains")
            return

        first = arrivals[0]
        line = first["line"]
        r, g, b = LINE_COLORS.get(line, (255, 255, 255))

        # 12×12 circle icon
        icon_x, icon_y = 1 + sx, y_offset + 2 + sy
        _draw_subway_icon(self.canvas, icon_x, icon_y, r, g, b)

        # Letter centered in 12×12 icon
        letter_x = icon_x + 4
        letter_y = icon_y + 9
        graphics.DrawText(self.canvas, self.font_md, letter_x, letter_y, white, line)

        # Primary time in 6x10
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_lg, TIME_X + sx, y_offset + 12 + sy, time_color, time_str)

        # Next train — right-aligned in 6x10, yellow (red if delayed)
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 6
            nxt_x = self.cols - nxt_width - RIGHT_PAD + sx
            nxt_color = graphics.Color(*RED) if nxt.get("delayed") else graphics.Color(*YELLOW)
            graphics.DrawText(self.canvas, self.font_lg, nxt_x, y_offset + 12 + sy, nxt_color, nxt_str)

    def _draw_bus_row(self, arrivals: list[dict], y_offset: int, sx: int = 0, sy: int = 0):
        """Draw bus row: Q98 15m          8m  (red if delayed)"""
        white = graphics.Color(255, 255, 255)
        dim = graphics.Color(160, 160, 160)
        bus_color = graphics.Color(0, 119, 187)

        # "Q98" label in 5x8, centered in label zone (0 to TIME_X-1)
        graphics.DrawText(self.canvas, self.font_md, 1 + sx, y_offset + 12 + sy, bus_color, "Q98")

        if not arrivals:
            graphics.DrawText(self.canvas, self.font_md, TIME_X + sx, y_offset + 12 + sy, dim, "No buses")
            return

        first = arrivals[0]
        mins = first["minutes_away"]
        time_str = "Now" if mins == 0 else f"{mins}m"
        time_color = graphics.Color(*RED) if first.get("delayed") else white
        graphics.DrawText(self.canvas, self.font_lg, TIME_X + sx, y_offset + 12 + sy, time_color, time_str)

        # Next bus — right-aligned in 6x10, yellow (red if delayed)
        if len(arrivals) >= 2:
            nxt = arrivals[1]
            nxt_str = f"{nxt['minutes_away']}m"
            nxt_width = len(nxt_str) * 6
            nxt_x = self.cols - nxt_width - RIGHT_PAD + sx
            nxt_color = graphics.Color(*RED) if nxt.get("delayed") else graphics.Color(*YELLOW)
            graphics.DrawText(self.canvas, self.font_lg, nxt_x, y_offset + 12 + sy, nxt_color, nxt_str)

    def _draw_notice(self, notice: str, sx: int = 0, sy: int = 0):
        """Draw scrolling notice text in the bottom row, left of clock."""
        yellow = graphics.Color(200, 165, 8)
        char_w = 6  # font_clock character width
        text_width = len(notice) * char_w

        # Scroll: text enters from right, exits left, then wraps
        speed = 40  # pixels per second
        scroll_range = text_width + self.cols
        scroll_pos = int(_time.time() * speed) % scroll_range
        text_x = self.cols - scroll_pos + sx

        graphics.DrawText(self.canvas, self.font_clock, text_x, 31 + sy, yellow, notice)

    def _draw_clock(self, sx: int = 0, sy: int = 0):
        """Draw clock in bottom-right corner: digits in 6x9 with tight spacing, hand-drawn 2×2 colon."""
        r, g, b = 150, 150, 150
        dim = graphics.Color(r, g, b)

        hour = str(int(_time.strftime("%I")))  # 12-hour, no leading zero
        minute = _time.strftime("%M")

        # Layout: digits at 5px pitch, 1px gap before colon, 1px gap between minute digits
        char_w = 5
        hour_w = len(hour) * char_w
        colon_w = 4  # 1px gap + 2px dots + 1px gap
        minute_w = 2 * char_w + 1  # 1px extra gap between minute digits
        total_w = hour_w + colon_w + minute_w

        clock_x = self.cols - total_w - RIGHT_PAD + sx

        # Clear clock area so scrolling notice doesn't bleed through
        for cy in range(23 + sy, 32 + sy):
            for cx in range(max(0, clock_x - 1), self.cols):
                if 0 <= cy < 32:
                    self.canvas.SetPixel(cx, cy, 0, 0, 0)

        x = clock_x
        baseline = 31 + sy

        # Hour digits
        for ch in hour:
            graphics.DrawText(self.canvas, self.font_clock, x, baseline, dim, ch)
            x += char_w

        x += 1  # 1px gap before colon

        # 2×2 colon dots
        for dy in (0, 1):
            for dx in (0, 1):
                self.canvas.SetPixel(x + dx, 25 + sy + dy, r, g, b)
                self.canvas.SetPixel(x + dx, 29 + sy + dy, r, g, b)
        x += 2

        # Minute digits with 1px extra gap between them
        graphics.DrawText(self.canvas, self.font_clock, x, baseline, dim, minute[0])
        x += char_w + 1
        graphics.DrawText(self.canvas, self.font_clock, x, baseline, dim, minute[1])
