document.addEventListener("DOMContentLoaded", () => {
  const bookingsData = JSON.parse(document.getElementById("bookings-data").textContent);
  const earningsData = JSON.parse(document.getElementById("earnings-data").textContent);
  const areaData = JSON.parse(document.getElementById("area-data").textContent);

  if (bookingsData.length > 0) {
    new Chart(document.getElementById("bookingsChart"), {
      type: "line",
      data: {
        labels: bookingsData.map(b => b.month),
        datasets: [{
          label: "Bookings",
          data: bookingsData.map(b => b.count),
          borderColor: "#ff6600",
          backgroundColor: "rgba(255,102,0,0.2)",
          fill: true,
          tension: 0.4
        }]
      },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });
  }

  if (earningsData.length > 0) {
    new Chart(document.getElementById("earningsChart"), {
      type: "bar",
      data: {
        labels: earningsData.map(e => e.month),
        datasets: [{
          label: "Earnings",
          data: earningsData.map(e => e.total),
          backgroundColor: "#007bff",
          borderRadius: 6
        }]
      },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });
  }

  if (areaData.length > 0) {
    new Chart(document.getElementById("mechanicAreaChart"), {
      type: "doughnut",
      data: {
        labels: areaData.map(a => a.area),
        datasets: [{
          data: areaData.map(a => a.count),
          backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
        }]
      },
      options: { responsive: true }
    });
  }
});
// Smooth scroll for sidebar links
document.querySelectorAll('.sidebar nav a').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.sidebar nav a').forEach(a => a.classList.remove('active'));
    link.classList.add('active');

    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
document.addEventListener("DOMContentLoaded", () => {
  const bookingsData = JSON.parse(document.getElementById("bookings-data").textContent);
  const earningsData = JSON.parse(document.getElementById("earnings-data").textContent);
  const areaData = JSON.parse(document.getElementById("area-data").textContent);

  // Chart 1: Bookings
  const ctx1 = document.getElementById("bookingsChart");
  if (ctx1 && bookingsData.length) {
    new Chart(ctx1, {
      type: "line",
      data: {
        labels: bookingsData.map(b => b.month),
        datasets: [{
          label: "Bookings",
          data: bookingsData.map(b => b.count),
          borderColor: "#ff6600",
          backgroundColor: "rgba(255,102,0,0.3)",
          fill: true,
          tension: 0.4
        }]
      },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });
  }

  // Chart 2: Earnings
  const ctx2 = document.getElementById("earningsChart");
  if (ctx2 && earningsData.length) {
    new Chart(ctx2, {
      type: "bar",
      data: {
        labels: earningsData.map(e => e.month),
        datasets: [{
          label: "Earnings (₹)",
          data: earningsData.map(e => e.total),
          backgroundColor: "#007bff"
        }]
      },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });
  }

  // Chart 3: Area Distribution
  const ctx3 = document.getElementById("mechanicAreaChart");
  if (ctx3 && areaData.length) {
    new Chart(ctx3, {
      type: "doughnut",
      data: {
        labels: areaData.map(a => a.area),
        datasets: [{
          data: areaData.map(a => a.count),
          backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  }
});
