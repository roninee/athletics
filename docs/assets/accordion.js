document.addEventListener("DOMContentLoaded", function () {

  function openPanel(panel) {
    if (!panel) return;
    if (panel.classList.contains("open") && panel.style.maxHeight === "none") return;
    panel.classList.add("open");
    panel.style.maxHeight = panel.scrollHeight + "px";
    const onEnd = function (e) {
      if (e.propertyName === "max-height") {
        if (panel.classList.contains("open")) {
          panel.style.maxHeight = "none";
        }
        panel.removeEventListener("transitionend", onEnd);
      }
    };
    panel.addEventListener("transitionend", onEnd);
  }

  function closePanel(panel) {
    if (!panel) return;
    panel.querySelectorAll(".panel.open").forEach(closePanel);
    if (panel.style.maxHeight === "none" || panel.style.maxHeight === "") {
      panel.style.maxHeight = panel.scrollHeight + "px";
    }
    panel.offsetHeight;
    panel.style.maxHeight = "0px";
    panel.classList.remove("open");
    const prev = panel.previousElementSibling;
    if (prev && prev.classList.contains("accordion")) {
      prev.classList.remove("active");
    }
  }

  function openAncestorPanelsOf(element) {
    if (!element) return;
    let card = element.closest(".section-card");
    while (card) {
      const parentPanel = card.parentElement;
      if (parentPanel && parentPanel.classList.contains("panel")) {
        openPanel(parentPanel);
        const prevTitle = parentPanel.previousElementSibling;
        if (prevTitle && prevTitle.classList.contains("accordion")) {
          prevTitle.classList.add("active");
        }
        card = parentPanel.closest(".section-card");
      } else break;
    }
  }

  // ===== 新增：统计内容行数并显示 badge =====
  document.querySelectorAll(".accordion").forEach(function (hdr) {
    const panel = hdr.nextElementSibling;
    if (!panel || !panel.classList.contains("panel")) return;
    // 统计非空行数（去掉空文本节点）
    const textLines = panel.innerText.split("\n").filter(l => l.trim() !== "");
    const count = textLines.length;
    const badge = document.createElement("span");
    badge.className = "accordion-badge";
    badge.textContent = count === 0 ? "空" : count + "行";
    hdr.appendChild(badge);
  });

  document.querySelectorAll(".accordion").forEach(function (hdr) {
    hdr.addEventListener("click", function () {
      const panel = hdr.nextElementSibling;
      if (!panel || !panel.classList.contains("panel")) return;
      const isOpen = panel.classList.contains("open");
      if (isOpen) {
        closePanel(panel);
        hdr.classList.remove("active");
      } else {
        openPanel(panel);
        hdr.classList.add("active");
      }
    });
  });

  // ===== 改进的 hash 定位，展开目标标题本身的 panel =====
  function smoothScrollToElement(el) {
    if (!el) return;
    const header = document.querySelector(".md-header");
    const headerHeight = header ? header.offsetHeight : 0;
    const offset = el.getBoundingClientRect().top + window.scrollY - headerHeight - 12;
    window.scrollTo({ top: offset, behavior: "smooth" });
  }

  function handleHashOpen() {
    const hash = decodeURIComponent(window.location.hash || "");
    if (!hash) return;
    const id = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!id) return;
    const target = document.getElementById(id);
    if (target) {
      openAncestorPanelsOf(target);
      // ===== 新增：如果目标标题本身有 panel，则展开它 =====
      if (target.classList.contains("accordion")) {
        const ownPanel = target.nextElementSibling;
        if (ownPanel && ownPanel.classList.contains("panel")) {
          openPanel(ownPanel);
          target.classList.add("active");
        }
      }
      setTimeout(function () {
        smoothScrollToElement(target);
      }, 60);
    }
  }

  window.addEventListener("hashchange", handleHashOpen, false);
  handleHashOpen();

  const navSelector = ".md-nav, .md-sidebar, .md-nav__list, .toc, .md-content";
  document.querySelectorAll(navSelector).forEach(function (nav) {
    nav.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener("click", function (ev) {
        const href = a.getAttribute("href");
        if (!href.startsWith("#")) return;
        const id = decodeURIComponent(href.slice(1));
        const target = document.getElementById(id);
        if (!target) return;
        ev.preventDefault();
        openAncestorPanelsOf(target);
        // ===== 同样展开目标本身 =====
        if (target.classList.contains("accordion")) {
          const ownPanel = target.nextElementSibling;
          if (ownPanel && ownPanel.classList.contains("panel")) {
            openPanel(ownPanel);
            target.classList.add("active");
          }
        }
        setTimeout(function () {
          location.hash = "#" + id;
        }, 50);
      });
    });
  });

  window.addEventListener("resize", function () {
    document.querySelectorAll(".panel.open").forEach(function (p) {
      if (!(p.style.maxHeight === "none" || p.style.maxHeight === "")) {
        p.style.maxHeight = p.scrollHeight + "px";
      }
    });
  });
});
