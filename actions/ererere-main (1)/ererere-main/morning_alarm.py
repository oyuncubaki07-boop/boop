"""
morning_alarm.py - J.A.R.V.I.S. Sabah Alarmı Modülü
Belirtilen saatte alarm çalar, erteleme seçeneği sunar.
"""

import threading
import time
import tkinter as tk
import winsound
import datetime
from typing import Optional

def _parse_time(time_str: str) -> tuple:
    """HH:MM formatını (saat, dakika) tamsayıya çevirir."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return hour, minute
        except ValueError:
            pass
    return None, None

def _calculate_wait_seconds(target_hour: int, target_minute: int) -> int:
    """Hedef saate kadar beklenmesi gereken saniye sayısını döndürür (bugün veya yarın)."""
    now = datetime.datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return int((target - now).total_seconds())

def _alarm_thread(target_time_str: str, root, player, snooze_minutes: int = 5):
    """Alarm thread'i, hedef saati bekler ve çaldırır."""
    hour, minute = _parse_time(target_time_str)
    if hour is None:
        return
    
    wait_seconds = _calculate_wait_seconds(hour, minute)
    
    if player:
        player.write_log(f"SYS: ⏰ Alarm kuruldu. {wait_seconds // 60} dakika sonra çalacak.")
    
    time.sleep(wait_seconds)
    
    # Alarmı tetikle (ana thread'de GUI işlemleri)
    if root:
        root.after(0, lambda: _play_alarm(root, player, snooze_minutes, target_time_str))

def _play_alarm(root, player, snooze_minutes: int, original_time: str):
    """Alarm penceresini gösterir, ses çalar ve erteleme seçeneği sunar."""
    try:
        # Önceki alarm penceresi varsa kapat
        for widget in root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "Alarm":
                widget.destroy()
        
        hud = tk.Toplevel(root)
        hud.title("Alarm")
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.95)
        hud.geometry("400x180+10+10")
        hud.configure(bg="#e65c00")
        
        tk.Label(hud, text="🌅 GÜNAYDIN PATRON", font=("Courier", 16, "bold"), fg="white", bg="#e65c00").pack(pady=10)
        tk.Label(hud, text="Sabah alarmınız çalıyor.\nYeni bir güne hazırız.", font=("Courier", 11), fg="white", bg="#e65c00").pack()
        
        # Buton çerçevesi
        btn_frame = tk.Frame(hud, bg="#e65c00")
        btn_frame.pack(pady=10)
        
        # Snooze butonu
        def snooze():
            if player:
                player.write_log(f"SYS: ⏰ Alarm {snooze_minutes} dakika ertelendi.")
            hud.destroy()
            # Yeni alarm thread'i başlat
            new_time = (datetime.datetime.now() + datetime.timedelta(minutes=snooze_minutes)).strftime("%H:%M")
            threading.Thread(target=_alarm_thread, args=(new_time, root, player, snooze_minutes), daemon=True).start()
            if root:
                root.after(0, lambda: _show_snooze_confirmation(root, snooze_minutes))
        
        def dismiss():
            if player:
                player.write_log("SYS: ✅ Alarm kapatıldı.")
            hud.destroy()
        
        tk.Button(btn_frame, text=f"Ertele ({snooze_minutes} dk)", command=snooze, bg="#ff9933", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Kapat", command=dismiss, bg="#cc4400", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10).pack(side="left", padx=10)
        
        # Ses döngüsü (10 kez veya pencere kapanana kadar)
        def beep_loop(count=10):
            if count > 0 and hud.winfo_exists():
                try:
                    winsound.Beep(900, 400)
                except:
                    pass
                hud.after(600, lambda: beep_loop(count - 1))
            elif hud.winfo_exists():
                # Ses bitti ama pencere açık kalabilir, kullanıcı kapatsın
                pass
        
        beep_loop(10)
        
        # 60 saniye sonra otomatik kapat (kullanıcı müdahale etmezse)
        root.after(60000, lambda: hud.destroy() if hud.winfo_exists() else None)
        
    except Exception as e:
        print(f"Alarm hatası: {e}")

def _show_snooze_confirmation(root, minutes: int):
    """Erteleme onayı için küçük bir bildirim gösterir."""
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.9)
        hud.geometry("250x60+10+70")
        hud.configure(bg="#333")
        tk.Label(hud, text=f"⏰ Alarm {minutes} dakika ertelendi.", font=("Courier", 10), fg="#ffcc00", bg="#333").pack(pady=15)
        root.after(2000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except:
        pass

def morning_alarm(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Sabah alarmı kurar.
    parameters: {
        "time": "07:30",          # zorunlu, HH:MM formatında
        "snooze": 5               # erteleme dakikası (varsayılan 5)
    }
    """
    params = parameters or {}
    target_time = params.get("time", "").strip()
    snooze_minutes = params.get("snooze", 5)
    
    if not target_time or ":" not in target_time:
        return "Alarm kurabilmem için lütfen saati (Örneğin 07:30) şeklinde belirtin."
    
    hour, minute = _parse_time(target_time)
    if hour is None:
        return "Geçersiz saat formatı. Lütfen HH:MM (00:00 ile 23:59 arası) girin."
    
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
        day_info = "yarın"
    else:
        day_info = "bugün"
    
    if player:
        player.write_log(f"SYS: 🌅 Sabah alarmı kuruluyor -> {target_time} ({day_info})")
    
    try:
        threading.Thread(target=_alarm_thread, args=(target_time, root, player, snooze_minutes), daemon=True).start()
        return f"Sabah alarmı {target_time} için {day_info} {target.strftime('%H:%M')}'de çalacak şekilde ayarlandı patron. Erteleme süresi {snooze_minutes} dakika. İyi uykular dilerim."
    except Exception as exc:
        if player:
            player.write_log(f"SYS: Alarm kurma hatası: {exc}")
        return "Sabah alarmını kurarken bir arıza meydana geldi."