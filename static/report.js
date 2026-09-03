const QUEUE_KEY = "ner-report-queue";

function queue() {
  return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
}
function saveQueue(items) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
}

function setNet() {
  const el = document.getElementById("net");
  if (!el) return;
  el.textContent = navigator.onLine
    ? "Online — reports go to the server (and any queued items will sync)."
    : "Low / no network — this report will stay on the phone until you reconnect.";
  el.className = "net " + (navigator.onLine ? "ok" : "off");
}

async function flushQueue() {
  if (!navigator.onLine) return;
  const items = queue();
  if (!items.length) return;
  const res = await fetch("/api/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reports: items })
  });
  if (res.ok) saveQueue([]);
}

async function refreshList() {
  const ul = document.getElementById("report-list");
  if (!ul) return;
  try {
    const data = await (await fetch("/api/reports")).json();
    ul.innerHTML = data
      .map(
        (r) =>
          `<li>${r.category} · ${r.reporter_role} · ${Number(r.lat).toFixed(3)}, ${Number(r.lon).toFixed(3)} — ${r.note || ""}</li>`
      )
      .join("") || "<li>None yet.</li>";
  } catch {
    ul.innerHTML = "<li>Could not load server list (offline). Local queue: " + queue().length + "</li>";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setNet();
  window.addEventListener("online", () => {
    setNet();
    flushQueue().then(refreshList);
  });
  window.addEventListener("offline", setNet);
  flushQueue().then(refreshList);

  const geoBtn = document.getElementById("geo");
  if (geoBtn) {
    geoBtn.addEventListener("click", () => {
      navigator.geolocation.getCurrentPosition((pos) => {
        document.getElementById("lat").value = pos.coords.latitude.toFixed(5);
        document.getElementById("lon").value = pos.coords.longitude.toFixed(5);
      });
    });
  }

  const form = document.getElementById("report-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("form-status");
    const fd = new FormData(form);
    fd.set("client_id", crypto.randomUUID());
    const file = form.querySelector('input[type="file"]').files[0];

    if (!navigator.onLine || (file && !navigator.onLine)) {
      if (file) {
        status.textContent = "Photo needs a network hop. Saved text report locally; retry photo when online.";
      }
      const item = {
        id: fd.get("client_id"),
        reporter_role: fd.get("reporter_role"),
        category: fd.get("category"),
        lat: Number(fd.get("lat")),
        lon: Number(fd.get("lon")),
        note: fd.get("note"),
        client_id: fd.get("client_id")
      };
      saveQueue(queue().concat(item));
      status.textContent = (status.textContent || "") + " Queued on this device.";
      return;
    }

    const res = await fetch("/api/reports", { method: "POST", body: fd });
    if (res.ok) {
      status.textContent = "Report received by the platform.";
      form.reset();
      refreshList();
    } else {
      status.textContent = "Server error — queued locally.";
      saveQueue(
        queue().concat({
          id: fd.get("client_id"),
          reporter_role: fd.get("reporter_role"),
          category: fd.get("category"),
          lat: Number(fd.get("lat")),
          lon: Number(fd.get("lon")),
          note: fd.get("note"),
          client_id: fd.get("client_id")
        })
      );
    }
  });
});
