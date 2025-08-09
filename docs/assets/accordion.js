document.addEventListener("DOMContentLoaded", function () {
  // 关闭 panel 及其内所有打开的子 panel
  function closePanel(panel) {
    if (!panel) return;
    // 先递归关闭子 panel
    panel.querySelectorAll(".panel.open").forEach(function (child) {
      child.style.maxHeight = null;
      child.classList.remove("open");
      // child.previousElementSibling 可能是对应的标题（.accordion）
      const prev = child.previousElementSibling;
      if (prev && prev.classList && prev.classList.contains("accordion")) {
        prev.classList.remove("active");
      }
    });
    panel.style.maxHeight = null;
    panel.classList.remove("open");
  }

  // 点击标题切换
  document.querySelectorAll(".accordion").forEach(function (hdr) {
    hdr.addEventListener("click", function (ev) {
      // panel 是标题的下一个兄弟节点（我们的插件按这个结构生成）
      const panel = hdr.nextElementSibling;
      if (!panel || !panel.classList.contains("panel")) return;

      const isOpen = panel.classList.contains("open");

      if (isOpen) {
        // 关闭自身（会同时关闭内部展开）
        closePanel(panel);
        hdr.classList.remove("active");
      } else {
        // 打开：设置最大高度为 scrollHeight，实现平滑动画
        panel.style.maxHeight = panel.scrollHeight + "px";
        panel.classList.add("open");
        hdr.classList.add("active");
      }
    });
  });

  // 窗口大小变化时，重新设置已打开 panel 的 maxHeight（防止内容换行后高度错位）
  window.addEventListener("resize", function () {
    document.querySelectorAll(".panel.open").forEach(function (p) {
      p.style.maxHeight = p.scrollHeight + "px";
    });
  });
});
