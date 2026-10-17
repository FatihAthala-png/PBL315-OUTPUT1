/* Halaman login: aktifkan tombol & tampilkan/sembunyikan kata sandi. */
(function () {
  var email = document.getElementById("email");
  var pass = document.getElementById("password");
  var btn = document.getElementById("submit-btn");
  var toggle = document.getElementById("toggle-password");
  if (!email || !pass || !btn) return;

  function check() {
    btn.disabled = !(email.value.trim() && pass.value);
  }

  function updateToggle() {
    var hasValue = pass.value.length > 0;
    toggle.classList.toggle("hidden", !hasValue);
    toggle.classList.toggle("flex", hasValue);

    // Kalau kolom dikosongkan, kembalikan ke mode tersembunyi.
    if (!hasValue) {
      pass.type = "password";
      toggle.querySelector("span").textContent = "visibility";
    }
  }

  email.addEventListener("input", check);
  pass.addEventListener("input", function () {
    check();
    updateToggle();
  });

  toggle.addEventListener("click", function () {
    var show = pass.type === "password";
    pass.type = show ? "text" : "password";
    toggle.querySelector("span").textContent = show
      ? "visibility_off"
      : "visibility";
    pass.focus();
  });

  check();
  updateToggle();
})();