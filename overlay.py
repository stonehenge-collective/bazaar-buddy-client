import signal
import sys
from typing import Optional

from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QGuiApplication, QPainter
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from system_handler import OPERATING_SYSTEM

INITIAL_SIZE = QSize(300, 200)  # starting size of the overlay (width × height)
MARGIN = 20  # minimal margin to screen edges


class Overlay(QWidget):
    PADDING = 10
    BG_COLOR = QColor(0, 0, 0)

    if OPERATING_SYSTEM == "Windows":
        FONT = QFont("Segoe UI", 12)
    else:
        FONT = QFont("Helvetica", 12)

    def __init__(self, text: str):
        super().__init__(flags=Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.85)

        self.text = text
        self._drag_pos: Optional[QPoint] = None

        self._build_ui()
        self._layout_overlay()
        self._update_close_button_position()

        self.show()
        self.raise_()
        self.activateWindow()

    # ---------- QWidget overrides ----------

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.BG_COLOR)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    # ––– dragging –––
    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()

    def resizeEvent(self, event):  # noqa: N802
        new_width = event.size().width()
        self.label.setFixedWidth(max(0, new_width - 2 * self.PADDING))

        grip_w = self.size_grips[0].sizeHint().width()
        grip_h = self.size_grips[0].sizeHint().height()
        self.size_grips[0].move(0, 0)
        self.size_grips[1].move(self.width() - grip_w, 0)
        self.size_grips[2].move(0, self.height() - grip_h)
        self.size_grips[3].move(self.width() - grip_w, self.height() - grip_h)

        self._update_close_button_position()
        super().resizeEvent(event)

    # ---------- helpers ----------

    def _build_ui(self) -> None:
        # ----- Text inside a scroll area -----
        self.label = QLabel(self.text, wordWrap=True,
                            alignment=Qt.AlignLeft | Qt.AlignTop)
        self.label.setFont(self.FONT)
        self.label.setStyleSheet("color: white; background: transparent;")
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.scroll = QScrollArea(frameShape=QScrollArea.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.label)
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.viewport().setStyleSheet("background: transparent;")

        # ----- Main layout -----
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.PADDING, self.PADDING,
                                  self.PADDING, self.PADDING)
        layout.addWidget(self.scroll)

        # ----- Corner size grips -----
        self.size_grips = [QSizeGrip(self) for _ in range(4)]
        for g in self.size_grips:
            g.setStyleSheet("background: transparent;")

        # ----- Close button -----
        self.close_button = QPushButton("✕", self, toolTip="Close (Esc or Q)")
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(
            "QPushButton{color:white;background:rgba(255,255,255,0);"
            "border:none;font-weight:bold;}"
            "QPushButton:hover{background:rgba(255,255,255,0.2);}"
        )
        self.close_button.raise_()

        # ----- Style the vertical scrollbar -----
        bar = self.scroll.verticalScrollBar()
        top_margin = self.close_button.height() + self.PADDING // 2
        bar.setStyleSheet(f"""
            QScrollBar:vertical {{
                background: transparent;
                width: 12px;
                margin: {top_margin}px 0 {self.PADDING // 2}px 0;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255,255,255,0.35);
                min-height: 20px;
                border-radius: 6px;
            }}
            /* hide arrow buttons */
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                width: 0px;
            }}
            /* no coloured “pages” above/below the handle */
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def _layout_overlay(self) -> None:
        screen_geom = QGuiApplication.primaryScreen().geometry()
        s_w, s_h = screen_geom.width(), screen_geom.height()

        w = min(INITIAL_SIZE.width(), s_w - 2 * MARGIN)
        h = min(INITIAL_SIZE.height(), s_h - 2 * MARGIN)
        self.resize(QSize(w, h))

        centre_x = int(s_w * 0.9)
        centre_y = int(s_h * 0.7)

        x = max(MARGIN, min(s_w - w - MARGIN, centre_x - w // 2))
        y = max(MARGIN, min(s_h - h - MARGIN, centre_y - h // 2))
        self.move(x, y)

    # ---------- utility ----------

    def _update_close_button_position(self) -> None:
        """Keep the button glued to the top-right corner (inside padding)."""
        self.close_button.move(
            self.width() - self.close_button.width() - self.PADDING // 2,
            self.PADDING // 2,
        )

    def set_message(self, text: str) -> None:
        if text == self.text:
            return
        self.text = text
        self.label.setText(text)
        self.scroll.verticalScrollBar().setValue(0)

def main() -> None:
    text = (
        "ter text to display:  display: asldfjalskdfj;alskdjf;alksdfj;alkdfj;alksdfj; "
        "alskdfj;alksnvzx,mcnv;qoirjtg;alksdjf;zlkjf;alksdjfa;lskdfja;ld"
    )  # get_text()
    app = QApplication(sys.argv)

    _ = Overlay(text)  # keep a reference so the window isn’t garbage‑collected

    # Allow Ctrl‑C to terminate from console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
