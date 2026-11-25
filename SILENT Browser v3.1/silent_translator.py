import urllib.request
import urllib.parse
import json
import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QApplication)
from PyQt5.QtCore import Qt


LANGUAGES = {
    "auto": "Автоопределение",
    "ru": "Русский",
    "en": "Английский",
    "es": "Испанский",
    "fr": "Французский",
    "de": "Немецкий",
    "it": "Итальянский",
    "pt": "Португальский",
    "zh": "Китайский",
    "ja": "Японский",
    "ko": "Корейский",
    "ar": "Арабский",
    "uk": "Украинский",
    "pl": "Польский"
}

_last_request_time = 0

def translate_text(text, target_lang="ru", source_lang="auto"):
    """Перевод через Google Translate с задержкой для избежания 429."""
    global _last_request_time
    if not text.strip():
        return "", source_lang
    
    # Задержка между запросами (2 секунды)
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    if time_since_last < 2.0:
        time.sleep(2.0 - time_since_last)
    
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source_lang,
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = "".join(part[0] for part in data[0] if part[0])
        detected = data[2] if len(data) > 2 else source_lang
        _last_request_time = time.time()
        return result, detected
    except Exception as e:
        return f"[Ошибка перевода: {e}]", source_lang


class TranslatorDialog(QDialog):
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Переводчик SILENT")
        self.setFixedSize(560, 520)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: #ffffff; }
            QLabel { color: #ffffff; font-size: 13px; }
            QLabel#title { font-size: 18px; font-weight: 700; margin-bottom: 5px; }
            QTextEdit { background-color: #2a2a2a; color: #ffffff; border: 1px solid #3a3a3a; border-radius: 8px; padding: 10px; font-size: 14px; }
            QTextEdit:focus { border: 1px solid #4a9eff; }
            QComboBox { background-color: #2a2a2a; color: #ffffff; border: 1px solid #3a3a3a; padding: 8px 12px; border-radius: 8px; font-size: 13px; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #ffffff; margin-right: 10px; }
            QPushButton { background-color: #ffffff; color: #000000; border: none; padding: 10px 20px; font-size: 13px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton#secondary { background-color: #2a2a2a; color: #ffffff; }
            QPushButton#secondary:hover { background-color: #3a3a3a; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Переводчик")
        title.setObjectName("title")
        layout.addWidget(title)

        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(10)

        lang_layout.addWidget(QLabel("Откуда:"))
        self.source_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.source_combo.addItem(name, code)
        self.source_combo.setCurrentIndex(0)
        lang_layout.addWidget(self.source_combo)

        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(40, 36)
        swap_btn.clicked.connect(self.swap_languages)
        lang_layout.addWidget(swap_btn)

        lang_layout.addWidget(QLabel("Куда:"))
        self.target_combo = QComboBox()
        for code, name in LANGUAGES.items():
            if code != "auto":
                self.target_combo.addItem(name, code)
        self.target_combo.setCurrentIndex(0)
        lang_layout.addWidget(self.target_combo)

        layout.addLayout(lang_layout)

        layout.addWidget(QLabel("Исходный текст:"))
        self.source_edit = QTextEdit()
        self.source_edit.setPlaceholderText("Введите текст для перевода...")
        if initial_text:
            self.source_edit.setPlainText(initial_text)
        layout.addWidget(self.source_edit)

        translate_btn = QPushButton("Перевести")
        translate_btn.clicked.connect(self.do_translate)
        layout.addWidget(translate_btn)

        layout.addWidget(QLabel("Перевод:"))
        self.target_edit = QTextEdit()
        self.target_edit.setReadOnly(True)
        layout.addWidget(self.target_edit)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("Копировать")
        copy_btn.setObjectName("secondary")
        copy_btn.clicked.connect(self.copy_result)
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def swap_languages(self):
        src = self.source_combo.currentData()
        tgt = self.target_combo.currentData()
        if src == "auto": return
        idx_src = self.target_combo.findData(src)
        idx_tgt = self.source_combo.findData(tgt)
        if idx_src >= 0 and idx_tgt >= 0:
            self.source_combo.setCurrentIndex(idx_tgt)
            self.target_combo.setCurrentIndex(idx_src)
            src_text = self.source_edit.toPlainText()
            tgt_text = self.target_edit.toPlainText()
            self.source_edit.setPlainText(tgt_text)
            self.target_edit.setPlainText(src_text)

    def do_translate(self):
        text = self.source_edit.toPlainText()
        if not text.strip():
            self.target_edit.setPlainText("")
            return
        src = self.source_combo.currentData()
        tgt = self.target_combo.currentData()
        self.target_edit.setPlainText("Перевожу...")
        QApplication.processEvents()
        result, detected = translate_text(text, tgt, src)
        self.target_edit.setPlainText(result)

    def copy_result(self):
        text = self.target_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)