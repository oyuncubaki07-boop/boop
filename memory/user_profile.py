# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Kullanıcı Profil ve Tercih Yönetim Motoru
"""

import json
import os
import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

class UserProfile:
    def __init__(self, profile_path: str = None):
        if profile_path is None:
            PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
            if PERSIST_DIR:
                self.path = Path(os.path.join(PERSIST_DIR, "profile.json"))
            else:
                self.path = get_base_dir() / "memory" / "profile.json"
        else:
            self.path = Path(profile_path)
            
        self.data = {
            "name": "Baki",
            "preferences": {},
            "facts": {},
            "schedule": {}
        }
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        self.data = json.loads(content)
            except Exception as e:
                print(f"[UserProfile] ⚠️ Yükleme hatası: {e}")

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[UserProfile] ⚠️ Kayıt hatası: {e}")

    def set_preference(self, key: str, value):
        self.data.setdefault("preferences", {})[key] = value
        self.save()

    def get_preference(self, key: str, default=None):
        return self.data.get("preferences", {}).get(key, default)

    def set_fact(self, key: str, value):
        self.data.setdefault("facts", {})[key] = value
        self.save()

    def get_fact(self, key: str, default="Henüz bilmiyorum."):
        return self.data.get("facts", {}).get(key, default)

    def add_to_schedule(self, time_str: str, event: str):
        self.data.setdefault("schedule", {})[time_str] = event
        self.save()

    def get_profile_context(self) -> str:
        """Sistem yönergesine (System Prompt) eklenecek özet metni döndürür."""
        name = self.data.get("name", "Efendim")
        facts = "; ".join([f"{k}: {v}" for k, v in self.data.get("facts", {}).items()])
        prefs = "; ".join([f"{k}: {v}" for k, v in self.data.get("preferences", {}).items()])
        
        context_parts = [f"Kullanıcı adı: {name}."]
        if facts:
            context_parts.append(f"Kullanıcı hakkında bilinenler: {facts}.")
        if prefs:
            context_parts.append(f"Kullanıcı tercihleri: {prefs}.")
        return " ".join(context_parts)
