(function () {
  var forms = document.querySelectorAll("[data-password-security-form]");
  if (!forms.length) {
    return;
  }

  function evaluate(password) {
    var hasUpper = /[A-Z]/.test(password);
    var hasLower = /[a-z]/.test(password);
    var hasDigit = /[0-9]/.test(password);
    var hasSpecial = /[^A-Za-z0-9]/.test(password);
    var score = 0;
    if (password.length >= 8) score += 1;
    if (hasUpper) score += 1;
    if (hasLower) score += 1;
    if (hasDigit) score += 1;
    if (hasSpecial) score += 1;
    if (password.length >= 12) score += 1;

    var percent = Math.max(10, Math.min(100, Math.round((score / 6) * 100)));
    var level = "Fragil";
    var css = "strength-fragil";
    if (score >= 5) {
      level = "Fuerte";
      css = "strength-fuerte";
    } else if (score >= 3) {
      level = "Regular";
      css = "strength-regular";
    }

    return {
      hasUpper: hasUpper,
      hasLower: hasLower,
      hasDigit: hasDigit,
      hasSpecial: hasSpecial,
      lengthOk: password.length >= 8,
      percent: percent,
      level: level,
      css: css,
    };
  }

  function setRule(form, selector, ok) {
    var el = form.querySelector(selector);
    if (!el) return;
    el.classList.toggle("rule-ok", !!ok);
  }

  forms.forEach(function (form) {
    var newInput = form.querySelector("[data-new-password]");
    var confirmInput = form.querySelector("[data-confirm-password]");
    var bar = form.querySelector("[data-strength-bar]");
    var text = form.querySelector("[data-strength-text]");
    var matchHint = form.querySelector("[data-password-match]");
    var toggles = form.querySelectorAll("[data-toggle-password]");
    var generationField = form.querySelector("[data-generation-time-ms]");
    var startAtMs = 0;

    if (!newInput) {
      return;
    }

    function refresh() {
      var password = newInput.value || "";
      var info = evaluate(password);

      if (bar) {
        bar.style.width = info.percent + "%";
        bar.classList.remove("strength-fragil", "strength-regular", "strength-fuerte");
        bar.classList.add(info.css);
      }
      if (text) {
        text.textContent = "Seguridad: " + info.level;
      }

      setRule(form, "[data-rule-length]", info.lengthOk);
      setRule(form, "[data-rule-upper]", info.hasUpper);
      setRule(form, "[data-rule-lower]", info.hasLower);
      setRule(form, "[data-rule-digit]", info.hasDigit);
      setRule(form, "[data-rule-special]", info.hasSpecial);

      if (confirmInput && matchHint) {
        if (!confirmInput.value) {
          matchHint.textContent = "Confirma la contraseña nueva.";
          matchHint.className = "text-muted small";
        } else if (confirmInput.value === password) {
          matchHint.textContent = "Las contraseñas coinciden.";
          matchHint.className = "text-success small";
        } else {
          matchHint.textContent = "Las contraseñas no coinciden.";
          matchHint.className = "text-danger small";
        }
      }
    }

    toggles.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = form.querySelector(btn.getAttribute("data-toggle-password"));
        if (!target) return;
        target.type = target.type === "password" ? "text" : "password";
      });
    });

    newInput.addEventListener("input", function () {
      if (!startAtMs && newInput.value.length > 0) {
        startAtMs = Date.now();
      }
      if (newInput.value.length === 0) {
        startAtMs = 0;
        if (generationField) generationField.value = "0";
      }
      refresh();
    });
    if (confirmInput) {
      confirmInput.addEventListener("input", refresh);
    }
    if (generationField) {
      form.addEventListener("submit", function () {
        if (newInput.value && startAtMs) {
          generationField.value = String(Math.max(Date.now() - startAtMs, 0));
        } else {
          generationField.value = "0";
        }
      });
    }
    refresh();
  });
})();
