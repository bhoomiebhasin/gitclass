"""
geocoder.py – Geocoding module for CityLens
Uses GeoPy + Nominatim (OpenStreetMap) for:
  - geocode_city:    free text → (lat, lon)
  - reverse_geocode: (lat, lon) → real place name from OpenStreetMap
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time

_geolocator = Nominatim(user_agent="CityLens/1.0 (urban-resilience-engine)")


import time

_last_request_time = 0.0

def _rate_limit():
    """Ensure at least 1.1 seconds between Nominatim calls to avoid being blocked."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_request_time = time.time()

def geocode_city(query: str) -> tuple[float, float] | None:
    """
    Convert a city name / free text query to (latitude, longitude).
    """
    try:
        _rate_limit()
        location = _geolocator.geocode(query, timeout=10)
        if location is None:
            return None
        return (location.latitude, location.longitude)

    except GeocoderTimedOut:
        return None
    except GeocoderUnavailable:
        return None
    except Exception:
        return None


def reverse_geocode(lat: float, lon: float) -> str:
    """
    Convert (lat, lon) to a real human-readable place name via Nominatim.
    Returns the most specific available name (suburb → neighbourhood → district → city).

    This grounds AI-generated zone coordinates with *verified* OSM place names,
    preventing Gemini from hallucinating neighbourhood labels.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        A real place name string, or a coordinate fallback label on failure.
    """
    try:
        _rate_limit()
        location = _geolocator.reverse(
            (lat, lon),
            exactly_one=True,
            timeout=10,
            language="en",
        )
        if location is None:
            return f"Zone ({lat:.3f}, {lon:.3f})"

        addr = location.raw.get("address", {})

        # Walk from most specific to least specific available field
        name = (
            addr.get("suburb")
            or addr.get("neighbourhood")
            or addr.get("quarter")
            or addr.get("village")
            or addr.get("town")
            or addr.get("city_district")
            or addr.get("district")
            or addr.get("county")
            or addr.get("city")
            or addr.get("state")
            or f"Zone ({lat:.3f}, {lon:.3f})"
        )
        return name

    except GeocoderTimedOut:
        return f"Zone ({lat:.3f}, {lon:.3f})"
    except GeocoderUnavailable:
        return f"Zone ({lat:.3f}, {lon:.3f})"
    except Exception:
        return f"Zone ({lat:.3f}, {lon:.3f})"
