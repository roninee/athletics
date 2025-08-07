document.addEventListener("DOMContentLoaded", () => {
  let tocHeadings = document.querySelectorAll(".md-nav__link[href^='#']");
  let contentHeadings = document.querySelectorAll("h2");

  contentHeadings.forEach((h2, index) => {
    let num = index + 1;
    let numberStr = num + ". ";

    // 防止重复编号
    if (!h2.textContent.startsWith(numberStr)) {
      h2.textContent = numberStr + h2.textContent;
    }

    // 匹配 TOC 中的链接
    tocHeadings.forEach((link) => {
      if (link.getAttribute("href") === "#" + h2.id) {
        let tocText = link.textContent.trim();
        if (!tocText.startsWith(numberStr)) {
          link.textContent = numberStr + tocText;
        }
      }
    });
  });
});
