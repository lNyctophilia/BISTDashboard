/**
 * BIST DASHBOARD - LOGIN OVERLAY LOGIC
 * Encrypted Client-Side Authentication (SHA-256)
 */

(function () {
  'use strict';

  // Default Fallback Config (bist2026 SHA-256 Hash)
  const DEFAULT_HASH = "70be4c693915a05f0b501204e2fccda891e7ae9a23d237ad60b00a7ab4b04bec";

  /**
   * Generates a SHA-256 hex string from string input using native Web Crypto API
   */
  async function computeSHA256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Console helper for user to generate password hash easily
  window.createPasswordHash = async function (plainTextPassword) {
    if (!plainTextPassword) {
      console.warn("Lütfen bir şifre girin. Örn: createPasswordHash('sifrem123')");
      return;
    }
    const hash = await computeSHA256(plainTextPassword);
    console.log("%c==========================================", "color: #3b82f6; font-weight: bold;");
    console.log(`%cŞifre: %c${plainTextPassword}`, "color: #94a3b8;", "color: #10b981; font-weight: bold;");
    console.log(`%cSHA-256 Hash: %c${hash}`, "color: #94a3b8;", "color: #f59e0b; font-weight: bold;");
    console.log("%cBu hash değerini auth-config.js dosyasına kopyalayabilirsiniz.", "color: #94a3b8; font-style: italic;");
    console.log("%c==========================================", "color: #3b82f6; font-weight: bold;");
    return hash;
  };

  function initLogin() {
    const config = window.AUTH_CONFIG || { passwordHash: DEFAULT_HASH, rememberMeDays: 7 };
    const expectedHash = (config.passwordHash || DEFAULT_HASH).toLowerCase();

    const screen = document.getElementById('login-screen');
    const form = document.getElementById('auth-form');
    const passwordInput = document.getElementById('auth-password');
    const toggleEye = document.getElementById('auth-toggle-pwd');
    const eyeIcon = document.getElementById('auth-eye-icon');
    const rememberCheckbox = document.getElementById('auth-remember');
    const errorBanner = document.getElementById('auth-error');
    const card = document.querySelector('.auth-card');

    if (!screen) return;

    // Check existing authentication state
    const sessionAuth = sessionStorage.getItem('bist_auth');
    const localAuth = localStorage.getItem('bist_remember_auth');

    if (sessionAuth === 'true' || localAuth === 'true') {
      document.documentElement.classList.add('bist-authenticated');
      screen.style.display = 'none';
      return;
    }

    // Toggle Password Visibility
    if (toggleEye && passwordInput) {
      toggleEye.addEventListener('click', function () {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        
        if (eyeIcon) {
          eyeIcon.innerHTML = isPassword
            ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>`
            : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>`;
        }
      });
    }

    // Handle Login Submission
    async function handleLoginSubmit(e) {
      if (e) e.preventDefault();

      const enteredPassword = passwordInput.value;
      if (!enteredPassword) {
        showError("Lütfen şifrenizi girin.");
        return;
      }

      const inputHash = await computeSHA256(enteredPassword);

      if (inputHash === expectedHash) {
        // Success
        hideError();
        if (rememberCheckbox && rememberCheckbox.checked) {
          localStorage.setItem('bist_remember_auth', 'true');
        }
        sessionStorage.setItem('bist_auth', 'true');

        screen.classList.add('auth-unlocked');
        setTimeout(() => {
          screen.style.display = 'none';
        }, 500);
      } else {
        // Fail
        showError("Hatalı şifre! Lütfen tekrar deneyin.");
        triggerShake();
        passwordInput.value = '';
        passwordInput.focus();
      }
    }

    function showError(msg) {
      if (errorBanner) {
        errorBanner.textContent = msg;
        errorBanner.style.display = 'block';
      }
    }

    function hideError() {
      if (errorBanner) {
        errorBanner.style.display = 'none';
      }
    }

    function triggerShake() {
      if (card) {
        card.classList.remove('auth-shake');
        // Force reflow
        void card.offsetWidth;
        card.classList.add('auth-shake');
        setTimeout(() => {
          card.classList.remove('auth-shake');
        }, 600);
      }
    }

    if (form) {
      form.addEventListener('submit', handleLoginSubmit);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLogin);
  } else {
    initLogin();
  }
})();
