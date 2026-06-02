from integrations.n8n_adapter import trigger_n8n_event

def run_action(parameters: dict) -> str:
    """
    n8n iş akışlarını tetikleyerek Gmail, GitHub, Shopify gibi servisler arasında entegrasyonu başlatır.
    
    Parametreler:
        parameters (dict):
            - 'event_name' (str, zorunlu): Tetiklenecek olayın adı (örn. 'sipariş_geldi', 'kod_yüklendi').
            - 'payload' (dict, isteğe bağlı): n8n'e gönderilecek ek veri paketi.
    """
    try:
        event_name = parameters.get("event_name")
        payload = parameters.get("payload") or {}
        
        if not event_name:
            return "Efendim, n8n otomasyonunu çalıştırmak için bir 'event_name' belirtmelisiniz. Örnek: {'event_name': 'test_akisi'}"
            
        result = trigger_n8n_event(event_name, payload)
        
        if result.get("status") == "error":
            return f"Efendim, n8n sinir sisteminde bir hata algılandı: {result.get('message')}"
            
        msg = f"Efendim, n8n iş akışı tetiklendi.\nOlay: {event_name}\n"
        if result.get("status") == "simulated":
            msg += "\n*(Not: n8n bağlantısı simülasyon modunda tetiklendi)*"
            
        return msg
        
    except Exception as e:
        return f"Efendim, n8n tetikleyicisinde beklenmeyen bir hata oluştu: {str(e)}"
