// docs/assets/javascripts/accordion.js
document.addEventListener("DOMContentLoaded", function () {

  // ---------------- helper: 打开单个 panel（带动画，并在 transitionend 清理） ---------------
  function openPanel(panel) {
    if (!panel) return;
    // 如果已经处于 open 且 style.maxHeight = none，直接返回
    if (panel.classList.contains("open") && panel.style.maxHeight === "none") return;

    // 先把 panel 的 maxHeight 设置为当前内容高度以启动动画
    panel.classList.add("open");
    // 先确保不是 none，这样 scrollHeight 可正确计算
    panel.style.maxHeight = panel.scrollHeight + "px";

    // 在动画结束后清理 inline maxHeight（便于内容自适应）
    const onEnd = function (e) {
      if (e.propertyName === "max-height") {
        // 只有在保持打开状态时才把 maxHeight 设为 none
        if (panel.classList.contains("open")) {
          panel.style.maxHeight = "none";
        }
        panel.removeEventListener("transitionend", onEnd);
      }
    };
    panel.addEventListener("transitionend", onEnd);
  }

  // ---------------- helper: 关闭单个 panel（递归关闭内部 open panel） ---------------
  function closePanel(panel) {
    if (!panel) return;
    // 先递归关闭内部已打开的子 panel（避免遗留 open 状态）
    panel.querySelectorAll(".panel.open").forEach(function (child) {
      closePanel(child);
    });

    // 如果当前为 none（内容自适应），先设置为实际高度以触发动画
    if (panel.style.maxHeight === "none" || panel.style.maxHeight === "") {
      panel.style.maxHeight = panel.scrollHeight + "px";
    }

    // 强制回流，确保浏览器识别上一步的高度
    /* eslint-disable no-unused-expressions */
    panel.offsetHeight;
    /* eslint-enable no-unused-expressions */

    // 启动收缩动画
    panel.style.maxHeight = "0px";
    panel.classList.remove("open");

    // 额外去掉标题的 active 状态（如果存在）
    const prev = panel.previousElementSibling;
    if (prev && prev.classList && prev.classList.contains("accordion")) {
      prev.classList.remove("active");
    }
  }

  // ---------------- 打开目标元素的所有祖先 panel（用于锚点跳转） ---------------
  function openAncestorPanelsOf(element) {
    if (!element) return;
    // 从包含这个元素的最近 .section-card 向上，打开每一级父 panel
    let card = element.closest(".section-card");
    while (card) {
      // 找到包裹这个 card 的上一级 panel（如果存在）
      const parentPanel = card.parentElement;
      if (parentPanel && parentPanel.classList && parentPanel.classList.contains("panel")) {
        // 打开这个 parentPanel（如果尚未打开）
        openPanel(parentPanel);
        // 标记上一级标题为 active（视觉）
        const prevTitle = parentPanel.previousElementSibling;
        if (prevTitle && prevTitle.classList && prevTitle.classList.contains("accordion")) {
          prevTitle.classList.add("active");
        }
        // 继续向上寻找：card = 包含 parentPanel 的上一层 .section-card
        card = parentPanel.closest(".section-card");
      } else {
        break;
      }
    }
  }

  // ---------------- 初始化：为每个 .accordion 标题加点击事件（切换 open/close） ---------------
  document.querySelectorAll(".accordion").forEach(function (hdr) {
    hdr.addEventListener("click", function (ev) {
      const panel = hdr.nextElementSibling;
      if (!panel || !panel.classList.contains("panel")) return;

      const isOpen = panel.classList.contains("open");
      if (isOpen) {
        // 关闭自身（会递归关闭子 panel）
        closePanel(panel);
        hdr.classList.remove("active");
      } else {
        // 打开自身
        openPanel(panel);
        hdr.classList.add("active");
      }
    });
  });

  // --------------- 当页面加载或 hash 变化时，自动展开包含目标锚点的所有祖先 panel ---------------
  function handleHashOpen() {
    const hash = decodeURIComponent(window.location.hash || "");
    if (!hash) return;
    const id = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!id) return;
    const target = document.getElementById(id);
    if (target) {
      openAncestorPanelsOf(target);
      // 等一小会儿让面板打开（0~60ms），然后平滑滚动到目标
      setTimeout(function () {
        // 用浏览器原生滚动，Material 可能有自己的 offset，通常效果正常
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    }
  }

  window.addEventListener("hashchange", handleHashOpen, false);
  // 初次加载时如果有 hash，也打开对应 panel
  handleHashOpen();

  // --------------- 拦截页面内侧边导航（仅 href 以 # 开头的链接），先自动展开面板再跳转 ---------------
  // 选择一些常见容器：Material 的侧边 nav 通常是 .md-nav 或 .md-sidebar 或 TOC 区域
  const navSelector = ".md-nav, .md-sidebar, .md-nav__list, .toc, .md-content"; // 包含常见位置
  document.querySelectorAll(navSelector).forEach(function (nav) {
    nav.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener("click", function (ev) {
        const href = a.getAttribute("href");
        if (!href || !href.startsWith("#")) return;
        const id = decodeURIComponent(href.slice(1));
        const target = document.getElementById(id);
        if (!target) return; // 不在当前页面或找不到
        // 阻止默认跳转，先打开包含目标的祖先面板，再设置 location.hash
        ev.preventDefault();
        openAncestorPanelsOf(target);
        // 等帧再更换 hash（确保浏览器滚动到位置）
        setTimeout(function () {
          // 改变 hash 会触发 hashchange -> handleHashOpen，但此时面板已打开
          location.hash = "#" + id;
        }, 50);
      }, { passive: false });
    });
  });

  // --------------- 窗口 resize 时，重新调整已打开 panel 的 maxHeight ---------------
  window.addEventListener("resize", function () {
    document.querySelectorAll(".panel.open").forEach(function (p) {
      // 如果当前是 none（内容自适应），把它设为 none（无变化）
      if (p.style.maxHeight === "none" || p.style.maxHeight === "") {
        // nothing
      } else {
        // 重新计算并设置（避免内容换行导致高度错位）
        p.style.maxHeight = p.scrollHeight + "px";
      }
    });
  });
});
