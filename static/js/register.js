/* Halaman daftar: validasi kata sandi & aktifkan tombol. */
(function () {
  var email = document.getElementById("email");
  var nama = document.getElementById("nama");
  var pass = document.getElementById("password");
  var confirmEl = document.getElementById("confirm");
  var agree = document.getElementById("agree");
  var btn = document.getElementById("submit-btn");
  var matchMsg = document.getElementById("match-msg");
  var ruleLen = document.querySelector('[data-rule="len"]');
  var ruleMix = document.querySelector('[data-rule="mix"]');
  if (!email || !pass || !confirmEl || !btn) return;

  function setRule(el, ok) {
    el.classList.toggle("text-green-700", ok);
    el.classList.toggle("text-slate-500", !ok);
  }

  // Tombol mata hanya muncul kalau kolomnya sudah terisi.
  function updateToggle(input) {
    var toggleBtn = document.querySelector(
      '[data-toggle="' + input.id + '"]',
    );
    if (!toggleBtn) return;

    var hasValue = input.value.length > 0;
    toggleBtn.classList.toggle("hidden", !hasValue);
    toggleBtn.classList.toggle("flex", hasValue);

    // Kalau dikosongkan, kembalikan ke mode tersembunyi.
    if (!hasValue) {
      input.type = "password";
      toggleBtn.querySelector("span").textContent = "visibility";
    }
  }

  function update() {
    var p = pass.value;
    var okLen = p.length >= 8;
    var okMix =
      /[A-Z]/.test(p) &&
      /[a-z]/.test(p) &&
      /\d/.test(p) &&
      /[^A-Za-z0-9]/.test(p);
    var okMatch = p !== "" && p === confirmEl.value;

    setRule(ruleLen, okLen);
    setRule(ruleMix, okMix);

    var showMismatch = confirmEl.value !== "" && !okMatch;
    matchMsg.classList.toggle("hidden", !showMismatch);
    matchMsg.classList.toggle("flex", showMismatch);

    btn.disabled = !(
      email.checkValidity() &&
      email.value.trim() &&
      nama.value.trim() &&
      okLen &&
      okMix &&
      okMatch &&
      agree.checked
    );
  }

  [email, nama].forEach(function (el) {
    el.addEventListener("input", update);
  });

  [pass, confirmEl].forEach(function (el) {
    el.addEventListener("input", function () {
      update();
      updateToggle(el);
    });
  });

  agree.addEventListener("change", update);

  document.querySelectorAll("[data-toggle]").forEach(function (b) {
    b.addEventListener("click", function () {
      var input = document.getElementById(b.getAttribute("data-toggle"));
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      b.querySelector("span").textContent = show
        ? "visibility_off"
        : "visibility";
      input.focus();
    });
  });

  update();
  updateToggle(pass);
  updateToggle(confirmEl);
})();