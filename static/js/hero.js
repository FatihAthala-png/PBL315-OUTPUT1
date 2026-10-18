/* Carousel hero di beranda. */
(function () {
  var root = document.getElementById("hero-carousel");
  if (!root) return;

  var track = root.querySelector("[data-track]");
  var total = track.children.length;
  var dots = root.querySelectorAll("[data-dot]");
  var index = 0;
  var timer;

  function go(n) {
    index = (n + total) % total;
    track.style.transform = "translateX(-" + index * 100 + "%)";
    dots.forEach(function (d, i) {
      d.classList.toggle("opacity-40", i !== index);
    });
  }

  function start() {
    stop();
    timer = setInterval(function () {
      go(index + 1);
    }, 2000);
  }

  function stop() {
    clearInterval(timer);
  }

  root.querySelector("[data-prev]").addEventListener("click", function () {
    go(index - 1);
  });
  root.querySelector("[data-next]").addEventListener("click", function () {
    go(index + 1);
  });
  dots.forEach(function (d, i) {
    d.addEventListener("click", function () {
      go(i);
    });
  });
  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);

  go(0);
  start();
})();