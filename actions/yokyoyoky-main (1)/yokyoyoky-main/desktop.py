import ctypes
from pathlib import Path

def desktop_control(parameters=None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower()

    if player: 
        player.write_log(f"SYS: 🖥️ Masaüstü Yöneticisi -> {action}")

    try:
        if action == "wallpaper":
            path_str = params.get("path", "")
            if not path_str:
                return "Duvar kağıdı yapmak için geçerli bir resim dizini belirtmelisiniz."
            
            target = Path(path_str).resolve()
            if not target.exists():
                return f"Görsel bulunamadı: {target}"
            
            # Windows API kullanarak arka planı doğrudan değiştir (Yeniden başlatmaya gerek kalmaz)
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(target), 3)
            return "Duvar kağıdı başarıyla değiştirildi patron."

        elif action in ["clean", "organize"]:
            desktop_path = Path.home() / "Desktop"
            archive_path = desktop_path / "Archive_JARVIS"
            archive_path.mkdir(exist_ok=True)
            
            count = 0
            for item in desktop_path.iterdir():
                # Kısayolları (.lnk) ve sistem dosyalarını (desktop.ini) yerinde tutarak diğerlerini arşive atar
                if item.is_file() and item.suffix.lower() != ".lnk" and item.name.lower() != "desktop.ini":
                    try:
                        item.rename(archive_path / item.name)
                        count += 1
                    except Exception as file_err:
                        # Eğer dosya kilitliyse veya kullanımdaysa loga yazıp diğer dosyaya geçer
                        if player: player.write_log(f"SYS: Dosya taşınamadı ({item.name}): {file_err}")
                        
            return f"Masaüstü organize edildi. Dağınık olan {count} dosya 'Archive_JARVIS' klasöründe toplandı."

        else:
            return f"Masaüstü yöneticisinde '{action}' komutu bulunamadı."
            
    except Exception as e:
        if player: player.write_log(f"SYS: Masaüstü işlem hatası: {e}")
        return "Masaüstü yönetim işlemi tamamlanamadı."