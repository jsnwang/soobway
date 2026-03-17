"""
soobway — NYC subway arrival display for matrix boards.
"""
import time
import threading
import config
import mta.feed as subway
import mta.bus as bus
import mta.alerts as alerts
from display.renderer import get_renderer

# Routes to watch for service alerts (R/M priority, then E/F)
ALERT_ROUTES = ["R", "M", "E", "F"]


def _build_notice(alert_list: list[dict]) -> str:
    """Build a notice string from alerts. R/M first, then E/F."""
    if not alert_list:
        return ""

    priority = {"R": 0, "M": 1, "E": 2, "F": 3}

    def sort_key(a):
        return min(priority.get(r, 99) for r in a["routes"])

    alert_list.sort(key=sort_key)

    parts = []
    for a in alert_list:
        routes = "/".join(a["routes"])
        parts.append(f"{routes}: {a['text']}")

    return "   ---   ".join(parts)


def _fetch_data():
    """Fetch all data sources. Returns (subway_arrivals, bus_arrivals, notice)."""
    subway_arrivals = []
    for feed in config.SUBWAY_FEEDS:
        try:
            subway_arrivals.extend(subway.get_arrivals(
                url=feed["url"],
                stop_id=feed["stop_id"],
            ))
        except Exception:
            pass
    subway_arrivals.sort(key=lambda x: x["minutes_away"])

    bus_arrivals = []
    for stop in config.BUS_STOPS:
        try:
            bus_arrivals.extend(bus.get_arrivals(
                api_key=config.BUSTIME_API_KEY,
                stop_ref=stop["stop_ref"],
                line=stop["line"],
                direction_ref=stop["direction_ref"],
            ))
        except Exception:
            pass
    bus_arrivals.sort(key=lambda x: x["minutes_away"])

    alert_list = alerts.get_alerts(ALERT_ROUTES)
    notice = _build_notice(alert_list)

    return subway_arrivals, bus_arrivals, notice


def main():
    renderer = get_renderer(config.DISPLAY_MODE)
    is_matrix = config.DISPLAY_MODE == "matrix"

    subway_arrivals = []
    bus_arrivals = []
    notice = ""
    fetch_pending = False
    lock = threading.Lock()

    def fetch_in_background():
        nonlocal subway_arrivals, bus_arrivals, notice, fetch_pending
        new_subway, new_bus, new_notice = _fetch_data()
        with lock:
            subway_arrivals = new_subway
            bus_arrivals = new_bus
            notice = new_notice
            fetch_pending = False

    last_fetch = 0

    while True:
        now = time.time()
        if now - last_fetch >= config.REFRESH_INTERVAL and not fetch_pending:
            fetch_pending = True
            last_fetch = now
            if is_matrix:
                threading.Thread(target=fetch_in_background, daemon=True).start()
            else:
                # Terminal mode: fetch synchronously (no scrolling to maintain)
                fetch_in_background()

        with lock:
            renderer.render(subway_arrivals, bus_arrivals, notice)

        time.sleep(0.05 if is_matrix else config.REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
