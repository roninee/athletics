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

document.addEventListener("DOMContentLoaded", () => {
  const content = document.querySelector(".md-content__inner"); // Material 的主容器
  if (!content) return;

  const nodes = Array.from(content.children);
  let currentSection = null;

  nodes.forEach((node) => {
    if (node.tagName === "H2") {
      currentSection = document.createElement("div");
      currentSection.className = "section-card";
      node.parentNode.insertBefore(currentSection, node);
    }

    if (currentSection) {
      currentSection.appendChild(node);
    }
  });
});
