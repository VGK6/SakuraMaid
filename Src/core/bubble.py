"""
气泡渲染 - 对话框绘制
"""
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPainterPath

class BubbleRenderer:
    MAX_WIDTH = 220

    def draw(self, p: QPainter, text: str, parent_w: int, anchor_y: int):
        if not text:
            return

        font = QFont('Microsoft YaHei', 11)
        p.setFont(font)
        fm = QFontMetrics(font)

        # 自动换行
        lines, line = [], ""
        for ch in text:
            t = line + ch
            if fm.horizontalAdvance(t) > self.MAX_WIDTH:
                lines.append(line)
                line = ch
            else:
                line = t
        if line:
            lines.append(line)

        lh = fm.height() + 4
        bw, bh = self.MAX_WIDTH + 20, len(lines) * lh + 20
        bx = (parent_w - bw) // 2
        by = anchor_y - bh - 5

        # 气泡背景
        path = QPainterPath()
        path.addRoundedRect(bx, by, bw, bh, 10, 10)
        p.fillPath(path, QColor(255, 255, 255, 235))
        p.setPen(QColor(200, 200, 200))
        p.drawPath(path)

        # 三角尾巴
        cx, cy = parent_w // 2, by + bh
        tri = QPainterPath()
        tri.moveTo(cx - 6, cy)
        tri.lineTo(cx, cy + 8)
        tri.lineTo(cx + 6, cy)
        tri.closeSubpath()
        p.fillPath(tri, QColor(255, 255, 255, 235))
        p.drawPath(tri)

        # 文字
        p.setPen(QColor(50, 50, 50))
        for i, l in enumerate(lines):
            p.drawText(bx + 10, by + 14 + i * lh, l)
