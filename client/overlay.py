import signal
import sys
from typing import Optional

from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QGuiApplication, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


INITIAL_SIZE = QSize(300, 200)  # starting size of the overlay (width × height)
MARGIN = 20                      # minimal margin to screen edges

class Overlay(QWidget):
    PADDING = 16
    BG_COLOR = QColor(0, 0, 0)  # painted with opacity; see __init__
    FONT = QFont("Segoe UI", 12)

    def __init__(self, text: str):
        super().__init__(flags=Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Overall translucency (85 % opaque)
        self.setWindowOpacity(0.85)
        self.text = text
        self._drag_pos: Optional[QPoint] = None

        # Build & layout UI
        self._build_ui()
        self._layout_overlay()

        # Expose window
        self.show()
        self.raise_()
        self.activateWindow()

    # ---------- QWidget overrides ----------

    def paintEvent(self, event):  # noqa: N802
        """Paint rounded translucent background; the text itself is drawn by QLabel."""
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
        """Keep label width in sync with viewport and reposition size grips."""
        new_width = event.size().width()
        self.label.setFixedWidth(max(0, new_width - 2 * self.PADDING))

        grip_w, grip_h = self.size_grips[0].sizeHint().width(), self.size_grips[0].sizeHint().height()
        # top‑left, top‑right, bottom‑left, bottom‑right
        self.size_grips[0].move(0, 0)
        self.size_grips[1].move(self.width() - grip_w, 0)
        self.size_grips[2].move(0, self.height() - grip_h)
        self.size_grips[3].move(self.width() - grip_w, self.height() - grip_h)

        super().resizeEvent(event)

    # ---------- helpers ----------

    def _build_ui(self) -> None:
        """Create scrollable label and four corner size grips for resizing."""
        self.label = QLabel(self.text)
        self.label.setFont(self.FONT)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label.setStyleSheet("color: white; background: transparent;")
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.label)

        # Keep viewport transparent so the dark background shows through
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.viewport().setStyleSheet("background: transparent;")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.PADDING, self.PADDING, 0, self.PADDING)
        layout.addWidget(self.scroll)

        # Four corner size grips
        self.size_grips = [QSizeGrip(self) for _ in range(4)]
        for g in self.size_grips:
            g.setStyleSheet("background: transparent;")

    def _layout_overlay(self) -> None:
        """Resize the window to INITIAL_SIZE and put its **centre**
        at 80 % of the screen width and 50 % of the screen height."""
        screen_geom = QGuiApplication.primaryScreen().geometry()
        s_w, s_h = screen_geom.width(), screen_geom.height()

        # Make sure the window fits on-screen
        w = min(INITIAL_SIZE.width(),  s_w - 2 * MARGIN)
        h = min(INITIAL_SIZE.height(), s_h - 2 * MARGIN)
        self.resize(QSize(w, h))

        # Desired centre point for the window
        centre_x = int(s_w * 0.9)
        centre_y = int(s_h * 0.7)

        # Convert that centre point to the window’s top-left coordinates,
        # then clamp so we never collide with the screen margin.
        x = max(MARGIN, min(s_w - w - MARGIN, centre_x - w // 2))
        y = max(MARGIN, min(s_h - h - MARGIN, centre_y - h // 2))

        self.move(x, y)

    def set_message(self, text: str) -> None:
        if text == self.text:
            return
        self.text = text
        self.label.setText(text)
        self.scroll.verticalScrollBar().setValue(0)

def main() -> None:
    text = "ter text to display:  display: asldfjalskdfj;alskdjf;alksdfj;alkdfj;alksdfj; alskdfj;alksnvzx,mcnv;qoirjtg;alksdjf;zlkjf;alksdjfa;lskdfja;ld"#get_text()
    app = QApplication(sys.argv)

    _ = Overlay(text)  # keep a reference so the window isn't garbage‑collected

    # Allow Ctrl‑C to terminate from console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
