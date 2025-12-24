from __future__ import annotations

# 取得する地図タイルのズーム（大きいほど細かい）
ZOOM = 13

# H3 の細かさ（大きいほど細かい六角形）
H3_RESOLUTION = 9

# 東京のだいたいの範囲（まずは狭めに）
TOKYO_BBOX = {
    "min_lat": 35.45,
    "min_lon": 139.55,
    "max_lat": 35.90,
    "max_lon": 139.95,
}

# 取引価格（01）だけ
PRICE_CLASSIFICATION = "01"

# 種類コード（01:土地, 02:土地+建物）
LAND_TYPE_CODE = "01,02"

# リクエスト間の待ち時間（安全のため）
SLEEP_SEC = 0.10

# 出力先
CACHE_DIR = "data/cache"
DOCS_DATA_DIR = "docs/data"
