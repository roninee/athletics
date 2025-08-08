# mkdocs_section_cards/plugin.py
from bs4 import BeautifulSoup
from mkdocs.plugins import BasePlugin

class SectionCardsPlugin(BasePlugin):
    def on_page_content(self, html, page, config, files):
        soup = BeautifulSoup(html, "html.parser")
        nodes = list(soup.contents)

        counters = {2: 0, 3: 0, 4: 0}
        stack = {2: None, 3: None, 4: None}
        result = []

        def find_parent(level):
            # 找到最近的父级 card（level-1, level-2 ...）
            for p in range(level-1, 1, -1):
                if stack.get(p):
                    return stack[p]
            return None

        for node in nodes:
            name = getattr(node, "name", None)
            if name in ("h2", "h3", "h4"):
                level = int(name[1])
                # 更新计数器
                if level == 2:
                    counters[2] += 1
                    counters[3] = counters[4] = 0
                    number = f"{counters[2]}"
                elif level == 3:
                    counters[3] += 1
                    counters[4] = 0
                    number = f"{counters[2]}.{counters[3]}"
                else:
                    counters[4] += 1
                    number = f"{counters[2]}.{counters[3]}.{counters[4]}"

                # 在标题最前插入编号 span
                num_span = soup.new_tag("span", **{"class": "section-number"})
                num_span.string = number + " "
                node.insert(0, num_span)

                # 添加折叠按钮占位
                btn = soup.new_tag("button", **{"class": "collapse-btn", "data-level": str(level), "aria-expanded": "true"})
                btn.string = "−"
                node.append(btn)

                # 创建 card 与 content 容器
                card = soup.new_tag("div", **{"class": f"section-card level-{level}"})
                content_div = soup.new_tag("div", **{"class": "section-content"})
                card.append(node)
                card.append(content_div)

                parent = find_parent(level)
                if parent is None:
                    result.append(card)
                else:
                    parent.find("div", {"class": "section-content"}).append(card)

                # 记录当前打开的卡片（用于把后续节点放入）
                stack[level] = card
                # 清除更低级别的 open 状态
                for deeper in range(level + 1, 5):
                    stack[deeper] = None
            else:
                # 普通节点：放到最近的 open 卡片的 content 中，优先级 4->3->2
                placed = False
                for lvl in (4, 3, 2):
                    if stack.get(lvl):
                        stack[lvl].find("div", {"class": "section-content"}).append(node)
                        placed = True
                        break
                if not placed:
                    result.append(node)

        return "".join(str(n) for n in result)
