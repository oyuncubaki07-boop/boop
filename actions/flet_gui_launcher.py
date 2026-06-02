from integrations.flet_adapter import start_flet_gui

def run_action(parameters: dict) -> str:
    """
    J.A.R.V.I.S. için Flet tabanlı gelişmiş masaüstü kontrol panelini (GUI) başlatır.
    
    Parametreler:
        parameters (dict): İsteğe bağlı arayüz renk teması veya yapılandırma ayarlarını alabilir.
    """
    try:
        result = start_flet_gui()
        
        status = result.get("status")
        if status == "started":
            return f"Efendim, Flet kontrol paneli arka planda başarıyla çalıştırıldı (Thread: {result.get('thread')})."
        elif status == "simulated":
            return f"Efendim, Flet kontrol paneli başlatma komutu simüle edildi:\n> {result.get('message')}"
            
        return "Efendim, kontrol paneli başlatma isteği tanımlanamayan bir durum döndürdü."
        
    except Exception as e:
        return f"Efendim, Flet gösterge paneli başlatılırken bir hata oluştu: {str(e)}"
