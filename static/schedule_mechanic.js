console.log("schedule_mechanic.js loaded");

// Make Get Location work ONLY for schedule page
document.addEventListener("DOMContentLoaded", () => {
    const detectBtn = document.getElementById("detectLocationBtn");
    const addressInput = document.getElementById("address");

    if (detectBtn) {
        detectBtn.addEventListener("click", () => {
            addressInput.value = "Detecting your location...";

            if (!navigator.geolocation) {
                addressInput.value = "Geolocation not supported.";
                return;
            }

            navigator.geolocation.getCurrentPosition(success, error);

            function success(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                fetch(`/api/reverse_geocode?lat=${lat}&lon=${lng}`)
                    .then(res => res.json())
                    .then(data => {
                        addressInput.value =
                            data.display_name || `${lat}, ${lng}`;
                    })
                    .catch(() => {
                        addressInput.value = `${lat}, ${lng}`;
                    });
            }

            function error() {
                addressInput.value = "Unable to detect. Please type manually.";
            }
        });
    }

    // Debug: Track form submission
    const form = document.getElementById("scheduleForm");
    form.addEventListener("submit", () => {
        console.log("FORM SUBMITTED!");
    });
});
