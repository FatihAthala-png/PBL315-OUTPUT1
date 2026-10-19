/* Keranjang: tombol "Add to cart" mengirim ke server lewat fetch, lalu
   memperbarui badge jumlah di header. Tamu diarahkan ke halaman login. */
(function () {
  var script = document.currentScript;
  var addUrl = (script && script.dataset.addUrl) || "/keranjang/tambah";
  var meta = document.querySelector('meta[name="csrf-token"]');
  var csrf = meta ? meta.getAttribute("content") : "";

  function setCount(n) {
    document.querySelectorAll("[data-cart-count]").forEach(function (el) {
      el.textContent = n > 99 ? "99+" : String(n);
      el.classList.toggle("hidden", !n);
    });
  }

  // Tampilkan hasil sebentar di tombol, lalu kembalikan seperti semula.
  function show(btn, icon, text, ok) {
    var original = btn.innerHTML;
    var cls = ok ? ["!bg-green-600", "!text-white"] : ["!bg-red-600", "!text-white"];
    btn.innerHTML =
      '<span class="material-symbols-outlined text-base">' + icon + "</span><span></span>";
    btn.lastChild.textContent = text;
    cls.forEach(function (c) {
      btn.classList.add(c);
    });
    setTimeout(function () {
      btn.innerHTML = original;
      cls.forEach(function (c) {
        btn.classList.remove(c);
      });
      delete btn.dataset.busy;
    }, 1800);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-cart]");
    if (!btn || !btn.dataset.productId || btn.dataset.busy) return;
    e.preventDefault();
    btn.dataset.busy = "1";

    var body = new URLSearchParams();
    body.set("product_id", btn.dataset.productId);
    body.set("qty", "1");
    body.set("next", window.location.pathname + window.location.search);

    fetch(addUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf,
        "X-Requested-With": "fetch",
        Accept: "application/json",
      },
      body: body,
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { status: res.status, data: data };
        });
      })
      .then(function (r) {
        if (r.status === 401 && r.data.login_url) {
          window.location.href = r.data.login_url;
          return;
        }
        if (r.data.ok) {
          setCount(r.data.count);
          show(btn, "check", r.data.limited ? "Maks. stok" : "Ditambahkan!", true);
        } else {
          show(btn, "error", r.data.message || "Gagal", false);
        }
      })
      .catch(function () {
        show(btn, "error", "Gagal, coba lagi", false);
      });
  });
})();
