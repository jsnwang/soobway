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

    def render(self, subway_arrivals: list[dict], bus_arrivals: list[dict]):
        os.system("cls" if os.name == "nt" else "clear")

        # Subway row
        if subway_arrivals:
            first = subway_arrivals[0]
            mins = first["minutes_away"]
            label = "Now" if mins == 0 else f"{mins}m"
            warn = " [!]" if first.get("delayed") else ""
            line_str = f"  [{first['line']}] {label}{warn}"
            if len(subway_arrivals) >= 2:
                nxt = subway_arrivals[1]
                nxt_str = f"{nxt['minutes_away']}m"
                print(f"{line_str:<25}{nxt_str:>15}")
            else:
                print(line_str)
        else:
            print("  No trains")

        # Bus row
        if bus_arrivals:
            first = bus_arrivals[0]
            mins = first["minutes_away"]
            label = "Now" if mins == 0 else f"{mins}m"
            warn = " [!]" if first.get("delayed") else ""
            line_str = f"  Q98 {label}{warn}"
            if len(bus_arrivals) >= 2:
                nxt_str = f"{bus_arrivals[1]['minutes_away']}m"
                print(f"{line_str:<25}{nxt_str:>15}")
            else:
                print(line_str)
        else:
            print("  No buses")

        print(f"{'':>34}{time.strftime('%H:%M')}")


def get_renderer(mode: str = "terminal"):
    """
    Factory for display renderers.
    mode: 'terminal' | 'matrix'
    """
    if mode == "matrix":
        from display.matrix import MatrixRenderer
        return MatrixRenderer()
    return TerminalRenderer()
