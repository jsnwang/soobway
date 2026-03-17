"""
Fetches subway arrivals from MTA GTFS-RT feeds.
No API key required — endpoints are public.
"""
import time
import requests
from google.transit import gtfs_realtime_pb2


def get_arrivals(url: str, stop_id: str, route_id: str | None = None, limit: int = 5) -> list[dict]:
    """
    Fetch upcoming arrivals for a subway stop from a GTFS-RT feed URL.

    Args:
        url: MTA GTFS-RT feed URL (see config.py SUBWAY_FEEDS for examples)
        stop_id: GTFS stop ID including direction suffix, e.g. 'G10S' (southbound = Manhattan-bound)
        route_id: Optional train line filter. If None, returns all lines at this stop.
        limit: Max arrivals to return

    Returns:
        List of dicts with keys: 'line', 'stop', 'minutes_away', 'delayed', 'type'
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    now = time.time()
    arrivals = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        trip = entity.trip_update
        if route_id and trip.trip.route_id != route_id:
            continue
        for stop_time in trip.stop_time_update:
            if stop_time.stop_id == stop_id:
                t = stop_time.arrival.time if stop_time.arrival.time else stop_time.departure.time
                if t > now:
                    delay_sec = stop_time.arrival.delay if stop_time.arrival.delay else 0
                    arrivals.append({
                        "line": trip.trip.route_id,
                        "stop": stop_id,
                        "minutes_away": int((t - now) / 60),
                        "delayed": delay_sec > 300,
                        "type": "subway",
                    })
                break  # only one match per trip

    arrivals.sort(key=lambda x: x["minutes_away"])
    return arrivals[:limit]
