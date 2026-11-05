/* Konfigurasi Tailwind untuk PokéVault. */

tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "secondary-fixed-dim": "#ffb95f",
        "error-container": "#ffdad6",
        "on-tertiary-fixed": "#410004",
        "on-tertiary-fixed-variant": "#930013",
        "surface-container-low": "#eff4ff",
        "primary-fixed-dim": "#bec6e0",
        "tertiary-container": "#410004",
        "tertiary-fixed": "#ffdad7",
        "tertiary-fixed-dim": "#ffb3ad",
        "on-surface": "#0b1c30",
        "surface-tint": "#565e74",
        "secondary-fixed": "#ffddb8",
        primary: "#000000",
        "on-primary-fixed-variant": "#3f465c",
        "on-tertiary": "#ffffff",
        "surface-dim": "#cbdbf5",
        "surface-container-high": "#dce9ff",
        "surface-bright": "#f8f9ff",
        "surface-container-highest": "#d3e4fe",
        "on-primary-container": "#7c839b",
        "inverse-surface": "#213145",
        "primary-container": "#131b2e",
        "inverse-on-surface": "#eaf1ff",
        "on-secondary-container": "#684000",
        "on-error": "#ffffff",
        "surface-variant": "#d3e4fe",
        "surface-container-lowest": "#ffffff",
        "on-primary-fixed": "#131b2e",
        "on-secondary-fixed": "#2a1700",
        outline: "#76777d",
        "surface-container": "#e5eeff",
        "on-surface-variant": "#45464d",
        error: "#ba1a1a",
        "on-primary": "#ffffff",
        "on-secondary-fixed-variant": "#653e00",
        surface: "#f8f9ff",
        secondary: "#855300",
        "on-background": "#0b1c30",
        background: "#f8f9ff",
        "secondary-container": "#fea619",
        "on-secondary": "#ffffff",
        "inverse-primary": "#bec6e0",
        tertiary: "#000000",
        "primary-fixed": "#dae2fd",
        "on-error-container": "#93000a",
        "outline-variant": "#c6c6cd",
        "on-tertiary-container": "#ef4444",
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
      spacing: {
        gutter: "1.5rem",
        "space-md": "1rem",
        "space-xl": "2.5rem",
        margin: "1rem",
        "gutter-desktop": "1.5rem",
        "space-xs": "0.25rem",
        "margin-desktop": "3rem",
        "space-sm": "0.5rem",
        "space-lg": "1.5rem",
      },
      fontFamily: {
        heading: ["Plus Jakarta Sans", "sans-serif"],
        "display-lg": ["Plus Jakarta Sans", "sans-serif"],
        "price-md": ["Plus Jakarta Sans", "sans-serif"],
        "headline-md": ["Plus Jakarta Sans", "sans-serif"],
        "label-md": ["Plus Jakarta Sans", "sans-serif"],
        "label-sm": ["Plus Jakarta Sans", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "body-sm": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "price-lg": ["Plus Jakarta Sans", "sans-serif"],
        "title-md": ["Plus Jakarta Sans", "sans-serif"],
        "headline-sm": ["Plus Jakarta Sans", "sans-serif"],
        "headline-lg": ["Plus Jakarta Sans", "sans-serif"],
      },
      fontSize: {
        "display-lg": [
          "40px",
          { lineHeight: "48px", letterSpacing: "-0.02em", fontWeight: "800" },
        ],
        "price-md": [
          "18px",
          { lineHeight: "24px", letterSpacing: "-0.01em", fontWeight: "700" },
        ],
        "headline-md": [
          "24px",
          { lineHeight: "32px", letterSpacing: "-0.01em", fontWeight: "700" },
        ],
        "label-md": [
          "12px",
          { lineHeight: "16px", letterSpacing: "0.04em", fontWeight: "700" },
        ],
        "label-sm": [
          "10px",
          { lineHeight: "12px", letterSpacing: "0.06em", fontWeight: "700" },
        ],
        "body-md": [
          "14px",
          { lineHeight: "20px", letterSpacing: "0em", fontWeight: "400" },
        ],
        "body-sm": [
          "12px",
          { lineHeight: "16px", letterSpacing: "0.01em", fontWeight: "400" },
        ],
        "body-lg": [
          "16px",
          { lineHeight: "24px", letterSpacing: "0em", fontWeight: "400" },
        ],
        "price-lg": [
          "22px",
          { lineHeight: "28px", letterSpacing: "-0.02em", fontWeight: "800" },
        ],
        "title-md": [
          "16px",
          { lineHeight: "24px", letterSpacing: "0em", fontWeight: "600" },
        ],
        "headline-sm": [
          "20px",
          { lineHeight: "28px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-lg": [
          "32px",
          { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" },
        ],
      },
    },
  },
};

/* Interaksi halaman katalog. */

function initializeCatalogInteractions() {
  // Toggle tampilan Grid / List
  const gridBtn = document.getElementById("view-grid-btn");
  const listBtn = document.getElementById("view-list-btn");
  const catalogContainer = document.getElementById("catalog-items-container");
  if (!catalogContainer) return;

  const ON = ["bg-blue-600", "text-white"];
  const OFF = ["text-slate-500", "hover:text-blue-600"];

  function setView(list) {
    catalogContainer.classList.toggle("is-list", list);
    catalogContainer.classList.toggle("grid-cols-1", list);
    catalogContainer.classList.toggle("grid-cols-2", !list);
    catalogContainer.classList.toggle("xl:grid-cols-3", !list);
    [[gridBtn, !list], [listBtn, list]].forEach(function (pair) {
      if (!pair[0]) return;
      ON.forEach(function (c) { pair[0].classList.toggle(c, pair[1]); });
      OFF.forEach(function (c) { pair[0].classList.toggle(c, !pair[1]); });
    });
  }
  if (gridBtn) gridBtn.addEventListener("click", function () { setView(false); });
  if (listBtn) listBtn.addEventListener("click", function () { setView(true); });

  // Wishlist & Add to cart
  catalogContainer.addEventListener("click", function (e) {
    const wish = e.target.closest("[data-wish]");
    if (wish) {
      const liked = wish.getAttribute("aria-pressed") !== "true";
      wish.setAttribute("aria-pressed", liked ? "true" : "false");
      wish.classList.toggle("text-red-500", liked);
      wish.classList.toggle("text-slate-500", !liked);
      wish.querySelector("span").style.fontVariationSettings = liked
        ? "'FILL' 1"
        : "'FILL' 0";
      return;
    }

    // Add to cart: ditangani static/js/cart.js
  });
}

document.addEventListener("DOMContentLoaded", function () {
  initializeCatalogInteractions();
});