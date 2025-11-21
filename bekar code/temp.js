document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('login-toggle');
    const dropdown = document.querySelector('.dropdown-content');

    // --- LOGIN DROPDOWN LOGIC (same as before) ---
    toggle.addEventListener('click', function(e) {
        e.preventDefault();
        dropdown.style.display = (dropdown.style.display === 'block') ? 'none' : 'block';
        e.stopPropagation();
    });

    dropdown.addEventListener('click', function(e) {
        dropdown.style.display = 'none';
        e.stopPropagation();
    });

    document.addEventListener('click', function(e) {
        if (!toggle.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // --- AUTO +91 LOGIC (SMART VERSION) ---
    const phoneInput = document.getElementById('phone');
    const form = phoneInput ? phoneInput.closest('form') : null;

    if (form && phoneInput) {
        form.addEventListener('submit', function() {
            let value = phoneInput.value.trim();

            // Agar field empty nahi hai aur +91 missing hai
            if (value && !value.startsWith('+91')) {
                phoneInput.value = '+91' + value;
            }
        });
    }
});

//our services ---adding details 
const modal = document.getElementById("service-modal");
const closeModal = document.getElementById("close-modal");
const modalTitle = document.getElementById("modal-title");
const modalText = document.getElementById("modal-text");

const serviceDetails = {
  brake: "We provide full brake inspection, pad replacements, rotor resurfacing, and brake fluid top-ups to ensure your safety.",
  engine: "We offer engine diagnostics, tuning, oil change, and maintenance to keep your engine running smoothly and efficiently.",
  tire: "We handle tire repairs, balancing, alignment, and replacements to ensure a smooth and safe ride.",
  cooling: "Professional cooling system maintenance, radiator cleaning, coolant refilling, and leak inspection to prevent overheating.",
  battery: "Quick battery checks, replacements, and maintenance for reliable starting power every time.",
  steering: "Comprehensive steering and suspension repairs, fluid top-ups, and wheel alignment for better control."
};

// Open modal on click
document.querySelectorAll(".details-link").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();

    const serviceKey = link.getAttribute("data-service");
    modalTitle.textContent = link.previousElementSibling.previousElementSibling.textContent;
    modalText.textContent = serviceDetails[serviceKey];

    modal.style.display = "flex";
  });
});

// Close modal on click (X button)
closeModal.addEventListener("click", () => {
  modal.style.display = "none";
});

// Close modal if clicking outside content
window.addEventListener("click", e => {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});


//Working of GET SERVICES BUTTON //
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("serviceModal");
  const openBtn = document.getElementById("getServiceBtn");
  const closeBtn = document.querySelector(".close-btn");
  const form = document.getElementById("serviceForm");
  const paymentSection = document.getElementById("paymentSection");
  const receiptSection = document.getElementById("receiptSection");
  const payNowBtn = document.getElementById("payNowBtn");
  const paymentDetails = document.getElementById("paymentDetails");
  const receiptText = document.getElementById("receiptText");
  const closeReceipt = document.getElementById("closeReceipt");

  // Open modal
  openBtn.addEventListener("click", (e) => {
    e.preventDefault();
    modal.style.display = "flex";
  });

  // Close modal
  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
    form.reset();
    paymentSection.style.display = "none";
    receiptSection.style.display = "none";
  });

  // Step 1: Fill form → go to fake payment
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const name = data.get("name");
    const service = data.get("service_type");
    const amount = data.get("amount");

    form.style.display = "none";
    paymentSection.style.display = "block";
    paymentDetails.innerHTML = `
      <strong>Name:</strong> ${name}<br>
      <strong>Service:</strong> ${service}<br>
      <strong>Amount:</strong> ₹${amount}
    `;
  });

  // Step 2: Fake payment success
  payNowBtn.addEventListener("click", () => {
    paymentSection.style.display = "none";
    receiptSection.style.display = "block";

    const now = new Date();
    const time = now.toLocaleString();

    receiptText.innerHTML = `
      ✅ <strong>Payment Successful!</strong><br><br>
      Date & Time: ${time}<br>
      <strong>Transaction ID:</strong> RB-${Math.floor(Math.random() * 100000)}<br>
    `;
  });

  // Step 3: Close receipt
  closeReceipt.addEventListener("click", () => {
    modal.style.display = "none";
    form.style.display = "block";
    form.reset();
    receiptSection.style.display = "none";
  });
});



// AFFORDABLE PLAN PAYMENT  //

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const modal = document.getElementById("bookingModal");
  const closeBtn = document.getElementById("bookingClose");
  const bookingForm = document.getElementById("bookingForm");
  const bookingStep = document.getElementById("bookingStep");
  const paymentStep = document.getElementById("paymentStep");
  const receiptStep = document.getElementById("receiptStep");
  const planNameEl = document.getElementById("planName");
  const planInput = document.getElementById("planInput");
  const amountInput = document.getElementById("amountInput");
  const amountDisplay = document.getElementById("amountDisplay");
  const paySummary = document.getElementById("paySummary");
  const payNowBtn = document.getElementById("payNowBtn");
  const backToForm = document.getElementById("backToForm");
  const receiptContent = document.getElementById("receiptContent");
  const welcomeMsg = document.getElementById("welcomeMsg");
  const closeReceiptBtn = document.getElementById("closeReceiptBtn");
  const printReceiptBtn = document.getElementById("printReceiptBtn");

  // open modal when clicking Pricing GET STARTED buttons
  document.querySelectorAll(".pricing-start").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const plan = btn.dataset.plan || "Plan";
      const amount = btn.dataset.amount || "0";

      planNameEl.textContent = plan;
      planInput.value = plan;
      amountInput.value = amount;
      amountDisplay.value = amount;

      // show booking form
      bookingStep.style.display = "block";
      paymentStep.style.display = "none";
      receiptStep.style.display = "none";

      modal.setAttribute("aria-hidden", "false");
    });
  });

  // close modal
  closeBtn.addEventListener("click", () => {
    modal.setAttribute("aria-hidden", "true");
    bookingForm.reset();
  });

  // booking form submit -> go to payment step
  bookingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const form = new FormData(bookingForm);
    const name = form.get("name");
    const plan = form.get("plan");
    const amount = form.get("amount");

    // Fill summary for payment
    paySummary.innerHTML = `<strong>${name}</strong>, you're booking <strong>${plan}</strong> for <strong>₹${amount}</strong>.`;
    bookingStep.style.display = "none";
    paymentStep.style.display = "block";
  });

  // back to form
  backToForm.addEventListener("click", () => {
    paymentStep.style.display = "none";
    bookingStep.style.display = "block";
  });

  // fake pay now -> show receipt
  payNowBtn.addEventListener("click", () => {
    // Gather details
    const name = document.getElementById("custName").value || "Customer";
    const phone = document.getElementById("custPhone").value || "";
    const address = document.getElementById("custAddress").value || "";
    const car = document.getElementById("custCar").value || "";
    const date = document.getElementById("custDate").value || "";
    const time = document.getElementById("custTime").value || "";
    const plan = planInput.value || "";
    const amount = amountInput.value || "0";
    const txid = `RB-${Math.floor(Math.random() * 900000) + 100000}`;


    // build receipt HTML
    receiptContent.innerHTML = `
      <p><strong>Transaction ID:</strong> ${txid}</p>
      <p><strong>Name:</strong> ${name}</p>
      <p><strong>Phone:</strong> ${phone}</p>
      <p><strong>Address:</strong> ${address}</p>
      <p><strong>Car Model:</strong> ${car}</p>
      <p><strong>Service:</strong> ${plan}</p>
      <p><strong>Amount Paid:</strong> ₹${amount}</p>
      <p><strong>Scheduled:</strong> ${date} ${time}</p>
    `;

    welcomeMsg.textContent = `Welcome to ROADBUDDY, ${name}! You're now part of our family — we'll contact you to confirm details.`;

    paymentStep.style.display = "none";
    receiptStep.style.display = "block";

    // OPTIONAL: send booking to server (uncomment and adapt to your endpoint)
    /*
    fetch('/get-service', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name, phone, address, car, date, time, plan, amount })
    }).then(r => r.json()).then(res => {
      console.log('saved', res);
    }).catch(err => console.warn(err));
    */
  });

  // close receipt -> hide modal and reset
  closeReceiptBtn.addEventListener("click", () => {
    modal.setAttribute("aria-hidden", "true");
    bookingForm.reset();
  });

  // print receipt
  printReceiptBtn.addEventListener("click", () => {
    const printWindow = window.open('', '_blank', 'width=600,height=700');
    printWindow.document.write('<html><head><title>Receipt</title></head><body style="background:#111;color:#fff;font-family:sans-serif;padding:20px;">');
    printWindow.document.write(<h2 style="color:#ff8a00;">ROADBUDDY Receipt</h2>);
    printWindow.document.write(receiptContent.innerHTML);
    printWindow.document.write(<p style="margin-top:20px;color:#ffd7a6;">${welcomeMsg.textContent}</p>);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
  });

  // close modal on outside click
  window.addEventListener("click", (e) => {
    if(e.target === modal) {
      modal.setAttribute("aria-hidden", "true");
      bookingForm.reset();
    }
  });

});

// ==============================
// AFFORDABLE PLAN PAYMENT (CLEAN FIXED VERSION)
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("bookingModal");
  const closeBtn = document.getElementById("bookingClose");
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
  const payNowBtn = paymentStep.querySelector("#payNowBtn"); // scoped to avoid conflicts
  const receiptContent = document.getElementById("receiptContent");
  const welcomeMsg = document.getElementById("welcomeMsg");
  const closeReceiptBtn = document.getElementById("closeReceiptBtn");
  const printReceiptBtn = document.getElementById("printReceiptBtn");

  // --- OPEN MODAL ---
  document.querySelectorAll(".pricing-start").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const plan = btn.dataset.plan || "Plan";
      const amount = btn.dataset.amount || "0";

      planNameEl.textContent = plan;
      planInput.value = plan;
      amountInput.value = amount;
      amountDisplay.value = amount;

      bookingStep.style.display = "block";
      paymentStep.style.display = "none";
      receiptStep.style.display = "none";

      modal.setAttribute("aria-hidden", "false");
    });
  });

  // --- CLOSE MODAL ---
  closeBtn.addEventListener("click", () => {
    modal.setAttribute("aria-hidden", "true");
    bookingForm.reset();
  });

  // --- BOOKING FORM -> PAYMENT STEP ---
  bookingForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const formData = new FormData(bookingForm);
    const name = formData.get("name");
    const plan = formData.get("plan");
    const amount = formData.get("amount");

    paySummary.innerHTML = `<strong>${name}</strong>, you're booking <strong>${plan}</strong> for <strong>₹${amount}</strong>.`;


    bookingStep.style.display = "none";
    paymentStep.style.display = "block";
  });

  // --- BACK BUTTON ---
  backToForm.addEventListener("click", (e) => {
    e.preventDefault();
    paymentStep.style.display = "none";
    bookingStep.style.display = "block";
  });

  // --- PAY NOW (Generates Receipt) ---
  payNowBtn.addEventListener("click", () => {
    const name = document.getElementById("custName").value || "Customer";
    const phone = document.getElementById("custPhone").value || "N/A";
    const address = document.getElementById("custAddress").value || "N/A";
    const car = document.getElementById("custCar").value || "N/A";
    const date = document.getElementById("custDate").value || "N/A";
    const time = document.getElementById("custTime").value || "N/A";
    const plan = planInput.value;
    const amount = amountInput.value;

    const txid = "RB-" + Math.floor(100000 + Math.random() * 900000);
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
      <p><strong>Transaction ID:</strong> ${txid}</p>
      <p><strong>Name:</strong> ${name}</p>
      <p><strong>Phone:</strong> ${phone}</p>
      <p><strong>Address:</strong> ${address}</p>
      <p><strong>Car Model:</strong> ${car}</p>
      <p><strong>Service Plan:</strong> ${plan}</p>
      <p><strong>Amount Paid:</strong> ₹${amount}</p>
      <p><strong>Scheduled:</strong> ${date} ${time}</p>
      <p><strong>Membership valid till:</strong> ${formattedExpiry}</p>
    `;

    welcomeMsg.textContent = `✅ Welcome to ROADBUDDY, ${name}! Your membership is active till ${formattedExpiry}.`;

  });

  // --- CLOSE RECEIPT ---
  closeReceiptBtn.addEventListener("click", () => {
    modal.setAttribute("aria-hidden", "true");
    bookingForm.reset();
  });

  // --- PRINT RECEIPT ---
  printReceiptBtn.addEventListener("click", () => {
    const printWindow = window.open("", "_blank", "width=600,height=700");
    printWindow.document.write(`
      <html><head><title>Receipt</title></head>
      <body style="background:#111;color:#fff;font-family:sans-serif;padding:20px;">
        <h2 style="color:#ff8a00;">ROADBUDDY RECEIPT</h2>
        ${receiptContent.innerHTML}
        <p style="margin-top:20px;color:#ffd7a6;">${welcomeMsg.textContent}</p>
      </body></html>
    `);
    printWindow.document.close();
    printWindow.print();
  });

  // --- CLOSE MODAL ON OUTSIDE CLICK ---
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.setAttribute("aria-hidden", "true");
      bookingForm.reset();
    }
  });
});