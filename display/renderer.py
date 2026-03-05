"""
Renders subway arrival data to a matrix display.
Supports both physical RGB LED matrix (via rpi-rgb-led-matrix) and
terminal/simulation mode for development.
"""
import os
import time

# Line colors per NYC subway branding
LINE_COLORS = {
    "1": (238, 53, 46), "2": (238, 53, 46), "3": (238, 53, 46),
    "4": (0, 147, 60), "5": (0, 147, 60), "6": (0, 147, 60),
    "7": (185, 51, 173),
    "A": (0, 57, 166), "C": (0, 57, 166), "E": (0, 57, 166),
    "B": (255, 99, 25), "D": (255, 99, 25), "F": (255, 99, 25), "M": (255, 99, 25),
    "G": (108, 190, 69),
    "J": (153, 102, 51), "Z": (153, 102, 51),
    "L": (167, 169, 172),
    "N": (252, 204, 10), "Q": (252, 204, 10), "R": (252, 204, 10), "W": (252, 204, 10),
    "S": (128, 129, 131),
}


class TerminalRenderer:
    """Renders arrivals to the terminal for development/simulation."""

    def render(self, arrivals: list[dict], stop_name: str = ""):
        os.system("cls" if os.name == "nt" else "clear")
        header = f" {stop_name} " if stop_name else " Arrivals "
        print(f"{'=' * 30}")
        print(f"{header:^30}")
        print(f"{'=' * 30}")
        if not arrivals:
            print("  No upcoming arrivals")
        for a in arrivals:
            mins = a["minutes_away"]
            label = "Now" if mins == 0 else f"{mins} min"
            print(f"  [{a['line']}]  {a['direction']}  {label:>6}")
        print(f"{'=' * 30}")
        print(f"  Updated: {time.strftime('%H:%M:%S')}")


def get_renderer(mode: str = "terminal"):
    """
    Factory for display renderers.
    mode: 'terminal' | 'matrix'
    """
    if mode == "matrix":
        from display.matrix import MatrixRenderer
        return MatrixRenderer()
    return TerminalRenderer()
