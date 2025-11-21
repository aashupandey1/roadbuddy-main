// -----------------------------
// profile.js — RoadBuddy Final Version (Fixed)
// -----------------------------

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Profile JS Loaded");

  const photoInput = document.getElementById("photo");
  const imgPreview = document.getElementById("preview-photo");
  const nameInput = document.getElementById("name");
  const previewName = document.getElementById("preview-name");
  const form =
    document.getElementById("user-profile-form") ||
    document.getElementById("mechanic-profile-form");
  const toast = document.getElementById("toast");

  // ===========================================================
  // LIVE PHOTO PREVIEW
  // ===========================================================
  if (photoInput && imgPreview) {
    photoInput.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          imgPreview.src = event.target.result;
          imgPreview.hidden = false;
        };
        reader.readAsDataURL(file);
      } else {
        imgPreview.hidden = true;
      }
    });
  }

  // ===========================================================
  // LIVE NAME PREVIEW
  // ===========================================================
  if (nameInput && previewName) {
    nameInput.addEventListener("input", (e) => {
      previewName.textContent = e.target.value.trim() || "Your name";
    });
  }

  // ===========================================================
  // TOAST (FLASH MESSAGE) ANIMATION
  // ===========================================================
  if (toast) {
    // Support multiple toasts from Flask flash messages
    const toasts = document.querySelectorAll("#toast");
    toasts.forEach((t) => {
      setTimeout(() => t.classList.add("show"), 200);
      setTimeout(() => {
        t.classList.remove("show");
        setTimeout(() => t.remove(), 400);
      }, 3000);
    });
  }

  // ===========================================================
  // FORM SUBMISSION (Visual Feedback + Client Validation)
  // ===========================================================
  if (form) {
    form.addEventListener("submit", (e) => {
      const requiredFields = form.querySelectorAll("[required]");
      for (let field of requiredFields) {
        if (!field.value.trim()) {
          e.preventDefault();
          alert("⚠️ Please fill all required fields before saving.");
          field.focus();
          return;
        }
      }

      // Optional UI feedback
      const saveBtn = form.querySelector(".btn.primary");
      if (saveBtn) {
        saveBtn.disabled = true;
        const originalText = saveBtn.textContent;
        saveBtn.textContent = "Saving...";
        // Re-enable button automatically (Flask reloads page soon anyway)
        setTimeout(() => {
          saveBtn.textContent = originalText;
          saveBtn.disabled = false;
        }, 2500);
      }
    });
  }

  // ===========================================================
  // BACK TO HOME (optional: safety net if button has class .back-home)
  // ===========================================================
  const backHomeBtn = document.querySelector(".btn.ghost");
  if (backHomeBtn) {
    backHomeBtn.addEventListener("click", (e) => {
      // Prevent double-click issues
      e.target.disabled = true;
      setTimeout(() => (window.location.href = "/"), 200);
    });
  }
});