const map = L.map('map').setView([28.6139, 77.2090], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const chargerIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/484/484167.png',
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -28]
});

let allStations = []; // to store fetched data

function loadEVStations(lat, lon) {
  fetch(`/api/ev_stations?lat=${lat}&lon=${lon}`)
    .then(res => res.json())
    .then(data => {
      allStations = data;
      updateMapAndList();
    })
    .catch(err => {
      console.error("Error fetching EV stations:", err);
      document.getElementById('stations').innerHTML =
        "<li>⚠ Unable to load EV stations. Please try again later.</li>";
    });
}

function updateMapAndList() {
  const list = document.getElementById('stations');
  list.innerHTML = "";

  const showFast = document.getElementById('filter-fast').checked;
  const showDC = document.getElementById('filter-dc').checked;

  map.eachLayer(layer => {
    if (layer instanceof L.Marker && !layer._icon.classList.contains('leaflet-control')) {
      map.removeLayer(layer);
    }
  });

  // Re-add user marker (optional)
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      const lat = pos.coords.latitude, lon = pos.coords.longitude;
      L.marker([lat, lon]).addTo(map).bindPopup("📍 You are here").openPopup();
    });
  }

  let visibleCount = 0;

  allStations.forEach(st => {
    const info = st.AddressInfo || {};
    const name = info.Title || "EV Charging Station";
    const address = info.AddressLine1 || "Address not available";
    const stationLat = info.Latitude;
    const stationLon = info.Longitude;

    const conn = st.Connections && st.Connections[0];
    const currentType = conn?.CurrentType?.Title || "Unknown";
    const level = conn?.Level?.Title || "Unknown";
    const powerKW = conn?.PowerKW || 0;

    const isFast = powerKW >= 22; // 22kW+ = fast charger
    const isDC = currentType.toLowerCase().includes("dc");

    if (showFast && !isFast) return;
    if (showDC && !isDC) return;

    visibleCount++;

    // Marker
    L.marker([stationLat, stationLon], { icon: chargerIcon })
      .addTo(map)
      .bindPopup(`
        <b>${name}</b><br>${address}<br>
        ⚡ Type: <b>${currentType}</b><br>
        🚀 Speed: ${isFast ? "<b style='color:green'>Fast</b>" : "Normal"}<br>
        🔋 Power: ${powerKW} kW<br>
        <a href="https://www.google.com/maps/dir/?api=1&destination=${stationLat},${stationLon}" target="_blank">
          🧭 Get Directions
        </a>
      `);

    // Sidebar list
    const li = document.createElement('li');
    li.innerHTML = `
      <b>${name}</b><br>
      <small>${address}</small><br>
      ⚡ <b>${currentType}</b><br>
      🚀 ${isFast ? "<b style='color:green'>Fast Charger</b>" : "Normal Charger"}<br>
      🔋 ${powerKW} kW<br>
      <a href="https://www.google.com/maps/dir/?api=1&destination=${stationLat},${stationLon}" target="_blank">
        Get Directions
      </a>
    `;
    list.appendChild(li);
  });

  if (visibleCount === 0) {
    list.innerHTML = "<li>⚠ No chargers match your filter.</li>";
  }
}

// Get user's live location
navigator.geolocation.getCurrentPosition(pos => {
  const lat = pos.coords.latitude;
  const lon = pos.coords.longitude;
  map.setView([lat, lon], 13);
  loadEVStations(lat, lon);
}, () => {
  alert("Please allow location access or use search.");
});

// Search location
document.getElementById('search-form').addEventListener('submit', e => {
  e.preventDefault();
  const query = document.getElementById('search-input').value.trim();
  if (!query) return;

  fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(locations => {
      if (locations.length === 0) {
        alert("Location not found. Try again.");
        return;
      }
      const lat = parseFloat(locations[0].lat);
      const lon = parseFloat(locations[0].lon);
      map.setView([lat, lon], 13);
      loadEVStations(lat, lon);
    });
});

// Filter checkboxes update dynamically
document.getElementById('filter-fast').addEventListener('change', updateMapAndList);
document.getElementById('filter-dc').addEventListener('change', updateMapAndList);
