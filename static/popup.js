// -----------------------------
// popup.js — RoadBuddy FINAL (2025)
// -----------------------------

let selectedRole = "";

// Prevent accidental page reload from form submits
document.addEventListener("submit", (e) => e.preventDefault());

// -----------------------------
// MAIN FLOW — DOM Ready
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("overlay");
  const rolePopup = document.getElementById("rolePopup");
  const otpPopup = document.getElementById("otpPopup");
  const verifyForm = document.getElementById("verifyOtpForm");
  const userBtn = document.getElementById("userBtn");
  const mechanicBtn = document.getElementById("mechanicBtn");
  const otpBtn = document.getElementById("getOtpBtn");
  const emailInput = document.getElementById("emailInput");

  // ✅ Show popup only once per session
  if (!sessionStorage.getItem("popupShown") && overlay && rolePopup) {
    overlay.classList.add("active");
    rolePopup.classList.add("active");
    document.body.classList.add("popup-active");
  }

  // ✅ Role button listeners
  if (userBtn) userBtn.addEventListener("click", () => selectRole("user"));
  if (mechanicBtn) mechanicBtn.addEventListener("click", () => selectRole("mechanic"));

  // ✅ OTP button listener
  if (otpBtn) otpBtn.addEventListener("click", generateOTP);

  // ✅ OTP form submit listener
  if (verifyForm) verifyForm.addEventListener("submit", verifyOtpHandler);

  // ✅ Autofocus on email when OTP popup opens
  if (emailInput) emailInput.focus();
});

// -----------------------------
// STEP 2: SELECT ROLE
// -----------------------------
function selectRole(role) {
  selectedRole = role;

  const overlay = document.getElementById("overlay");
  const rolePopup = document.getElementById("rolePopup");
  const otpPopup = document.getElementById("otpPopup");
  const title = document.getElementById("roleTitle");
  const emailInput = document.getElementById("emailInput");

  if (rolePopup && otpPopup && overlay && title) {
    rolePopup.classList.remove("active");
    otpPopup.classList.add("active");
    overlay.classList.add("active");
    document.body.classList.add("popup-active");
    title.innerText = `LOGIN AS ${role === "user" ? "USER" : "MECHANIC"}`;
    if (emailInput) emailInput.focus();
  } else {
    console.error("Popup elements not found in DOM!");
  }
}

// -----------------------------
// STEP 3: GENERATE OTP
// -----------------------------
async function generateOTP() {
  const emailInput = document.getElementById("emailInput");
  const btn = document.getElementById("getOtpBtn");

  if (!emailInput || !btn) return;

  const email = emailInput.value.trim();
  if (!email || !email.includes("@")) {
    alert("⚠️ Please enter a valid email address.");
    emailInput.focus();
    return;
  }

  btn.disabled = true;
  btn.innerText = "Sending...";

  try {
    const formData = new FormData();
    formData.append("email", email);
    formData.append("role", selectedRole);

    const response = await fetch("/send_otp_email", {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ OTP sent to your email!");
      emailInput.disabled = true; // prevent change after OTP sent
      document.getElementById("otpForm").style.display = "none";
      document.getElementById("verifyOtpForm").style.display = "flex";
      document.getElementById("otpInput")?.focus();
    } else {
      alert("❌ " + (data.message || "Failed to send OTP."));
    }
  } catch (err) {
    console.error("OTP send error:", err);
    alert("❌ Server error while sending OTP. Please check backend logs.");
  } finally {
    btn.disabled = false;
    btn.innerText = "Get OTP";
  }
}

// -----------------------------
// STEP 4: VERIFY OTP HANDLER
// -----------------------------
async function verifyOtpHandler(e) {
  e.preventDefault();

  const otpInput = document.getElementById("otpInput");
  const emailInput = document.getElementById("emailInput");
  const verifyBtn = document.getElementById("verifyOtpBtn");

  const otp = otpInput?.value.trim();
  const email = emailInput?.value.trim();

  if (!otp) {
    alert("⚠️ Please enter the OTP.");
    otpInput.focus();
    return;
  }

  verifyBtn.disabled = true;
  verifyBtn.innerText = "Verifying...";

  try {
    const formData = new FormData();
    formData.append("otp", otp);
    formData.append("email", email);
    formData.append("role", selectedRole);

    const response = await fetch("/verify_otp_email", {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ OTP Verified Successfully!");

      // Hide popups & overlay
      document.getElementById("otpPopup")?.classList.remove("active");
      document.getElementById("rolePopup")?.classList.remove("active");
      document.getElementById("overlay")?.classList.remove("active");
      document.body.classList.remove("popup-active");

      // Remember session
      sessionStorage.setItem("popupShown", "true");

      // Redirect logic
      if (data.redirect) {
        window.location.href = data.redirect;
      } else if (selectedRole === "user") {
        window.location.href = "/";
      } else {
        window.location.href = "/mechanic_profile";
      }
    } else {
      alert("❌ " + (data.message || "Invalid OTP."));
    }
  } catch (err) {
    console.error("OTP verify error:", err);
    alert("❌ Server error during verification.");
  } finally {
    verifyBtn.disabled = false;
    verifyBtn.innerText = "Verify OTP";
  }
}