import os
import subprocess
from pathlib import Path

def code_helper(parameters=None, player=None, speak=None) -> str:
    params = parameters or {}
    action = params.get("action", "auto").lower()
    description = params.get("description", "")
    language = params.get("language", "python").lower()
    code_content = params.get("code", "")
    file_path_str = params.get("file_path", "")
    output_path_str = params.get("output_path", "")
    
    if player: 
        player.write_log(f"SYS: 💻 Kod Asistanı aktif. İşlem: {action}")

    try:
        if action == "run":
            if not file_path_str:
                return "Çalıştırılacak dosya yolu belirtilmedi."
            target_file = Path(file_path_str).resolve()
            
            if not target_file.exists():
                return f"Dosya bulunamadı: {target_file}"
                
            if language == "python":
                # Timeout ekleyerek scriptin sonsuz döngüde asistanı kilitlemesi engellenir
                result = subprocess.run(["python", str(target_file)], capture_output=True, text=True, timeout=30)
                out = result.stdout.strip()
                err = result.stderr.strip()
                
                if result.returncode == 0:
                    return f"Kod başarıyla çalıştı. Çıktı: {out[:200]}"
                else:
                    return f"Kod çalışırken hata verdi: {err[:200]}"
            else:
                return f"Şu an için {language} çalıştırma desteği sınırlı."

        elif action == "write" or action == "edit":
            if not output_path_str and not file_path_str:
                return "Kaydedilecek dosya yolu belirtilmedi."
            
            target_path = Path(output_path_str or file_path_str).resolve()
            
            # Kod yazımı (AI tarafından oluşturulan code parametresi kullanılarak)
            if code_content:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(code_content, encoding="utf-8")
                return f"Kod başarıyla '{target_path.name}' dosyasına yazıldı."
            else:
                return "Yazılacak herhangi bir kod sağlanmadı."

        else:
            return f"'{action}' işlemi için talimatlar anlaşıldı. Lütfen daha belirgin bir komut verin."

    except subprocess.TimeoutExpired:
        if player: player.write_log("SYS: Kod zaman aşımına uğradı!")
        return "Çalıştırılan kod zaman aşımına uğradı (Sonsuz döngü hatası olabilir)."
    except Exception as e:
        if player: player.write_log(f"SYS: Kod asistanı hatası: {e}")
        return f"Kod asistanı işlemi tamamlayamadı: {e}"