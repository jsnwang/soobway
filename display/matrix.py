"""
RGB LED matrix renderer using rpi-rgb-led-matrix.
Only functional on Raspberry Pi with the matrix hardware connected.
"""
import time
from display.renderer import LINE_COLORS

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False


def _make_options(rows: int = 32, cols: int = 64, chain: int = 1, brightness: int = 50) -> "RGBMatrixOptions":
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain
    options.brightness = brightness
    options.hardware_mapping = "adafruit-hat"
    options.gpio_slowdown = 4  # RPi 4 requires slowdown of 4
    return options


class MatrixRenderer:
    """Renders arrivals onto an RGB LED matrix panel."""

    def __init__(self, rows: int = 32, cols: int = 64, chain: int = 1, brightness: int = 50):
        if not HAS_MATRIX:
            raise RuntimeError(
                "rpi-rgb-led-matrix is not installed or not running on a Raspberry Pi. "
                "Use TerminalRenderer for development."
            )
        self.matrix = RGBMatrix(options=_make_options(rows, cols, chain, brightness))
        self.canvas = self.matrix.CreateFrameCanvas()
        self.font = graphics.Font()
        self.font.LoadFont("/usr/share/fonts/misc/5x8.bdf")  # adjust path as needed

    def render(self, arrivals: list[dict], stop_name: str = ""):
        self.canvas.Clear()
        font = self.font
        y = 8

        if stop_name:
            graphics.DrawText(self.canvas, font, 1, y, graphics.Color(255, 255, 255), stop_name[:12])
            y += 10

        for arrival in arrivals[:3]:
            line = arrival["line"]
            mins = arrival["minutes_away"]
            r, g, b = LINE_COLORS.get(line, (255, 255, 255))
            color = graphics.Color(r, g, b)
            label = "Now" if mins == 0 else f"{mins}m"
            text = f"{line} {arrival['direction']} {label}"
            graphics.DrawText(self.canvas, font, 1, y, color, text)
            y += 9

        self.canvas = self.matrix.SwapOnVSync(self.canvas)
