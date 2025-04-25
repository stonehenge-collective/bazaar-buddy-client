#!/usr/bin/env python
"""
overlay_text.py  –  Always-on-top, semi-transparent text overlay for Windows.

Usage
-----
# 1) Install PyQt5 once:
#    pip install PyQt5
#
# 2) Display a message:
#    python overlay_text.py "Overlay message here"
#
#    ...or pipe/redirect text:
#    echo Hello world | python overlay_text.py
"""

import sys
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QGuiApplication, QFontMetrics
from PyQt5.QtWidgets import QApplication, QWidget

def get_text() -> str:
    """Return text from argv, stdin, or an interactive prompt."""
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()

    if not sys.stdin.isatty():       # piped data
        data = sys.stdin.read().strip()
        if data:
            return data

    # Fallback prompt
    return input("Enter text to display: ").strip()

class Overlay(QWidget):
    """Frameless, click-through-optional, semi-transparent overlay."""
    PADDING = 32
    BG_COLOR = QColor(0, 0, 0, 180)      # RGBA – alpha 180 ≈ 70 % opacity
    TEXT_COLOR = Qt.white
    FONT = QFont("Segoe UI", 12)

    def __init__(self, text: str):
        super().__init__(flags=(
            Qt.WindowStaysOnTopHint   |  # always on top
            Qt.FramelessWindowHint    |  # no title bar
            Qt.Tool                  ))   # doesn’t appear in task-switcher
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.text = text
        self._layout_overlay()
        self.show()

    # ---------- QWidget overrides ----------

    def paintEvent(self, event):           # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Draw rounded semi-transparent rectangle
        painter.setBrush(self.BG_COLOR)
        painter.setPen(Qt.NoPen)
        rect = self.rect()
        painter.drawRoundedRect(rect, 12, 12)

        # Draw the actual text
        painter.setPen(QPen(self.TEXT_COLOR))
        painter.setFont(self.FONT)
        painter.drawText(rect.adjusted(self.PADDING, self.PADDING,
                                       -self.PADDING, -self.PADDING),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                         self.text)

    def keyPressEvent(self, event):        # noqa: N802
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()

    # ---------- helpers ----------

    def _layout_overlay(self) -> None:
        """Resize the widget so the text fits, then center it on the primary screen."""
        metrics = QFontMetrics(self.FONT)
        max_width = 640                   # wrap text if longer
        text_rect: QRect = metrics.boundingRect(
            0, 0, max_width, 10_000,
            Qt.TextWordWrap, self.text)

        w = text_rect.width()  + 2 * self.PADDING
        h = text_rect.height() + 2 * self.PADDING

        # Ensure we don’t exceed the screen
        screen = QGuiApplication.primaryScreen().geometry()
        w = min(w, screen.width()  - 40)
        h = min(h, screen.height() - 40)
        self.resize(QSize(w, h))

        # Center on screen
        self.move((screen.width()  - w) // 2,
                  (screen.height() - h) // 2)

def main() -> None:
    text = get_text()
    if not text:
        print("No text provided.", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    Overlay(text)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
