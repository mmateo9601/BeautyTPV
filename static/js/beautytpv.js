"use strict";
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".sidebar nav a").forEach(link => {
    if (window.location.pathname.startsWith(new URL(link.href).pathname)) link.setAttribute("aria-current", "page");
  });
  document.querySelectorAll("[data-filter-target]").forEach(input => input.addEventListener("input", () => {
    const query = input.value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    document.querySelectorAll(input.dataset.filterTarget).forEach(item => {
      const text = (item.dataset.filterText || item.textContent).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      item.hidden = !text.includes(query);
    });
  }));
  document.querySelectorAll("[data-select-user]").forEach(button => button.addEventListener("click", () => {
    const username = document.getElementById("id_username");
    const credential = document.getElementById("id_credential");
    const passwordMode = document.getElementById("id_password_mode");
    if (username) username.value = button.dataset.selectUser;
    if (passwordMode) passwordMode.checked = false;
    if (credential) { credential.value = ""; credential.setAttribute("inputmode", "numeric"); credential.focus(); }
  }));
  const updateChange = () => {
    const cash = document.getElementById("cash-amount");
    const received = document.getElementById("received");
    const output = document.getElementById("change-output");
    if (cash && received && output) {
      const cents = Math.max(0, Math.round(Number(received.value || 0) * 100) - Math.round(Number(cash.value || 0) * 100));
      output.textContent = (cents / 100).toLocaleString("es-ES", {style: "currency", currency: "EUR"});
    }
  };
  document.querySelectorAll("[data-payment-input]").forEach(input => input.addEventListener("input", updateChange));
  updateChange();
});
document.addEventListener("submit", event => {
  const form = event.target;
  if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) { event.preventDefault(); return; }
  if (!form.hasAttribute("data-submit-lock")) return;
  if (form.dataset.submitting === "true") { event.preventDefault(); return; }
  form.dataset.submitting = "true";
  form.setAttribute("aria-busy", "true");
  window.setTimeout(() => form.querySelectorAll("button[type=submit],button:not([type])").forEach(button => { button.disabled = true; }), 0);
});
window.addEventListener("pageshow", () => document.querySelectorAll("form[data-submit-lock]").forEach(form => {
  delete form.dataset.submitting; form.removeAttribute("aria-busy");
  form.querySelectorAll("button").forEach(button => { button.disabled = false; });
}));
document.addEventListener("htmx:sendError", () => document.getElementById("network-error")?.classList.remove("d-none"));
document.addEventListener("htmx:responseError", () => document.getElementById("network-error")?.classList.remove("d-none"));
