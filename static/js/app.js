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
        "display-lg": ["Plus Jakarta Sans"],
        "price-md": ["Plus Jakarta Sans"],
        "headline-md": ["Plus Jakarta Sans"],
        "label-md": ["Plus Jakarta Sans"],
        "label-sm": ["Plus Jakarta Sans"],
        "body-md": ["Inter"],
        "body-sm": ["Inter"],
        "body-lg": ["Inter"],
        "price-lg": ["Plus Jakarta Sans"],
        "title-md": ["Plus Jakarta Sans"],
        "headline-sm": ["Plus Jakarta Sans"],
        "headline-lg": ["Plus Jakarta Sans"],
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
  // Toggle Grid and List views
  const gridBtn = document.getElementById("view-grid-btn");
  const listBtn = document.getElementById("view-list-btn");
  const catalogContainer = document.getElementById("catalog-items-container");

  if (gridBtn && listBtn && catalogContainer) {
    gridBtn.addEventListener("click", function () {
      gridBtn.classList.add(
        "bg-surface-container-lowest",
        "text-primary",
        "shadow-sm",
      );
      gridBtn.classList.remove("text-on-surface-variant");
      listBtn.classList.remove(
        "bg-surface-container-lowest",
        "text-primary",
        "shadow-sm",
      );
      listBtn.classList.add("text-on-surface-variant");

      catalogContainer.className =
        "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-space-lg";
    });

    listBtn.addEventListener("click", function () {
      listBtn.classList.add(
        "bg-surface-container-lowest",
        "text-primary",
        "shadow-sm",
      );
      listBtn.classList.remove("text-on-surface-variant");
      gridBtn.classList.remove(
        "bg-surface-container-lowest",
        "text-primary",
        "shadow-sm",
      );
      gridBtn.classList.add("text-on-surface-variant");

      catalogContainer.className = "grid grid-cols-1 gap-space-md";
    });
  }

  // Add feedback when clicking + Keranjang
  const cartButtons = document.querySelectorAll(
    'button:has(span.material-symbols-outlined:contains("shopping_cart")), article button',
  );
  cartButtons.forEach((btn) => {
    if (btn.innerText.includes("Keranjang")) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const originalHTML = this.innerHTML;
        this.innerHTML =
          '<span class="material-symbols-outlined text-body-md">check</span><span>Ditambahkan!</span>';
        this.classList.add("bg-primary", "text-on-primary");
        this.classList.remove(
          "bg-secondary-container",
          "text-on-secondary-container",
        );

        setTimeout(() => {
          this.innerHTML = originalHTML;
          this.classList.remove("bg-primary", "text-on-primary");
          this.classList.add(
            "bg-secondary-container",
            "text-on-secondary-container",
          );
        }, 1800);
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  initializeCatalogInteractions();
});
