from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Tuple

from .aggregate_h3 import aggregate_points_to_h3_polygons
from .config import DOCS_DATA_DIR, H3_RESOLUTION, LAND_TYPE_CODE, PRICE_CLASSIFICATION, TOKYO_BBOX, ZOOM
from .fetch_xpt001 import fetch_bbox_points


def quarter_of(d: date) -> Tuple[int, int]:
    q = (d.month - 1) // 3 + 1
    return d.year, q


def shift_quarter(year: int, q: int, delta: int) -> Tuple[int, int]:
    idx = year * 4 + (q - 1)
    idx2 = idx + delta
    y2 = idx2 // 4
    q2 = (idx2 % 4) + 1
    return y2, q2


def qcode(year: int, q: int) -> str:
    return f"{year}{q}"


def main() -> None:
    api_key = os.environ.get("REINFOLIB_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("環境変数 REINFOLIB_API_KEY がありません。先に設定してください。")

    today = date.today()
    y, q = quarter_of(today)

    # 直前の四半期まで（今の四半期はまだ揃ってないことが多い）
    to_y, to_q = shift_quarter(y, q, -1)
    from_y, from_q = shift_quarter(to_y, to_q, -3)  # 直近4四半期

    from_str = qcode(from_y, from_q)
    to_str = qcode(to_y, to_q)
    print(f"[range] from={from_str} to={to_str}")

    Path(DOCS_DATA_DIR).mkdir(parents=True, exist_ok=True)

    points = fetch_bbox_points(
        api_key=api_key,
        bbox=TOKYO_BBOX,
        z=ZOOM,
        from_q=from_str,
        to_q=to_str,
        price_classification=PRICE_CLASSIFICATION,
        land_type_code=LAND_TYPE_CODE,
    )
    print(f"[points] {len(points)}")

    hexes = aggregate_points_to_h3_polygons(
        point_features=points,
        h3_resolution=H3_RESOLUTION,
        price_field="u_unit_price_per_tsubo_ja",
    )
    print(f"[hexes] {len(hexes.get('features', []))}")

    out_geojson = Path(DOCS_DATA_DIR) / "latest.geojson"
    out_meta = Path(DOCS_DATA_DIR) / "meta.json"

    out_geojson.write_text(json.dumps(hexes, ensure_ascii=False), encoding="utf-8")

    meta = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "range_from": from_str,
        "range_to": to_str,
        "zoom": ZOOM,
        "h3_resolution": H3_RESOLUTION,
        "priceClassification": PRICE_CLASSIFICATION,
        "landTypeCode": LAND_TYPE_CODE,
        "bbox": TOKYO_BBOX,
    }
    out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] wrote docs/data/latest.geojson and meta.json")


if __name__ == "__main__":
    main()
