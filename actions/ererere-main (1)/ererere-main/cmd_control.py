import subprocess
import re

FORBIDDEN_COMMANDS = ["format", "del /s", "del /f", "rmdir /s", "diskpart", "shutdown -p"]

def _is_safe(command: str) -> tuple[bool, str]:
    cmd_lower = command.lower()
    for forbidden in FORBIDDEN_COMMANDS:
        if forbidden in cmd_lower:
            return False, f"Yasaklı komut tespit edildi: {forbidden}"
    return True, ""

def cmd_control(parameters=None, response=None, player=None, session_memory=None) -> str:
    params = parameters or {}
    task = params.get("task", "").strip()
    command = params.get("command", "").strip()

    if not task and not command:
        return "Ne yapmak istediğinizi açıklayın veya komutu verin lütfen."

    if not command:
        # Eğer AI komut üretmemişse doğrudan task'ı komut varsay (Geliştirilebilir)
        command = task

    safe, reason = _is_safe(command)
    if not safe:
        if player: player.write_log(f"SYS: [CMD ENGELLENDI] {reason}")
        return f"Güvenlik nedeniyle engellendi: {reason}"

    if player:
        player.write_log(f"SYS: [CMD] Çalıştırılıyor -> {command[:60]}")

    try:
        # Maksimum 15 saniye timeout (donmayı engeller)
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=15,
            encoding="cp857", # Türkçe Windows için CMD karakter formatı
            errors="ignore"
        )
        
        output = result.stdout.strip()
        err_output = result.stderr.strip()
        
        if result.returncode == 0:
            if not output:
                return "Komut başarıyla çalıştırıldı (Çıktı yok)."
            # Çıktı çok uzunsa kırp
            return f"İşlem tamamlandı. Çıktı:\n{output[:300]}..." if len(output) > 300 else f"İşlem tamamlandı:\n{output}"
        else:
            return f"Komut hata döndürdü (Kod {result.returncode}): {err_output[:200]}"
            
    except subprocess.TimeoutExpired:
        if player: player.write_log("SYS: [CMD] Zaman aşımı (15s)")
        return "Komut çok uzun sürdü ve zaman aşımına uğradı."
    except Exception as e:
        if player: player.write_log(f"SYS: [CMD HATA] {e}")
        return f"Komut çalıştırılamadı: {str(e)}"