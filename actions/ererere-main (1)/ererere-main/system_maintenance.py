# actions/system_maintenance.py
# J.A.R.V.I.S. Sistem Bakım Modülü (Disk, Temp, Geri Dönüşüm)

import os
import shutil
import tempfile
import ctypes
import platform
from pathlib import Path

def get_size(path: Path) -> int:
    """Bir dosya veya klasörün toplam boyutunu byte cinsinden hesaplar."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except:
                pass
    return total

def system_maintenance(parameters=None, player=None) -> str:
    """
    Geçici dosyaları temizler, geri dönüşüm kutusunu boşaltır (Windows),
    ve disk alanı raporu verir.
    """
    if player:
        player.write_log("SYS: 🧹 Sistem Bakım Protokolü başlatıldı...")

    try:
        total_cleaned = 0
        temp_dir = Path(tempfile.gettempdir())
        user_temp = Path.home() / "AppData" / "Local" / "Temp" if platform.system() == "Windows" else Path("/tmp")

        # 1. Geçici dosya temizliği (temp klasörü)
        for temp_path in [temp_dir, user_temp]:
            if temp_path.exists():
                before_size = get_size(temp_path)
                for item in temp_path.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                    except Exception:
                        continue
                after_size = get_size(temp_path)
                total_cleaned += (before_size - after_size)

        # 2. Geri Dönüşüm Kutusu (sadece Windows)
        if platform.system() == "Windows":
            try:
                # SHERB_NOCONFIRMATION=1, SHERB_NOPROGRESSUI=2, SHERB_NOSOUND=4 => toplam 7
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
                if player:
                    player.write_log("SYS: 🗑️ Geri dönüşüm kutusu boşaltıldı.")
            except Exception as e:
                if player:
                    player.write_log(f"SYS: Çöp kutusu temizlenemedi: {e}")

        # 3. Disk kullanım raporu
        disk_usage = shutil.disk_usage("/")
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)
        cleaned_mb = total_cleaned / (1024 * 1024)

        result = (
            f"✅ Sistem bakımı tamamlandı.\n"
            f"🧹 Temizlenen geçici veri: {cleaned_mb:.1f} MB\n"
            f"💾 Boş disk alanı: {free_gb:.1f} GB / {total_gb:.1f} GB\n"
            f"♻️ Geri dönüşüm kutusu boşaltıldı (Windows)."
        )
        return result

    except Exception as exc:
        if player:
            player.write_log(f"SYS: Sistem bakım hatası: {exc}")
        return "Sistem bakımı sırasında bir hata oluştu. Bazı dosyalara erişilemedi."