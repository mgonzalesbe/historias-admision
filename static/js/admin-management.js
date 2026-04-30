(function () {
  function initTableSearch() {
    const inputEl = document.querySelector("[data-search-input]");
    const tableEl = document.querySelector("[data-search-table]");
    if (!inputEl || !tableEl) return;

    const tbodyRows = Array.from(tableEl.querySelectorAll("tbody tr"));
    inputEl.addEventListener("input", () => {
      const query = inputEl.value.trim().toLowerCase();
      tbodyRows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  }

  function initToasts() {
    document.querySelectorAll(".toast").forEach((toastEl) => {
      const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { autohide: false });
      toast.show();
      window.setTimeout(() => toast.hide(), 3000);
    });
  }

  function initConfirmModal() {
    const confirmModalEl = document.getElementById("confirmActionModal");
    const confirmMessageEl = document.getElementById("confirmActionMessage");
    const confirmActionBtn = document.getElementById("confirmActionBtn");

    if (!confirmModalEl || !confirmMessageEl || !confirmActionBtn) return;

    const confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
    let pendingForm = null;

    document.querySelectorAll("form[data-confirm]").forEach((formEl) => {
      formEl.addEventListener("submit", (event) => {
        event.preventDefault();
        pendingForm = formEl;
        confirmMessageEl.textContent = formEl.getAttribute("data-confirm") || "¿Confirmar acción?";
        confirmModal.show();
      });
    });

    document.querySelectorAll(".js-delete-btn").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const formEl = buttonEl.closest("form[data-confirm]");
        if (!formEl) return;
        pendingForm = formEl;
        confirmMessageEl.textContent = formEl.getAttribute("data-confirm") || "¿Confirmar acción?";
        confirmModal.show();
      });
    });

    confirmActionBtn.addEventListener("click", () => {
      if (pendingForm) pendingForm.submit();
    });
  }

  function initAdminCreateUserPasswordLock() {
    const form = document.getElementById("adminCreateUserForm");
    if (!form) return;

    const nombreInput = document.getElementById("createNombreCompleto");
    const usernameInput = document.getElementById("createUsername");
    const emailInput = document.getElementById("createEmail");
    const roleInput = document.getElementById("createRole");
    const passwordInput = document.getElementById("createPassword");
    const passwordHint = document.getElementById("createPasswordHint");
    const toggleBtn = document.getElementById("createTogglePassword");
    const generationField = document.getElementById("createGenerationTimeMs");
    const bar = document.getElementById("createPasswordStrengthBar");
    const text = document.getElementById("createPasswordStrengthText");
    const lengthRange = document.getElementById("createPasswordLengthRange");
    const lengthValue = document.getElementById("createPasswordLengthValue");
    const refreshBtn = document.getElementById("createRefreshSuggestion");
    const ruleLength = document.getElementById("createRuleLength");
    const ruleUpper = document.getElementById("createRuleUpper");
    const ruleLower = document.getElementById("createRuleLower");
    const ruleNumber = document.getElementById("createRuleNumber");
    const ruleSpecial = document.getElementById("createRuleSpecial");

    if (!passwordInput) return;

    let startAtMs = 0;
    let unlockedForEditing = false;

    function isValidEmail(email) {
      return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email || "");
    }

    function requiredFieldsReady() {
      const nombreOk = !!(nombreInput && nombreInput.value.trim());
      const usernameOk = !!(usernameInput && usernameInput.value.trim());
      const emailOk = !!(emailInput && emailInput.value.trim()) && isValidEmail(emailInput.value.trim());
      const roleOk = !!(roleInput && roleInput.value.trim());
      return nombreOk && usernameOk && emailOk && roleOk;
    }

    function secureRandomIndex(max) {
      if (max <= 0) return 0;
      if (window.crypto && window.crypto.getRandomValues) {
        const arr = new Uint32Array(1);
        window.crypto.getRandomValues(arr);
        return arr[0] % max;
      }
      return Math.floor(Math.random() * max);
    }

    function pickRandom(chars) {
      return chars.charAt(secureRandomIndex(chars.length));
    }

    function shuffleArray(items) {
      const arr = items.slice();
      for (let i = arr.length - 1; i > 0; i -= 1) {
        const j = secureRandomIndex(i + 1);
        const temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
      }
      return arr;
    }

    function getSelectedLength() {
      if (!lengthRange) return 12;
      const parsed = Number.parseInt(lengthRange.value, 10);
      if (Number.isNaN(parsed)) return 12;
      return Math.max(8, Math.min(15, parsed));
    }

    function updateLengthLabel() {
      if (lengthValue) {
        lengthValue.textContent = String(getSelectedLength());
      }
    }

    function generateStrongSuggestion(length) {
      const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
      const lower = "abcdefghijkmnopqrstuvwxyz";
      const digits = "23456789";
      const special = "!@#$%&*+-_=?";
      const all = upper + lower + digits + special;
      const chars = [pickRandom(upper), pickRandom(lower), pickRandom(digits), pickRandom(special)];
      for (let i = chars.length; i < length; i += 1) {
        chars.push(pickRandom(all));
      }
      return shuffleArray(chars).join("");
    }

    function toggleRule(ruleEl, ok) {
      if (!ruleEl) return;
      ruleEl.classList.toggle("rule-ok", !!ok);
    }

    function evaluatePassword(password) {
      const hasLength = password.length >= 8;
      const hasUpper = /[A-Z]/.test(password);
      const hasLower = /[a-z]/.test(password);
      const hasNumber = /\d/.test(password);
      const hasSpecial = /[^A-Za-z0-9]/.test(password);
      let score = 0;
      if (hasLength) score += 1;
      if (hasUpper) score += 1;
      if (hasLower) score += 1;
      if (hasNumber) score += 1;
      if (hasSpecial) score += 1;
      if (password.length >= 12) score += 1;

      let label = "Fragil";
      let width = 18;
      let className = "strength-fragil";
      if (score >= 5) {
        label = "Fuerte";
        width = 100;
        className = "strength-fuerte";
      } else if (score >= 3) {
        label = "Regular";
        width = 66;
        className = "strength-regular";
      }

      return {
        valid: hasLength && hasUpper && hasLower && hasNumber && hasSpecial,
        label,
        width,
        className,
        rules: {
          length: hasLength,
          upper: hasUpper,
          lower: hasLower,
          number: hasNumber,
          special: hasSpecial,
        },
      };
    }

    function refreshMeter() {
      const state = evaluatePassword(passwordInput.value || "");
      if (bar) {
        bar.classList.remove("strength-fragil", "strength-regular", "strength-fuerte");
        bar.classList.add(state.className);
        bar.style.width = `${state.width}%`;
      }
      if (text) {
        text.textContent = `Fortaleza: ${state.label}`;
      }
      toggleRule(ruleLength, state.rules.length);
      toggleRule(ruleUpper, state.rules.upper);
      toggleRule(ruleLower, state.rules.lower);
      toggleRule(ruleNumber, state.rules.number);
      toggleRule(ruleSpecial, state.rules.special);

      if (!state.valid) {
        passwordInput.setCustomValidity(
          "La contraseña debe tener mínimo 8 caracteres y contener mayúscula, minúscula, número y carácter especial."
        );
      } else {
        passwordInput.setCustomValidity("");
      }
    }

    function applyGeneratedSuggestion(forceReplace) {
      if (passwordInput.disabled || passwordInput.readOnly) return;
      if (!forceReplace && passwordInput.value) return;
      passwordInput.value = generateStrongSuggestion(getSelectedLength());
      if (!startAtMs) startAtMs = Date.now();
      refreshMeter();
      passwordInput.focus();
    }

    function refreshPasswordLock() {
      const ready = requiredFieldsReady();
      passwordInput.disabled = !ready;
      if (!ready) {
        unlockedForEditing = false;
        passwordInput.value = "";
        passwordInput.readOnly = true;
        startAtMs = 0;
        if (generationField) generationField.value = "0";
      } else {
        passwordInput.readOnly = !unlockedForEditing;
      }
      if (passwordHint) {
        passwordHint.classList.toggle("d-none", ready && unlockedForEditing);
      }
      if (toggleBtn) {
        toggleBtn.disabled = !ready || !unlockedForEditing;
      }
      if (lengthRange) {
        lengthRange.disabled = !ready || !unlockedForEditing;
      }
      if (refreshBtn) {
        refreshBtn.disabled = !ready || !unlockedForEditing;
      }
      refreshMeter();
    }

    [nombreInput, usernameInput, emailInput, roleInput].forEach((el) => {
      if (!el) return;
      el.addEventListener("input", refreshPasswordLock);
      el.addEventListener("change", refreshPasswordLock);
    });

    passwordInput.addEventListener("click", () => {
      if (!requiredFieldsReady()) return;
      if (!unlockedForEditing) {
        unlockedForEditing = true;
        passwordInput.readOnly = false;
        applyGeneratedSuggestion(false);
        refreshPasswordLock();
      }
    });

    passwordInput.addEventListener("focus", () => {
      if (!requiredFieldsReady()) return;
      if (!unlockedForEditing) {
        unlockedForEditing = true;
        passwordInput.readOnly = false;
        applyGeneratedSuggestion(false);
        refreshPasswordLock();
      }
    });

    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        if (passwordInput.disabled || passwordInput.readOnly) return;
        const isPassword = passwordInput.getAttribute("type") === "password";
        passwordInput.setAttribute("type", isPassword ? "text" : "password");
      });
    }

    if (lengthRange) {
      lengthRange.addEventListener("input", () => {
        updateLengthLabel();
        if (passwordInput.disabled) return;
        applyGeneratedSuggestion(true);
      });
    }

    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        if (passwordInput.disabled) return;
        applyGeneratedSuggestion(true);
      });
    }

    passwordInput.addEventListener("input", () => {
      if (!passwordInput.disabled && !startAtMs && passwordInput.value.length > 0) {
        startAtMs = Date.now();
      }
      refreshMeter();
    });

    form.addEventListener("submit", () => {
      refreshMeter();
      if (generationField && startAtMs) {
        generationField.value = String(Math.max(Date.now() - startAtMs, 0));
      }
    });

    updateLengthLabel();
    refreshPasswordLock();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTableSearch();
    initToasts();
    initConfirmModal();
    initAdminCreateUserPasswordLock();
  });
})();

