/* Carousel "Most Popular Items": panah geser kiri/kanan + wishlist. */
(function () {
  var root = document.getElementById("popular-items");
  if (!root) return;

  var scroller = root.querySelector("[data-scroller]");
  var prev = root.querySelector("[data-prev]");
  var next = root.querySelector("[data-next]");
  if (!scroller || !prev || !next) return;

  function step() {
    var card = scroller.querySelector("article");
    return card ? (card.offsetWidth + 16) * 2 : 300; // geser 2 kartu
  }

  function setVisible(btn, visible) {
    btn.classList.toggle("opacity-0", !visible);
    btn.classList.toggle("pointer-events-none", !visible);
  }

  function update() {
    var max = scroller.scrollWidth - scroller.clientWidth - 1;
    setVisible(prev, scroller.scrollLeft > 0);
    setVisible(next, scroller.scrollLeft < max);
  }

  prev.addEventListener("click", function () {
    scroller.scrollBy({ left: -step(), behavior: "smooth" });
  });
  next.addEventListener("click", function () {
    scroller.scrollBy({ left: step(), behavior: "smooth" });
  });

  scroller.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();

  /* ---------- Wishlist: love jadi merah & terisi saat dipencet ---------- */
  root.addEventListener("click", function (e) {
    var wish = e.target.closest("[data-wish]");
    if (!wish) return;

    var liked = wish.getAttribute("aria-pressed") !== "true";
    wish.setAttribute("aria-pressed", liked ? "true" : "false");
    wish.classList.toggle("text-red-500", liked);
    wish.classList.toggle("text-slate-500", !liked);
    wish.querySelector("span").style.fontVariationSettings = liked
      ? "'FILL' 1"
      : "'FILL' 0";
  });
})();