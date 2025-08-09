# plugins/section_cards.py
from mkdocs.plugins import BasePlugin
from bs4 import BeautifulSoup, NavigableString, Tag

class SectionCardsPlugin(BasePlugin):
    def on_page_content(self, html, **kwargs):
        soup = BeautifulSoup(html, "html.parser")
        nodes = list(soup.contents)

        # 计数器与当前打开的卡片（按级别）
        counters = {2: 0, 3: 0, 4: 0}
        current_card_stack = {2: None, 3: None, 4: None}

        # 最终输出的顶级节点列表
        output = []

        for node in nodes:
            # 处理文本节点或其它非 Tag（如换行等）
            if isinstance(node, NavigableString):
                # 放到最近的打开 panel 中，优先级 4 -> 3 -> 2；否则放到输出根
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

                # 更新编号计数器
                if level == 2:
                    counters[2] += 1
                    counters[3] = 0
                    counters[4] = 0
                    number = f"{counters[2]}"
                elif level == 3:
                    counters[3] += 1
                    counters[4] = 0
                    number = f"{counters[2]}.{counters[3]}"
                else:  # h4
                    counters[4] += 1
                    number = f"{counters[2]}.{counters[3]}.{counters[4]}"

                # 给原生标题添加 class 便于前端 JS/CSS 使用（不替换标签）
                existing_classes = node.get("class", [])
                if "accordion" not in existing_classes:
                    node["class"] = existing_classes + ["accordion"]

                # 在标题内部插入左侧三角占位与编号 span（尽量不破坏原有子节点）
                icon = soup.new_tag("span", **{"class": "accordion-icon", "aria-hidden": "true"})
                num_span = soup.new_tag("span", **{"class": "section-number"})
                num_span.string = number + " "

                # 插入顺序： icon, number, 然后原有内容（insert at head)
                node.insert(0, icon)
                node.insert(1, num_span)

                # 创建 card 包裹（title + panel）
                card = soup.new_tag("div", **{"class": f"section-card level-{level}"})
                panel = soup.new_tag("div", **{"class": "panel"})
                card.append(node)
                card.append(panel)

                # 找到最近的父级 panel（level-1 向上查找），有则放入其 panel，否则放到 output 顶层
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

                # 标记当前级别为打开的 card，并清除更深的级别
                current_card_stack[level] = card
                for deeper in range(level + 1, 5):
                    current_card_stack[deeper] = None

            else:
                # 普通节点：放到最近的打开 panel（优先 4->3->2），否则顶层 output
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

        # 返回最终 HTML（保持原有头部 id/permalink 等）
        return "".join(str(n) for n in output)
