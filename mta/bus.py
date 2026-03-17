"""
Fetches bus arrivals from the MTA BusTime SIRI API.
Requires a BusTime API key (BUSTIME_API_KEY in .env).
"""
from datetime import datetime, timezone
import requests

SIRI_URL = "https://bustime.mta.info/api/siri/stop-monitoring.json"


def get_arrivals(api_key: str, stop_ref: str, line: str, direction_ref: str, limit: int = 5) -> list[dict]:
    """
    Fetch upcoming bus arrivals for a stop.

    Args:
        api_key: MTA BusTime API key
        stop_ref: BusTime stop ID, numeric only (e.g. '504456')
                  Find yours at https://bustime.mta.info — search your stop, copy the ID from the URL
        line: Bus route without prefix, e.g. 'Q98'
        direction_ref: '0' or '1' — check bustime.mta.info for which direction is towards your destination
        limit: Max arrivals to return

    Returns:
        List of dicts with keys: 'line', 'stop', 'minutes_away', 'type'
    """
    params = {
        "key": api_key,
        "MonitoringRef": stop_ref,
        "LineRef": f"MTA NYCT_{line}",
        "DirectionRef": direction_ref,
        "MaximumStopVisits": limit,
    }
    response = requests.get(SIRI_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    visits = (
        data.get("Siri", {})
            .get("ServiceDelivery", {})
            .get("StopMonitoringDelivery", [{}])[0]
            .get("MonitoredStopVisit", [])
    )

    now = datetime.now(timezone.utc)
    arrivals = []

    for visit in visits:
        call = visit.get("MonitoredVehicleJourney", {}).get("MonitoredCall", {})
        expected_str = call.get("ExpectedArrivalTime")
        aimed_str = call.get("AimedArrivalTime")
        time_str = expected_str or aimed_str
        if not time_str:
            continue
        arrival_dt = datetime.fromisoformat(time_str)
        minutes = int((arrival_dt - now).total_seconds() / 60)
        delayed = False
        if expected_str and aimed_str:
            expected_dt = datetime.fromisoformat(expected_str)
            aimed_dt = datetime.fromisoformat(aimed_str)
            delayed = (expected_dt - aimed_dt).total_seconds() > 300
        if minutes >= 0:
            arrivals.append({
                "line": line,
                "stop": stop_ref,
                "minutes_away": minutes,
                "delayed": delayed,
                "type": "bus",
            })

    return arrivals[:limit]
