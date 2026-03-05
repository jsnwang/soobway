"""
soobway — NYC subway arrival display for matrix boards.
"""
import time
import config
from mta.feed import get_arrivals
from display.renderer import get_renderer


def main():
    renderer = get_renderer(config.DISPLAY_MODE)

    while True:
        all_arrivals = []
        for stop in config.STOPS:
            arrivals = get_arrivals(
                api_key=config.MTA_API_KEY,
                feed_id=stop["feed_id"],
                stop_id=stop["stop_id"],
                line=stop["line"],
                direction=stop["direction"],
            )
            all_arrivals.extend(arrivals)

        stop_name = config.STOPS[0]["name"] if config.STOPS else ""
        renderer.render(all_arrivals, stop_name=stop_name)
        time.sleep(config.REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
