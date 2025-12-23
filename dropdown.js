(function () {
  const dd = document.getElementById("modelDropdown");
  const btn = dd.querySelector(".dropdown-btn");
  const menu = dd.querySelector(".dropdown-content");
  const hiddenInput = document.getElementById("modeHidden");

  // toggle
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    dd.classList.toggle("open");
    btn.setAttribute("aria-expanded", dd.classList.contains("open"));
  });

  // clicking an option
  menu.addEventListener("click", (e) => {
    const label = e.target.closest("label.row");
    if (!label || label.classList.contains("disabled")) return;

    const radio = label.querySelector('input[type="radio"]');
    radio.checked = true;

    // update button text and hidden input for the form
    hiddenInput.value = radio.value;
    btn.firstChild.textContent = `LLM (${radio.value}) `;

    dd.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
  });

  // close on outside click / escape
  document.addEventListener("click", () => dd.classList.remove("open"));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") dd.classList.remove("open");
  });
})();
