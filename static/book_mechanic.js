console.log("book_mechanic.js is loaded correctly");

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded");

  const addressInput = document.getElementById("address");
  const detectBtn = document.getElementById("detectLocationBtn");
  const bookBtn = document.getElementById("bookNowBtn");
  const latInput = document.getElementById("lat");
  const lngInput = document.getElementById("lng");

  function setBookBtnState() {
    const address = addressInput?.value.trim() || "";
    const enabled = address !== "" && address !== "Detecting your location...";
    if (bookBtn) {
        bookBtn.disabled = !enabled;
        bookBtn.style.opacity = enabled ? "1" : "0.6";
    }
  }

  if (addressInput) {
    addressInput.removeAttribute("readonly");
    addressInput.addEventListener("input", () => {
      if(latInput) latInput.value = "";
      if(lngInput) lngInput.value = "";
      setBookBtnState();
    });
  }

  setBookBtnState();

  // Detect Location
  if (detectBtn) {
    detectBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        addressInput.value = "Geolocation not supported.";
        setBookBtnState();
        return;
      }

      addressInput.value = "Detecting your location...";
      setBookBtnState();

      navigator.geolocation.getCurrentPosition(success, error, {
        enableHighAccuracy: true,
        timeout: 12000,
      });

      function success(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        if(latInput) latInput.value = lat;
        if(lngInput) lngInput.value = lon;

        fetch(`/api/reverse_geocode?lat=${lat}&lon=${lon}`)
          .then((res) => res.json())
          .then((data) => {
            addressInput.value = data?.display_name || `${lat}, ${lon}`;
            setBookBtnState();
          })
          .catch(() => {
            addressInput.value = `${lat}, ${lon}`;
            setBookBtnState();
          });
      }

      function error() {
        addressInput.value =
          "Unable to fetch location. Please type address manually.";
        setBookBtnState();
      }
    });
  }

  // ⭐⭐⭐ FIXED PART — REAL EMERGENCY BOOKING ⭐⭐⭐
  if (bookBtn) {
      bookBtn.addEventListener("click", async (e) => {
        e.preventDefault();

        const fullname = document.getElementById("name").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const vehicle = document.getElementById("vehicle").value.trim();
        const problem = document.getElementById("service_type").value.trim();
        const address = addressInput.value.trim();
        const lat = latInput ? latInput.value : "0";
        const lng = lngInput ? lngInput.value : "0";

        if (!fullname || !phone || !vehicle || !problem || !address) {
          showPopup("⚠️ Please fill all required fields!", "error");
          return;
        }

        bookBtn.disabled = true;
        const oldText = bookBtn.innerText;
        bookBtn.innerText = "Booking...";

        try {
          const formData = new FormData();
          formData.append("name", fullname);
          formData.append("phone", phone);
          formData.append("vehicle", vehicle);
          formData.append("address", address);
          formData.append("lat", lat);
          formData.append("lng", lng);
          formData.append("service_type", problem);

          // ⭐ SEND TO FLASK ⭐
          const resp = await fetch("/process_booking", {
            method: "POST",
            body: formData,
          });
          
          // ✅ FIX: Check if request was successful
          // Flask redirect karta hai, toh resp.url mein naya URL (success page) aa jata hai
          if (resp.ok) {
              // Browser ko naye URL par bhejo
              window.location.href = resp.url;
              return;
          }

          showPopup("⚠️ Server error. Could not book.", "error");

        } catch (err) {
          console.error(err);
          showPopup("⚠️ Connection error. Try again.", "error");
        } finally {
          bookBtn.disabled = false;
          bookBtn.innerText = oldText;
          setBookBtnState();
        }
      });
  }
});

// Popup message function
function showPopup(message, type = "success") {
  const popup = document.createElement("div");
  popup.style.position = "fixed";
  popup.style.bottom = "26px";
  popup.style.right = "26px";
  popup.style.padding = "12px 18px";
  popup.style.borderRadius = "10px";
  popup.style.zIndex = 99999;
  popup.style.fontSize = "15px";
  popup.style.color = "#fff";
  popup.style.background = type === "error" ? "#e74c3c" : "#28a745";
  popup.textContent = message;

  document.body.appendChild(popup);

  setTimeout(() => {
    popup.style.opacity = "0";
    popup.style.transition = "opacity 0.35s ease";
    setTimeout(() => popup.remove(), 400);
  }, 2300);
}