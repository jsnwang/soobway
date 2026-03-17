"""
soobway — NYC subway arrival display for matrix boards.
"""
import time
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


def main():
    renderer = get_renderer(config.DISPLAY_MODE)
    is_matrix = config.DISPLAY_MODE == "matrix"

    last_fetch = 0
    subway_arrivals = []
    bus_arrivals = []
    notice = ""

    while True:
        now = time.time()
        if now - last_fetch >= config.REFRESH_INTERVAL:
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

            last_fetch = now

        renderer.render(subway_arrivals, bus_arrivals, notice)
        # Matrix needs fast frames for smooth scrolling; terminal just refreshes with data
        time.sleep(0.05 if is_matrix else config.REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
