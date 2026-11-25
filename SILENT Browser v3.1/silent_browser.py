import sys
import json
import os
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabBar,
    QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QWidget, QDialog, QLabel, QComboBox, QColorDialog,
    QFrame, QFileDialog, QScrollArea, QProgressBar,
    QListWidget, QListWidgetItem, QMenu, QSizePolicy,
    QStyle, QStyleOptionTab, QShortcut, QSlider,
    QInputDialog, QMessageBox, QCheckBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QSize, QRect
from PyQt5.QtGui import QColor, QPalette, QFont, QKeySequence, QCursor, QPainter

from silent_connect import ConnectManager, ConnectPopup
from silent_spaces import SpacesManager
from silent_speeddial import generate_speed_dial_html
from silent_translator import TranslatorDialog
from silent_switcher import QuickSwitcher


# ======================================================================
# УПРАВЛЕНИЕ SPEED DIAL (Qt-диалог)
# ======================================================================

def load_speed_dial():
    if os.path.exists("silent_speeddial.json"):
        try:
            with open("silent_speeddial.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_speed_dial(tiles):
    with open("silent_speeddial.json", "w", encoding="utf-8") as f:
        json.dump(tiles, f, ensure_ascii=False, indent=2)


class SpeedDialManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление Speed Dial")
        self.setFixedSize(500, 500)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #202124; font-size: 16px; font-weight: 600; }
            QListWidget { background-color: #ffffff; color: #202124;
                border: 1px solid #dadce0; border-radius: 8px; font-size: 14px; padding: 5px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #f1f3f4; }
            QListWidget::item:selected { background-color: #e8f0fe; color: #1a73e8; }
            QPushButton { background-color: #1a73e8; color: #ffffff;
                border: none; padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton#secondary { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; }
            QPushButton#secondary:hover { background-color: #f8f9fa; }
            QPushButton#danger { background-color: #d93025; }
            QPushButton#danger:hover { background-color: #b3261e; }
            QLineEdit { background-color: #ffffff; color: #202124;
                border: 1px solid #dadce0; padding: 10px 12px; font-size: 14px; border-radius: 8px; }
            QLineEdit:focus { border: 2px solid #1a73e8; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        layout.addWidget(QLabel("Speed Dial — любимые сайты"))

        self.list_widget = QListWidget()
        self.tiles = load_speed_dial()
        self._refresh_list()
        layout.addWidget(self.list_widget)

        form_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название")
        form_layout.addWidget(self.title_input)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL (например: youtube.com)")
        form_layout.addWidget(self.url_input)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(50)
        add_btn.clicked.connect(self.add_tile)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("Изменить")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_tile)
        del_btn = QPushButton("Удалить")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self.delete_tile)
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _refresh_list(self):
        self.list_widget.clear()
        for tile in self.tiles:
            item = QListWidgetItem(f"{tile['title']}  —  {tile['url']}")
            self.list_widget.addItem(item)

    def add_tile(self):
        title = self.title_input.text().strip()
        url = self.url_input.text().strip()
        if not title or not url:
            QMessageBox.warning(self, "Ошибка", "Заполните название и URL")
            return
        if not url.startswith("http"):
            url = "https://" + url
        self.tiles.append({"title": title, "url": url})
        save_speed_dial(self.tiles)
        self.title_input.clear()
        self.url_input.clear()
        self._refresh_list()

    def edit_tile(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.row(item)
        tile = self.tiles[idx]
        new_title, ok = QInputDialog.getText(self, "Название", "Новое название:", text=tile['title'])
        if not ok:
            return
        new_url, ok = QInputDialog.getText(self, "URL", "Новый URL:", text=tile['url'])
        if not ok:
            return
        self.tiles[idx] = {"title": new_title, "url": new_url}
        save_speed_dial(self.tiles)
        self._refresh_list()

    def delete_tile(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.row(item)
        self.tiles.pop(idx)
        save_speed_dial(self.tiles)
        self._refresh_list()


# ======================================================================
# КАСТОМНЫЙ TAB BAR (крестик слева, тонкие разделители)
# ======================================================================

class SilentTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setMovable(False)
        self.setTabsClosable(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            self.style().drawControl(QStyle.CE_TabBarTab, opt, painter)
            rect = self.tabRect(i)
            close_rect = QRect(rect.left() + 6, rect.center().y() - 6, 12, 12)
            hover = close_rect.contains(self.mapFromGlobal(QCursor.pos()))
            painter.setPen(Qt.NoPen)
            if hover:
                painter.setBrush(QColor("#d93025"))
                painter.drawRoundedRect(close_rect, 3, 3)
            else:
                is_dark = opt.palette.window().color().lightness() < 128
                painter.setBrush(QColor("#5f6368") if is_dark else QColor("#80868b"))
                painter.drawRoundedRect(close_rect, 3, 3)
            painter.setPen(QColor("#ffffff" if hover else ("#1a1a1a" if opt.palette.window().color().lightness() < 128 else "#ffffff")))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(close_rect.left() + 3, close_rect.top() + 3,
                             close_rect.right() - 3, close_rect.bottom() - 3)
            painter.drawLine(close_rect.left() + 3, close_rect.bottom() - 3,
                             close_rect.right() - 3, close_rect.top() + 3)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for i in range(self.count()):
                rect = self.tabRect(i)
                close_rect = QRect(rect.left() + 6, rect.center().y() - 6, 12, 12)
                if close_rect.contains(event.pos()):
                    self.tabCloseRequested.emit(i)
                    return
        super().mousePressEvent(event)


# ======================================================================
# НАСТРОЙКИ БРАУЗЕРА
# ======================================================================

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(540, 760)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #202124; font-size: 14px; font-weight: 500; }
            QLabel#section { font-size: 16px; font-weight: 600; margin-top: 15px; margin-bottom: 8px; }
            QComboBox { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; padding: 10px 15px; font-size: 14px; border-radius: 8px; }
            QComboBox:hover { border: 1px solid #202124; }
            QPushButton { background-color: #1a73e8; color: #ffffff; border: none; padding: 12px 30px; font-size: 14px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton#color-btn { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; padding: 10px 20px; font-size: 14px; border-radius: 8px; }
            QPushButton#color-btn:hover { background-color: #f8f9fa; border: 1px solid #202124; }
            QPushButton#cancel { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; }
            QPushButton#cancel:hover { background-color: #f8f9fa; }
            QPushButton#default-btn { background-color: #5f6368; color: #ffffff; }
            QPushButton#default-btn:hover { background-color: #3c4043; }
            QSlider::groove:horizontal { background: #dadce0; height: 4px; border-radius: 2px; }
            QSlider::handle:horizontal { background: #1a73e8; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        title = QLabel("Настройки персонализации")
        title.setStyleSheet("font-size: 20px; font-weight: 600; margin-bottom: 10px;")
        layout.addWidget(title)

        s1 = QLabel("Поисковая система")
        s1.setObjectName("section")
        layout.addWidget(s1)
        self.search_engine_combo = QComboBox()
        self.search_engines = {
            "Google": "https://www.google.com/search?q=",
            "Bing": "https://www.bing.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Yahoo": "https://search.yahoo.com/search?p=",
            "Yandex": "https://yandex.ru/search/?text="
        }
        for e in self.search_engines.keys():
            self.search_engine_combo.addItem(e)
        layout.addWidget(self.search_engine_combo)

        s3 = QLabel("Цвета")
        s3.setObjectName("section")
        layout.addWidget(s3)
        self.bg_color_btn = QPushButton("Фон приложения")
        self.bg_color_btn.setObjectName("color-btn")
        self.bg_color = "#1a1a1a"
        self.bg_color_btn.clicked.connect(lambda: self._pick("bg"))
        layout.addWidget(self.bg_color_btn)
        self.sidebar_color_btn = QPushButton("Боковая панель")
        self.sidebar_color_btn.setObjectName("color-btn")
        self.sidebar_color = "#0f0f0f"
        self.sidebar_color_btn.clicked.connect(lambda: self._pick("sidebar"))
        layout.addWidget(self.sidebar_color_btn)
        self.accent_color_btn = QPushButton("Акцентный цвет (по умолчанию — белый)")
        self.accent_color_btn.setObjectName("color-btn")
        self.accent_color = "#ffffff"
        self.accent_color_btn.clicked.connect(lambda: self._pick("accent"))
        layout.addWidget(self.accent_color_btn)

        default_btn = QPushButton("Сбросить цвета по умолчанию")
        default_btn.setObjectName("default-btn")
        default_btn.clicked.connect(self.reset_to_default)
        layout.addWidget(default_btn)

        s_ui = QLabel("Интерфейс")
        s_ui.setObjectName("section")
        layout.addWidget(s_ui)
        layout.addWidget(QLabel("Прозрачность сайдбара:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(40)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        layout.addWidget(self.opacity_slider)
        layout.addWidget(QLabel("Скругление углов (px):"))
        self.radius_combo = QComboBox()
        self.radius_combo.addItems(["0 (острые)", "4", "8", "12", "16"])
        layout.addWidget(self.radius_combo)
        layout.addWidget(QLabel("Размер шрифта:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Мелкий (12)", "Обычный (13)", "Крупный (15)", "Огромный (17)"])
        layout.addWidget(self.font_combo)

        s4 = QLabel("Фоновое изображение")
        s4.setObjectName("section")
        layout.addWidget(s4)
        self.bg_image_btn = QPushButton("Выбрать картинку...")
        self.bg_image_btn.setObjectName("color-btn")
        self.bg_image_path = ""
        self.bg_image_btn.clicked.connect(self.pick_image)
        layout.addWidget(self.bg_image_btn)
        self.clear_image_btn = QPushButton("Убрать картинку")
        self.clear_image_btn.setObjectName("cancel")
        self.clear_image_btn.clicked.connect(self.clear_image)
        layout.addWidget(self.clear_image_btn)
        self.image_preview = QLabel("Картинка не выбрана")
        self.image_preview.setStyleSheet("color: #5f6368; font-size: 12px; padding: 5px;")
        layout.addWidget(self.image_preview)

        layout.addStretch()
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        self.load_settings()

    def reset_to_default(self):
        self.bg_color = "#1a1a1a"
        self.sidebar_color = "#0f0f0f"
        self.accent_color = "#ffffff"
        self._update_btn_colors()

    def _pick(self, t):
        color = QColorDialog.getColor()
        if color.isValid():
            h = color.name()
            if t == "bg": self.bg_color = h
            elif t == "sidebar": self.sidebar_color = h
            elif t == "accent": self.accent_color = h
            self._update_btn_colors()

    def _update_btn_colors(self):
        self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color}; color: #fff;")
        self.sidebar_color_btn.setStyleSheet(f"background-color: {self.sidebar_color}; color: #fff;")
        text = "#000" if self.accent_color.lower() in ["#ffffff", "#f8f9fa"] else "#fff"
        self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color}; color: {text};")

    def pick_image(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Картинка", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if fp:
            self.bg_image_path = fp
            self.image_preview.setText(f"Выбрано: {os.path.basename(fp)}")

    def clear_image(self):
        self.bg_image_path = ""
        self.image_preview.setText("Картинка не выбрана")

    def load_settings(self):
        s = self._load()
        if "search_engine" in s:
            i = self.search_engine_combo.findText(s["search_engine"])
            if i >= 0: self.search_engine_combo.setCurrentIndex(i)
        self.bg_color = s.get("bg_color", "#1a1a1a")
        self.sidebar_color = s.get("sidebar_color", "#0f0f0f")
        self.accent_color = s.get("accent_color", "#ffffff")
        self.bg_image_path = s.get("bg_image_path", "")
        self.opacity_slider.setValue(s.get("sidebar_opacity", 100))
        r = s.get("corner_radius", "8")
        i = self.radius_combo.findText(r + (" (острые)" if r == "0" else ""))
        if i >= 0: self.radius_combo.setCurrentIndex(i)
        fs = s.get("font_size", 13)
        fs_map = {12: 0, 13: 1, 15: 2, 17: 3}
        self.font_combo.setCurrentIndex(fs_map.get(fs, 1))
        if self.bg_image_path and os.path.exists(self.bg_image_path):
            self.image_preview.setText(f"Выбрано: {os.path.basename(self.bg_image_path)}")
        self._update_btn_colors()

    def _load(self):
        if os.path.exists("silent_settings.json"):
            try:
                with open("silent_settings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings_to_file(self):
        s = self._load()
        radius_text = self.radius_combo.currentText()
        radius = radius_text.split(" ")[0]
        font_text = self.font_combo.currentText()
        font_size = int(font_text.split("(")[1].split(")")[0])
        s.update({
            "search_engine": self.search_engine_combo.currentText(),
            "bg_color": self.bg_color,
            "sidebar_color": self.sidebar_color,
            "accent_color": self.accent_color,
            "bg_image_path": self.bg_image_path,
            "sidebar_opacity": self.opacity_slider.value(),
            "corner_radius": radius,
            "font_size": font_size
        })
        with open("silent_settings.json", "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)

    def accept(self):
        self.save_settings_to_file()
        super().accept()


# ======================================================================
# ИСТОРИЯ
# ======================================================================

class HistoryDialog(QDialog):
    def __init__(self, history_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История поиска")
        self.setFixedSize(500, 500)
        self.history_list = history_list
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #202124; font-size: 16px; font-weight: 600; }
            QListWidget { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; font-size: 14px; padding: 5px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #f1f3f4; }
            QListWidget::item:selected { background-color: #e8f0fe; color: #1a73e8; }
            QPushButton { background-color: #1a73e8; color: #ffffff; border: none; padding: 10px 25px; font-size: 14px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton#danger { background-color: #d93025; }
            QPushButton#danger:hover { background-color: #b3261e; }
            QPushButton#cancel { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; }
            QPushButton#cancel:hover { background-color: #f8f9fa; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        layout.addWidget(QLabel("История поиска"))
        self.list_widget = QListWidget()
        for item in reversed(self.history_list):
            li = QListWidgetItem(f"{item['query']}  —  {item['time']}")
            li.setData(Qt.UserRole, item['query'])
            self.list_widget.addItem(li)
        self.list_widget.itemDoubleClicked.connect(self._on_dbl)
        layout.addWidget(self.list_widget)
        bl = QHBoxLayout()
        clear_btn = QPushButton("Очистить историю")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear)
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("cancel")
        close_btn.clicked.connect(self.reject)
        bl.addWidget(clear_btn)
        bl.addWidget(close_btn)
        layout.addLayout(bl)
        self.setLayout(layout)
        self.selected_query = None

    def _on_dbl(self, item):
        self.selected_query = item.data(Qt.UserRole)
        self.accept()

    def _clear(self):
        self.history_list.clear()
        self.list_widget.clear()
        save_history(self.history_list)


# ======================================================================
# ЗАГРУЗКИ
# ======================================================================

class DownloadsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузки")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #202124; font-size: 16px; font-weight: 600; }
            QPushButton { background-color: #1a73e8; color: #ffffff; border: none; padding: 10px 25px; font-size: 14px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton#cancel { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; }
            QFrame#download-item { background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 10px; }
            QProgressBar { border: 1px solid #dadce0; border-radius: 6px; text-align: center; background-color: #ffffff; color: #202124; height: 20px; }
            QProgressBar::chunk { background-color: #1a73e8; border-radius: 5px; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        layout.addWidget(QLabel("Загрузки"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self.downloads_container = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_container)
        self.downloads_layout.setContentsMargins(0, 0, 0, 0)
        self.downloads_layout.setSpacing(10)
        self.downloads_layout.addStretch()
        scroll.setWidget(self.downloads_container)
        layout.addWidget(scroll)
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("cancel")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        self.setLayout(layout)
        self.download_widgets = {}

    def add_download(self, did, fn):
        f = QFrame()
        f.setObjectName("download-item")
        il = QVBoxLayout(f)
        il.setContentsMargins(12, 12, 12, 12)
        il.setSpacing(8)
        nl = QLabel(fn)
        nl.setStyleSheet("font-size: 14px; font-weight: 500;")
        nl.setWordWrap(True)
        pb = QProgressBar()
        pb.setRange(0, 100)
        pb.setValue(0)
        pb.setFormat("%p%")
        sl = QLabel("Загрузка...")
        sl.setStyleSheet("color: #5f6368; font-size: 12px;")
        il.addWidget(nl)
        il.addWidget(pb)
        il.addWidget(sl)
        self.downloads_layout.insertWidget(self.downloads_layout.count() - 1, f)
        self.download_widgets[did] = {"frame": f, "progress": pb, "status": sl}

    def update_download(self, did, p, s="Загрузка..."):
        if did in self.download_widgets:
            self.download_widgets[did]["progress"].setValue(int(p))
            self.download_widgets[did]["status"].setText(s)

    def finish_download(self, did, path=""):
        if did in self.download_widgets:
            self.download_widgets[did]["progress"].setValue(100)
            self.download_widgets[did]["status"].setText(f"Завершено: {path}")
            self.download_widgets[did]["status"].setStyleSheet("color: #188038; font-size: 12px; font-weight: 500;")


# ======================================================================
# ВКЛАДКА БРАУЗЕРА
# ======================================================================

class BrowserTab(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWebEngineView { background-color: #ffffff; }")


# ======================================================================
# ИСТОРИЯ (файл)
# ======================================================================

def load_history():
    if os.path.exists("silent_history.json"):
        try:
            with open("silent_history.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(h):
    with open("silent_history.json", "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)


# ======================================================================
# ГЛАВНОЕ ОКНО
# ======================================================================

class SilentBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SILENT")
        self.setGeometry(100, 100, 1400, 900)

        self.search_engines = {
            "Google": "https://www.google.com/search?q=",
            "Bing": "https://www.bing.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Yahoo": "https://search.yahoo.com/search?p=",
            "Yandex": "https://yandex.ru/search/?text="
        }

        self.settings = self.load_settings()
        self.current_search_engine = self.settings.get("search_engine", "Google")
        self.bg_color = self.settings.get("bg_color", "#1a1a1a")
        self.sidebar_color = self.settings.get("sidebar_color", "#0f0f0f")
        self.accent_color = self.settings.get("accent_color", "#ffffff")
        self.bg_image_path = self.settings.get("bg_image_path", "")
        self.sidebar_opacity = self.settings.get("sidebar_opacity", 100)
        self.corner_radius = self.settings.get("corner_radius", "8")
        self.font_size = self.settings.get("font_size", 13)

        self.incognito_mode = False
        self.normal_bg = self.bg_color
        self.normal_sb = self.sidebar_color
        self.normal_ac = self.accent_color
        self.normal_img = self.bg_image_path

        self.history = load_history()
        self.downloads_dialog = None

        self.connect_manager = ConnectManager()
        self.spaces_manager = SpacesManager()
        self.connect_popup = None

        self.tabs_per_space = {}
        self.active_space_tab_index = {}

        self.setup_ui()
        self.setup_downloads()
        self.setup_shortcuts()
        self.apply_theme()
        self._switch_to_space(self.spaces_manager.current_index, initial=True)

        if self.connect_manager.auto_connect:
            self.connect_manager.connect()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setup_sidebar()
        self.setup_content_area()

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(10)

        title = QLabel("SILENT")
        title.setObjectName("title-label")
        sidebar_layout.addWidget(title)

        space_row = QHBoxLayout()
        space_row.setSpacing(6)
        self.space_combo = QComboBox()
        self.space_combo.setObjectName("space-combo")
        self._refresh_space_combo()
        self.space_combo.currentIndexChanged.connect(self._on_space_combo_changed)
        space_row.addWidget(self.space_combo)
        add_space_btn = QPushButton("+")
        add_space_btn.setFixedSize(36, 36)
        add_space_btn.setObjectName("nav-btn")
        add_space_btn.setToolTip("Новое пространство")
        add_space_btn.clicked.connect(self._add_space)
        space_row.addWidget(add_space_btn)
        sidebar_layout.addLayout(space_row)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Поиск или URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setObjectName("url-bar")
        sidebar_layout.addWidget(self.url_bar)

        nav1 = QHBoxLayout()
        nav1.setSpacing(8)
        self.back_btn = self._nav_btn("←", self.go_back)
        self.forward_btn = self._nav_btn("→", self.go_forward)
        self.reload_btn = self._nav_btn("⟳", self.reload_page)
        self.menu_btn = self._nav_btn("☰", self.show_menu)
        nav1.addWidget(self.back_btn)
        nav1.addWidget(self.forward_btn)
        nav1.addWidget(self.reload_btn)
        nav1.addWidget(self.menu_btn)
        sidebar_layout.addLayout(nav1)

        nav2 = QHBoxLayout()
        nav2.setSpacing(8)
        self.connect_btn = self._make_connect_button()
        self.incognito_btn = self._nav_btn("🕶", self.toggle_incognito)
        self.incognito_btn.setToolTip("Режим инкогнито")
        nav2.addWidget(self.connect_btn)
        nav2.addWidget(self.incognito_btn)
        sidebar_layout.addLayout(nav2)

        nav3 = QHBoxLayout()
        nav3.setSpacing(8)
        self.speeddial_btn = self._nav_btn("⭐", self.open_speed_dial)
        self.speeddial_btn.setToolTip("Speed Dial")
        self.translate_btn = self._nav_btn("🌐", self.open_translator)
        self.translate_btn.setToolTip("Переводчик")
        self.settings_btn = self._nav_btn("⚙", self.open_settings)
        self.settings_btn.setToolTip("Настройки")
        nav3.addWidget(self.speeddial_btn)
        nav3.addWidget(self.translate_btn)
        nav3.addWidget(self.settings_btn)
        sidebar_layout.addLayout(nav3)

        sidebar_layout.addStretch()
        footer = QLabel("v3.1 · Spaces · Speed Dial · Connect")
        footer.setObjectName("footer-label")
        sidebar_layout.addWidget(footer)

        self.sidebar.setLayout(sidebar_layout)
        self.main_layout.addWidget(self.sidebar)

    def _nav_btn(self, text, cb):
        b = QPushButton(text)
        b.setFixedSize(45, 45)
        b.clicked.connect(cb)
        b.setObjectName("nav-btn")
        return b

    def _make_connect_button(self):
        b = QPushButton("CONNECT")
        b.setFixedHeight(45)
        b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        b.clicked.connect(self.show_connect_popup)
        b.setObjectName("connect-btn")
        b.setCursor(Qt.PointingHandCursor)
        return b

    def setup_content_area(self):
        self.content_area = QWidget()
        self.content_area.setObjectName("content-area")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Таб-бар с крестиком слева
        self.tab_bar = SilentTabBar()
        self.tab_bar.setObjectName("tab-bar")
        self.tab_bar.setFixedHeight(34)  # ФИКС: фиксированная высота
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)

        # Стек вкладок (занимает всё оставшееся место)
        self.tab_stack = QWidget()
        self.tab_stack.setObjectName("tab-stack")
        self.tab_stack_layout = QVBoxLayout(self.tab_stack)
        self.tab_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_stack_layout.setSpacing(0)

        # Ряд: [таб-бар] [+] [растяжение]
        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(0)
        bar_row.addWidget(self.tab_bar)
        self.add_tab_btn = QPushButton("+")
        self.add_tab_btn.setFixedSize(36, 32)
        self.add_tab_btn.setObjectName("add-tab-btn")
        self.add_tab_btn.setToolTip("Новая вкладка")
        self.add_tab_btn.clicked.connect(lambda: self._add_new_tab())
        bar_row.addWidget(self.add_tab_btn)
        bar_row.addStretch()

        bar_container = QWidget()
        bar_container.setObjectName("bar-container")
        bar_container.setLayout(bar_row)
        bar_container.setFixedHeight(34)  # ФИКС: фиксированная высота

        # ФИКС: stretch=0 для бара, stretch=1 для стека
        content_layout.addWidget(bar_container, 0)
        content_layout.addWidget(self.tab_stack, 1)

        self.main_layout.addWidget(self.content_area)

    def setup_downloads(self):
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.on_download_requested)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, self.show_quick_switcher)
        for i in range(1, 10):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self, lambda idx=i-1: self._switch_to_space(idx))
        QShortcut(QKeySequence("Ctrl+N"), self, lambda: self._add_new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_current_tab)
        QShortcut(QKeySequence("F11"), self, self.toggle_focus_mode)

    # ============== SPACES ==============
    def _refresh_space_combo(self):
        self.space_combo.blockSignals(True)
        self.space_combo.clear()
        for i, s in enumerate(self.spaces_manager.spaces):
            self.space_combo.addItem(f"● {s.name}", i)
            self.space_combo.setItemData(i, QColor(s.color), Qt.DecorationRole)
        self.space_combo.setCurrentIndex(self.spaces_manager.current_index)
        self.space_combo.blockSignals(False)

    def _on_space_combo_changed(self, idx):
        if idx >= 0:
            self._switch_to_space(idx)

    def _switch_to_space(self, idx, initial=False):
        if idx < 0 or idx >= len(self.spaces_manager.spaces):
            return
        cur = self.spaces_manager.current_index
        if not initial and cur in self.tabs_per_space:
            self._save_current_space_state()
        self.spaces_manager.switch_to(idx)
        self._refresh_space_combo()
        self._restore_space_state(idx)

    def _save_current_space_state(self):
        si = self.spaces_manager.current_index
        tabs = []
        for i in range(self.tab_stack_layout.count()):
            w = self.tab_stack_layout.itemAt(i).widget()
            if isinstance(w, BrowserTab):
                tabs.append({"url": w.url().toString(), "title": w.page().title() or "Вкладка"})
        self.tabs_per_space[si] = tabs
        self.active_space_tab_index[si] = self.tab_bar.currentIndex()

    def _restore_space_state(self, si):
        while self.tab_stack_layout.count():
            item = self.tab_stack_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        tabs = self.tabs_per_space.get(si, [])
        if not tabs:
            self._add_new_tab(url="silent://newtab", title="Speed Dial")
        else:
            for t in tabs:
                self._add_new_tab(url=t.get("url", "silent://newtab"),
                                  title=t.get("title", "Вкладка"), activate=False)
            active_idx = self.active_space_tab_index.get(si, 0)
            if 0 <= active_idx < self.tab_bar.count():
                self.tab_bar.setCurrentIndex(active_idx)

    def _add_space(self):
        name, ok = QInputDialog.getText(self, "Новое пространство", "Имя:", text="Новое")
        if ok and name.strip():
            self.spaces_manager.add_space(name.strip())
            self._refresh_space_combo()
            self._switch_to_space(len(self.spaces_manager.spaces) - 1)

    # ============== ВКЛАДКИ ==============
    def _add_new_tab(self, url="silent://newtab", title="Speed Dial", activate=True):
        tab = BrowserTab()
        if url == "silent://newtab":
            tab.setHtml(self._get_speed_dial_html())
        else:
            tab.setUrl(QUrl(url))
        self.tab_stack_layout.addWidget(tab)
        self.tab_bar.addTab(title)
        tab.titleChanged.connect(lambda t, w=tab: self._update_tab_title(w, t))
        tab.urlChanged.connect(lambda u, w=tab: self._update_url(w, u))
        if activate:
            self.tab_bar.setCurrentIndex(self.tab_bar.count() - 1)
            self.url_bar.setText(url if url != "silent://newtab" else "")
            self.url_bar.setFocus()

    def _close_tab(self, index):
        if self.tab_bar.count() <= 1:
            w = self.tab_stack_layout.itemAt(0).widget()
            if w:
                w.setHtml(self._get_speed_dial_html())
                self.tab_bar.setTabText(0, "Speed Dial")
            return
        w = self.tab_stack_layout.itemAt(index).widget()
        self.tab_stack_layout.removeWidget(w)
        w.deleteLater()
        self.tab_bar.removeTab(index)

    def _close_current_tab(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def _on_tab_changed(self, index):
        if index < 0:
            return
        w = self.tab_stack_layout.itemAt(index).widget()
        if isinstance(w, BrowserTab):
            self.url_bar.setText(w.url().toString())

    def _update_tab_title(self, tab, title):
        for i in range(self.tab_stack_layout.count()):
            if self.tab_stack_layout.itemAt(i).widget() == tab:
                t = title[:25] + "..." if len(title) > 25 else title
                self.tab_bar.setTabText(i, t)
                break

    def _update_url(self, tab, url):
        for i in range(self.tab_stack_layout.count()):
            if self.tab_stack_layout.itemAt(i).widget() == tab:
                if self.tab_bar.currentIndex() == i:
                    self.url_bar.setText(url.toString())
                break

    def _get_speed_dial_html(self):
        is_dark = self._is_dark(self.bg_color)
        text = "#ffffff" if is_dark else "#202124"
        tile_bg = "#2a2a2a" if is_dark else "#ffffff"
        border = "#3a3a3a" if is_dark else "#dadce0"
        icon_text = "#ffffff"
        muted = "#5f6368" if is_dark else "#80868b"
        tiles = load_speed_dial()
        return generate_speed_dial_html(
            bg=self.bg_color, text=text, accent=self.accent_color,
            tile_bg=tile_bg, border=border, icon_text=icon_text, muted=muted,
            tiles=tiles
        )

    def _is_dark(self, color):
        c = color.lstrip("#")
        if len(c) != 6:
            return False
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return (0.299 * r + 0.587 * g + 0.114 * b) < 128

    # ============== НАВИГАЦИЯ ==============
    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if text == "silent://newtab":
            w = self._current_tab()
            if w:
                w.setHtml(self._get_speed_dial_html())
            return
        if not self.incognito_mode:
            self.history.append({
                "query": text,
                "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "engine": self.current_search_engine
            })
            save_history(self.history)
        if "." in text and " " not in text:
            if not text.startswith("http"):
                text = "https://" + text
            qurl = QUrl(text)
        else:
            qurl = QUrl(self.search_engines[self.current_search_engine] + text)
        w = self._current_tab()
        if w:
            w.setUrl(qurl)

    def _current_tab(self):
        idx = self.tab_bar.currentIndex()
        if idx < 0:
            return None
        w = self.tab_stack_layout.itemAt(idx).widget()
        return w if isinstance(w, BrowserTab) else None

    def go_back(self):
        w = self._current_tab()
        if w:
            w.back()

    def go_forward(self):
        w = self._current_tab()
        if w:
            w.forward()

    def reload_page(self):
        w = self._current_tab()
        if w:
            w.reload()

    # ============== ЗАГРУЗКИ ==============
    @pyqtSlot('QWebEngineDownloadItem*')
    def on_download_requested(self, download):
        if self.downloads_dialog is None:
            self.downloads_dialog = DownloadsDialog(self)
        old_path = download.path()
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", old_path)
        if not path:
            download.cancel()
            return
        download.setPath(path)
        download.accept()
        did = id(download)
        self.downloads_dialog.add_download(did, os.path.basename(path))
        self.downloads_dialog.show()
        self.downloads_dialog.raise_()
        download.downloadProgress.connect(
            lambda r, t, d=download, i=did: self._on_dl_progress(d, i, r, t))
        download.finished.connect(
            lambda d=download, i=did, p=path: self._on_dl_finished(d, i, p))

    def _on_dl_progress(self, d, did, r, t):
        if t > 0 and self.downloads_dialog:
            p = (r / t) * 100
            self.downloads_dialog.update_download(did, p, f"{r/(1024*1024):.1f} MB / {t/(1024*1024):.1f} MB")

    def _on_dl_finished(self, d, did, p):
        if self.downloads_dialog:
            self.downloads_dialog.finish_download(did, p)

    # ============== МЕНЮ ==============
    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; padding: 5px; font-size: 14px; }
            QMenu::item { padding: 10px 30px; border-radius: 6px; }
            QMenu::item:selected { background-color: #e8f0fe; color: #1a73e8; }
        """)
        a1 = menu.addAction("📜 История поиска")
        a2 = menu.addAction("⬇ Загрузки")
        menu.addSeparator()
        a3 = menu.addAction("⭐ Speed Dial")
        a4 = menu.addAction("⚙️ Управление Speed Dial")
        menu.addSeparator()
        a5 = menu.addAction("➕ Новая вкладка (Ctrl+N)")
        a6 = menu.addAction("🔀 Quick Switcher (Ctrl+T)")
        menu.addSeparator()
        a7 = menu.addAction("📌 Spaces: управление...")
        action = menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        if action == a1: self.show_history()
        elif action == a2: self.show_downloads()
        elif action == a3: self.open_speed_dial()
        elif action == a4: self.manage_speed_dial()
        elif action == a5: self._add_new_tab()
        elif action == a6: self.show_quick_switcher()
        elif action == a7: self._manage_spaces()

    def show_history(self):
        d = HistoryDialog(self.history, self)
        if d.exec_() == QDialog.Accepted and d.selected_query:
            self.url_bar.setText(d.selected_query)
            self.navigate_to_url()

    def show_downloads(self):
        if self.downloads_dialog is None:
            self.downloads_dialog = DownloadsDialog(self)
        self.downloads_dialog.show()
        self.downloads_dialog.raise_()

    def open_speed_dial(self):
        self._add_new_tab(url="silent://newtab", title="Speed Dial")

    def manage_speed_dial(self):
        dlg = SpeedDialManager(self)
        dlg.exec_()
        w = self._current_tab()
        if w and w.url().toString() in ["", "about:blank", "silent://newtab"]:
            w.setHtml(self._get_speed_dial_html())

    def _manage_spaces(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; padding: 5px; font-size: 14px; }
            QMenu::item { padding: 10px 30px; border-radius: 6px; }
            QMenu::item:selected { background-color: #e8f0fe; color: #1a73e8; }
        """)
        actions = []
        for i, s in enumerate(self.spaces_manager.spaces):
            a = menu.addAction(f"● {s.name}")
            actions.append((a, i))
        menu.addSeparator()
        rename_a = menu.addAction("✏️ Переименовать текущее")
        delete_a = menu.addAction("🗑️ Удалить текущее")
        action = menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        for a, i in actions:
            if action == a:
                self._switch_to_space(i)
                return
        if action == rename_a:
            cur = self.spaces_manager.current
            name, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", text=cur.name)
            if ok and name.strip():
                self.spaces_manager.rename_space(self.spaces_manager.current_index, name.strip())
                self._refresh_space_combo()
        elif action == delete_a:
            if len(self.spaces_manager.spaces) > 1:
                r = QMessageBox.question(self, "Удалить?", "Удалить текущее пространство?")
                if r == QMessageBox.Yes:
                    self.spaces_manager.remove_space(self.spaces_manager.current_index)
                    self._refresh_space_combo()
                    self._switch_to_space(self.spaces_manager.current_index)
            else:
                QMessageBox.information(self, "Нельзя", "Должно быть хотя бы одно пространство")

    # ============== CONNECT ==============
    def show_connect_popup(self):
        if self.connect_popup is not None:
            self.connect_popup.close()
            self.connect_popup.deleteLater()
        self.connect_popup = ConnectPopup(self.connect_manager, self)
        pos = self.connect_btn.mapToGlobal(self.connect_btn.rect().topRight())
        self.connect_popup.move(pos.x() + 10, pos.y())
        self.connect_popup.show()
        self.connect_popup.raise_()
        self.connect_popup.activateWindow()

    # ============== ПЕРЕВОДЧИК ==============
    def open_translator(self):
        w = self._current_tab()
        if not w:
            return
        def _got(text):
            dlg = TranslatorDialog(text or "", self)
            dlg.exec_()
        w.page().runJavaScript("window.getSelection().toString();", _got)

    # ============== QUICK SWITCHER ==============
    def collect_all_tabs(self):
        self._save_current_space_state()
        cur = self.spaces_manager.current_index
        if cur not in self.tabs_per_space:
            tabs = []
            for i in range(self.tab_stack_layout.count()):
                w = self.tab_stack_layout.itemAt(i).widget()
                if isinstance(w, BrowserTab):
                    tabs.append({"url": w.url().toString(), "title": w.page().title() or "Вкладка"})
            self.tabs_per_space[cur] = tabs
        result = []
        for si, space in enumerate(self.spaces_manager.spaces):
            tabs = self.tabs_per_space.get(si, [])
            for ti, t in enumerate(tabs):
                result.append({
                    "space_index": si,
                    "tab_index": ti,
                    "title": t.get("title", "Вкладка"),
                    "url": t.get("url", ""),
                    "space_name": space.name,
                    "space_color": space.color
                })
        return result

    def show_quick_switcher(self):
        qs = QuickSwitcher(self, self)
        qs.tab_selected.connect(self._on_qs_selected)
        qs.move(self.geometry().center().x() - 260, self.geometry().center().y() - 210)
        qs.exec_()

    def _on_qs_selected(self, space_idx, tab_idx):
        self._switch_to_space(space_idx)
        if 0 <= tab_idx < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(tab_idx)

    # ============== ИНКОГНИТО ==============
    def toggle_incognito(self):
        self.incognito_mode = not self.incognito_mode
        if self.incognito_mode:
            self.bg_color = "#000000"
            self.sidebar_color = "#0a0a0a"
            self.accent_color = "#888888"
            self.bg_image_path = ""
        else:
            self.bg_color = self.normal_bg
            self.sidebar_color = self.normal_sb
            self.accent_color = self.normal_ac
            self.bg_image_path = self.normal_img
        self.apply_theme()

    # ============== FOCUS MODE ==============
    def toggle_focus_mode(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    # ============== НАСТРОЙКИ ==============
    def open_settings(self):
        d = SettingsDialog(self)
        if d.exec_() == QDialog.Accepted:
            self.settings = self.load_settings()
            self.current_search_engine = self.settings.get("search_engine", "Google")
            if not self.incognito_mode:
                self.normal_bg = self.settings.get("bg_color", "#1a1a1a")
                self.normal_sb = self.settings.get("sidebar_color", "#0f0f0f")
                self.normal_ac = self.settings.get("accent_color", "#ffffff")
                self.normal_img = self.settings.get("bg_image_path", "")
                self.bg_color = self.normal_bg
                self.sidebar_color = self.normal_sb
                self.accent_color = self.normal_ac
                self.bg_image_path = self.normal_img
            self.sidebar_opacity = self.settings.get("sidebar_opacity", 100)
            self.corner_radius = self.settings.get("corner_radius", "8")
            self.font_size = self.settings.get("font_size", 13)
            self.apply_theme()
            w = self._current_tab()
            if w and w.url().toString() in ["", "about:blank", "silent://newtab"]:
                w.setHtml(self._get_speed_dial_html())

    def load_settings(self):
        if os.path.exists("silent_settings.json"):
            try:
                with open("silent_settings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def apply_theme(self):
        is_dark = self._is_dark(self.bg_color)
        text_color = "#ffffff" if is_dark else "#202124"

        if self.bg_image_path and os.path.exists(self.bg_image_path) and not self.incognito_mode:
            bg_style = f"background-image: url('file:///{self.bg_image_path}'); background-size: cover; background-color: {self.bg_color};"
        else:
            bg_style = f"background-color: {self.bg_color};"

        accent_visible = self.accent_color
        if not is_dark and self.accent_color.lower() in ["#ffffff", "#f8f9fa"]:
            accent_visible = "#1a73e8"

        r = self.corner_radius
        opacity = self.sidebar_opacity / 100.0
        try:
            self.sidebar.setWindowOpacity(opacity)
        except:
            pass

        self.sidebar.setStyleSheet(f"""
            QFrame {{ background-color: {self.sidebar_color}; border-right: 1px solid #2a2a2a; }}
            QLabel#title-label {{ color: {self.accent_color}; font-size: 22px; font-weight: 700; letter-spacing: 2px; padding: 5px 0; }}
            QLabel#footer-label {{ color: #5f6368; font-size: 11px; }}
            QLineEdit#url-bar {{ background-color: #ffffff; color: #202124; border: 1px solid #dadce0; padding: 12px 15px; font-size: {self.font_size}px; border-radius: {r}px; }}
            QLineEdit#url-bar:focus {{ border: 2px solid {accent_visible}; }}
            QPushButton#nav-btn {{ background-color: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: {r}px; font-size: 18px; font-weight: 500; }}
            QPushButton#nav-btn:hover {{ background-color: #f8f9fa; border: 1px solid {accent_visible}; }}
            QPushButton#nav-btn:pressed {{ background-color: #e8eaed; }}
            QPushButton#connect-btn {{ background-color: {self.accent_color}; color: #000000; border: none; border-radius: {r}px; font-size: 13px; font-weight: 700; letter-spacing: 1px; }}
            QPushButton#connect-btn:hover {{ background-color: #e0e0e0; }}
            QComboBox#space-combo {{ background-color: #ffffff; color: #202124; border: 1px solid #dadce0; padding: 8px 12px; font-size: {self.font_size}px; border-radius: {r}px; }}
            QComboBox#space-combo:hover {{ border: 1px solid {accent_visible}; }}
        """)

        self.content_area.setStyleSheet(f"""
            QWidget#content-area {{ {bg_style} }}
            QWidget#bar-container {{ background-color: {self.sidebar_color}; }}
            QWidget#tab-stack {{ background-color: {self.bg_color}; }}
        """)

        self.tab_bar.setStyleSheet(f"""
            QTabBar {{ background-color: transparent; border: none; }}
            QTabBar::tab {{
                background-color: {self.sidebar_color}; color: #8a8a8a;
                padding: 8px 20px 8px 28px; border: none;
                border-right: 1px solid #2a2a2a;
                border-top-left-radius: {r}px; border-top-right-radius: {r}px;
                margin-right: 0px; font-size: {self.font_size}px; font-weight: 500;
                min-width: 100px; max-width: 200px;
            }}
            QTabBar::tab:selected {{ background-color: {self.bg_color}; color: {self.accent_color}; border-bottom: 2px solid {self.accent_color}; }}
            QTabBar::tab:hover {{ background-color: #2a2a2a; color: {self.accent_color}; }}
        """)

        self.add_tab_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {self.sidebar_color}; color: {self.accent_color}; border: none; border-top-right-radius: {r}px; font-size: 18px; font-weight: 700; }}
            QPushButton:hover {{ background-color: #2a2a2a; }}
        """)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.bg_color))
        palette.setColor(QPalette.WindowText, QColor(text_color))
        palette.setColor(QPalette.Base, QColor(self.bg_color))
        palette.setColor(QPalette.Text, QColor(text_color))
        palette.setColor(QPalette.Button, QColor(self.sidebar_color))
        palette.setColor(QPalette.ButtonText, QColor(text_color))
        palette.setColor(QPalette.Link, QColor(self.accent_color))
        palette.setColor(QPalette.Highlight, QColor(self.accent_color))
        palette.setColor(QPalette.HighlightedText, QColor("#000" if self.accent_color.lower() in ["#ffffff", "#f8f9fa"] else "#fff"))
        QApplication.setPalette(palette)


# ======================================================================
# ЗАПУСК
# ======================================================================

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    window = SilentBrowser()
    window.show()
    sys.exit(app.exec_())