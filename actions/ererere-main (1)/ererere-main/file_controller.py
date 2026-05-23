import os
import shutil
from pathlib import Path

SAFE_DIRS = {"desktop": "Desktop", "documents": "Documents", "downloads": "Downloads", "pictures": "Pictures"}

def _resolve_path(raw_path: str) -> Path:
    rp = raw_path.lower()
    user_home = Path.home()
    if rp in SAFE_DIRS:
        return user_home / SAFE_DIRS[rp]
    return Path(raw_path).resolve()

def file_controller(parameters=None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower()
    path_str = params.get("path", "")

    if not action:
        return "Dosya işlemi belirtilmedi."

    if player: player.write_log(f"SYS: 📂 Dosya Yöneticisi -> {action}")

    try:
        if action == "list":
            target = _resolve_path(path_str) if path_str else Path.cwd()
            if not target.exists() or not target.is_dir():
                return f"Klasör bulunamadı: {target.name}"
            items = os.listdir(target)
            return f"Klasördeki öğeler: {', '.join(items[:10])}" + ("..." if len(items)>10 else "")

        elif action == "read":
            target = _resolve_path(path_str)
            if not target.exists() or not target.is_file():
                return f"Dosya bulunamadı: {target.name}"
            text = target.read_text(encoding="utf-8")
            return f"Dosya içeriği: {text[:500]}"

        elif action == "delete":
            target = _resolve_path(path_str)
            # Kritik sistem koruması! Asla izin verilmez.
            if "windows" in str(target).lower() or "system32" in str(target).lower():
                return "Güvenlik İhlali: Sistem dosyalarını silme yetkim kısıtlanmıştır patron."
            
            if target.is_file():
                target.unlink()
                return "Dosya güvenle silindi."
            elif target.is_dir():
                shutil.rmtree(target)
                return "Klasör ve içindekiler güvenle silindi."
            return "Silinecek hedef bulunamadı."
            
        else:
            return f"Dosya yöneticisi '{action}' komutunu henüz desteklemiyor."

    except Exception as e:
        if player: player.write_log(f"SYS: Dosya işlem hatası: {e}")
        return f"Dosya işleminde hata: Erişilemiyor olabilir."