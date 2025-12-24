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

function makeLegend(minV, maxV) {
  const legend = document.getElementById("legend");
  legend.innerHTML = `
    <div style="font-weight:600; margin-bottom:6px;">坪単価（中央値）</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(0)}"></span>低</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(0.5)}"></span>中</div>
    <div class="legend-row"><span class="swatch" style="background:${colorScale(1)}"></span>高</div>
    <div style="margin-top:6px; color:#444;">
      範囲：${Math.round(minV).toLocaleString()} 〜 ${Math.round(maxV).toLocaleString()}
    </div>
  `;
}

(async () => {
  const map = L.map("map").setView([35.68, 139.76], 11);

  L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "地理院タイル",
  }).addTo(map);

  const meta = await loadJSON("./data/meta.json");
  document.getElementById("meta").textContent =
    `更新: ${meta.updated_at} / 期間: ${meta.range_from}〜${meta.range_to}`;

  const gj = await loadJSON("./data/latest.geojson");

  const values = gj.features
    .map(f => f.properties?.p_med_tsubo)
    .filter(v => typeof v === "number" && isFinite(v));

  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  makeLegend(minV, maxV);

  function styleFn(feature) {
    const v = feature.properties.p_med_tsubo;
    const t = (v - minV) / (maxV - minV + 1e-9);
    return {
      color: "rgba(0,0,0,0.15)",
      weight: 1,
      fillColor: colorScale(t),
      fillOpacity: 0.45,
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
