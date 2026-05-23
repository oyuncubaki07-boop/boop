"""
guardian_shield.py - J.A.R.V.I.S. Gardiyan Kalkanı
İndirilenler klasörünü izler, son eklenen dosyayı analiz eder, riskli dosyaları tespit eder.
"""

import os
import glob
import time
import platform
import tkinter as tk
import winsound
from typing import Optional, Dict, List, Tuple

# Riskli dosya uzantıları ve risk skorları
RISK_EXTENSIONS = {
    '.exe': 90, '.msi': 85, '.bat': 80, '.cmd': 80, '.ps1': 85,
    '.vbs': 75, '.js': 70, '.jar': 65, '.scr': 90, '.com': 95,
    '.reg': 70, '.dll': 60, '.ocx': 60, '.app': 50, '.sh': 70,
    '.py': 30,  # Python script riskli olabilir ama genelde daha az
    '.rb': 30, '.pl': 30
}

# Tamamen güvenli kabul edilen uzantılar
SAFE_EXTENSIONS = {
    '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp3', '.mp4',
    '.avi', '.mkv', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
    '.pptx', '.zip', '.rar', '.7z', '.tar', '.gz', '.iso', '.img'
}

def get_downloads_folder() -> str:
    """Platforma göre İndirilenler klasörünü döndürür."""
    system = platform.system().lower()
    home = os.path.expanduser("~")
    if system == "windows":
        return os.path.join(home, "Downloads")
    elif system == "darwin":  # macOS
        return os.path.join(home, "Downloads")
    else:  # Linux ve diğerleri
        return os.path.join(home, "Downloads")  # Çoğu Linux dağıtımında böyledir

def get_risk_score(filename: str) -> Tuple[int, str]:
    """
    Dosya adına göre risk skoru (0-100) ve risk seviyesi metni döndürür.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext in RISK_EXTENSIONS:
        score = RISK_EXTENSIONS[ext]
        if score >= 80:
            level = "YÜKSEK RİSK"
        elif score >= 60:
            level = "ORTA RİSK"
        else:
            level = "DÜŞÜK RİSK"
        return score, level
    elif ext in SAFE_EXTENSIONS:
        return 0, "GÜVENLİ"
    else:
        # Bilinmeyen uzantı: orta risk
        return 50, "BİLİNMEYEN"

def format_file_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevirir."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def show_guardian_hud(root, file_name: str, risk_score: int, risk_level: str, file_size: int, file_time: float):
    """Gardiyan uyarı HUD'u."""
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.95)
        hud.geometry("500x160+10+10")
        
        if risk_score >= 80:
            bg_color = "#330000"
            fg_color = "#ff3333"
            title = "⚠️ GARDİYAN KRİTİK UYARI"
        elif risk_score >= 50:
            bg_color = "#332200"
            fg_color = "#ffaa33"
            title = "🛡️ GARDİYAN UYARISI"
        else:
            bg_color = "#003300"
            fg_color = "#66ff66"
            title = "✅ GARDİYAN RAPORU"
        
        hud.configure(bg=bg_color)
        tk.Label(hud, text=title, font=("Courier", 12, "bold"), fg=fg_color, bg=bg_color).pack(pady=5)
        tk.Label(hud, text=f"Dosya: {file_name[:50]}", font=("Courier", 10), fg="white", bg=bg_color, wraplength=480).pack()
        tk.Label(hud, text=f"Boyut: {format_file_size(file_size)}  |  Tarih: {time.ctime(file_time)}", font=("Courier", 9), fg="#cccccc", bg=bg_color).pack()
        
        risk_text = f"Risk Skoru: {risk_score} - {risk_level}"
        risk_color = "#ff6666" if risk_score >= 80 else ("#ffaa66" if risk_score >= 50 else "#66ff66")
        tk.Label(hud, text=risk_text, font=("Courier", 10, "bold"), fg=risk_color, bg=bg_color).pack(pady=5)
        
        if risk_score >= 80:
            tk.Label(hud, text="🔴 Bu dosya POTANSİYEL ZARARLI olabilir! Dikkatli olun.", font=("Courier", 9, "bold"), fg="red", bg=bg_color).pack()
        elif risk_score >= 50:
            tk.Label(hud, text="🟠 Bu dosya bilinmeyen veya riskli olabilir. Kaynağına güvenmiyorsanız açmayın.", font=("Courier", 9), fg="#ffaa66", bg=bg_color).pack()
        else:
            tk.Label(hud, text="✅ Dosya güvenli görünüyor. Yine de dikkatli olun.", font=("Courier", 9), fg="#66ff66", bg=bg_color).pack()
        
        # Sesli uyarı
        try:
            if risk_score >= 80:
                winsound.Beep(1000, 500)
                winsound.Beep(800, 300)
            elif risk_score >= 50:
                winsound.Beep(800, 300)
            else:
                winsound.Beep(500, 200)
        except:
            pass
        
        root.after(8000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except Exception as e:
        print(f"HUD hatası: {e}")

def guardian_shield(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Gardiyan kalkanı: İndirilenler klasöründeki son dosyayı analiz eder.
    parameters: {
        "silent": False,           # HUD gösterme
        "auto_delete_high_risk": False  # Yüksek riskli dosyayı sil (dikkat!)
    }
    """
    params = parameters or {}
    silent = params.get("silent", False)
    auto_delete = params.get("auto_delete_high_risk", False)
    
    if player:
        player.write_log("SYS: 💽 Gardiyan kalkanı devrede. İndirilenler taranıyor...")
    
    downloads_folder = get_downloads_folder()
    if not os.path.exists(downloads_folder):
        return "İndirilenler klasörü bulunamadı patron."
    
    # Tüm dosyaları al (klasörleri filtrele)
    all_files = []
    for item in glob.glob(os.path.join(downloads_folder, '*')):
        if os.path.isfile(item):
            all_files.append(item)
    
    if not all_files:
        return "İndirilenler klasörünüz tamamen temiz patron. Hiç dosya yok."
    
    # En son eklenen dosyayı bul (oluşturulma veya değiştirilme zamanına göre)
    latest_file = max(all_files, key=lambda f: max(os.path.getctime(f), os.path.getmtime(f)))
    file_name = os.path.basename(latest_file)
    file_size = os.path.getsize(latest_file)
    file_time = max(os.path.getctime(latest_file), os.path.getmtime(latest_file))
    
    risk_score, risk_level = get_risk_score(file_name)
    
    if not silent and root:
        show_guardian_hud(root, file_name, risk_score, risk_level, file_size, file_time)
    
    # Otomatik silme işlemi (YÜKSEK RİSK için)
    if auto_delete and risk_score >= 80:
        try:
            os.remove(latest_file)
            if player:
                player.write_log(f"SYS: ⚠️ Yüksek riskli dosya otomatik silindi: {file_name}")
            return f"🚨 Gardiyan kritik uyarı! '{file_name}' dosyası yüksek riskli olduğu için otomatik olarak silindi. Sisteminiz güvende."
        except Exception as e:
            if player:
                player.write_log(f"SYS: Otomatik silme başarısız: {e}")
    
    # Normal raporlama
    if risk_score >= 80:
        return f"🚨 GARDİYAN KRİTİK UYARISI! Son dosya: {file_name} (Risk: {risk_score} - {risk_level}). Bu dosya çalıştırılabilir ve POTANSİYEL ZARARLI olabilir. Lütfen kaynağına güvenmiyorsanız açmayın veya silin."
    elif risk_score >= 50:
        return f"🛡️ Gardiyan uyarısı: Son dosya '{file_name}' (Risk: {risk_score} - {risk_level}). Bilinmeyen veya riskli bir dosya olabilir. Dikkatli olun."
    else:
        return f"✅ Gardiyan raporu: Son dosya '{file_name}' güvenli görünüyor. (Risk: {risk_score} - {risk_level})"