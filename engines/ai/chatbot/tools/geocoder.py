"""
Geocoder -- Phase KU-2
Global city -> (latitude, longitude) resolution for the Kundli tool.

Lookup chain (fastest / most reliable first):
  1. Built-in CITY_COORDS dict in kundli_calculator (offline, ~120 cities)
  2. Learned cache data/reference/city_coords_cache.csv (offline, grows over time)
  3. Nominatim / OpenStreetMap via geopy (online, global, no API key)
     - polite usage: custom User-Agent, >= 1.1s between requests, 10s timeout
     - every successful online hit is appended to the learned cache so the
       same city never needs the network again

Returns (lat, lon, resolved_name) or None. Never raises -- offline/network
failure degrades to None and the caller keeps its manual lat/long fallback.
"""

import csv
import shutil
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
CACHE_CSV = _ROOT / "data" / "reference" / "city_coords_cache.csv"

_CACHE_COLS = ["city_key", "latitude", "longitude", "resolved_name", "source", "added_on"]

_lock = threading.Lock()
_last_nominatim_call = 0.0
_mem_cache: dict[str, tuple[float, float, str]] | None = None


def _load_cache() -> dict[str, tuple[float, float, str]]:
    global _mem_cache
    if _mem_cache is not None:
        return _mem_cache
    cache: dict[str, tuple[float, float, str]] = {}
    if CACHE_CSV.exists():
        try:
            with open(CACHE_CSV, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        cache[row["city_key"]] = (
                            float(row["latitude"]), float(row["longitude"]),
                            row.get("resolved_name", row["city_key"]),
                        )
                    except (ValueError, KeyError):
                        continue
        except Exception:
            pass
    _mem_cache = cache
    return cache


def _append_cache(key: str, lat: float, lon: float, name: str) -> None:
    """Atomic append (read-modify-write with dedupe, G-D-02/G-D-05 spirit)."""
    with _lock:
        cache = _load_cache()
        if key in cache:
            return
        cache[key] = (lat, lon, name)
        CACHE_CSV.parent.mkdir(parents=True, exist_ok=True)
        from datetime import date
        rows = []
        if CACHE_CSV.exists():
            try:
                with open(CACHE_CSV, newline="", encoding="utf-8") as f:
                    rows = [r for r in csv.DictReader(f) if r.get("city_key") != key]
            except Exception:
                rows = []
        rows.append({
            "city_key": key, "latitude": f"{lat:.6f}", "longitude": f"{lon:.6f}",
            "resolved_name": name, "source": "nominatim", "added_on": date.today().isoformat(),
        })
        tmp = CACHE_CSV.with_suffix(".tmp.csv")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_CACHE_COLS)
            w.writeheader()
            w.writerows(rows)
        shutil.move(str(tmp), str(CACHE_CSV))


def _nominatim(city: str) -> tuple[float, float, str] | None:
    """Online lookup via OpenStreetMap Nominatim. Rate-limited, never raises."""
    global _last_nominatim_call
    try:
        from geopy.geocoders import Nominatim
    except ImportError:
        return None
    try:
        with _lock:
            wait = 1.1 - (time.time() - _last_nominatim_call)
            if wait > 0:
                time.sleep(wait)
            _last_nominatim_call = time.time()
        geo = Nominatim(user_agent="fii-dii-kundli-tool", timeout=10)
        loc = geo.geocode(city)
        if loc is None:
            # Retry biased to India -- most kundli queries are Indian towns
            loc = geo.geocode(f"{city}, India")
        if loc is None:
            return None
        # ASCII-sanitize resolved name (cp1252 console safety)
        name = loc.address.encode("ascii", "replace").decode("ascii")[:80]
        return (float(loc.latitude), float(loc.longitude), name)
    except Exception:
        return None


def resolve_city(city: str, builtin: dict | None = None) -> tuple[float, float, str] | None:
    """Resolve a city name to (lat, lon, resolved_name). None if all tiers fail."""
    if not city or not city.strip():
        return None
    key = city.strip().lower()

    # Tier 1: built-in dict (exact, then substring -- preserves old behavior)
    if builtin:
        if key in builtin:
            lat, lon = builtin[key]
            return (lat, lon, city.strip().title())
        for name, coords in builtin.items():
            if key in name or name in key:
                return (coords[0], coords[1], name.title())

    # Tier 2: learned cache
    cached = _load_cache().get(key)
    if cached:
        return cached

    # Tier 3: Nominatim online
    hit = _nominatim(city.strip())
    if hit:
        _append_cache(key, hit[0], hit[1], hit[2])
        return hit
    return None


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Bokaro"
    print(resolve_city(q))
