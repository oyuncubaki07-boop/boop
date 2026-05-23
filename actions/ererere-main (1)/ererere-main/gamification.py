import json
from pathlib import Path

class GamificationCore:
    def __init__(self, memory_dir: Path):
        self.file_path = Path(memory_dir) / "gamification.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load_data()

    def load_data(self):
        if not self.file_path.exists():
            return {"level": 1, "xp": 0, "streak": 0, "last_login": ""}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"level": 1, "xp": 0, "streak": 0, "last_login": ""}

    def save_data(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_xp(self, amount: int, reason: str = "") -> str:
        self.data["xp"] += amount
        level_up_threshold = self.data["level"] * 1000
        
        response = f"+{amount} XP kazandın. ({reason})"
        
        if self.data["xp"] >= level_up_threshold:
            self.data["level"] += 1
            self.data["xp"] = 0
            response += f"\nSEVİYE ATLADIN, Komutan. Yeni Seviye: {self.data['level']}. Hedeflere bir adım daha yakınsın."
            
        self.save_data()
        return response

    def punish(self, amount: int, reason: str = "") -> str:
        self.data["xp"] = max(0, self.data["xp"] - amount)
        self.save_data()
        return f"-{amount} XP kaybettin. Zayıflık kabul edilemez. ({reason})"