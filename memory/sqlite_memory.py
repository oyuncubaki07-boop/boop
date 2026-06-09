# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. SQLite Uzun Süreli Hafıza Modülü (SQLite Long-Term Memory)
---------------------------------------------------------------------
Bu modül, kullanıcının kişisel bilgilerini, tercihlerini, projelerini ve
diğer önemli detayları kalıcı olarak yerel bir SQLite veritabanında saklar.
Model (Groq / Ollama / Gemini) ile konuşurken bu bilgiler bağlam olarak sunulur.
"""

import os
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger("JARVIS_SQLiteMemory")

class SQLiteMemoryManager:
    """SQLite veritabanı kullanarak uzun süreli hafıza işlemlerini yöneten sınıf."""
    
    def __init__(self, db_name="jarvis_memory.db"):
        # Veritabanını J.A.R.V.I.S.'in ana hafıza dizininde veya çalışma alanında saklayalım
        PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
        if PERSIST_DIR:
            self.db_path = os.path.join(PERSIST_DIR, db_name)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, db_name)
        self._init_db()

    def _init_db(self):
        """Hafıza tablosunu oluşturur (yoksa)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,       -- identity, preference, project, relationship, vb.
                        key TEXT NOT NULL,            -- e.g. 'user_name', 'favorite_food'
                        value TEXT NOT NULL,          -- Hatırlanacak değer
                        updated_at TEXT NOT NULL,     -- Güncellenme tarihi (YYYY-MM-DD)
                        UNIQUE(category, key)         -- Aynı kategoride aynı anahtardan tek kayıt olmalı
                    )
                """)
                conn.commit()
            logger.info(f"[SQLiteMemory] Veritabanı başlatıldı: {self.db_path}")
        except Exception as e:
            logger.error(f"[SQLiteMemory] Veritabanı başlatma hatası: {e}")

    def save_fact(self, category: str, key: str, value: str) -> str:
        """
        Veritabanına yeni bir bilgi kaydeder veya mevcut bilgiyi günceller.
        """
        category = category.lower().strip()
        key = key.lower().replace(" ", "_").strip()
        value = value.strip()
        today = datetime.now().strftime("%Y-%m-%d")

        if not category or not key or not value:
            return "Hata: Kategori, anahtar veya değer boş olamaz."

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # UPSERT yapısı: Kayıt varsa UPDATE et, yoksa INSERT yap
                cursor.execute("""
                    INSERT INTO memories (category, key, value, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(category, key) 
                    DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """, (category, key, value, today))
                conn.commit()
            msg = f"Kayıt Başarılı: [{category}] {key} = '{value}'"
            logger.info(f"[SQLiteMemory] {msg}")
            return msg
        except Exception as e:
            err_msg = f"Hafızaya kaydetme hatası: {e}"
            logger.error(f"[SQLiteMemory] {err_msg}")
            return err_msg

    def delete_fact(self, category: str, key: str) -> str:
        """Hafızadan belirli bir anahtara ait bilgiyi siler."""
        category = category.lower().strip()
        key = key.lower().replace(" ", "_").strip()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE category = ? AND key = ?", (category, key))
                conn.commit()
                if cursor.rowcount > 0:
                    return f"Hafızadan silindi: [{category}] {key}"
                else:
                    return f"Belirtilen bilgi bulunamadı: [{category}] {key}"
        except Exception as e:
            return f"Silme işlemi başarısız: {e}"

    def get_all_context(self) -> str:
        """
        Veritabanındaki tüm bilgileri okur ve dil modelinin sistem promptuna (system instruction)
        bağlam olarak yerleştirilebilecek şekilde düzgün bir metin bloğu haline getirir.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT category, key, value FROM memories ORDER BY category, key")
                rows = cursor.fetchall()
            
            if not rows:
                return ""

            # Kategorilere göre gruplayıp güzel bir metin oluşturalım
            categorized = {}
            for category, key, value in rows:
                if category not in categorized:
                    categorized[category] = []
                # Anahtarı okunaklı hale getir
                display_key = key.replace("_", " ").title()
                categorized[category].append(f"  - {display_key}: {value}")

            context_lines = [
                "\n=== J.A.R.V.I.S. UZUN SÜRELİ BELLEK (Kullanıcı Hakkında Bilinenler) ===",
                "Not: Aşağıdaki bilgileri konuşma sırasında doğal bir şekilde kullan, ezbere liste olarak okuma."
            ]

            for cat, items in categorized.items():
                context_lines.append(f"\n[{cat.upper()}]")
                context_lines.extend(items)

            context_lines.append("=====================================================================\n")
            return "\n".join(context_lines)
        except Exception as e:
            logger.error(f"[SQLiteMemory] Bağlam oluşturma hatası: {e}")
            return ""

    def search_facts(self, query: str) -> list:
        """Kullanıcının sorduğu soruya göre veritabanında arama yapar (basit LIKE araması)."""
        query_cleaned = f"%{query.lower().strip()}%"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT category, key, value FROM memories 
                    WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                """, (query_cleaned, query_cleaned, query_cleaned))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"[SQLiteMemory] Arama hatası: {e}")
            return []

# Test amaçlı tek başına çalıştırma desteği
if __name__ == "__main__":
    db = SQLiteMemoryManager()
    
    # Bilgi kaydetme örnekleri
    print(db.save_fact("identity", "user_name", "Baki"))
    print(db.save_fact("preferences", "favorite_music", "Rock ve Klasik Müzik"))
    print(db.save_fact("projects", "jarvis_project", "Yapay zeka asistanı geliştirme"))
    print(db.save_fact("wishes", "next_trip", "Japonya seyahati planlamak"))
    
    # Prompt bağlam formatı testi
    print("\n--- Model için oluşturulan bağlam metni ---")
    print(db.get_all_context())
    
    # Arama testi
    print("\n--- 'seya' için arama sonuçları ---")
    print(db.search_facts("seya"))
