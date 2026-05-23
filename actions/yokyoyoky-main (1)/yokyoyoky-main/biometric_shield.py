# actions/biometric_shield.py
# J.A.R.V.I.S. Biyometrik Kalkan - Mini Mimari Versiyonu
# AI asla bloklanmaz, kamera ayrı açılır

import uuid
from services import get_task_queue, get_camera_service, TaskPriority
from actions.hud_helper import show_hud_preset
from typing import Optional


def biometric_shield(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Biyometrik taraması başlat
    - AI'yı bloklamaz
    - Sonuç arka planda gelir
    - HUD ile bilgilendir
    
    Args:
        parameters: {"action": "activate|deactivate|status", "task_id": "..."}
        player: UI logger
        root: Parent widget
    
    Returns:
        Durum mesajı (anında döner, beklemez)
    """
    if parameters is None:
        parameters = {}
    
    action = parameters.get("action", "activate")
    
    # Kamera servisi al
    camera_svc = get_camera_service()
    
    if action == "activate":
        # Görev ID'si oluştur
        task_id = f"biometric_{uuid.uuid4().hex[:8]}"
        
        if player:
            player.write_log(f"🛡️ Biyometrik kalkan başlatılıyor (Task: {task_id})")
        
        # HUD göster
        show_hud_preset(
            "🧬 BİYOMETRİK KALKAN AKTİF",
            "Kameraya doğruca bakın. Tarama başladı.",
            preset="processing",
            duration=10000,
            parent=root
        )
        
        # Görev kuyruğuna gönder (AI ASLA BEKLEMEZ)
        task_queue = get_task_queue()
        task_queue.submit(
            task_id=task_id,
            name="biometric_scan",
            handler=camera_svc.scan_face,
            args=(task_id, 8.0),
            priority=TaskPriority.HIGH
        )
        
        return f"Biyometrik tarama başlatıldı (ID: {task_id}). Sonuç arka planda işleniyor."
    
    elif action == "status":
        # Son görevin durumunu sorgula
        task_id = parameters.get("task_id")
        if not task_id:
            return "Görev ID'si gerekli"
        
        result = get_camera_service().get_result(task_id)
        if result:
            status = "✅ Başarılı" if result.get("success") else "❌ Başarısız"
            return f"{status}: {result.get('message', '')}"
        else:
            return "Sonuç bulunamadı (hala işleniyor olabilir)"
    
    elif action == "deactivate":
        if camera_svc.camera:
            try:
                camera_svc.camera.release()
            except:
                pass
            camera_svc.camera = None
        
        if player:
            player.write_log("🛡️ Biyometrik kalkan kapatıldı")
        
        return "Biyometrik kalkan kapatıldı."
    
    else:
        return f"Bilinmeyen aksiyon: {action}"