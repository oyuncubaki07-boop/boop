import os
from integrations.face_recognition_adapter import identify_person

def run_action(parameters: dict) -> str:
    """
    Kamera görüntüsündeki kişiyi bilinen yüz veritabanıyla karşılaştırarak biyometrik tarama yapar.
    
    Parametreler:
        parameters (dict): 'image_path' (str) anahtarını bekler.
                           Belirtilmezse varsayılan bir kamera karesini tarar.
    """
    try:
        image_path = parameters.get("image_path")
        
        # Kamera kaydı simülasyonu
        if not image_path:
            image_path = "temp_biometric_face.jpg"
            with open(image_path, "wb") as f:
                f.write(b"")
                
        result = identify_person(image_path)
        
        # Geçici resim temizliği
        if os.path.exists("temp_biometric_face.jpg"):
            try:
                os.remove("temp_biometric_face.jpg")
            except Exception:
                pass
                
        if "error" in result:
            return f"Efendim, biyometrik tarama sırasında bir sistem hatası tespit edildi: {result['error']}"
            
        status = result.get("status")
        
        if status == "no_face_found":
            return "Efendim, taranan görüntüde herhangi bir yüz tespit edilemedi. Lütfen kameraya düzgünce bakın."
            
        elif status == "unknown_face":
            return "Biyometrik tarama başarısız. Efendim, sizi tanıyamadım. Erişim reddedildi."
            
        elif status == "matched":
            user = result.get("user", "Baki")
            confidence = int(result.get("confidence", 0.95) * 100)
            
            # Custom Jarvis welcoming message
            msg = f"Tarama Başarılı. Hoş geldiniz {user}! (Biyometrik doğruluk: %{confidence})\n"
            msg += f"Efendim, bugün Amerika hedeflerimiz ve aktif projelerimiz için hangi kodları yazıyoruz? Hazır durumdayım."
            
            if result.get("offline"):
                msg += "\n\n*(Not: face_recognition kitaplığı çevrimdışı olduğu için tarama simüle edildi)*"
                
            return msg
            
        return "Efendim, tarama işlemi tanımlanamayan bir durumla sonuçlandı."
        
    except Exception as e:
        return f"Efendim, biyometrik tarayıcıda bir sorun oluştu: {str(e)}"
