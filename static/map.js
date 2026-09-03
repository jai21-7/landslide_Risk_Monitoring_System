function bootMap(elId, state) {
  const map = L.map(elId).setView([26.2, 92.4], 6);
  const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap"
  });
  const sat = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    { attribution: "Tiles &copy; Esri" }
  );
  osm.addTo(map);

  const layers = {
    heat: L.heatLayer(state.heatmap, { radius: 28, blur: 22, maxZoom: 8 }),
    stations: L.layerGroup(),
    roads: L.layerGroup(),
    villages: L.layerGroup(),
    infra: L.layerGroup(),
    reports: L.layerGroup()
  };

  state.stations.forEach((s) => {
    const m = L.circleMarker([s.lat, s.lon], {
      radius: 9,
      color: "#1a1814",
      weight: 1,
      fillColor: s.color,
      fillOpacity: 0.95
    });
    m.bindPopup(
      `<strong>${s.station_name}</strong><br>${s.state}<br>` +
      `${s.level} (${Math.round((s.probability || 0) * 100)}%)<br>${s.advice}`
    );
    m.on("click", () => {
      const box = document.getElementById("feeds");
      if (box) box.textContent = JSON.stringify(s.feeds, null, 2);
    });
    layers.stations.addLayer(m);
  });

  state.assets.roads.forEach((r) => {
    const line = L.polyline(r.coords, { color: r.color, weight: 5, opacity: 0.9 });
    line.bindPopup(`<strong>${r.name}</strong><br>${r.status}`);
    layers.roads.addLayer(line);
  });

  state.assets.villages.forEach((v) => {
    const m = L.circleMarker([v.lat, v.lon], {
      radius: 6,
      fillColor: "#3d4f7a",
      color: "#1a1814",
      fillOpacity: 0.9
    });
    m.bindPopup(`${v.name}<br>${v.population} people · ${v.status}`);
    layers.villages.addLayer(m);
  });

  state.assets.infrastructure.forEach((i) => {
    const m = L.marker([i.lat, i.lon]);
    m.bindPopup(`${i.name} (${i.kind})<br>${i.status}`);
    layers.infra.addLayer(m);
  });

  (state.reports || []).forEach((r) => {
    const m = L.circleMarker([r.lat, r.lon], {
      radius: 7,
      fillColor: "#111",
      color: "#f3efe6",
      fillOpacity: 1
    });
    const media = r.media_path
      ? `<br><a href="/${r.media_path}" target="_blank">media</a>`
      : "";
    m.bindPopup(`${r.category} · ${r.reporter_role}<br>${r.note || ""}${media}`);
    layers.reports.addLayer(m);
  });

  Object.values(layers).forEach((g) => g.addTo(map));

  document.querySelectorAll("#layers input[data-layer]").forEach((box) => {
    box.addEventListener("change", () => {
      const layer = layers[box.getAttribute("data-layer")];
      if (box.checked) map.addLayer(layer);
      else map.removeLayer(layer);
    });
  });
  const satBox = document.getElementById("sat");
  if (satBox) {
    satBox.addEventListener("change", () => {
      if (satBox.checked) {
        map.removeLayer(osm);
        sat.addTo(map);
      } else {
        map.removeLayer(sat);
        osm.addTo(map);
      }
    });
  }
  return map;
}
