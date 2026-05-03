function copyLink() {
  const input = document.getElementById("linkInput");
  if (!input) return;

  navigator.clipboard.writeText(input.value).then(() => {
    var toastEl = document.getElementById("copyToast");
    if (toastEl) {
      new bootstrap.Toast(toastEl, { delay: 3000 }).show();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnCopyLink")?.addEventListener("click", copyLink);
});

