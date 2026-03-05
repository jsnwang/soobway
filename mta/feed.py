"""
Fetches GTFS-RT feeds from the MTA API.
"""
import time
import requests
from nyct_gtfs import NYCTFeed


def get_arrivals(api_key: str, feed_id: str, stop_id: str, line: str, direction: str = "N", limit: int = 5) -> list[dict]:
    """
    Fetch upcoming arrivals for a stop.

    Args:
        api_key: MTA API key
        feed_id: GTFS-RT feed ID (e.g. '1' for 1/2/3/4/5/6/S, 'A' for A/C/E, etc.)
        stop_id: Stop ID (e.g. '127' for Times Square on the 1/2/3)
        line: Train line (e.g. '1', 'A', 'N')
        direction: 'N' or 'S'
        limit: Max number of arrivals to return

    Returns:
        List of dicts with keys: 'line', 'direction', 'stop', 'minutes_away'
    """
    feed = NYCTFeed(line, api_key=api_key)
    now = time.time()
    arrivals = []

    for trip in feed.filter_trips(headed_for_stop_id=stop_id, underway=True):
        for update in trip.stop_time_updates:
            if update.stop_id.startswith(stop_id):
                arrival_time = update.arrival if update.arrival else update.departure
                if arrival_time and arrival_time > now:
                    minutes = int((arrival_time - now) / 60)
                    arrivals.append({
                        "line": trip.nyct_trip_descriptor.train_id or line,
                        "direction": direction,
                        "stop": stop_id,
                        "minutes_away": minutes,
                    })

    arrivals.sort(key=lambda x: x["minutes_away"])
    return arrivals[:limit]
