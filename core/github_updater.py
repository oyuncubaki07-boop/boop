import os
import shutil
import subprocess
import datetime
import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
BACKUP_DIR = BASE_DIR / "backups"
# BURAYA KENDI GITHUB REPO URL'NI YAZ:
REPO_URL = "https://github.com/kullanici/mark-xxxix-or.git" 

def update_system_from_github():
    print("[GitHub Updater] Güncelleme kontrolü başlatılıyor...")
    
    # 1. Yedekleme
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"jarvis_backup_{timestamp}"
    
    try:
        shutil.copytree(BASE_DIR / "core", backup_path / "core", dirs_exist_ok=True)
        shutil.copytree(BASE_DIR / "actions", backup_path / "actions", dirs_exist_ok=True)
        shutil.copytree(BASE_DIR / "agent", backup_path / "agent", dirs_exist_ok=True)
        shutil.copy2(BASE_DIR / "main.py", backup_path / "main.py")
        print(f"[GitHub Updater] Mevcut stabil sürüm yedeklendi: {backup_path}")
    except Exception as e:
        print(f"[GitHub Updater] Yedekleme hatası: {e}. Güncelleme iptal edildi.")
        return

    # 2. Git Pull İşlemi
    try:
        result = subprocess.run(["git", "pull", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
        if "Already up to date." in result.stdout:
            print("[GitHub Updater] Sistem zaten en güncel sürümde.")
            return
            
        if result.returncode != 0:
            raise Exception(result.stderr)
            
        # Bağımlılıkları güncelle
        req_path = BASE_DIR / "requirements.txt"
        if req_path.exists():
            subprocess.run(["pip", "install", "-r", str(req_path)], check=True)
            
        print("[GitHub Updater] Güncelleme başarıyla tamamlandı ve arka planda sisteme entegre edildi.")
    except Exception as e:
        print(f"[GitHub Updater] Hata oluştu: {e}. Eski sürüme dönülüyor...")
        shutil.copytree(backup_path / "actions", BASE_DIR / "actions", dirs_exist_ok=True)
        shutil.copytree(backup_path / "core", BASE_DIR / "core", dirs_exist_ok=True)
        shutil.copytree(backup_path / "agent", BASE_DIR / "agent", dirs_exist_ok=True)