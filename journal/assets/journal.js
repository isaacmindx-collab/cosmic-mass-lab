// Co-exist Journal: math rendering (KaTeX) and the filter by kind on the index.
document.addEventListener("DOMContentLoaded", function () {
  if (window.renderMathInElement) {
    renderMathInElement(document.body, {
      delimiters: [
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false },
      ],
      throwOnError: false,
    });
  }
  var chips = document.querySelectorAll(".chip");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var f = chip.getAttribute("data-filter");
      chips.forEach(function (c) { c.classList.toggle("on", c === chip); });
      document.querySelectorAll(".card").forEach(function (card) {
        card.hidden = f !== "all" && card.getAttribute("data-kind") !== f;
      });
    });
  });
});
