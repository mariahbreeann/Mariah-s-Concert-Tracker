"""
ticketmaster.py — fetch concert events from the Ticketmaster Discovery API.

Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
Free tier: 5000 req/day, 200 req/hour
"""

import os
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, date
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

TM_BASE = "https://app.ticketmaster.com/discovery/v2"
API_KEY = os.getenv("TICKETMASTER_API_KEY", "")

# Bounding boxes for regions we care about.
# Format: (latlong center, radius in miles) — TM uses geoPoint + radius
REGIONS = {
    "northern_california": {"latlong": "37.7749,-122.4194", "radius": "150"},  # SF center
    "las_vegas":           {"latlong": "36.1699,-115.1398", "radius": "50"},
}


def _get(endpoint: str, params: dict) -> dict:
    """Raw GET with basic retry on 429."""
    if not API_KEY:
        raise ValueError(
            "TICKETMASTER_API_KEY not set. "
            "Add it to your .env file — get a free key at "
            "https://developer.ticketmaster.com"
        )
    params["apikey"] = API_KEY
    url = f"{TM_BASE}/{endpoint}"
    for attempt in range(3):
        r = requests.get(url, params=params, timeout=10, verify=False)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Ticketmaster API rate limit exceeded after retries.")


def search_artist_events(
    artist: str,
    date_start: date,
    date_end: date,
    region: Optional[str] = None,
) -> list[dict]:
    """
    Search for events matching `artist` within a date range.
    If region is given (key in REGIONS), constrain to that geo.
    Returns a list of normalized event dicts.
    """
    start_str = datetime.combine(date_start, datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str   = datetime.combine(date_end,   datetime.max.time()).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "keyword":          artist,
        "classificationName": "music",
        "startDateTime":    start_str,
        "endDateTime":      end_str,
        "size":             10,
        "sort":             "date,asc",
        "locale":           "*",
    }

    if region and region in REGIONS:
        geo = REGIONS[region]
        params["latlong"] = geo["latlong"]
        params["radius"]  = geo["radius"]
        params["unit"]    = "miles"

    data = _get("events.json", params)
    raw_events = (
        data.get("_embedded", {}).get("events", [])
    )
    return [_normalize(e) for e in raw_events]


def search_all_regions(
    artist: str,
    date_start: date,
    date_end: date,
) -> list[dict]:
    """
    Search all configured regions for an artist and deduplicate by event ID.
    """
    seen = {}
    for region in REGIONS:
        events = search_artist_events(artist, date_start, date_end, region)
        for ev in events:
            seen[ev["id"]] = ev
    return list(seen.values())


def _normalize(event: dict) -> dict:
    """Flatten a raw TM event into a clean dict."""
    venue_info = (event.get("_embedded") or {}).get("venues", [{}])[0]
    loc = venue_info.get("location", {})

    # Date/time
    dates = event.get("dates", {}).get("start", {})
    show_date_str = dates.get("localDate")
    show_date = datetime.strptime(show_date_str, "%Y-%m-%d").date() if show_date_str else None

    # Price range
    price_ranges = event.get("priceRanges", [])
    price_min = price_ranges[0].get("min") if price_ranges else None
    price_max = price_ranges[0].get("max") if price_ranges else None

    # Artist (attractions)
    attractions = (event.get("_embedded") or {}).get("attractions", [])
    artist_name = attractions[0].get("name", event.get("name", "Unknown")) if attractions else event.get("name", "Unknown")

    return {
        "id":          event.get("id"),
        "artist":      artist_name,
        "event_name":  event.get("name"),
        "venue":       venue_info.get("name"),
        "city":        venue_info.get("city", {}).get("name"),
        "state":       venue_info.get("state", {}).get("stateCode"),
        "address":     venue_info.get("address", {}).get("line1"),
        "lat":         float(loc["latitude"])  if loc.get("latitude")  else None,
        "lon":         float(loc["longitude"]) if loc.get("longitude") else None,
        "show_date":   show_date,
        "show_date_str": show_date_str,
        "price_min":   price_min,
        "price_max":   price_max,
        "url":         event.get("url"),
    }


if __name__ == "__main__":
    # Quick smoke test — run:  python ticketmaster.py
    from datetime import date
    results = search_all_regions("Noah Kahan", date(2025, 7, 1), date(2025, 12, 31))
    for r in results:
        print(r["show_date"], r["artist"], "|", r["venue"], r["city"], r["state"])
