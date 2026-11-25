from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class QuickSwitcher(QDialog):
    tab_selected = pyqtSignal(int, int)

    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Quick Switcher")
        self.setFixedSize(520, 420)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 12px; }
            QLineEdit { background-color: #2a2a2a; color: #ffffff; border: 1px solid #3a3a3a; padding: 12px 16px; font-size: 15px; border-radius: 10px; }
            QLineEdit:focus { border: 1px solid #4a9eff; }
            QListWidget { background-color: transparent; color: #ffffff; border: none; font-size: 14px; outline: none; }
            QListWidget::item { padding: 10px 14px; border-radius: 8px; margin: 2px 4px; }
            QListWidget::item:selected { background-color: #2a2a2a; }
            QListWidget::item:hover { background-color: #252525; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск вкладок...")
        self.search_input.textChanged.connect(self.filter_tabs)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.itemActivated.connect(self.on_selected)
        self.list_widget.installEventFilter(self)
        layout.addWidget(self.list_widget)

        self.all_tabs = browser.collect_all_tabs()
        self._render_tabs()
        self.search_input.setFocus()

    def _render_tabs(self, filter_text=""):
        self.list_widget.clear()
        filter_text = filter_text.lower()
        for t in self.all_tabs:
            if filter_text and filter_text not in t["title"].lower() and filter_text not in t["url"].lower():
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, t)
            frame = QFrame()
            frame.setStyleSheet("background: transparent;")
            lay = QHBoxLayout(frame)
            lay.setContentsMargins(4, 4, 4, 4)
            lay.setSpacing(10)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {t['space_color']}; font-size: 14px;")
            lay.addWidget(dot)
            info = QVBoxLayout()
            info.setSpacing(2)
            title_lbl = QLabel(t["title"][:60])
            title_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 500;")
            info.addWidget(title_lbl)
            url_lbl = QLabel(t["url"][:70])
            url_lbl.setStyleSheet("color: #8a8a8a; font-size: 11px;")
            info.addWidget(url_lbl)
            lay.addLayout(info)
            lay.addStretch()
            space_lbl = QLabel(t["space_name"])
            space_lbl.setStyleSheet(f"color: {t['space_color']}; font-size: 11px; font-weight: 600;")
            lay.addWidget(space_lbl)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, frame)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_tabs(self, text):
        self._render_tabs(text)

    def on_selected(self, item):
        data = item.data(Qt.UserRole)
        if data:
            self.tab_selected.emit(data["space_index"], data["tab_index"])
            self.accept()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Down:
                row = self.list_widget.currentRow()
                if row < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(row + 1)
                return True
            elif event.key() == Qt.Key_Up:
                row = self.list_widget.currentRow()
                if row > 0:
                    self.list_widget.setCurrentRow(row - 1)
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                item = self.list_widget.currentItem()
                if item:
                    self.on_selected(item)
                return True
            elif event.key() == Qt.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, event)