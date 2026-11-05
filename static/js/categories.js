/* Shop By Category: tab kategori, ikon GIF diam/jalan saat hover, wishlist & keranjang. */
(function () {
  var root = document.getElementById("shop-by-category");
  if (!root) return;

  var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-cat]"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-panel]"));
  var seeAll = document.getElementById("see-all-link");
  var on = root.dataset.tileOn.split(" ").filter(Boolean);
  var off = root.dataset.tileOff.split(" ").filter(Boolean);

  /* ---------- Ganti kategori ---------- */
  function select(key) {
    tabs.forEach(function (tab) {
      var active = tab.dataset.cat === key;
      tab.setAttribute("aria-selected", active ? "true" : "false");
      on.forEach(function (c) {
        tab.classList.toggle(c, active);
      });
      off.forEach(function (c) {
        tab.classList.toggle(c, !active);
      });
      if (active && seeAll) seeAll.href = tab.dataset.href;
    });
    panels.forEach(function (panel) {
      panel.classList.toggle("hidden", panel.dataset.panel !== key);
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      select(tab.dataset.cat);
    });
  });

  /* ---------- Ikon GIF: diam saat idle, jalan saat hover ---------- */
  tabs.forEach(function (tab) {
    var img = tab.querySelector("[data-gif-icon]");
    if (!img) return;
    var gifSrc = img.getAttribute("data-gif");
    var stillSrc = null;

    var probe = new Image();
    probe.onload = function () {
      try {
        var canvas = document.createElement("canvas");
        canvas.width = probe.naturalWidth;
        canvas.height = probe.naturalHeight;
        canvas.getContext("2d").drawImage(probe, 0, 0);
        stillSrc = canvas.toDataURL("image/png");
        img.src = stillSrc;
      } catch (e) {
        stillSrc = null; // gagal: biarkan GIF jalan terus
      }
    };
    probe.src = gifSrc;

    function play() {
      if (stillSrc) img.src = gifSrc;
    }
    function pause() {
      if (stillSrc) img.src = stillSrc;
    }

    tab.addEventListener("pointerenter", play);
    tab.addEventListener("pointerleave", pause);
    tab.addEventListener("focus", play);
    tab.addEventListener("blur", pause);
  });

  /* ---------- Wishlist & keranjang ---------- */
  root.addEventListener("click", function (e) {
    var wish = e.target.closest("[data-wish]");
    if (wish) {
      var liked = wish.getAttribute("aria-pressed") !== "true";
      wish.setAttribute("aria-pressed", liked ? "true" : "false");
      wish.classList.toggle("text-red-500", liked);
      wish.classList.toggle("text-slate-500", !liked);
      wish.querySelector("span").style.fontVariationSettings = liked
        ? "'FILL' 1"
        : "'FILL' 0";
      return;
    }
  });

  select(tabs.length ? tabs[0].dataset.cat : "");
})();