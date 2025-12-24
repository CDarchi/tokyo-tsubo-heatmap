from __future__ import annotations

import re
from statistics import median
from typing import Any, Dict, List

import h3


def _to_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", "")
        # 例: "12,345円" "123万円" みたいな文字が混ざっていても数字だけ残す
        s = re.sub(r"[^0-9.\-]", "", s)
        if s == "" or s == "-" or s == ".":
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _pick_price(props: Dict[str, Any], prefer: str) -> float | None:
    # よくありそうな候補を順に試す（データのキー名が違っても拾えるようにする）
    candidates = [
        prefer,
        "u_unit_price_per_tsubo_ja",
        "u_unit_price_per_tsubo",
        "unit_price_per_tsubo",
        "u_unit_price",
        "unit_price",
    ]
    for k in candidates:
        if k and k in props:
            v = _to_float(props.get(k))
            if v is not None:
                return v

    # 最後の手段：キー名に "tsubo" と "price" が含まれるものを探す
    for k, v in props.items():
        lk = str(k).lower()
        if ("tsubo" in lk) and ("price" in lk or "unit" in lk):
            vv = _to_float(v)
            if vv is not None:
                return vv

    return None


def aggregate_points_to_h3_polygons(
    *,
    point_features: List[Dict[str, Any]],
    h3_resolution: int,
    price_field: str = "u_unit_price_per_tsubo_ja",
) -> Dict[str, Any]:
    buckets: Dict[str, List[float]] = {}

    for f in point_features:
        geom = (f or {}).get("geometry") or {}
        coords = geom.get("coordinates")
        if not (isinstance(coords, list) and len(coords) >= 2):
            continue
        lon, lat = coords[0], coords[1]

        props = (f or {}).get("properties") or {}
        price = _pick_price(props, price_field)
        if price is None:
            continue

        cell = h3.latlng_to_cell(lat, lon, h3_resolution)
        buckets.setdefault(cell, []).append(price)

    out_features: List[Dict[str, Any]] = []
    for cell, prices in buckets.items():
        p_med = float(median(prices))
        p_cnt = int(len(prices))

        boundary_latlng = h3.cell_to_boundary(cell)
        ring = [[lng, lat] for (lat, lng) in boundary_latlng]
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])

        out_features.append(
            {
                "type": "Feature",
                "properties": {"h3": cell, "p_med_tsubo": p_med, "p_count": p_cnt},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    return {"type": "FeatureCollection", "features": out_features}
