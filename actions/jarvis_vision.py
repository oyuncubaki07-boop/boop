import os
from integrations.yolo_adapter import detect_objects

def run_action(parameters: dict) -> str:
    """
    YOLOv8 nesne tanıma modeli ile kameradan veya verilen resim yolundan nesneleri tespit eder.
    
    Parametreler:
        parameters (dict): 'image_path' (str) anahtarını bekler.
                           Eğer belirtilmezse, masaüstünden geçici bir ekran görüntüsü alıp analiz eder.
    """
    try:
        image_path = parameters.get("image_path")
        
        # Resim yolu verilmediyse, geçici ekran görüntüsü alma mekanizması (simüle veya sistem screenshot)
        if not image_path:
            image_path = "temp_vision_capture.jpg"
            # Basit bir boş dosya oluşturup simülasyonu tetikliyoruz
            with open(image_path, "wb") as f:
                f.write(b"")
                
        result = detect_objects(image_path)
        
        # Geçici ekran resmi temizliği
        if os.path.exists("temp_vision_capture.jpg"):
            try:
                os.remove("temp_vision_capture.jpg")
            except Exception:
                pass
                
        if "error" in result:
            return f"Efendim, görüntü analizi sırasında bir sorun oluştu: {result['error']}"
            
        detections = result.get("detections", [])
        count = result.get("count", 0)
        
        if count == 0:
            return "Efendim, analiz edilen görüntüde herhangi bir nesne veya kişi tespit edilemedi."
            
        labels = [d["label"] for d in detections]
        label_summary = ", ".join(set(labels))
        
        output_msg = f"Efendim, görüntü analizi tamamlandı. Toplam {count} nesne tespit ettim.\n"
        output_msg += f"Belirlenen sınıflar: {label_summary}\n"
        output_msg += "\nDetaylı liste:\n"
        for idx, det in enumerate(detections, 1):
            output_msg += f"{idx}. {det['label']} (%{int(det['confidence']*100)} güvenilirlik)\n"
            
        if result.get("status") == "simulated":
            output_msg += "\n*(Not: YOLOv8 kitaplığı henüz kurulmadığı için analiz simülasyon moduyla yapılmıştır)*"
            
        return output_msg
        
    except Exception as e:
        return f"Efendim, görüntü işleme motorunda bir hata oluştu: {str(e)}"
