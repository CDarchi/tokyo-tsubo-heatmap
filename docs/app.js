// --- 画面上の「最終更新/取引点数/六角形数」を管理する ---
const META_UI = { updated: null, points: null, hexes: null };

function renderMeta() {
  const el = document.getElementById("meta");
  if (!el) return;

  const parts = [];
  parts.push(`最終更新: ${META_UI.updated ?? "読み込み中…"}`);
  if (META_UI.points != null) parts.push(`取引点数: ${Number(META_UI.points).toLocaleString()}`);
  if (META_UI.hexes != null) parts.push(`六角形: ${Number(META_UI.hexes).toLocaleString()}`);

  el.textContent = parts.join(" / ");
}
renderMeta();

// meta.json を読んで「最終更新」を埋める（points/hexes が無くてもOK）
fetch("./data/meta.json", { cache: "no-store" })
  .then(r => r.json())
  .then(meta => {
    META_UI.updated = meta.updated_at || meta.updated || meta.date || meta.generated_at || "不明";
    renderMeta();
  })
  .catch(() => {
    // 失敗しても地図は動かす。表示だけ注意書きにする
    META_UI.updated = "不明（meta取得失敗）";
    renderMeta();
  });
// ---------------------------------------------------------

// ----------------------------------------------

async function loadJSON(path) {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`fetch failed: ${path} ${r.status}`);
  return await r.json();
}

function colorScale(t) {
  const clamped = Math.max(0, Math.min(1, t));
  const r = Math.round(255 * clamped);
  const g = Math.round(80 * (1 - clamped));
  const b = Math.round(255 * (1 - clamped));
  return `rgb(${r},${g},${b})`;
}

// q=0.05 なら「下位5%」の値を返す（だいたいの境界値）
function quantile(sortedValues, q) {
  const n = sortedValues.length;
  if (n === 0) return NaN;
  if (n === 1) return sortedValues[0];
  const pos = (n - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const a = sortedValues[base];
  const b = sortedValues[Math.min(base + 1, n - 1)];
  return a + (b - a) * rest;
}

function makeLegend(minV, maxV) {
  const legend = document.getElementById("legend");
  legend.innerHTML = `
    <div style="font-weight:600; margin-bottom:6px;">坪単価（中央値）</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(0)}"></span>低</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(0.5)}"></span>中</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(1)}"></span>高</div>
    <div style="margin-top:6px; color:#444;">
      表示範囲（外れ値カット）：${Math.round(minV).toLocaleString()} 〜 ${Math.round(maxV).toLocaleString()}
    </div>
    <div style="margin-top:4px; color:#666; font-size:12px;">
      ※ 下位5%・上位5%は同じ色に丸めています
    </div>
  `;
}

(async () => {
  const map = L.map("map").setView([35.68, 139.76], 11);

  L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "地理院タイル",
    className: "basemap",
  }).addTo(map);

 // const meta = await loadJSON("./data/meta.json");
 // document.getElementById("meta").textContent =
 //  `更新: ${meta.updated_at} / 期間: ${meta.range_from}〜${meta.range_to}`;

  const gj = await loadJSON("./data/latest.geojson");

  META_UI.hexes = gj.features?.length ?? 0;
  META_UI.points = (gj.features ?? []).reduce((s, f) => s + (Number(f?.properties?.p_count) || 0), 0);
  renderMeta();

  const values = gj.features
    .map(f => f.properties?.p_med_tsubo)
    .filter(v => typeof v === "number" && isFinite(v))
    .sort((a, b) => a - b);

  // 外れ値カット：下位5%〜上位95%の範囲で色付けする
  const minV = quantile(values, 0.05);
  const maxV = quantile(values, 0.95);
  makeLegend(minV, maxV);

function styleFn(feature) {
  let v = feature.properties.p_med_tsubo;

  // 範囲外は端に丸める（＝外れ値は同じ色になる）
  v = Math.max(minV, Math.min(maxV, v));

  const denom = (maxV - minV) + 1e-9;
  const t = (v - minV) / denom;

  return {
  color: "rgba(255,255,255,0.9)",  // 縁を白で少し強く
  weight: 1.3,
  opacity: 0.95,
  fillColor: colorScale(t),
  fillOpacity: 0.75,              // 中身も少し濃く
  lineJoin: "round",
};

}

  const layer = L.geoJSON(gj, {
    style: styleFn,
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      layer.on("click", () => {
        const msg = `
          <div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;">
            <div style="font-weight:600;">坪単価（中央値）</div>
            <div>${Math.round(p.p_med_tsubo).toLocaleString()}</div>
            <div style="margin-top:6px;color:#444;">件数: ${p.p_count}</div>
          </div>
        `;
        layer.bindPopup(msg).openPopup();
      });
    },
  }).addTo(map);

  if (layer.getBounds().isValid()) {
    map.fitBounds(layer.getBounds());
  }
})();
