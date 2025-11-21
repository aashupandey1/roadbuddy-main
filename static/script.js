document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ RoadBuddy JS Loaded");

  // ===========================================================
  // LOGIN DROPDOWN
  // ===========================================================
  const toggle = document.getElementById("login-toggle");
  const dropdown = document.querySelector(".dropdown-content");

  if (toggle && dropdown) {
    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropdown.style.display =
        dropdown.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", (e) => {
      if (
        dropdown.style.display === "block" &&
        !dropdown.contains(e.target) &&
        !toggle.contains(e.target)
      ) {
        dropdown.style.display = "none";
      }
    });
  }

  // ===========================================================
  // AUTO +91 IN PHONE FIELD
  // ===========================================================
  const phoneInputs = document.querySelectorAll('input[type="tel"]');
  phoneInputs.forEach((input) => {
    input.addEventListener("blur", () => {
      let value = input.value.trim();
      if (value && !value.startsWith("+91")) {
        input.value = "+91" + value.replace(/^0+/, "");
      }
    });
  });

  // ===========================================================
  // SERVICE DETAILS MODAL
  // ===========================================================
  const modal = document.getElementById("service-modal");
  const closeModal = document.getElementById("close-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalText = document.getElementById("modal-text");

  const serviceDetails = {
    brake:
      "We provide full brake inspection, pad replacements, rotor resurfacing, and brake fluid top-ups to ensure your safety.",
    engine:
      "We offer engine diagnostics, tuning, oil change, and maintenance to keep your engine running smoothly and efficiently.",
    tire:
      "We handle tire repairs, balancing, alignment, and replacements to ensure a smooth and safe ride.",
    cooling:
      "Professional cooling system maintenance, radiator cleaning, coolant refilling, and leak inspection to prevent overheating.",
    battery:
      "Quick battery checks, replacements, and maintenance for reliable starting power every time.",
    steering:
      "Comprehensive steering and suspension repairs, fluid top-ups, and wheel alignment for better control.",
  };

  const serviceLinks = document.querySelectorAll(".details-link");
  serviceLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const key = link.dataset.service;
      if (!modal || !modalTitle || !modalText) return;
      modalTitle.textContent = link.textContent || "Service Details";
      modalText.textContent =
        serviceDetails[key] || "Details not available at this time.";
      modal.style.display = "flex";
    });
  });

  if (modal && closeModal) {
    closeModal.addEventListener("click", () => (modal.style.display = "none"));
    window.addEventListener("click", (e) => {
      if (e.target === modal) modal.style.display = "none";
    });
  }

  // ===========================================================
  // GET SERVICE MODAL (FAKE PAYMENT FLOW)
  // ===========================================================
  const serviceModal = document.getElementById("serviceModal");
  const openBtn = document.getElementById("getServiceBtn");
  const closeBtn = document.querySelector(".close-btn");
  const serviceForm = document.getElementById("serviceForm");
  const paymentSection = document.getElementById("paymentSection");
  const receiptSection = document.getElementById("receiptSection");
  const payNowBtn = document.getElementById("payNowBtn");
  const paymentDetails = document.getElementById("paymentDetails");
  const receiptText = document.getElementById("receiptText");
  const closeReceipt = document.getElementById("closeReceipt");

  if (openBtn && serviceModal) {
    openBtn.addEventListener("click", (e) => {
      e.preventDefault();
      serviceModal.style.display = "flex";
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      resetModal(serviceForm, paymentSection, receiptSection, serviceModal);
    });
  }

  if (serviceForm) {
    serviceForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = new FormData(serviceForm);
      const name = data.get("name") || "Customer";
      const service = data.get("service_type") || "Unknown Service";
      const amount = data.get("amount") || "0";

      serviceForm.style.display = "none";
      paymentSection.style.display = "block";
      paymentDetails.innerHTML = `
        <strong>Name:</strong> ${name}<br>
        <strong>Service:</strong> ${service}<br>
        <strong>Amount:</strong> ₹${amount}
      `;
    });
  }

  if (payNowBtn) {
    payNowBtn.addEventListener("click", () => {
      paymentSection.style.display = "none";
      receiptSection.style.display = "block";
      const now = new Date();
      const time = now.toLocaleString();
      const txId = `RB-${Math.floor(Math.random() * 1000000)}`;
      receiptText.innerHTML = `
        ✅ <strong>Payment Successful!</strong><br><br>
        Date & Time: ${time}<br>
        <strong>Transaction ID:</strong> ${txId}<br>
      `;
    });
  }

  if (closeReceipt) {
    closeReceipt.addEventListener("click", () => {
      resetModal(serviceForm, paymentSection, receiptSection, serviceModal);
    });
  }

  // ===========================================================
  // AFFORDABLE PLAN PAYMENT FLOW
  // ===========================================================
  const bookingModal = document.getElementById("bookingModal");
  const bookingClose = document.getElementById("bookingClose");
  const bookingForm = document.getElementById("bookingForm");
  const bookingStep = document.getElementById("bookingStep");
  const paymentStep = document.getElementById("paymentStep");
  const receiptStep = document.getElementById("receiptStep");
  const planNameEl = document.getElementById("planName");
  const planInput = document.getElementById("planInput");
  const amountInput = document.getElementById("amountInput");
  const amountDisplay = document.getElementById("amountDisplay");
  const paySummary = document.getElementById("paySummary");
  const backToForm = document.getElementById("backToForm");
  const planPayBtn = document.querySelector("#paymentStep #payNowBtn");
  const receiptContent = document.getElementById("receiptContent");
  const welcomeMsg = document.getElementById("welcomeMsg");
  const closeReceiptBtn = document.getElementById("closeReceiptBtn");
  const printReceiptBtn = document.getElementById("printReceiptBtn");

  const planButtons = document.querySelectorAll(".pricing-start");
  planButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const plan = btn.dataset.plan || "Custom Plan";
      const amount = btn.dataset.amount || "0";
      if (!bookingModal) return;

      planNameEl.textContent = plan;
      planInput.value = plan;
      amountInput.value = amount;
      amountDisplay.value = amount;

      bookingStep.style.display = "block";
      paymentStep.style.display = "none";
      receiptStep.style.display = "none";
      bookingModal.style.display = "flex";
    });
  });

  if (bookingClose) {
    bookingClose.addEventListener("click", () => {
      closeModalReset(bookingModal, bookingForm);
    });
  }

  if (bookingForm) {
    bookingForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = new FormData(bookingForm);
      const name = data.get("name");
      const plan = data.get("plan");
      const amount = data.get("amount");

      paySummary.innerHTML = `<strong>${name}</strong>, you're booking <strong>${plan}</strong> for <strong>₹${amount}</strong>.`;

      bookingStep.style.display = "none";
      paymentStep.style.display = "block";
    });
  }

  if (backToForm) {
    backToForm.addEventListener("click", (e) => {
      e.preventDefault();
      paymentStep.style.display = "none";
      bookingStep.style.display = "block";
    });
  }

  if (planPayBtn) {
    planPayBtn.addEventListener("click", () => {
      const name = document.getElementById("custName").value || "Customer";
      const phone = document.getElementById("custPhone").value || "N/A";
      const plan = planInput.value;
      const amount = amountInput.value;
      const txId = "RB-" + Math.floor(100000 + Math.random() * 900000);

      const expiryDate = new Date();
      expiryDate.setMonth(expiryDate.getMonth() + 1);
      const formattedExpiry = expiryDate.toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });

      paymentStep.style.display = "none";
      receiptStep.style.display = "block";

      receiptContent.innerHTML = `
        <p><strong>Transaction ID:</strong> ${txId}</p>
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Phone:</strong> ${phone}</p>
        <p><strong>Service Plan:</strong> ${plan}</p>
        <p><strong>Amount Paid:</strong> ₹${amount}</p>
        <p><strong>Membership valid till:</strong> ${formattedExpiry}</p>
      `;

      welcomeMsg.textContent = `✅ Welcome to RoadBuddy, ${name}! Your plan is active till ${formattedExpiry}`;
    });
  }

  if (closeReceiptBtn) {
    closeReceiptBtn.addEventListener("click", () => {
      closeModalReset(bookingModal, bookingForm);
    });
  }

  if (printReceiptBtn) {
    printReceiptBtn.addEventListener("click", () => {
      const printWindow = window.open("", "_blank", "width=600,height=700");
      printWindow.document.write(`
        <html><head><title>RoadBuddy Receipt</title></head>
        <body style="background:#111;color:#fff;font-family:sans-serif;padding:20px;">
          <h2 style="color:#ff8a00;">ROADBUDDY RECEIPT</h2>
          ${receiptContent.innerHTML}
          <p style="margin-top:20px;color:#ffd7a6;">${welcomeMsg.textContent}</p>
        </body></html>
      `);
      printWindow.document.close();
      printWindow.print();
    });
  }

  // Close modal when clicking outside
  window.addEventListener("click", (e) => {
    if (e.target === bookingModal) {
      closeModalReset(bookingModal, bookingForm);
    }
  });

  // ===========================================================
  // HELPER FUNCTIONS
  // ===========================================================
  function resetModal(form, paySection, receiptSection, modal) {
    if (!form || !modal) return;
    form.style.display = "block";
    form.reset();
    if (paySection) paySection.style.display = "none";
    if (receiptSection) receiptSection.style.display = "none";
    modal.style.display = "none";
  }

  function closeModalReset(modal, form) {
    if (modal) modal.style.display = "none";
    if (form) form.reset();
  }
});

// chatbot //
// === Chatbot Toggle & Messaging ===
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("chatbot-btn");
  const popup = document.getElementById("chatbot-popup");
  const sendBtn = document.getElementById("send-btn");
  const input = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-output");

  let isOpen = false; // 👈 Track chatbot state manually

  // ✅ Chatbot open/close toggle + greeting message
  btn.addEventListener("click", () => {
    if (isOpen) {
      // 👇 Close chatbot
      popup.style.opacity = "0";
      popup.style.transform = "translateY(20px)";
      setTimeout(() => {
        popup.style.display = "none";
      }, 200);
      isOpen = false;
    } else {
      // 👇 Open chatbot
      popup.style.display = "block";
      setTimeout(() => {
        popup.style.opacity = "1";
        popup.style.transform = "translateY(0)";
      }, 10);
      if (chatBox.innerHTML.trim() === "") {
        chatBox.innerHTML = `<div style='margin:6px 0; text-align:left; color:#222;'>Bot:</b> Hi! 👋 I'm your RoadBuddy assistant. How can I help you today?</div>`;
      }
      isOpen = true;
    }
  });

  // ✅ Send message function
  const sendMessage = async () => {
    const msg = input.value.trim();
    if (!msg) return;

    chatBox.innerHTML += `<div style='margin:6px 0; text-align:right; color:#007bff;'><b>You:</b> ${msg}</div>`;
    input.value = "";

    try {
      const res = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: "9999999999", text: msg })
      });
      const data = await res.json();
      chatBox.innerHTML += `<div style='margin:6px 0; text-align:left; color:#222;'><b>Bot:</b> ${data.reply}</div>`;
    } catch (err) {
      chatBox.innerHTML += `<div style='color:red;'>Error: ${err.message}</div>`;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
  };

  // ✅ Send button click
  sendBtn.addEventListener("click", sendMessage);

  // ✅ Press Enter to send
  input.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });
});