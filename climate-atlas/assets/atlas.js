(function () {
  var state = { var: "all", scen: "all", win: "all", type: "all" };
  var allCards = Array.prototype.slice.call(document.querySelectorAll(".fig-card"));
  // 筛选与计数只针对图册区的 36 张结果图；阅读指引区的附图（流域划定检查图）不参与筛选
  var cards = allCards.filter(function (c) { return !!c.closest("#gallery"); });
  var groups = Array.prototype.slice.call(document.querySelectorAll(".group"));
  var countEl = document.getElementById("fcount");

  function applyFilter() {
    var visible = 0;
    cards.forEach(function (card) {
      var ok = (state.var === "all" || card.dataset.var === state.var) &&
               (state.scen === "all" || card.dataset.scen === state.scen) &&
               (state.win === "all" || card.dataset.win === state.win) &&
               (state.type === "all" || card.dataset.type === state.type);
      card.style.display = ok ? "" : "none";
      if (ok) visible++;
    });
    groups.forEach(function (g) {
      var any = g.querySelectorAll(".fig-card:not([style*='none'])").length > 0;
      g.style.display = any ? "" : "none";
    });
    if (countEl) countEl.textContent = "显示 " + visible + " / " + cards.length + " 张";
  }

  document.querySelectorAll(".fbtn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var dim = btn.dataset.dim;
      document.querySelectorAll('.fbtn[data-dim="' + dim + '"]').forEach(function (b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      state[dim] = btn.dataset.val;
      applyFilter();
    });
  });

  applyFilter();

  // ---------- Lightbox ----------
  var lb = document.getElementById("lightbox");
  var lbImg = document.getElementById("lb-img");
  var lbCap = document.getElementById("lb-cap");
  var currentList = [];
  var current = -1;

  function visibleCards() {
    return cards.filter(function (c) { return c.style.display !== "none"; });
  }

  function open(card) {
    var list = visibleCards();
    var idx = list.indexOf(card);
    if (idx === -1) { list = [card]; idx = 0; }   // 附图等非筛选图：单图模式
    currentList = list;
    current = idx;
    var img = card.querySelector("img");
    lbImg.src = img.getAttribute("src");
    var no = card.querySelector(".fig-no");
    var title = card.querySelector("figcaption h4").textContent;
    lbCap.textContent = (no ? no.textContent + " · " : "") + title;
    lb.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function close() {
    lb.classList.remove("open");
    document.body.style.overflow = "";
    currentList = [];
    current = -1;
  }

  allCards.forEach(function (card) {
    card.querySelector("img").addEventListener("click", function () {
      open(card);
    });
  });

  document.getElementById("lb-close").addEventListener("click", close);
  lb.addEventListener("click", function (e) {
    if (e.target === lb) close();
  });
  document.getElementById("lb-prev").addEventListener("click", function (e) {
    e.stopPropagation();
    var n = currentList.length;
    if (!n) return;
    open(currentList[(current - 1 + n) % n]);
  });
  document.getElementById("lb-next").addEventListener("click", function (e) {
    e.stopPropagation();
    var n = currentList.length;
    if (!n) return;
    open(currentList[(current + 1) % n]);
  });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") document.getElementById("lb-prev").click();
    if (e.key === "ArrowRight") document.getElementById("lb-next").click();
  });
})();
