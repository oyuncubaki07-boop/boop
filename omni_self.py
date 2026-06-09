# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Omni-Self - Cognitive Continuity
Logs and analyzes user's stream of thoughts to generate proactive guidance.
"""

import os
import json
import datetime
from jarvise_core import think

class CognitiveContinuity:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
        if PERSIST_DIR:
            self.thoughts_file = os.path.join(PERSIST_DIR, "omni_self_stream.json")
        else:
            self.thoughts_file = os.path.join(self.base_dir, "memory", "omni_self_stream.json")
        self.thoughts = self.load_thoughts()
        
    def load_thoughts(self) -> list:
        if os.path.exists(self.thoughts_file):
            try:
                with open(self.thoughts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception:
                return []
        return []
        
    def save_thoughts(self):
        try:
            os.makedirs(os.path.dirname(self.thoughts_file), exist_ok=True)
            with open(self.thoughts_file, "w", encoding="utf-8") as f:
                json.dump(self.thoughts[-100:], f, indent=2, ensure_ascii=False)  # Keep last 100 entries
        except Exception:
            pass
            
    def record_thought(self, user_text: str):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "thought": user_text
        }
        self.thoughts.append(entry)
        self.save_thoughts()
        
    def generate_proactive_thought(self) -> str:
        """Analyzes recent thoughts to produce a brief predictive advice."""
        # Only trigger proactivity occasionally to prevent voice chat spam
        if len(self.thoughts) < 3 or (len(self.thoughts) % 4 != 0):
            return ""
            
        recent = [t["thought"] for t in self.thoughts[-5:]]
        prompt = f"""Kullanıcının son birkaç etkileşimi ve düşüncesi şunlardır:
        {recent}
        
        Kullanıcının odaklandığı ana konuyu veya zihinsel durumunu çıkar.
        J.A.R.V.I.S. kimliğiyle, ona yardımcı olabilecek, bir sonraki adımı öngören proaktif bir tavsiye ver.
        Tavsiye son derece kısa (en fazla 15 kelime), asil, bilgece ve teşvik edici olmalıdır. Yanıtında sadece tavsiyeyi yaz, başka hiçbir açıklama yapma."""
        
        try:
            thought = think(prompt, use_memory=False)
            return thought.strip()
        except Exception:
            return ""
