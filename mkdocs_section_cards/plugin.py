# plugins/section_cards.py
import re
from mkdocs.plugins import BasePlugin
from bs4 import BeautifulSoup, NavigableString, Tag

class SectionCardsPlugin(BasePlugin):
    """
    两阶段插件：
      1) on_page_markdown: 在 markdown 源里给 h2/h3/h4 编号（MkDocs 的 TOC 由此识别编号）
      2) on_page_content: 在生成的 HTML 中保留原生 <h2/h3/h4>，插入 accordion icon，并把标题与后续内容包装成 .section-card/.panel 嵌套
         并且在构建时递归统计 panel 的行数（包含图片、段落、列表、代码等），父节点会包含子节点统计（child_total + 1）。
    """

    # ---------- markdown 阶段：在生成 HTML 前修改 markdown 文本，确保 TOC 能识别编号 ----------
    def on_page_markdown(self, markdown, page=None, config=None, files=None):
        lines = markdown.splitlines(keepends=True)

        fence_re = re.compile(r'^(\s*)(`{3,}|~{3,})(.*)\r?\n?$')
        atx_re = re.compile(r'^(\s{0,3})(#{2,4})\s*(.*?)\s*(\{[^\}]*\}\s*)?(\r?\n)?$')
        setext_h2_re = re.compile(r'^\s*-{2,}\s*(\r?\n)?$')

        in_fence = False
        fence_marker = None

        counters = {2: 0, 3: 0, 4: 0}
        out_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # fenced code block handling
            m_fence = fence_re.match(line)
            if m_fence:
                marker = m_fence.group(2)
                if not in_fence:
                    in_fence = True
                    fence_marker = marker
                else:
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

            # ATX headings (##/###/####)
            m_atx = atx_re.match(line)
            if m_atx:
                indent = m_atx.group(1) or ""
                hashes = m_atx.group(2)
                raw_text = (m_atx.group(3) or "").strip()
                attr = m_atx.group(4) or ""
                nl = m_atx.group(5) or "\n"
                level = len(hashes)

                # 只为未以数字开头的标题添加编号
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

                    attr_str = (" " + attr.strip()) if attr else ""
                    new_line = f"{indent}{hashes} {number} {raw_text}{attr_str}{nl}"
                    out_lines.append(new_line)
                    i += 1
                    continue
                else:
                    out_lines.append(line)
                    i += 1
                    continue

            # setext H2 (underline with ---)
            if i + 1 < len(lines):
                if setext_h2_re.match(lines[i + 1]) and not re.match(r'^\s*$', line):
                    textline = line.rstrip("\r\n")
                    text = textline.strip()
                    if text and not re.match(r'^\d+(\.\d+)*\s+', text):
                        counters[2] += 1
                        counters[3] = 0
                        counters[4] = 0
                        number = f"{counters[2]}"

                        indent = re.match(r'^(\s*)', line).group(1)
                        new_line = f"{indent}{number} {text}\n"
                        out_lines.append(new_line)
                        out_lines.append(lines[i + 1])
                        i += 2
                        continue

            out_lines.append(line)
            i += 1

        return "".join(out_lines)


    # ---------- HTML 阶段：构建 accordion 结构，并在构建时递归统计行数（计入子卡片） ----------
    def on_page_content(self, html, **kwargs):
        soup = BeautifulSoup(html, "html.parser")
        nodes = list(soup.contents)

        current_card_stack = {2: None, 3: None, 4: None}
        output = []

        # first pass: build nested section-card / panel structure (preserve original headings)
        for node in nodes:
            # text nodes -> put into nearest panel (4->3->2) else root
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

                # add accordion class (preserve existing)
                existing_classes = node.get("class", [])
                if "accordion" not in existing_classes:
                    node["class"] = existing_classes + ["accordion"]

                # insert icon if missing
                if not node.find("span", class_="accordion-icon"):
                    icon = soup.new_tag("span", **{"class": "accordion-icon", "aria-hidden": "true"})
                    node.insert(0, icon)

                # create card and panel
                card = soup.new_tag("div", **{"class": f"section-card level-{level}"})
                panel = soup.new_tag("div", **{"class": "panel"})
                card.append(node)
                card.append(panel)

                # insert into nearest parent panel (level-1 upward), else root output
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

                current_card_stack[level] = card
                for deeper in range(level + 1, 5):
                    current_card_stack[deeper] = None

            else:
                # normal node -> put in nearest open panel or root
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

        # -------------------------------------------------------------------
        # now we have nested section-card elements inside `output` list.
        # We'll recursively compute totals for each card:
        #   total_for_card = own_lines_excluding_child_cards + sum(child_total + 1)
        # where +1 accounts for the child header itself.
        # -------------------------------------------------------------------

        def count_in_node(node):
            """统计单个 node 的行数（不进入 class=section-card 的子树）"""
            total = 0
            if isinstance(node, NavigableString):
                lines = [l for l in str(node).splitlines() if l.strip()]
                return len(lines)
            if not isinstance(node, Tag):
                return 0
            # skip nested cards entirely
            if "section-card" in (node.get("class") or []):
                return 0
            name = node.name.lower()

            # 图片直接算 1 行（并且这里也会统计 <img> 在 <p> 内的情况）
            if name == "img":
                return 1
            if name == "li":
                return 1
            if name == "pre":
                pre_lines = node.get_text("\n").split("\n")
                return sum(1 for l in pre_lines if l.strip())

            # 对于 p/blockquote/td/th：统计文字行 + 内部 <img> 个数
            if name in ("p", "blockquote", "td", "th"):
                lines = node.get_text("\n").split("\n")
                text_count = sum(1 for l in lines if l.strip())
                # count images inside this node (not entering nested section-card because those were skipped above)
                img_count = len(node.find_all("img"))
                return text_count + img_count

            # aggregate for generic container tags (recurse)
            for child in node.children:
                total += count_in_node(child)
            return total

        def count_own_panel_lines(panel_tag):
            """统计 panel 顶层 children 的行数（不进入 nested section-card）"""
            total = 0
            for child in panel_tag.children:
                total += count_in_node(child)
            return total

        # 递归：计算单个 card 的 total（包含子卡片贡献），并在 heading 上插入 badge
        def compute_card_total(card_tag):
            # find its direct panel (should exist)
            panel = None
            for ch in card_tag.contents:
                if isinstance(ch, Tag) and ch.name == "div" and "panel" in (ch.get("class") or []):
                    panel = ch
                    break
            if panel is None:
                own = 0
                children_total = 0
            else:
                own = count_own_panel_lines(panel)
                children_total = 0
                # find immediate child cards (direct children in panel)
                for child in list(panel.children):
                    if isinstance(child, Tag) and "section-card" in (child.get("class") or []):
                        ctot = compute_card_total(child)  # recursion: computes child's badge too
                        # add child's total + 1 (for the child header itself)
                        children_total += (ctot + 1)
                # note: count_own_panel_lines already ignored nested section-card content

            total = own + children_total

            # insert/update badge on this card's heading
            heading = None
            for c in card_tag.contents:
                if isinstance(c, Tag) and c.name and c.name.lower() in ("h2", "h3", "h4"):
                    heading = c
                    break
            if heading is not None:
                existing = heading.find("span", class_="accordion-badge")
                if existing:
                    existing.string = "空" if total == 0 else f"{total} 行"
                else:
                    badge = BeautifulSoup("", "html.parser").new_tag("span")
                    badge["class"] = "accordion-badge"
                    badge.string = "空" if total == 0 else f"{total} 行"
                    heading.append(badge)

            return total

        # run compute on top-level output items to annotate badges recursively
        for top in output:
            if isinstance(top, Tag):
                # traverse to find section-cards in output
                if "section-card" in (top.get("class") or []):
                    compute_card_total(top)
                else:
                    # top may be a container; find any direct section-card children within it
                    for child in top.find_all("div", class_="section-card", recursive=False):
                        compute_card_total(child)

        return "".join(str(n) for n in output)
