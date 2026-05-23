# actions/smart_notes.py
# J.A.R.V.I.S. Akıllı Not Defteri Modülü

import os
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import winsound
import threading

def _get_notes_dir():
    """Notların kaydedileceği dizini oluşturur/gösterir."""
    notes_dir = os.path.join(os.path.expanduser("~"), "JARVIS_Notlar")
    if not os.path.exists(notes_dir):
        os.makedirs(notes_dir)
    return notes_dir

def _save_note(content, filename=None):
    """Notu dosyaya kaydeder. Dosya adı yoksa otomatik oluşturur."""
    notes_dir = _get_notes_dir()
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"not_{timestamp}.txt"
    filepath = os.path.join(notes_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath, filename

def _list_notes():
    """Tüm notları listeler (dosya adları ve tarihler)."""
    notes_dir = _get_notes_dir()
    notes = []
    for f in os.listdir(notes_dir):
        if f.endswith(".txt"):
            full_path = os.path.join(notes_dir, f)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
            notes.append((f, mod_time, full_path))
    notes.sort(key=lambda x: x[1], reverse=True)  # En yeniden eskiye
    return notes

def take_note(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Akıllı not alma / yönetim modülü.
    
    Parametreler:
        note_text (str): Kaydedilecek not metni (gerekli)
        action (str): "save", "list", "delete", "read" (varsayılan: "save")
        filename (str): İşlem yapılacak dosya adı (list, delete, read için)
    """
    params = parameters or {}
    action = params.get("action", "save").lower()
    note_text = params.get("note_text", "").strip()
    filename = params.get("filename", "").strip()

    if player:
        player.write_log(f"SYS: 📝 Not işlemi -> {action}")

    # ----- KAYDET -----
    if action == "save":
        if not note_text:
            return "Patron, neyi not almam gerektiğini söylemediniz."

        try:
            filepath, saved_name = _save_note(note_text)
            # HUD gösterimi
            if root:
                try:
                    hud = tk.Toplevel(root)
                    hud.overrideredirect(True)
                    hud.attributes("-topmost", True, "-alpha", 0.92)
                    hud.geometry("360x90+15+15")
                    hud.configure(bg="#0a2a0a")
                    tk.Label(hud, text="📝 NOT KAYDEDİLDİ", font=("Orbitron", 11, "bold"),
                             fg="#00ff88", bg="#0a2a0a").pack(pady=5)
                    tk.Label(hud, text=f"{saved_name}", font=("Segoe UI", 9),
                             fg="white", bg="#0a2a0a").pack()
                    try:
                        winsound.Beep(700, 150)
                    except:
                        pass
                    root.after(3000, hud.destroy)
                except:
                    pass

            if speak:
                speak("Notunuz başarıyla kaydedildi efendim.")

            return f"✅ Not kaydedildi: {saved_name}\n📂 Konum: {filepath}"
        except Exception as e:
            return f"Not kaydedilemedi: {str(e)}"

    # ----- NOTLARI LİSTELE -----
    elif action == "list":
        notes = _list_notes()
        if not notes:
            return "Henüz hiç not alınmamış, patron."

        result = "📋 KAYITLI NOTLAR:\n" + "-" * 30 + "\n"
        for i, (fname, mod_time, _) in enumerate(notes[:10], 1):  # son 10 not
            result += f"{i}. {fname} - {mod_time.strftime('%d.%m.%Y %H:%M')}\n"
        if len(notes) > 10:
            result += f"\n... ve {len(notes)-10} not daha. Detay için 'notları göster' deyin."
        return result

    # ----- NOT SİL -----
    elif action == "delete":
        if not filename:
            return "Silmek için dosya adını belirtin, patron. Örneğin: filename='not_20250315_123456.txt'"
        notes_dir = _get_notes_dir()
        filepath = os.path.join(notes_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"🗑️ Not silindi: {filename}"
        else:
            return f"Dosya bulunamadı: {filename}"

    # ----- NOT OKU (içeriğini göster) -----
    elif action == "read":
        if not filename:
            # En son notu oku
            notes = _list_notes()
            if not notes:
                return "Okunacak not yok."
            filename = notes[0][0]
        notes_dir = _get_notes_dir()
        filepath = os.path.join(notes_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Uzun notları kırp
            if len(content) > 1000:
                content = content[:1000] + "\n... (not çok uzun, kırpıldı)"
            if speak:
                speak(f"Not okunuyor: {content[:200]}")
            return f"📄 {filename} içeriği:\n\n{content}"
        else:
            return f"Dosya bulunamadı: {filename}"

    else:
        return f"Bilinmeyen işlem: {action}. Kullanılabilir: save, list, delete, read"