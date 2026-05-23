import os
import shutil
from pathlib import Path

SAFE_DIRS = {
    "desktop": "Desktop", 
    "documents": "Documents", 
    "downloads": "Downloads", 
    "pictures": "Pictures"
}

def _resolve_path(raw_path: str) -> Path:
    if not raw_path:
        return Path.cwd()
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

    if player: 
        player.write_log(f"SYS: 📂 Dosya Yöneticisi -> {action}")

    try:
        if action == "list":
            target = _resolve_path(path_str)
            if not target.exists() or not target.is_dir():
                return f"Klasör bulunamadı: {target.name}"
            items = os.listdir(target)
            return f"Klasördeki öğeler: {', '.join(items[:10])}" + ("..." if len(items)>10 else "")

        elif action == "read":
            target = _resolve_path(path_str)
            if not target.exists() or not target.is_file():
                return f"Dosya bulunamadı veya bu bir klasör: {target.name}"
            
            # Bellek koruması: Devasa dosyaların sistemi çökertmesini önler
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read(1000)
            return f"Dosya içeriği: {text[:500]}..." if len(text) >= 500 else f"Dosya içeriği: {text}"

        elif action == "delete":
            target = _resolve_path(path_str)
            target_str = str(target).lower()
            
            # Genişletilmiş kritik sistem koruması! Asla izin verilmez.
            protected_paths = ["windows", "system32", "program files", "appdata"]
            
            # Kök dizinin (Örn: C:\) silinmesini engeller
            is_root = target == Path(target.anchor) 

            if any(p in target_str for p in protected_paths) or is_root:
                if player: player.write_log("SYS: GÜVENLİK İHLALİ ENGELLENDİ!")
                return "Güvenlik İhlali: Sistem veya kök dizin dosyalarını silme yetkim kısıtlanmıştır patron."
            
            if target.is_file():
                target.unlink()
                return f"'{target.name}' dosyası güvenle silindi."
            elif target.is_dir():
                shutil.rmtree(target)
                return f"'{target.name}' klasörü ve içindekiler güvenle silindi."
            
            return "Silinecek hedef bulunamadı."
            
        else:
            return f"Dosya yöneticisi '{action}' komutunu henüz desteklemiyor."

    except PermissionError:
        if player: player.write_log("SYS: Dosya erişim izni reddedildi.")
        return "Erişim reddedildi: Bu dosya veya klasör üzerinde işlem yapmak için yeterli iznim yok veya dosya başka bir program tarafından kullanılıyor."
    except Exception as e:
        if player: player.write_log(f"SYS: Dosya işlem hatası: {e}")
        return f"Dosya işleminde hata: Erişilemiyor olabilir. Detay: {str(e)}"