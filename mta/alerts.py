"""
Fetches subway service alerts from MTA GTFS-RT alerts feed.
No API key required.
"""
import time
import requests
from google.transit import gtfs_realtime_pb2

ALERTS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts"


def get_alerts(routes: list[str]) -> list[dict]:
    """
    Fetch active service alerts for specific subway routes.

    Args:
        routes: Route IDs to filter for, e.g. ["R", "M", "E", "F"]

    Returns:
        List of dicts with keys: 'routes' (list[str]), 'text' (str)
    """
    try:
        response = requests.get(ALERTS_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    now = time.time()
    route_set = set(routes)
    alerts = []

    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert

        # Which of our routes are affected?
        affected = set()
        for informed in alert.informed_entity:
            if informed.route_id in route_set:
                affected.add(informed.route_id)
        if not affected:
            continue

        # Check if currently active
        active = not alert.active_period
        for period in alert.active_period:
            start = period.start if period.start else 0
            end = period.end if period.end else float('inf')
            if start <= now <= end:
                active = True
                break
        if not active:
            continue

        # Get English header text
        header = ""
        if alert.header_text and alert.header_text.translation:
            for t in alert.header_text.translation:
                if t.language == "en" or not t.language:
                    header = t.text
                    break
            if not header:
                header = alert.header_text.translation[0].text

        if header:
            alerts.append({
                "routes": sorted(affected),
                "text": header,
            })

    return alerts
