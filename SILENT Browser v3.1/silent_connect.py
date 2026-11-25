import json
import os
import time
import socket
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QCheckBox, QLineEdit,
    QMessageBox, QListWidget, QListWidgetItem, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread


class PingWorker(QObject):
    finished = pyqtSignal(str, float)
    def __init__(self, dns_list):
        super().__init__()
        self.dns_list = dns_list
    def run(self):
        for key, ip in self.dns_list:
            self.finished.emit(key, self._ping(ip))
    def _ping(self, ip):
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.5)
            sock.connect((ip, 53))
            sock.close()
            return (time.time() - start) * 1000
        except Exception:
            return -1


class ConnectManager(QObject):
    status_changed = pyqtSignal(str)
    latency_updated = pyqtSignal(dict)

    BUILT_IN_DNS = {
        "cloudflare": {"name": "Cloudflare", "ip": "1.1.1.1"},
        "google":     {"name": "Google DNS", "ip": "8.8.8.8"},
        "quad9":      {"name": "Quad9", "ip": "9.9.9.9"},
        "adguard":    {"name": "AdGuard DNS", "ip": "94.140.14.14"},
        "opendns":    {"name": "OpenDNS", "ip": "208.67.222.222"},
        "yandex":     {"name": "Яндекс DNS", "ip": "77.88.8.8"}
    }

    def __init__(self):
        super().__init__()
        self._status = "disconnected"
        self._mode = "dns"
        self._active_dns = "cloudflare"
        self._auto_mode = False
        self._auto_connect = False
        self._run_with_windows = False
        self._custom_dns = {}
        self._latencies = {}
        self.load_settings()

    @property
    def status(self): return self._status
    @property
    def mode(self): return self._mode
    @property
    def active_dns(self): return self._active_dns
    @property
    def auto_mode(self): return self._auto_mode
    @property
    def auto_connect(self): return self._auto_connect
    @property
    def latencies(self): return self._latencies

    def all_dns(self):
        result = dict(self.BUILT_IN_DNS)
        result.update(self._custom_dns)
        return result

    def active_dns_name(self):
        dns = self.all_dns().get(self._active_dns)
        return dns["name"] if dns else "Не выбран"

    def active_dns_ip(self):
        dns = self.all_dns().get(self._active_dns)
        return dns["ip"] if dns else "—"

    def mode_name(self):
        return "Auto (лучший DNS)" if self._auto_mode else f"DNS: {self.active_dns_name()}"

    def connect(self):
        if self._status == "connected": return
        self._set_status("connecting")
        if self._auto_mode:
            self._ping_all(on_complete=self._on_auto_done)
        else:
            QTimer.singleShot(1200, lambda: self._set_status("connected"))

    def _on_auto_done(self):
        valid = {k: v for k, v in self._latencies.items() if v > 0}
        if not valid:
            self._set_status("error"); return
        self._active_dns = min(valid, key=valid.get)
        self.save_settings()
        self._set_status("connected")

    def disconnect(self):
        self._set_status("disconnected")

    def _set_status(self, s):
        self._status = s
        self.status_changed.emit(s)

    def set_mode(self, m):
        if m in ("dns", "tunnel"):
            self._mode = m
            if self._status == "connected": self.disconnect()

    def set_auto_mode(self, v): self._auto_mode = v
    def set_active_dns(self, k):
        if k in self.all_dns():
            self._active_dns = k
            if self._status == "connected" and not self._auto_mode: self.disconnect()
    def set_auto_connect(self, v): self._auto_connect = v
    def set_run_with_windows(self, v): self._run_with_windows = v

    def add_custom_dns(self, name, ip):
        key = "custom_" + str(int(time.time() * 1000))
        self._custom_dns[key] = {"name": name, "ip": ip}
        self.save_settings()
        return key

    def remove_custom_dns(self, key):
        if key in self._custom_dns:
            del self._custom_dns[key]
            if self._active_dns == key: self._active_dns = "cloudflare"
            self.save_settings()

    def update_custom_dns(self, key, name, ip):
        if key in self._custom_dns:
            self._custom_dns[key] = {"name": name, "ip": ip}
            self.save_settings()

    def _ping_all(self, on_complete=None):
        self._ping_thread = QThread()
        dns_list = [(k, v["ip"]) for k, v in self.all_dns().items()]
        self._ping_worker = PingWorker(dns_list)
        self._ping_worker.moveToThread(self._ping_thread)
        self._ping_thread.started.connect(self._ping_worker.run)
        self._ping_worker.finished.connect(self._on_ping_result)
        self._on_complete_cb = on_complete
        self._pending = len(dns_list)
        def _done():
            self._ping_thread.quit()
            self._ping_thread.wait()
            if self._on_complete_cb: self._on_complete_cb()
        self._ping_thread.finished.connect(_done)
        self._ping_thread.start()

    def _on_ping_result(self, key, latency):
        self._latencies[key] = latency
        self._pending -= 1
        self.latency_updated.emit(dict(self._latencies))
        if self._pending <= 0:
            self._ping_thread.quit()

    def ping_all(self):
        self._latencies = {}
        self._ping_all()

    def save_settings(self):
        settings = self._load_all()
        settings["connect"] = {
            "mode": self._mode, "active_dns": self._active_dns,
            "auto_mode": self._auto_mode, "auto_connect": self._auto_connect,
            "run_with_windows": self._run_with_windows,
            "custom_dns": self._custom_dns
        }
        try:
            with open("silent_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Connect save error: {e}")

    def load_settings(self):
        s = self._load_all()
        c = s.get("connect", {})
        self._mode = c.get("mode", "dns")
        self._active_dns = c.get("active_dns", "cloudflare")
        self._auto_mode = c.get("auto_mode", False)
        self._auto_connect = c.get("auto_connect", False)
        self._run_with_windows = c.get("run_with_windows", False)
        self._custom_dns = c.get("custom_dns", {})

    def _load_all(self):
        if os.path.exists("silent_settings.json"):
            try:
                with open("silent_settings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return {}
        return {}


class ConnectPopup(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("SILENT CONNECT")
        self.setFixedSize(400, 580)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("QDialog { background-color: #1a1a1a; border: 1px solid #2a2a2a; } QLabel { color: #ffffff; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("SILENT CONNECT")
        title.setStyleSheet("font-size: 16px; font-weight: 700; letter-spacing: 1px;")
        header.addWidget(title); header.addStretch()
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: #ffffff; border: none; border-radius: 16px; font-size: 16px; } QPushButton:hover { background-color: #3a3a3a; }")
        settings_btn.clicked.connect(self.open_settings)
        header.addWidget(settings_btn)
        layout.addLayout(header)

        self.status_circle = QLabel("●")
        self.status_circle.setAlignment(Qt.AlignCenter)
        self.status_circle.setFixedSize(130, 130)
        layout.addWidget(self.status_circle, alignment=Qt.AlignCenter)

        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(self.status_label)

        self.mode_label = QLabel()
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("color: #8a8a8a; font-size: 13px;")
        layout.addWidget(self.mode_label)

        self.dns_label = QLabel()
        self.dns_label.setAlignment(Qt.AlignCenter)
        self.dns_label.setStyleSheet("color: #8a8a8a; font-size: 12px;")
        layout.addWidget(self.dns_label)

        self.latency_label = QLabel()
        self.latency_label.setAlignment(Qt.AlignCenter)
        self.latency_label.setStyleSheet("color: #4a9eff; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.latency_label)

        layout.addStretch()

        self.action_btn = QPushButton("Connect")
        self.action_btn.setFixedHeight(48)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("QPushButton { background-color: #ffffff; color: #000000; border: none; border-radius: 12px; font-size: 15px; font-weight: 700; } QPushButton:hover { background-color: #e0e0e0; } QPushButton:disabled { background-color: #3a3a3a; color: #8a8a8a; }")
        self.action_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.action_btn)

        ping_btn = QPushButton("📡 Проверить скорость DNS")
        ping_btn.setFixedHeight(38)
        ping_btn.setCursor(Qt.PointingHandCursor)
        ping_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: #ffffff; border: none; border-radius: 10px; font-size: 13px; } QPushButton:hover { background-color: #3a3a3a; }")
        ping_btn.clicked.connect(self.run_ping)
        layout.addWidget(ping_btn)

        demo_label = QLabel("Demo · Network engine not configured")
        demo_label.setAlignment(Qt.AlignCenter)
        demo_label.setStyleSheet("color: #5f6368; font-size: 10px; font-style: italic;")
        layout.addWidget(demo_label)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: #ffffff; border: none; border-radius: 8px; font-size: 13px; } QPushButton:hover { background-color: #3a3a3a; }")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.manager.status_changed.connect(self.update_status)
        self.manager.latency_updated.connect(self.update_latencies)
        self.update_status(self.manager.status)
        self.update_info()

    def update_status(self, status):
        colors = {
            "disconnected": ("#5f6368", "#2a2a2a"),
            "connecting":   ("#f9ab00", "#3a2f10"),
            "connected":    ("#34a853", "#1a3a20"),
            "error":        ("#ea4335", "#3a1a1a")
        }
        texts = {
            "disconnected": "Disconnected", "connecting": "Connecting...",
            "connected": "Connected", "error": "Error"
        }
        dot_color, bg_color = colors.get(status, colors["disconnected"])
        self.status_label.setText(texts.get(status, "Unknown"))
        self.status_circle.setStyleSheet(f"font-size: 80px; background-color: {bg_color}; border-radius: 65px; color: {dot_color};")
        if status == "connected":
            self.action_btn.setText("Disconnect"); self.action_btn.setEnabled(True)
        elif status == "connecting":
            self.action_btn.setText("Connecting..."); self.action_btn.setEnabled(False)
            QTimer.singleShot(1600, lambda: self.action_btn.setEnabled(True))
        else:
            self.action_btn.setText("Connect"); self.action_btn.setEnabled(True)

    def update_info(self):
        self.mode_label.setText(f"Mode: {self.manager.mode_name()}")
        self.dns_label.setText(f"DNS: {self.manager.active_dns_name()} ({self.manager.active_dns_ip()})")
        self.update_latencies(self.manager.latencies)

    def update_latencies(self, latencies):
        if not latencies:
            self.latency_label.setText(""); return
        current = latencies.get(self.manager.active_dns)
        if current and current > 0:
            self.latency_label.setText(f"⚡ Задержка: {current:.0f} мс")
        else:
            self.latency_label.setText("")

    def toggle_connection(self):
        if self.manager.status == "connected":
            self.manager.disconnect()
        else:
            self.manager.connect()
        self.update_info()

    def run_ping(self):
        self.latency_label.setText("📡 Проверяю...")
        self.manager.ping_all()

    def open_settings(self):
        dialog = ConnectSettingsDialog(self.manager, self)
        dialog.exec_()
        self.update_info()


class ConnectSettingsDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("SILENT CONNECT · Настройки")
        self.setFixedSize(480, 620)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: #ffffff; }
            QLabel { color: #ffffff; font-size: 13px; }
            QLabel#section { font-size: 14px; font-weight: 600; margin-top: 10px; }
            QComboBox, QLineEdit { background-color: #2a2a2a; color: #ffffff; border: 1px solid #3a3a3a; padding: 10px 12px; border-radius: 8px; font-size: 13px; }
            QComboBox:hover, QLineEdit:hover { border: 1px solid #4a4a4a; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #ffffff; margin-right: 10px; }
            QCheckBox { color: #ffffff; font-size: 13px; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #4a4a4a; background-color: #2a2a2a; }
            QCheckBox::indicator:checked { background-color: #ffffff; border: 1px solid #ffffff; }
            QListWidget { background-color: #2a2a2a; color: #ffffff; border: 1px solid #3a3a3a; border-radius: 8px; font-size: 13px; padding: 4px; }
            QListWidget::item { padding: 8px; border-radius: 6px; }
            QListWidget::item:selected { background-color: #3a3a3a; }
            QPushButton { background-color: #ffffff; color: #000000; border: none; padding: 10px 20px; font-size: 13px; font-weight: 600; border-radius: 8px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton#secondary { background-color: #2a2a2a; color: #ffffff; }
            QPushButton#secondary:hover { background-color: #3a3a3a; }
            QPushButton#danger { background-color: #ea4335; color: #ffffff; }
            QPushButton#danger:hover { background-color: #c5221f; }
        """)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(10)

        title = QLabel("Настройки подключения")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        s1 = QLabel("Режим"); s1.setObjectName("section"); layout.addWidget(s1)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("DNS (безопасный резолвер)", "dns")
        self.mode_combo.addItem("Tunnel (полный туннель)", "tunnel")
        idx = self.mode_combo.findData(manager.mode)
        if idx >= 0: self.mode_combo.setCurrentIndex(idx)
        layout.addWidget(self.mode_combo)

        self.auto_check = QCheckBox("Автоматически выбирать самый быстрый DNS")
        self.auto_check.setChecked(manager.auto_mode)
        layout.addWidget(self.auto_check)

        s2 = QLabel("Активный DNS-сервер"); s2.setObjectName("section"); layout.addWidget(s2)
        self.dns_combo = QComboBox()
        self._refresh_dns_combo()
        layout.addWidget(self.dns_combo)

        s3 = QLabel("Мои DNS-серверы"); s3.setObjectName("section"); layout.addWidget(s3)
        self.custom_list = QListWidget()
        self.custom_list.setMaximumHeight(120)
        self._refresh_custom_list()
        layout.addWidget(self.custom_list)

        add_layout = QHBoxLayout()
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Имя")
        add_layout.addWidget(self.name_input)
        self.ip_input = QLineEdit(); self.ip_input.setPlaceholderText("IP (например: 1.1.1.1)")
        add_layout.addWidget(self.ip_input)
        add_btn = QPushButton("+"); add_btn.setFixedWidth(40)
        add_btn.clicked.connect(self.add_custom)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        btns_layout = QHBoxLayout()
        edit_btn = QPushButton("Изменить"); edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_custom)
        del_btn = QPushButton("Удалить"); del_btn.setObjectName("danger")
        del_btn.clicked.connect(self.delete_custom)
        btns_layout.addWidget(edit_btn); btns_layout.addWidget(del_btn)
        layout.addLayout(btns_layout)

        s4 = QLabel("Поведение"); s4.setObjectName("section"); layout.addWidget(s4)
        self.auto_connect_check = QCheckBox("Автоподключение при запуске")
        self.auto_connect_check.setChecked(manager.auto_connect)
        layout.addWidget(self.auto_connect_check)
        self.win_check = QCheckBox("Запускать вместе с Windows")
        self.win_check.setChecked(manager.run_with_windows)
        layout.addWidget(self.win_check)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена"); cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить"); save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn); btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        scroll.setWidget(content)
        main_l = QVBoxLayout(self); main_l.setContentsMargins(0, 0, 0, 0)
        main_l.addWidget(scroll)

    def _refresh_dns_combo(self):
        self.dns_combo.clear()
        for key, dns in self.manager.all_dns().items():
            latency = self.manager.latencies.get(key)
            lat_str = f" · {latency:.0f}мс" if latency and latency > 0 else ""
            self.dns_combo.addItem(f"{dns['name']} ({dns['ip']}){lat_str}", key)
        idx = self.dns_combo.findData(self.manager.active_dns)
        if idx >= 0: self.dns_combo.setCurrentIndex(idx)

    def _refresh_custom_list(self):
        self.custom_list.clear()
        for key, dns in self.manager._custom_dns.items():
            item = QListWidgetItem(f"{dns['name']}  —  {dns['ip']}")
            item.setData(Qt.UserRole, key)
            self.custom_list.addItem(item)

    def add_custom(self):
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()
        if not name or not ip:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и IP"); return
        self.manager.add_custom_dns(name, ip)
        self.name_input.clear(); self.ip_input.clear()
        self._refresh_custom_list(); self._refresh_dns_combo()

    def edit_custom(self):
        item = self.custom_list.currentItem()
        if not item: return
        key = item.data(Qt.UserRole)
        dns = self.manager._custom_dns.get(key)
        if not dns: return
        from PyQt5.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Имя", "Новое имя:", text=dns['name'])
        if not ok: return
        new_ip, ok = QInputDialog.getText(self, "IP", "Новый IP:", text=dns['ip'])
        if not ok: return
        self.manager.update_custom_dns(key, new_name, new_ip)
        self._refresh_custom_list(); self._refresh_dns_combo()

    def delete_custom(self):
        item = self.custom_list.currentItem()
        if not item: return
        key = item.data(Qt.UserRole)
        self.manager.remove_custom_dns(key)
        self._refresh_custom_list(); self._refresh_dns_combo()

    def accept(self):
        self.manager.set_mode(self.mode_combo.currentData())
        self.manager.set_auto_mode(self.auto_check.isChecked())
        self.manager.set_active_dns(self.dns_combo.currentData())
        self.manager.set_auto_connect(self.auto_connect_check.isChecked())
        self.manager.set_run_with_windows(self.win_check.isChecked())
        self.manager.save_settings()
        super().accept()