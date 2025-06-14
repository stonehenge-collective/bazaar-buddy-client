from __future__ import annotations

from typing import Optional, Dict

from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal, QEvent, QObject
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPaintEvent, QMouseEvent, QKeyEvent, QResizeEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QToolButton,
)

# ──────────────────────────  constants  ──────────────────────────
INITIAL_SIZE = QSize(300, 200)  # starting overlay size
MARGIN = 20  # min distance to screen edge (px)
PADDING = 10
BG_COLOR = QColor(0, 0, 0)  # semi-transparent black
# ─────────────────────────────────────────────────────────────────


class Overlay(QWidget):
    """Always-on-top, frameless, draggable, resizable overlay with
    optional ‘Yes/No’ prompt buttons."""

    yes_clicked = pyqtSignal()
    no_clicked = pyqtSignal()
    about_to_close = pyqtSignal()

    # ──────────────────────────  life-cycle  ─────────────────────
    def __init__(self, text: str, configuration, file_writer=None) -> None:
        super().__init__(flags=Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(0.85)

        self._font = QFont("Segoe UI" if configuration.operating_system == "Windows" else "Helvetica", 12)
        self.text = text
        self._drag_pos: Optional[QPoint] = None  # start corner while dragging
        self._file_writer = file_writer
        self._saved_position = self._load_saved_position()

        self._build_ui()
        self.label.installEventFilter(self)
        self.scroll_area.viewport().installEventFilter(self)  # type: ignore

        self._layout_overlay()
        self._update_button_positions()

        self.show()
        self.raise_()
        self.activateWindow()

        # ───────────────────────  event filter  ───────────────────────

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        from PyQt6.QtGui import QMouseEvent  # local import to avoid circular issues

        if obj in (self.label, self.scroll_area.viewport()) and isinstance(
            event, QMouseEvent
        ):  # ensure we have a mouse event
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return True

            if (
                event.type() == QEvent.Type.MouseMove
                and self._drag_pos is not None
                and (event.buttons() & Qt.MouseButton.LeftButton)
            ):
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return True

            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_pos = None
                event.accept()
                return True

        return super().eventFilter(obj, event)

    # ──────────────────────────  paint  ──────────────────────────
    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(BG_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    # ──────────────────────  mouse interaction  ─────────────────
    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            # globalPosition() → QPointF in Qt 6; convert to QPoint for arithmetic
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._drag_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ───────────────────────  key handling  ────────────────────
    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self._save_position()
            self.about_to_close.emit()  # type: ignore[attr-defined]
            self.close()
        else:
            super().keyPressEvent(event)

    # ───────────────────────  resize handling  ─────────────────
    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        """Keep the size-grips & buttons where they belong."""
        grip_w = self.size_grips[0].sizeHint().width()
        grip_h = self.size_grips[0].sizeHint().height()

        self.size_grips[0].move(-grip_w, -grip_h)
        self.size_grips[1].move(self.width() - grip_w, 0)
        self.size_grips[2].move(0, self.height() - grip_h)
        self.size_grips[3].move(self.width() - grip_w, self.height() - grip_h)

        self._update_button_positions()
        super().resizeEvent(event)

    # ─────────────────────────  UI building  ─────────────────────
    def _build_ui(self) -> None:
        self.search_bar = QLineEdit(self)
        self.search_bar.setFont(self._font)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFixedHeight(24)
        self.search_bar.setStyleSheet(
            """
            QLineEdit {
                color: white;
                background: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.40);
                border-radius: 4px;
            }
            QLineEdit::placeholder {
                color: rgba(255,255,255,0.50);   /* semi-transparent */
            }
            """
        )
        self.search_bar.hide()

        # ── main text inside scroll-area ──
        self.label = QLabel(
            self.text,
        )
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setFont(self._font)
        self.label.setStyleSheet("color:white;background:transparent;")
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.label.setContentsMargins(1, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setStyleSheet("background:transparent;")
        self.scroll_area.viewport().setStyleSheet("background:transparent;")  # type: ignore

        # ── container layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)  # right margin now = PADDING
        layout.addWidget(self.search_bar)
        layout.addWidget(self.scroll_area)  # type: ignore

        # ── corner size-grips ──
        self.size_grips = [QSizeGrip(self) for _ in range(4)]
        for g in self.size_grips:
            g.setStyleSheet("background:transparent;")
            g.raise_()

        # ── close button ──
        self.close_button = QPushButton("✕", self)
        self.close_button.setToolTip("Close (Esc or Q)")
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(self.close)
        self.close_button.clicked.connect(self._handle_close)
        self.close_button.setStyleSheet(
            "QPushButton{color:white;background:rgba(255,255,255,0);border:none;font-weight:bold;}"
            "QPushButton:hover{background:rgba(255,255,255,0.2);}"
        )
        self.close_button.raise_()

        self.toggle_button = QToolButton(self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.clicked.connect(self._toggle_content)
        self.toggle_button.setStyleSheet(
            "QToolButton{color:white;background:rgba(255,255,255,0);border:none;font-weight:bold;}"
            "QToolButton:hover{background:rgba(255,255,255,0.2);}"
        )
        self.toggle_button.setText("-")

        # ── custom scroll-bar style ──
        bar = self.scroll_area.verticalScrollBar()
        bar.setStyleSheet(  # type: ignore
            f"""
            QScrollBar:vertical {{
                background:transparent;
                width:12px;
                margin:12px 0 0px 0;
                border:none;
            }}
            QScrollBar::handle:vertical {{
                background:rgba(255,255,255,0.35);
                min-height:20px;
                border-radius:6px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height:0px; width:0px;                     /* hide arrows   */
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background:none;                           /* hide ‘pages’ */
            }}"""
        )

    # ──────────────────────────  geometry  ───────────────────────
    def _layout_overlay(self) -> None:
        screen = QGuiApplication.primaryScreen().geometry()  # type: ignore
        s_w, s_h = screen.width(), screen.height()

        # Use saved position if available, otherwise use defaults
        if self._saved_position:
            w = max(200, min(self._saved_position.get("width", INITIAL_SIZE.width()), s_w - 2 * MARGIN))
            h = max(150, min(self._saved_position.get("height", INITIAL_SIZE.height()), s_h - 2 * MARGIN))
            self.resize(QSize(w, h))

            x = max(MARGIN, min(s_w - w - MARGIN, self._saved_position.get("x", int(s_w * 0.9) - w // 2)))
            y = max(MARGIN, min(s_h - h - MARGIN, self._saved_position.get("y", int(s_h * 0.7) - h // 2)))
            self.move(x, y)
        else:
            # Default positioning logic
            w = min(INITIAL_SIZE.width(), s_w - 2 * MARGIN)
            h = min(INITIAL_SIZE.height(), s_h - 2 * MARGIN)
            self.resize(QSize(w, h))

            centre_x = int(s_w * 0.9)
            centre_y = int(s_h * 0.7)

            x = max(MARGIN, min(s_w - w - MARGIN, centre_x - w // 2))
            y = max(MARGIN, min(s_h - h - MARGIN, centre_y - h // 2))
            self.move(x, y)

    # ──────────────────────  internal helpers  ───────────────────
    def _update_button_positions(self) -> None:
        # ── position the two buttons ──
        right_edge = self.width() - PADDING // 2
        self.close_button.move(right_edge - self.close_button.width(), self.search_bar.y())
        self.toggle_button.move(self.close_button.x() - self.toggle_button.width(), self.search_bar.y())

        # ── keep the search bar clear of the buttons ──
        available_w = self.toggle_button.x() - PADDING - 2  # leave the normal left margin
        self.search_bar.setFixedWidth(available_w)

    def set_message(self, text: str) -> None:
        if text == self.text:
            return
        self.text = text
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setText(text)
        self.scroll_area.verticalScrollBar().setValue(0)  # type: ignore

    def _toggle_content(self) -> None:
        if self.toggle_button.isChecked():
            self.scroll_area.hide()
            self._collapsed_height = self.height()
            self.setFixedHeight(self.search_bar.height())# + PADDING*2)
            self.toggle_button.setText("+")
        else:
            if hasattr(self, "_collapsed_height"):
                self.scroll_area.show()
                self.setFixedHeight(self._collapsed_height)
                self.setMinimumHeight(0)
                self.setMaximumHeight(16777215)
            self.toggle_button.setText("-")

    # ───── prompt-button public API ─────
    def show_prompt_buttons(self, question: str, yes_text: str | None = None, no_text: str | None = None) -> None:
        self.set_message(question)

        self.button_container = QWidget(self)
        button_layout = QHBoxLayout(self.button_container)

        if yes_text:
            yes_btn = QPushButton(yes_text, self)
            yes_btn.setStyleSheet("background:#4CAF50;color:white;border-radius:4px;padding:6px;")
            yes_btn.clicked.connect(lambda: self._handle_button_click(True))
            button_layout.addWidget(yes_btn)

        if no_text:
            no_btn = QPushButton(no_text, self)
            no_btn.setStyleSheet("background:#F44336;color:white;border-radius:4px;padding:6px;")
            no_btn.clicked.connect(lambda: self._handle_button_click(False))
            button_layout.addWidget(no_btn)

        self.button_container.setGeometry(PADDING, self.height() - 50 - PADDING, self.width() - 2 * PADDING, 50)
        self.button_container.show()

    def _handle_button_click(self, is_yes: bool) -> None:
        self.hide_prompt_buttons()
        (self.yes_clicked if is_yes else self.no_clicked).emit()

    def hide_prompt_buttons(self) -> None:
        if hasattr(self, "button_container") and self.button_container:
            self.button_container.hide()
            self.button_container.deleteLater()
            self.button_container = None

    def _load_saved_position(self) -> Optional[Dict[str, int]]:
        """Load saved overlay position from config file."""
        if not self._file_writer:
            return None

        try:
            if self._file_writer.exists():
                config_data = self._file_writer.read()
                if config_data and config_data.overlay_position:
                    return config_data.overlay_position
        except Exception:
            # If loading fails, just use default position
            pass
        return None

    def _save_position(self) -> None:
        """Save the current overlay position and size to config."""
        if self._file_writer:
            try:
                # Read current config
                config_data = self._file_writer.read()
                if not config_data:
                    from file_writer import ConfigData

                    config_data = ConfigData()

                # Update overlay position
                pos = self.pos()
                size = self.size()
                config_data.update_overlay_position(pos.x(), pos.y(), size.width(), size.height())

                # Save to file
                self._file_writer.write(config_data)
            except Exception:
                # Silently fail - position saving is not critical
                pass

    def _handle_close(self) -> None:
        self._save_position()
        self.about_to_close.emit()
