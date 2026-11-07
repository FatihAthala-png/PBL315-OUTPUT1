/* Wishlist: tombol hati [data-wish] menyimpan ke server lewat fetch.
   Tampilan berubah langsung (optimistis), dikembalikan jika gagal.
   Tamu diarahkan ke halaman login. Dipakai di semua halaman. */
(function () {
  var script = document.currentScript;
  var toggleUrl = (script && script.dataset.toggleUrl) || "/wishlist/toggle";
  var meta = document.querySelector('meta[name="csrf-token"]');
  var csrf = meta ? meta.getAttribute("content") : "";

  function setCount(n) {
    document.querySelectorAll("[data-wish-count]").forEach(function (el) {
      el.textContent = n > 99 ? "99+" : String(n);
      el.classList.toggle("hidden", !n);
    });
  }

  function paint(btn, liked) {
    var name = btn.getAttribute("aria-label").replace(/^(Tambah|Hapus)\s+/, "")
      .replace(/\s+(ke|dari)\s+wishlist$/, "");
    btn.setAttribute("aria-pressed", liked ? "true" : "false");
    btn.setAttribute(
      "aria-label",
      (liked ? "Hapus " : "Tambah ") + name + (liked ? " dari" : " ke") + " wishlist"
    );
    btn.classList.toggle("text-red-500", liked);
    btn.classList.toggle("text-slate-500", !liked);
    var icon = btn.querySelector("span");
    if (icon) icon.style.fontVariationSettings = liked ? "'FILL' 1" : "'FILL' 0";
  }

  // Semua tombol untuk produk yang sama (kartu ganda di beranda) disamakan.
  function paintAll(productId, liked) {
    document.querySelectorAll('[data-wish][data-product-id="' + productId + '"]').forEach(function (b) {
      paint(b, liked);
    });
  }

  function afterChange(btn, liked) {
    // Di halaman wishlist, kartu yang di-unlove dihapus dari daftar.
    var page = document.querySelector("[data-wishlist-page]");
    if (!page || liked) return;
    var card = btn.closest("[data-wish-item]");
    if (card) card.remove();
    if (!page.querySelector("[data-wish-item]")) {
      var empty = document.querySelector("[data-wishlist-empty]");
      var list = document.querySelector("[data-wishlist-list]");
      if (list) list.classList.add("hidden");
      if (empty) empty.classList.remove("hidden");
    }
    var total = document.querySelector("[data-wishlist-total]");
    if (total) total.textContent = String(page.querySelectorAll("[data-wish-item]").length);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-wish]");
    if (!btn || !btn.dataset.productId || btn.dataset.busy) return;
    e.preventDefault();
    btn.dataset.busy = "1";

    var id = btn.dataset.productId;
    var want = btn.getAttribute("aria-pressed") !== "true";
    paintAll(id, want);

    var body = new URLSearchParams();
    body.set("product_id", id);
    body.set("state", want ? "on" : "off");
    body.set("next", window.location.pathname + window.location.search);

    fetch(toggleUrl, {
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
          paintAll(id, !want);
          window.location.href = r.data.login_url;
          return;
        }
        if (r.data.ok) {
          paintAll(id, r.data.liked);
          setCount(r.data.count);
          afterChange(btn, r.data.liked);
        } else {
          paintAll(id, !want);
        }
      })
      .catch(function () {
        paintAll(id, !want);
      })
      .then(function () {
        delete btn.dataset.busy;
      });
  });
})();
