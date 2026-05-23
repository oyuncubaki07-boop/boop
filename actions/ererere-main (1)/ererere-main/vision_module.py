# actions/vision_module.py
# J.A.R.V.I.S. Vision Module - Kamera ile görüntü analizi
# Gemini 2.0 Flash ile entegre, platform bağımsız

import cv2
import os
import json
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

def get_base_dir():
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("gemini_api_key", "").strip()
            if not key:
                raise ValueError("Gemini API key bulunamadı.")
            return key
    except Exception as e:
        raise RuntimeError(f"API anahtarı okunamadı: {e}")

def vision_scan(parameters: Optional[Dict] = None, speak=None, player=None) -> str:
    """
    Kameradan görüntü alır, Gemini ile analiz yapar.
    
    Parametreler:
        prompt (str): Analiz için özel soru (varsayılan: "Bu görüntüde ne görüyorsun? ...")
        camera_index (int): Kamera indeksi (varsayılan: 0)
        preview_duration (int): Önizleme süresi (saniye, varsayılan: 3)
        save_image (bool): Görüntüyü kaydet (varsayılan: False)
    """
    params = parameters or {}
    prompt = params.get("prompt", "Bu görüntüde ne görüyorsun? Bir yapay zeka asistanı gibi kısa ve net analiz et.")
    camera_index = int(params.get("camera_index", 0))
    preview_duration = float(params.get("preview_duration", 3.0))
    save_image = params.get("save_image", False)
    
    if player:
        player.write_log("[VİZYON] Kamera başlatılıyor...")
    
    # Platforma göre backend seçimi (Windows: CAP_DSHOW, Linux/Mac: varsayılan)
    if os.name == 'nt':  # Windows
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        error_msg = f"Kameraya erişilemedi (index {camera_index}). Lütfen kameranın bağlı olduğundan emin olun."
        if player:
            player.write_log(f"[VİZYON] HATA: {error_msg}")
        return error_msg
    
    if player:
        player.write_log("[VİZYON] Canlı akış başladı. Hedef taranıyor...")
    
    start_time = time.time()
    captured_frame = None
    
    # Önizleme penceresi oluştur
    window_name = "J.A.R.V.I.S. Vision HUD"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if player:
                    player.write_log("[VİZYON] Kameradan görüntü alınamadı.")
                break
            
            # Görüntüyü göster
            cv2.imshow(window_name, frame)
            
            # Belirlenen süre geçtiyse veya 'q'/'esc' tuşuna basıldıysa çek
            elapsed = time.time() - start_time
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' veya ESC
                captured_frame = frame
                break
            if elapsed >= preview_duration:
                captured_frame = frame
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    if captured_frame is None:
        return "Görüntü yakalanamadı, efendim. Lütfen tekrar deneyin."
    
    # Geçici dosyaya kaydet
    temp_file = None
    try:
        # Geçici dosya oluştur (otomatik temizlenir)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            temp_path = tmp.name
        cv2.imwrite(temp_path, captured_frame)
        
        if save_image and player:
            # Kalıcı kaydet
            save_dir = BASE_DIR / "captures"
            save_dir.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            perm_path = save_dir / f"vision_{timestamp}.jpg"
            cv2.imwrite(str(perm_path), captured_frame)
            player.write_log(f"[VİZYON] Görüntü kaydedildi: {perm_path}")
        
        # Gemini analizi
        if player:
            player.write_log("[VİZYON] Görüntü analiz ediliyor...")
        
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=_get_api_key())
        with open(temp_path, "rb") as f:
            image_data = f.read()
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
            ]
        )
        
        result = response.text.strip()
        if not result:
            result = "Analiz sonucu boş, lütfen tekrar deneyin."
        
        # Sonucu sesli olarak da söyle (isteğe bağlı)
        if speak:
            speak(result)
        
        return result
    
    except Exception as e:
        error_msg = f"Analiz sırasında hata oluştu: {str(e)}"
        if player:
            player.write_log(f"[VİZYON] HATA: {error_msg}")
        return error_msg
    finally:
        # Geçici dosyayı temizle
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass