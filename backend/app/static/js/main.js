// Spendly Main JavaScript - Dark Theme Toggle & Interactive UI

document.addEventListener('DOMContentLoaded', function() {
  initThemeToggle();
  initToasts();
  initRipples();
  initInputGlow();
});

/**
 * Initialize theme toggle button
 */
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;
  
  const root = document.body;
  const saved = localStorage.getItem('spendly-theme') || 'spendly-dark';
  
  // Apply saved theme
  root.className = saved;
  updateThemeButtonText(saved === 'spendly-dark');
  
  // Toggle on click
  toggleBtn.addEventListener('click', function(e) {
    e.preventDefault();
    const isDark = root.classList.contains('spendly-dark');
    const next = isDark ? 'spendly-light' : 'spendly-dark';
    
    root.className = next;
    updateThemeButtonText(next === 'spendly-dark');
    localStorage.setItem('spendly-theme', next);
  });
}

/**
 * Update theme button text and icon
 */
function updateThemeButtonText(isDark) {
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    if (isDark) {
      btn.innerHTML = '<i class="fas fa-moon"></i> Dark';
    } else {
      btn.innerHTML = '<i class="fas fa-sun"></i> Light';
    }
  }
}

/**
 * Toast notification system
 */
function initToasts() {
  window.showToast = function(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toastId = 'toast-' + Date.now();
    const html = `
      <div id="${toastId}" class="toast ${type}" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-body d-flex align-items-center">
          ${getToastIcon(type)}
          <span class="ms-2">${escapeHtml(message)}</span>
          <button type="button" class="btn-close btn-close-white ms-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: duration });
    toast.show();
    
    // Remove from DOM after hidden
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
  };
}

/**
 * Get icon HTML for toast type
 */
function getToastIcon(type) {
  const icons = {
    'success': '<i class="fas fa-check-circle text-success"></i>',
    'danger': '<i class="fas fa-exclamation-circle text-danger"></i>',
    'warning': '<i class="fas fa-exclamation-triangle text-warning"></i>',
    'info': '<i class="fas fa-info-circle text-info"></i>'
  };
  return icons[type] || icons['info'];
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return unsafe.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2
  }).format(amount);
}

/**
 * Format date
 */
function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(new Date(date));
}

/**
 * Add ripple effect to buttons
 */
function initRipples() {
  document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });
}

/**
 * Input focus glow helper: add `input-glow` class to inputs to enable glow
 */
function initInputGlow() {
  document.querySelectorAll('input, textarea, select').forEach(el => {
    el.addEventListener('focus', () => el.classList.add('input-glow'));
    el.addEventListener('blur', () => el.classList.remove('input-glow'));
  });
}
