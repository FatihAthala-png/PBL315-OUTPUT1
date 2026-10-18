/* Filter, urutan, dan chip "Filter Aktif" di halaman katalog. */
(function () {
  var root = document.getElementById("catalog-filters");
  var container = document.getElementById("catalog-items-container");
  if (!root || !container) return;

  var GROUPS = ["type", "sub", "availability", "rarity", "brand"];
  var items = Array.prototype.slice.call(
    container.querySelectorAll("[data-product]"),
  );

  var minRange = document.getElementById("price-min-range");
  var maxRange = document.getElementById("price-max-range");
  var minInput = document.getElementById("price-min-input");
  var maxInput = document.getElementById("price-max-input");
  var fill = document.getElementById("price-fill");
  var presets = root.querySelectorAll("[data-preset]");
  var sortSelect = document.getElementById("sort-selector");
  var chipsBox = document.getElementById("active-filter-chips");
  var noFilterText = document.getElementById("no-filter-text");
  var resetAllBtn = document.getElementById("reset-all-btn");
  var emptyState = document.getElementById("empty-state");
  var counters = document.querySelectorAll("[data-result-count]");

  var bound = {
    min: Number(root.dataset.priceMin),
    max: Number(root.dataset.priceMax),
  };
  var price = { min: bound.min, max: bound.max };

  /* ---------- Helper ---------- */
  function num(el, key) {
    return Number(el.dataset[key]);
  }

  function tagsOf(el, key) {
    return (el.dataset[key] || "").split(" ").filter(Boolean);
  }

  function formatRp(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function shortRp(n) {
    if (n >= 1000000) {
      var v = Math.round((n / 1000000) * 10) / 10;
      return "Rp " + String(v).replace(".", ",") + "jt";
    }
    return "Rp " + Math.round(n / 1000) + "rb";
  }

  function parseRp(text, fallback) {
    var v = parseInt(String(text).replace(/\D/g, ""), 10);
    return isNaN(v) ? fallback : v;
  }

  function checked(group) {
    return Array.prototype.slice.call(
      root.querySelectorAll(
        'input[data-filter-group="' + group + '"]:checked',
      ),
    );
  }

  /* ---------- Harga ---------- */
  function presetRange(btn) {
    var mx = btn.dataset.max === "max" ? bound.max : Number(btn.dataset.max);
    return {
      min: Math.max(bound.min, Number(btn.dataset.min)),
      max: Math.min(bound.max, mx),
    };
  }

  function syncPrice() {
    minRange.value = price.min;
    maxRange.value = price.max;
    minInput.value = formatRp(price.min);
    maxInput.value = formatRp(price.max);

    var span = bound.max - bound.min || 1;
    fill.style.left = ((price.min - bound.min) / span) * 100 + "%";
    fill.style.width = ((price.max - price.min) / span) * 100 + "%";

    // Supaya thumb min tetap bisa digeser saat dua thumb bertumpuk di kanan.
    minRange.style.zIndex = price.min > bound.min + span * 0.9 ? 5 : 3;
    maxRange.style.zIndex = 4;

    presets.forEach(function (btn) {
      var r = presetRange(btn);
      var on = r.min === price.min && r.max === price.max;
      btn.classList.toggle("font-bold", on);
      btn.classList.toggle("bg-blue-600", on);
      btn.classList.toggle("text-white", on);
      btn.classList.toggle("bg-slate-50", !on);
      btn.classList.toggle("text-slate-600", !on);
    });
  }

  function setPrice(min, max) {
    min = Math.min(Math.max(min, bound.min), bound.max);
    max = Math.min(Math.max(max, bound.min), bound.max);
    if (min > max) {
      var t = min;
      min = max;
      max = t;
    }
    price.min = min;
    price.max = max;
    syncPrice();
    apply();
  }

  /* ---------- Chip Filter Aktif ---------- */
  function makeChip(label, onRemove) {
    var el = document.createElement("span");
    el.className =
      "inline-flex items-center gap-1 px-3 py-1 rounded-full bg-sky-100 text-blue-700 text-xs font-bold hover:bg-sky-200 transition-colors cursor-pointer";
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.setAttribute("aria-label", "Hapus filter " + label);
    el.appendChild(document.createTextNode(label + " "));

    var icon = document.createElement("span");
    icon.className = "material-symbols-outlined text-base";
    icon.textContent = "close";
    el.appendChild(icon);

    el.addEventListener("click", onRemove);
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onRemove();
      }
    });
    return el;
  }

  function renderChips() {
    chipsBox.innerHTML = "";
    var total = 0;

    GROUPS.forEach(function (group) {
      checked(group).forEach(function (input) {
        chipsBox.appendChild(
          makeChip(input.dataset.label, function () {
            input.checked = false;
            apply();
          }),
        );
        total++;
      });
    });

    if (price.min > bound.min || price.max < bound.max) {
      var label;
      if (price.min <= bound.min) label = "Maks " + shortRp(price.max);
      else if (price.max >= bound.max) label = "Min " + shortRp(price.min);
      else label = shortRp(price.min) + " - " + shortRp(price.max);

      chipsBox.appendChild(
        makeChip(label, function () {
          setPrice(bound.min, bound.max);
        }),
      );
      total++;
    }

    noFilterText.style.display = total === 0 ? "" : "none";
    resetAllBtn.style.display = total === 0 ? "none" : "";
  }

  /* ---------- Urutan ---------- */
  var sorters = {
    popular: function (a, b) {
      return num(a, "order") - num(b, "order");
    },
    "price-low": function (a, b) {
      return num(a, "price") - num(b, "price");
    },
    "price-high": function (a, b) {
      return num(b, "price") - num(a, "price");
    },
    newest: function (a, b) {
      return num(b, "order") - num(a, "order");
    },
    rating: function (a, b) {
      return (
        num(b, "rating") - num(a, "rating") || num(a, "order") - num(b, "order")
      );
    },
  };

    /* ---------- Sub-kategori mengikuti jenis produk yang dipilih ---------- */
  function syncSubOptions() {
    var types = checked("type").map(function (i) {
      return i.value;
    });
    root.querySelectorAll("[data-parent]").forEach(function (label) {
      var show = types.length === 0 || types.indexOf(label.dataset.parent) !== -1;
      label.style.display = show ? "" : "none";
      if (!show) {
        var input = label.querySelector("input");
        if (input) input.checked = false;
      }
    });
  }

  /* ---------- Terapkan filter ---------- */
  function apply() {
    syncSubOptions();
    var selected = {};
    GROUPS.forEach(function (group) {
      selected[group] = checked(group).map(function (i) {
        return i.value;
      });
    });

    var visible = 0;
    items.forEach(function (el) {
      var p = num(el, "price");
      var ok = p >= price.min && p <= price.max;

      GROUPS.forEach(function (group) {
        if (!ok || selected[group].length === 0) return;
        var tags = tagsOf(el, group);
        ok = selected[group].some(function (v) {
          return tags.indexOf(v) !== -1;
        });
      });

      el.style.display = ok ? "" : "none";
      if (ok) visible++;
    });

    var sorter =
      sorters[sortSelect ? sortSelect.value : "popular"] || sorters.popular;
    items
      .slice()
      .sort(sorter)
      .forEach(function (el) {
        container.appendChild(el);
      });

    counters.forEach(function (c) {
      c.textContent = visible;
    });
    if (emptyState) emptyState.style.display = visible === 0 ? "" : "none";

    renderChips();
  }

  function resetAll() {
    root
      .querySelectorAll("input[data-filter-group]")
      .forEach(function (i) {
        i.checked = false;
      });
    setPrice(bound.min, bound.max);
  }

  /* ---------- Event ---------- */
  root.addEventListener("change", function (e) {
    if (e.target.matches("input[data-filter-group]")) apply();
  });

  root.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-preset]");
    if (!btn) return;
    var r = presetRange(btn);
    var active = r.min === price.min && r.max === price.max;
    if (active) setPrice(bound.min, bound.max);
    else setPrice(r.min, r.max);
  });

  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-reset-filters]")) resetAll();
  });

  minRange.addEventListener("input", function () {
    setPrice(Math.min(Number(minRange.value), price.max), price.max);
  });
  maxRange.addEventListener("input", function () {
    setPrice(price.min, Math.max(Number(maxRange.value), price.min));
  });

  minInput.addEventListener("change", function () {
    setPrice(parseRp(minInput.value, bound.min), price.max);
  });
  maxInput.addEventListener("change", function () {
    setPrice(price.min, parseRp(maxInput.value, bound.max));
  });

  if (sortSelect) sortSelect.addEventListener("change", apply);

    /* ---------- Buka/tutup filter di HP ---------- */
  var filterToggle = document.getElementById("filter-toggle");
  if (filterToggle) {
    filterToggle.addEventListener("click", function () {
      root.classList.toggle("hidden");
      root.classList.toggle("flex");
      filterToggle.setAttribute(
        "aria-expanded",
        root.classList.contains("hidden") ? "false" : "true",
      );
    });
  }

  /* ---------- Awal ---------- */
  // Link seperti /semua-produk?type=tcg otomatis mencentang filter jenisnya.
  var presetType = new URLSearchParams(window.location.search).get("type");
  if (presetType) {
    var presetBox = root.querySelector(
      'input[data-filter-group="type"][value="' + presetType + '"]',
    );
    if (presetBox) presetBox.checked = true;
  }

  syncPrice();
  apply();
})();