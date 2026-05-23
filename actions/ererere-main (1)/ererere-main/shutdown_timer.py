# actions/shutdown_timer.py
# J.A.R.V.I.S. Sistem Kapanma Zamanlayıcısı (Windows)

import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import winsound

def _is_windows() -> bool:
    return sys.platform == "win32"

def _cancel_shutdown(player) -> str:
    """Kapanma komutunu iptal eder."""
    if not _is_windows():
        return "Bu özellik sadece Windows'ta çalışır, patron."
    try:
        result = subprocess.run("shutdown /a", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return "Sistem kapanma zamanlayıcısı başarıyla iptal edildi patron."
        else:
            # Hata çıktısında "no pending" gibi bir ifade olabilir
            if "no pending" in result.stdout.lower() or "bulunamadı" in result.stdout.lower():
                return "Aktif bir kapanma zamanlayıcısı bulunmuyor."
            return f"İptal başarısız: {result.stdout.strip() or result.stderr.strip()}"
    except Exception as e:
        return f"İptal sırasında hata: {e}"

def _show_hud(root, minutes, player):
    """Kapanma bilgilendirme HUD'u (kalan süre gösterimi ve iptal butonu)."""
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.95)
        hud.geometry("380x140+15+15")
        hud.configure(bg="#330000")

        tk.Label(hud, text="⚠️ SİSTEM KAPANACAK ⚠️", font=("Orbitron", 12, "bold"),
                 fg="#ff5555", bg="#330000").pack(pady=5)
        label_time = tk.Label(hud, text="", font=("Segoe UI", 10, "bold"),
                              fg="#ffaaaa", bg="#330000")
        label_time.pack(pady=5)
        tk.Label(hud, text="Kalan süre aşağıda gösteriliyor.", font=("Segoe UI", 9),
                 fg="#dddddd", bg="#330000").pack()

        def update_countdown(remaining_seconds):
            if remaining_seconds <= 0:
                label_time.config(text="KAPANIYOR...")
                return
            mins, secs = divmod(remaining_seconds, 60)
            label_time.config(text=f"{mins:02d}:{secs:02d} dakika")
            if hud.winfo_exists():
                hud.after(1000, lambda: update_countdown(remaining_seconds - 1))

        # İptal butonu
        def cancel_and_close():
            result_msg = _cancel_shutdown(player)
            if player:
                player.write_log(f"SYS: {result_msg}")
            hud.destroy()
            # Ayrıca ana pencereye de bilgi gönder
            if hasattr(player, "write_log"):
                player.write_log(f"HUD: {result_msg}")

        btn_cancel = tk.Button(hud, text="✖ KAPANMAYI İPTAL ET", command=cancel_and_close,
                               bg="#aa0000", fg="white", font=("Segoe UI", 9, "bold"),
                               relief=tk.FLAT, padx=10, pady=3)
        btn_cancel.pack(pady=5)

        # Otomatik kapanma (zamanlayıcı süresi dolunca)
        total_seconds = int(minutes * 60)
        update_countdown(total_seconds)

        # HUD 20 saniye sonra otomatik kapanmaz, kullanıcı iptal edene veya süre dolana kadar kalır.
        # Ancak root kapanırsa HUD'u da kapat
        def on_root_close():
            if hud.winfo_exists():
                hud.destroy()
        root.bind("<Destroy>", lambda e: on_root_close())

        # Uyarı sesi
        winsound.Beep(700, 300)
    except Exception as e:
        if player:
            player.write_log(f"SYS: Shutdown HUD hatası: {e}")

def shutdown_timer(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Sistem kapanma zamanlayıcısı kurar veya iptal eder.
    
    Parametreler:
        minutes (int/float): Kaç dakika sonra kapanacağı (0'dan büyük)
        action (str): "set" veya "cancel" (varsayılan: "set")
    """
    if not _is_windows():
        return "Bu özellik yalnızca Windows işletim sisteminde çalışır, efendim."

    params = parameters or {}
    minutes = params.get("minutes", 0)
    action = params.get("action", "set").lower()

    if player:
        player.write_log(f"SYS: ⏱️ Kapanma zamanlayıcı -> {action}")

    try:
        if action == "cancel" or action == "iptal":
            result = _cancel_shutdown(player)
            if speak:
                speak(result)
            return result

        if action == "set":
            if minutes <= 0:
                return "Geçerli bir süre belirtin, patron. Örnek: minutes=10"
            seconds = int(minutes * 60)
            # Windows shutdown komutu
            os.system(f"shutdown /s /t {seconds} /c \"J.A.R.V.I.S. tarafından planlanan kapatma\"")
            if player:
                player.write_log(f"SYS: Kapanma {minutes} dakika sonraya ayarlandı.")
            if speak:
                speak(f"Sistem {minutes} dakika sonra kapanacak şekilde ayarlandı, efendim.")

            # HUD'u ayrı bir thread'de göster (ana thread bloke olmasın)
            if root:
                threading.Thread(target=_show_hud, args=(root, minutes, player), daemon=True).start()

            return f"✅ Bilgisayar {minutes} dakika sonra kapanacak şekilde programlandı. İptal etmek için 'iptal et' veya 'kapanmayı iptal et' deyin."
        else:
            return f"Bilinmeyen aksiyon: {action}. Kullanılabilir: set, cancel"

    except Exception as exc:
        if player:
            player.write_log(f"SYS: Kapanma zamanlayıcı hatası: {exc}")
        return f"Kapanma zamanlayıcı ayarlanamadı: {exc}"