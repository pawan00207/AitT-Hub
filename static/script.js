// AirTrack — Frontend Script

// Toggle collapsible form sections
function toggleForm(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}

// Toggle SQL query display
function toggleSQL(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.toggle('hidden');
    const btn = event.target;
    btn.textContent = el.classList.contains('hidden') ? 'Show SQL' : 'Hide SQL';
  }
}

// Live table search
function setupTableSearch(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;
  input.addEventListener('input', () => {
    const q = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

// Ticket price display updater
function updatePrice(cls) {
  const prices = { Economy: '$199.99', Business: '$599.99', First: '$1,199.99' };
  const el = document.getElementById('price-display');
  if (el) {
    el.style.transform = 'scale(1.1)';
    el.textContent = prices[cls] || '$199.99';
    setTimeout(() => el.style.transform = '', 200);
  }
}

// Animate probability bar on page load
function animateProbBar() {
  const bars = document.querySelectorAll('.prob-bar-fill[data-width]');
  bars.forEach(bar => {
    const targetWidth = bar.getAttribute('data-width');
    setTimeout(() => {
      bar.style.width = targetWidth + '%';
    }, 200);
  });
}

// Auto-dismiss alerts
function setupAlertDismiss() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });
}

// On DOM ready
document.addEventListener('DOMContentLoaded', () => {
  setupTableSearch('flightSearch', 'flightsTable');
  setupTableSearch('passengerSearch', 'passengersTable');
  animateProbBar();
  setupAlertDismiss();
});
