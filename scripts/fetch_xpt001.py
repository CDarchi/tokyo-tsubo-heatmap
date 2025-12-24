from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from .config import CACHE_DIR, SLEEP_SEC

XPT001_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/XPT001"


def deg2tile(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - (math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi)) / 2.0 * n)
    return xtile, ytile


def bbox_to_tile_range(min_lat: float, min_lon: float, max_lat: float, max_lon: float, zoom: int) -> Tuple[int, int, int, int]:
    x1, y1 = deg2tile(max_lat, min_lon, zoom)  # NW
    x2, y2 = deg2tile(min_lat, max_lon, zoom)  # SE
    return min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)


def _cache_path(z: int, x: int, y: int, from_q: str, to_q: str, price_classification: str, land_type_code: str) -> Path:
    safe = f"XPT001_z{z}_x{x}_y{y}_from{from_q}_to{to_q}_pc{price_classification}_lt{land_type_code.replace(',', '-')}.geojson"
    return Path(CACHE_DIR) / safe


def fetch_tile_geojson(
    *,
    api_key: str,
    z: int,
    x: int,
    y: int,
    from_q: str,
    to_q: str,
    price_classification: str,
    land_type_code: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(z, x, y, from_q, to_q, price_classification, land_type_code)

    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "response_format": "geojson",
        "z": str(z),
        "x": str(x),
        "y": str(y),
        "from": from_q,
        "to": to_q,
        "priceClassification": price_classification,
        "landTypeCode": land_type_code,
    }

    r = requests.get(XPT001_URL, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(SLEEP_SEC)
    return data


def fetch_bbox_points(
    *,
    api_key: str,
    bbox: Dict[str, float],
    z: int,
    from_q: str,
    to_q: str,
    price_classification: str,
    land_type_code: str,
) -> List[Dict[str, Any]]:
    x_min, x_max, y_min, y_max = bbox_to_tile_range(
        bbox["min_lat"], bbox["min_lon"], bbox["max_lat"], bbox["max_lon"], z
    )

    all_features: List[Dict[str, Any]] = []
    total = (x_max - x_min + 1) * (y_max - y_min + 1)
    done = 0

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            done += 1
            print(f"[fetch] {done}/{total} z={z} x={x} y={y}")
            try:
                gj = fetch_tile_geojson(
                    api_key=api_key,
                    z=z,
                    x=x,
                    y=y,
                    from_q=from_q,
                    to_q=to_q,
                    price_classification=price_classification,
                    land_type_code=land_type_code,
                    use_cache=True,
                )
                feats = gj.get("features", [])
                if isinstance(feats, list) and feats:
                    all_features.extend(feats)
            except Exception as e:
                print(f"  ! error tile z={z} x={x} y={y}: {e}")

    return all_features
