import json
import os
from PyQt5.QtCore import QObject, pyqtSignal


class Space:
    def __init__(self, name="Space", color="#4a9eff"):
        self.name = name
        self.color = color
        self.tabs_data = []
        self.speed_dial = []

    def to_dict(self):
        return {"name": self.name, "color": self.color,
                "tabs_data": self.tabs_data, "speed_dial": self.speed_dial}

    @staticmethod
    def from_dict(d):
        s = Space(d.get("name", "Space"), d.get("color", "#4a9eff"))
        s.tabs_data = d.get("tabs_data", [])
        s.speed_dial = d.get("speed_dial", [])
        return s


class SpacesManager(QObject):
    spaces_changed = pyqtSignal()
    current_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.spaces = [Space("Главное", "#4a9eff")]
        self.current_index = 0
        self.load()

    @property
    def current(self): return self.spaces[self.current_index]

    def add_space(self, name="Новое", color="#4a9eff"):
        self.spaces.append(Space(name, color))
        self.save(); self.spaces_changed.emit()

    def remove_space(self, index):
        if len(self.spaces) <= 1: return
        if 0 <= index < len(self.spaces):
            self.spaces.pop(index)
            if self.current_index >= len(self.spaces):
                self.current_index = len(self.spaces) - 1
            self.save(); self.spaces_changed.emit()

    def rename_space(self, index, name):
        if 0 <= index < len(self.spaces):
            self.spaces[index].name = name
            self.save(); self.spaces_changed.emit()

    def switch_to(self, index):
        if 0 <= index < len(self.spaces):
            self.current_index = index
            self.save(); self.current_changed.emit(index)

    def save(self):
        data = {"spaces": [s.to_dict() for s in self.spaces],
                "current_index": self.current_index}
        try:
            with open("silent_spaces.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Spaces save error: {e}")

    def load(self):
        if not os.path.exists("silent_spaces.json"): return
        try:
            with open("silent_spaces.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self.spaces = [Space.from_dict(d) for d in data.get("spaces", [])]
            if not self.spaces: self.spaces = [Space("Главное", "#4a9eff")]
            self.current_index = min(data.get("current_index", 0), len(self.spaces) - 1)
        except Exception as e:
            print(f"Spaces load error: {e}")
            self.spaces = [Space("Главное", "#4a9eff")]