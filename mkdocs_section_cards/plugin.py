# plugins/section_cards.py
import re
from mkdocs.plugins import BasePlugin
from bs4 import BeautifulSoup, NavigableString, Tag

class SectionCardsPlugin(BasePlugin):
    """
    两阶段插件：
      1) on_page_markdown: 在 markdown 源里给 h2/h3/h4 编号（MkDocs 的 TOC 由此识别编号）
      2) on_page_content: 在生成的 HTML 中保留原生 <h2/h3/h4>，插入 accordion icon，并把标题与后续内容包装成 .section-card/.panel 嵌套
    """

    # ---------- markdown 阶段：在生成 HTML 前修改 markdown 文本，确保 TOC 能识别编号 ----------
    def on_page_markdown(self, markdown, page=None, config=None, files=None):
        lines = markdown.splitlines(keepends=True)
        out_lines = []

        # 正则
        fence_re = re.compile(r'^(\s*)(`{3,}|~{3,})(.*)\r?\n?$')
        atx_re = re.compile(r'^(\s{0,3})(#{2,4})\s*(.*?)\s*(\{[^\}]*\}\s*)?(\r?\n)?$')
        setext_h2_re = re.compile(r'^\s*-{2,}\s*(\r?\n)?$')

        in_fence = False
        fence_marker = None

        counters = {2: 0, 3: 0, 4: 0}
        i = 0
        while i < len(lines):
            line = lines[i]

            # 处理 fenced code 块开/关
            m_fence = fence_re.match(line)
            if m_fence:
                marker = m_fence.group(2)
                if not in_fence:
                    in_fence = True
                    fence_marker = marker
                else:
                    # 结束 fence（只匹配相同种类的 fence）
                    if marker == fence_marker:
                        in_fence = False
                        fence_marker = None
                out_lines.append(line)
                i += 1
                continue

            if in_fence:
                out_lines.append(line)
                i += 1
                continue

            # ATX 标题（## / ### / ####）
            m_atx = atx_re.match(line)
            if m_atx:
                indent = m_atx.group(1) or ""
                hashes = m_atx.group(2)
                raw_text = (m_atx.group(3) or "").strip()
                attr = m_atx.group(4) or ""
                nl = m_atx.group(5) or "\n"
                level = len(hashes)

                # 只处理非空标题且未以编号开头的
                if raw_text and not re.match(r'^\d+(\.\d+)*\s+', raw_text):
                    if level == 2:
                        counters[2] += 1
                        counters[3] = 0
                        counters[4] = 0
                        number = f"{counters[2]}"
                    elif level == 3:
                        counters[3] += 1
                        counters[4] = 0
                        number = f"{counters[2]}.{counters[3]}"
                    else:  # level == 4
                        counters[4] += 1
                        number = f"{counters[2]}.{counters[3]}.{counters[4]}"

                    # 保证 attr 前有空格（如果存在）
                    attr_str = (" " + attr.strip()) if attr else ""
                    new_line = f"{indent}{hashes} {number} {raw_text}{attr_str}{nl}"
                    out_lines.append(new_line)
                    i += 1
                    continue
                else:
                    out_lines.append(line)
                    i += 1
                    continue

            # setext 风格的 H2：当前行不是空行且下一行是 '----'（把当前行当作 h2）
            if i + 1 < len(lines):
                if setext_h2_re.match(lines[i + 1]) and not re.match(r'^\s*$', line):
                    textline = line.rstrip("\r\n")
                    text = textline.strip()
                    if text and not re.match(r'^\d+(\.\d+)*\s+', text):
                        counters[2] += 1
                        counters[3] = 0
                        counters[4] = 0
                        number = f"{counters[2]}"

                        # 保留前导空白
                        indent = re.match(r'^(\s*)', line).group(1)
                        new_line = f"{indent}{number} {text}\n"
                        out_lines.append(new_line)
                        # 把 underline 行原样追加
                        out_lines.append(lines[i + 1])
                        i += 2
                        continue

            # 其它情况原样保留
            out_lines.append(line)
            i += 1

        return "".join(out_lines)

    # ---------- HTML 阶段：构建 accordion 结构，但不改动标题文本（编号已在 markdown） ----------
    def on_page_content(self, html, **kwargs):
        soup = BeautifulSoup(html, "html.parser")
        nodes = list(soup.contents)

        current_card_stack = {2: None, 3: None, 4: None}
        output = []

        for node in nodes:
            # 文本节点直接尝试放入最近的 panel（优先 4->3->2），否则放顶层
            if isinstance(node, NavigableString):
                placed = False
                for lvl in (4, 3, 2):
                    card = current_card_stack.get(lvl)
                    if card:
                        panel = card.find("div", class_="panel")
                        if panel is not None:
                            panel.append(node)
                            placed = True
                            break
                if not placed:
                    output.append(node)
                continue

            if not isinstance(node, Tag):
                output.append(node)
                continue

            name = node.name.lower()

            if name in ("h2", "h3", "h4"):
                level = int(name[1])

                # 给标题添加 class（不移除已有 class）
                existing_classes = node.get("class", [])
                if "accordion" not in existing_classes:
                    node["class"] = existing_classes + ["accordion"]

                # 如果还没有左侧图标，则插入一个（放在最前面）
                if not node.find("span", class_="accordion-icon"):
                    icon = soup.new_tag("span", **{"class": "accordion-icon", "aria-hidden": "true"})
                    node.insert(0, icon)

                # 创建 card（不改动 heading 本身的文本；编号已经在 markdown）
                card = soup.new_tag("div", **{"class": f"section-card level-{level}"})
                panel = soup.new_tag("div", **{"class": "panel"})
                card.append(node)
                card.append(panel)

                # 找到最近的父级 panel（从 level-1 向上找），有则放入其 panel，否则放到 output
                parent_panel = None
                for p in range(level - 1, 1, -1):
                    parent_card = current_card_stack.get(p)
                    if parent_card:
                        parent_panel = parent_card.find("div", class_="panel")
                        if parent_panel is not None:
                            break

                if parent_panel:
                    parent_panel.append(card)
                else:
                    output.append(card)

                # 标记当前级别为最近打开的 card，并清除更深级别的引用
                current_card_stack[level] = card
                for deeper in range(level + 1, 5):
                    current_card_stack[deeper] = None

            else:
                # 普通节点：放到最近的 panel，否则顶层
                placed = False
                for lvl in (4, 3, 2):
                    card = current_card_stack.get(lvl)
                    if card:
                        panel = card.find("div", class_="panel")
                        if panel is not None:
                            panel.append(node)
                            placed = True
                            break
                if not placed:
                    output.append(node)

        return "".join(str(n) for n in output)
