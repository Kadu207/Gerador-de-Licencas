(function () {
  var sidebar = document.querySelector("[data-sidebar]");
  var backdrop = document.querySelector("[data-sidebar-backdrop]");
  var toggle = document.querySelector("[data-sidebar-toggle]");

  function setOpen(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    if (backdrop) backdrop.hidden = !open;
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("sidebar-open", open);
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      setOpen(!sidebar.classList.contains("is-open"));
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", function () {
      setOpen(false);
    });
  }

  document.querySelectorAll("[data-open-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-open-modal");
      var dialog = id ? document.getElementById(id) : null;
      if (dialog && typeof dialog.showModal === "function") dialog.showModal();
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var dialog = btn.closest("dialog");
      if (dialog) dialog.close();
    });
  });
})();
