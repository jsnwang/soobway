"""
soobway — NYC subway arrival display for matrix boards.
"""
import time
import config
import mta.feed as subway
import mta.bus as bus
from display.renderer import get_renderer


def main():
    renderer = get_renderer(config.DISPLAY_MODE)

    while True:
        subway_arrivals = []
        for stop in config.SUBWAY_STOPS:
            subway_arrivals.extend(subway.get_arrivals(
                url=stop["url"],
                stop_id=stop["stop_id"],
                route_id=stop["route_id"],
            ))
        subway_arrivals.sort(key=lambda x: x["minutes_away"])

        bus_arrivals = []
        for stop in config.BUS_STOPS:
            bus_arrivals.extend(bus.get_arrivals(
                api_key=config.BUSTIME_API_KEY,
                stop_ref=stop["stop_ref"],
                line=stop["line"],
                direction_ref=stop["direction_ref"],
            ))
        bus_arrivals.sort(key=lambda x: x["minutes_away"])

        renderer.render(subway_arrivals, bus_arrivals)
        time.sleep(config.REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
