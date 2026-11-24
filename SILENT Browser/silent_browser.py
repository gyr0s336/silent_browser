import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget,
    QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QWidget, QDialog, QLabel, QComboBox, QFormLayout,
    QColorDialog, QFrame)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtGui import QColor, QPalette, QFont


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #202124;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#section {
                font-size: 16px;
                font-weight: 600;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            QComboBox {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                padding: 10px 15px;
                font-size: 14px;
            }
            QComboBox:hover {
                border: 1px solid #202124;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #202124;
                margin-right: 10px;
            }
            QPushButton {
                background-color: #1a73e8;
                color: #ffffff;
                border: none;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
            QPushButton#color-btn {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton#color-btn:hover {
                background-color: #f8f9fa;
                border: 1px solid #202124;
            }
            QPushButton#cancel {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
            }
            QPushButton#cancel:hover {
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("Настройки персонализации")
        title.setStyleSheet("font-size: 20px; font-weight: 600; margin-bottom: 10px;")
        layout.addWidget(title)

        # Поисковая система
        section1 = QLabel("Поисковая система")
        section1.setObjectName("section")
        layout.addWidget(section1)
        
        self.search_engine_combo = QComboBox()
        self.search_engines = {
            "Google": "https://www.google.com/search?q=",
            "Bing": "https://www.bing.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Yahoo": "https://search.yahoo.com/search?p=",
            "Yandex": "https://yandex.ru/search/?text="
        }
        for engine in self.search_engines.keys():
            self.search_engine_combo.addItem(engine)
        layout.addWidget(self.search_engine_combo)

        # Тема
        section2 = QLabel("Тема оформления")
        section2.setObjectName("section")
        layout.addWidget(section2)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Чёрная"])
        layout.addWidget(self.theme_combo)

        # Цвета
        section3 = QLabel("Цвета")
        section3.setObjectName("section")
        layout.addWidget(section3)

        color_layout1 = QHBoxLayout()
        self.bg_color_btn = QPushButton("Фон приложения")
        self.bg_color_btn.setObjectName("color-btn")
        self.bg_color = "#ffffff"
        self.bg_color_btn.clicked.connect(lambda: self.pick_color("bg"))
        color_layout1.addWidget(self.bg_color_btn)
        layout.addLayout(color_layout1)

        color_layout2 = QHBoxLayout()
        self.sidebar_color_btn = QPushButton("Боковая панель")
        self.sidebar_color_btn.setObjectName("color-btn")
        self.sidebar_color = "#f8f9fa"
        self.sidebar_color_btn.clicked.connect(lambda: self.pick_color("sidebar"))
        color_layout2.addWidget(self.sidebar_color_btn)
        layout.addLayout(color_layout2)

        color_layout3 = QHBoxLayout()
        self.accent_color_btn = QPushButton("Акцентный цвет")
        self.accent_color_btn.setObjectName("color-btn")
        self.accent_color = "#1a73e8"
        self.accent_color_btn.clicked.connect(lambda: self.pick_color("accent"))
        color_layout3.addWidget(self.accent_color_btn)
        layout.addLayout(color_layout3)

        layout.addStretch()

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.load_settings()

    def pick_color(self, color_type):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if color_type == "bg":
                self.bg_color = hex_color
                self.bg_color_btn.setStyleSheet(f"background-color: {hex_color};")
            elif color_type == "sidebar":
                self.sidebar_color = hex_color
                self.sidebar_color_btn.setStyleSheet(f"background-color: {hex_color};")
            elif color_type == "accent":
                self.accent_color = hex_color
                self.accent_color_btn.setStyleSheet(f"background-color: {hex_color};")

    def load_settings(self):
        settings = self.load_settings_from_file()
        if "search_engine" in settings:
            index = self.search_engine_combo.findText(settings["search_engine"])
            if index >= 0:
                self.search_engine_combo.setCurrentIndex(index)
        if "theme" in settings:
            index = self.theme_combo.findText(settings["theme"])
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
        if "bg_color" in settings:
            self.bg_color = settings["bg_color"]
            self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color};")
        if "sidebar_color" in settings:
            self.sidebar_color = settings["sidebar_color"]
            self.sidebar_color_btn.setStyleSheet(f"background-color: {self.sidebar_color};")
        if "accent_color" in settings:
            self.accent_color = settings["accent_color"]
            self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color};")

    def save_settings_to_file(self):
        settings = {
            "search_engine": self.search_engine_combo.currentText(),
            "theme": self.theme_combo.currentText(),
            "bg_color": self.bg_color,
            "sidebar_color": self.sidebar_color,
            "accent_color": self.accent_color
        }
        with open("silent_settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def load_settings_from_file(self):
        if os.path.exists("silent_settings.json"):
            with open("silent_settings.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def accept(self):
        self.save_settings_to_file()
        super().accept()


class BrowserTab(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)


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
        self.bg_color = self.settings.get("bg_color", "#ffffff")
        self.sidebar_color = self.settings.get("sidebar_color", "#f8f9fa")
        self.accent_color = self.settings.get("accent_color", "#1a73e8")
        
        self.setup_ui()
        self.apply_theme()

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
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.sidebar_color};
                border-right: 1px solid #dadce0;
            }}
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(20)

        # Заголовок
        title = QLabel("SILENT")
        title.setStyleSheet(f"""
            color: {self.accent_color};
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        sidebar_layout.addWidget(title)

        # Поисковая строка
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Поиск или URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                padding: 12px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.accent_color};
            }}
        """)
        sidebar_layout.addWidget(self.url_bar)

        # Навигационные кнопки
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        self.back_btn = self.create_nav_button("←", self.go_back)
        self.forward_btn = self.create_nav_button("→", self.go_forward)
        self.reload_btn = self.create_nav_button("⟳", self.reload_page)
        self.settings_btn = self.create_nav_button("⚙", self.open_settings)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.reload_btn)
        nav_layout.addWidget(self.settings_btn)
        sidebar_layout.addLayout(nav_layout)

        sidebar_layout.addStretch()

        # Подпись
        footer = QLabel("v1.0")
        footer.setStyleSheet("color: #5f6368; font-size: 12px;")
        sidebar_layout.addWidget(footer)

        self.sidebar.setLayout(sidebar_layout)
        self.main_layout.addWidget(self.sidebar)

    def create_nav_button(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedSize(45, 45)
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                font-size: 18px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #f8f9fa;
                border: 1px solid {self.accent_color};
            }}
            QPushButton:pressed {{
                background-color: #e8eaed;
            }}
        """)
        return btn

    def setup_content_area(self):
        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"background-color: {self.bg_color};")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.change_tab)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {self.bg_color};
            }}
            QTabBar::tab {{
                background-color: {self.sidebar_color};
                color: #5f6368;
                padding: 12px 25px;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 0px;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {self.bg_color};
                color: {self.accent_color};
                border-bottom: 2px solid {self.accent_color};
            }}
            QTabBar::tab:hover {{
                background-color: #e8eaed;
                color: #202124;
            }}
            QTabBar::close-button {{
                image: none;
                subcontrol-position: right;
                padding: 5px;
            }}
            QTabBar::close-button:hover {{
                background-color: #dadce0;
            }}
        """)

        content_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.content_area)

        self.add_new_tab(QUrl("https://www.google.com"), "Новая вкладка")

    def add_new_tab(self, qurl, title):
        new_tab = BrowserTab()
        new_tab.setUrl(qurl)
        idx = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(idx)
        self.url_bar.setText(qurl.toString())
        self.url_bar.setFocus()
        new_tab.titleChanged.connect(lambda t, tab=new_tab: self.update_tab_title(tab, t))
        new_tab.urlChanged.connect(lambda u, tab=new_tab: self.update_url(tab, u))

    def update_tab_title(self, tab, title):
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            self.tabs.setTabText(idx, title[:30] + "..." if len(title) > 30 else title)

    def update_url(self, tab, url):
        if self.tabs.currentWidget() == tab:
            self.url_bar.setText(url.toString())

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if "." in text and " " not in text:
            if not text.startswith("http"):
                text = "https://" + text
            qurl = QUrl(text)
        else:
            search_url = self.search_engines[self.current_search_engine] + text
            qurl = QUrl(search_url)
        self.tabs.currentWidget().setUrl(qurl)

    def go_back(self):
        self.tabs.currentWidget().back()

    def go_forward(self):
        self.tabs.currentWidget().forward()

    def reload_page(self):
        self.tabs.currentWidget().reload()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.add_new_tab(QUrl("https://www.google.com"), "Новая вкладка")

    def change_tab(self, index):
        if index >= 0:
            url = self.tabs.currentWidget().url()
            self.url_bar.setText(url.toString())

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = self.load_settings()
            self.current_search_engine = self.settings.get("search_engine", "Google")
            self.bg_color = self.settings.get("bg_color", "#ffffff")
            self.sidebar_color = self.settings.get("sidebar_color", "#f8f9fa")
            self.accent_color = self.settings.get("accent_color", "#1a73e8")
            self.apply_theme()

    def load_settings(self):
        if os.path.exists("silent_settings.json"):
            with open("silent_settings.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def apply_theme(self):
        # Обновляем стили
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.sidebar_color};
                border-right: 1px solid #dadce0;
            }}
        """)
        
        self.content_area.setStyleSheet(f"background-color: {self.bg_color};")
        
        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                padding: 12px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.accent_color};
            }}
        """)

        # Обновляем палитру
        palette = QPalette()
        
        if self.bg_color == "#ffffff" or self.bg_color == "#f8f9fa":
            # Светлая тема
            palette.setColor(QPalette.Window, QColor(self.bg_color))
            palette.setColor(QPalette.WindowText, QColor("#202124"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#202124"))
            palette.setColor(QPalette.Button, QColor(self.sidebar_color))
            palette.setColor(QPalette.ButtonText, QColor("#202124"))
        else:
            # Тёмная тема
            palette.setColor(QPalette.Window, QColor(self.bg_color))
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.Base, QColor("#202124"))
            palette.setColor(QPalette.Text, QColor("#ffffff"))
            palette.setColor(QPalette.Button, QColor(self.sidebar_color))
            palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        
        palette.setColor(QPalette.Link, QColor(self.accent_color))
        palette.setColor(QPalette.Highlight, QColor(self.accent_color))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        
        QApplication.setPalette(palette)

        # Современный шрифт
        font = QFont("Segoe UI", 13)
        font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(font)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    window = SilentBrowser()
    window.show()
    sys.exit(app.exec_())