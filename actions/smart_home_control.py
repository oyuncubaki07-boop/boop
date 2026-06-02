from integrations.home_assistant_adapter import call_ha_service, get_ha_state

def run_action(parameters: dict) -> str:
    """
    Home Assistant akıllı ev otomasyonu üzerinden cihazları ve senaryoları yönetir.
    
    Parametreler:
        parameters (dict):
            - 'domain' (str, zorunlu): Servis kategorisi (örn. 'light', 'switch', 'climate').
            - 'service' (str, zorunlu): Yapılacak işlem (örn. 'turn_on', 'turn_off', 'toggle').
            - 'entity_id' (str, isteğe bağlı): Hedef akıllı cihaz kimliği (örn. 'light.salon_lamba').
            - 'service_data' (dict, isteğe bağlı): Ek parametreler (örn. {"brightness": 255}).
    """
    try:
        domain = parameters.get("domain")
        service = parameters.get("service")
        entity_id = parameters.get("entity_id")
        service_data = parameters.get("service_data") or {}
        
        if not domain or not service:
            return "Efendim, akıllı ev sistemini yönetmek için en azından bir 'domain' ve 'service' belirtmelisiniz. Örnek: {'domain': 'light', 'service': 'turn_on', 'entity_id': 'light.calisma_odasi'}"
            
        if entity_id:
            service_data["entity_id"] = entity_id
            
        result = call_ha_service(domain, service, service_data)
        
        if result.get("status") == "error":
            return f"Efendim, Home Assistant servisi çalıştırılırken bir hata rapor edildi: {result.get('message')}"
            
        msg = f"Efendim, '{domain}.{service}' komutunuz başarıyla akıllı ev sistemine iletildi.\n"
        if entity_id:
            msg += f"Hedef Cihaz: {entity_id}\n"
            
        if result.get("status") == "simulated":
            msg += "\n*(Not: Home Assistant bağlantısı simülasyon modundadır)*"
            
        return msg
        
    except Exception as e:
        return f"Efendim, akıllı ev denetim motorunda beklenmeyen bir hata oluştu: {str(e)}"
