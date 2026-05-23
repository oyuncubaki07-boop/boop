import subprocess

def scan_devices(parameters=None, speak=None, player=None):
    """Sisteme bağlı USB, Bluetooth ve Oyun Kolları gibi çevre birimlerini PowerShell ile tarar."""
    try:
        print("[DONANIM] Sistem portları Powershell üzerinden taranıyor...")
        
        # Windows'un en güvenilir tarama yöntemi (PowerShell)
        ps_command = (
            "Get-PnpDevice -PresentOnly | "
            "Where-Object { $_.Class -match 'USB' -or $_.Class -match 'Bluetooth' -or $_.FriendlyName -match 'PlayStation' -or $_.FriendlyName -match 'Xbox' } | "
            "Select-Object -ExpandProperty FriendlyName"
        )
        
        # Karakter hatalarını önlemek için byte olarak alıp güvenli çözümlüyoruz
        output_bytes = subprocess.check_output(["powershell", "-Command", ps_command], stderr=subprocess.DEVNULL)
        text_output = output_bytes.decode('utf-8', errors='ignore') 
        
        # Çıktıyı temizle ve listeye çevir
        devices = [line.strip() for line in text_output.split('\n') if line.strip()]
        unique_devices = list(set(devices)) # Tekrar edenleri sil
        
        if not unique_devices:
            return "Efendim, şu anda sisteme bağlı yeni veya dikkat çekici bir USB veya Bluetooth donanımı bulamadım."
        
        # Anlaşılır olması için sadece ilk 4 cihazı sayalım
        rapor = "Sisteme bağlı cihazları taradım. Şunları tespit ettim: " + ", ".join(unique_devices[:4]) + "."
        
        # Oyun kolu kontrolü
        if any("PlayStation" in d or "Xbox" in d or "Controller" in d or "Wireless" in d for d in unique_devices):
            rapor += " Ayrıca bir kontrolcü veya kablosuz cihaz bağlandığını görüyorum. Sistem donanımı başarıyla tanıdı."
            
        return rapor
        
    except Exception as e:
        return f"Donanım taraması sırasında Windows Powershell engeline takıldım efendim: {str(e)}"