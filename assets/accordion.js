document.addEventListener("DOMContentLoaded", function () {

  // ========== 配置项（可编辑） ==========
  // 如果你想页面加载时默认全部展开，把下面设为 true
  const EXPAND_ALL_ON_LOAD = false;

  // 如果你想点击页面任意处或打开页面时不自动展开 hash 对应的 panels，
  // 把下面设为 false; 默认我们是会根据 hash 打开祖先并展开目标
  const AUTO_OPEN_ON_HASH = true;

  // ========== 辅助函数 ==========
  function openPanel(panel) {
    if (!panel) return;
    if (panel.classList.contains("open") && panel.style.maxHeight === "none") return;
    panel.classList.add("open");
    panel.style.maxHeight = panel.scrollHeight + "px";
    const onEnd = function (e) {
      if (e.propertyName === "max-height") {
        if (panel.classList.contains("open")) {
          // 把 inline maxHeight 设为 none，这样内部内容变化（图片加载、字体换行）不会被限制
          panel.style.maxHeight = "none";
        }
        panel.removeEventListener("transitionend", onEnd);
      }
    };
    panel.addEventListener("transitionend", onEnd);
  }

  function closePanel(panel) {
    if (!panel) return;
    // 递归关闭内部已经打开的子 panel，防止遗留状态
    panel.querySelectorAll(".panel.open").forEach(closePanel);

    if (panel.style.maxHeight === "none" || panel.style.maxHeight === "") {
      panel.style.maxHeight = panel.scrollHeight + "px";
    }
    // 触发回流，确保动画能执行
    panel.offsetHeight;
    panel.style.maxHeight = "0px";
    panel.classList.remove("open");
    const prev = panel.previousElementSibling;
    if (prev && prev.classList.contains("accordion")) {
      prev.classList.remove("active");
    }
  }

  // 打开目标元素的所有祖先 panel（用于 hash 跳转）
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

  // ========== 为每个标题添加点击切换行为 ==========
  document.querySelectorAll(".accordion").forEach(function (hdr) {
    hdr.addEventListener("click", function (ev) {
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

  // ========== 页面加载时是否默认展开全部（可选） ==========
  if (EXPAND_ALL_ON_LOAD) {
    document.querySelectorAll(".panel").forEach(function (p) {
      openPanel(p);
      const prev = p.previousElementSibling;
      if (prev && prev.classList && prev.classList.contains("accordion")) {
        prev.classList.add("active");
      }
    });
  }

  // ========== 平滑滚动（考虑页面顶栏高度） ==========
  function smoothScrollToElement(el) {
    if (!el) return;
    const header = document.querySelector(".md-header");
    const headerHeight = header ? header.offsetHeight : 0;
    const offset = el.getBoundingClientRect().top + window.scrollY - headerHeight - 12;
    window.scrollTo({ top: offset, behavior: "smooth" });
  }

  // ========== 处理 hash（打开祖先并展开目标） ==========
  function handleHashOpen() {
    if (!AUTO_OPEN_ON_HASH) return;
    const hash = decodeURIComponent(window.location.hash || "");
    if (!hash) return;
    const id = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!id) return;
    const target = document.getElementById(id);
    if (target) {
      openAncestorPanelsOf(target);
      // 如果目标本身有 panel，则展开它（这样用户能看到目标下的内容）
      if (target.classList.contains("accordion")) {
        const ownPanel = target.nextElementSibling;
        if (ownPanel && ownPanel.classList.contains("panel")) {
          openPanel(ownPanel);
          target.classList.add("active");
        }
      }
      // 平滑滚动到目标（给面板打开留个小延迟）
      setTimeout(function () {
        smoothScrollToElement(target);
      }, 60);
    }
  }

  window.addEventListener("hashchange", handleHashOpen, false);
  // 首次加载页面时执行（如果 url 含 hash）
  handleHashOpen();

  // ========== 侧边导航点击拦截：先展开面板再跳转（保证可见性） ==========
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

        // 打开所有祖先 panel（确保目标可见）
        openAncestorPanelsOf(target);

        // 同时展开目标本身（如果有 panel）
        if (target.classList.contains("accordion")) {
          const ownPanel = target.nextElementSibling;
          if (ownPanel && ownPanel.classList.contains("panel")) {
            openPanel(ownPanel);
            target.classList.add("active");
          }
        }

        // 等一点时间，再设置 hash（触发浏览器滚动）
        setTimeout(function () {
          location.hash = "#" + id;
        }, 50);
      });
    });
  });

  // ========== 窗口大小变化时修正已打开 panel 的高度 ==========
  window.addEventListener("resize", function () {
    document.querySelectorAll(".panel.open").forEach(function (p) {
      if (!(p.style.maxHeight === "none" || p.style.maxHeight === "")) {
        p.style.maxHeight = p.scrollHeight + "px";
      }
    });
  });
});
