from integrations.autogpt_adapter import run_autogpt_task

def run_action(parameters: dict) -> str:
    """
    AutoGPT otonom ajanını tetikleyerek internet üzerinden derinlemesine araştırma yapılmasını sağlar.
    
    Parametreler:
        parameters (dict): 'task' (str, zorunlu) anahtarını bekler.
                           Örnek: {"task": "Konya Karatay hava durumuna göre günlük plan oluştur"}
    """
    try:
        task = parameters.get("task")
        
        if not task:
            return "Efendim, otonom araştırma başlatabilmem için bir 'task' (hedef tanımı) belirtmelisiniz. Örnek: {'task': 'Python asyncio hata çözümü bul'}"
            
        result = run_autogpt_task(task)
        
        if "error" in result:
            return f"Efendim, AutoGPT araştırması başlatılırken bir hata oluştu: {result['error']}"
            
        notes = result.get("research_notes", "Efendim, araştırma sonucu boş döndü.")
        
        output_msg = f"Efendim, AutoGPT otonom araştırmacı görevini tamamladı.\n\n"
        output_msg += f"{notes}\n"
        
        if result.get("offline"):
            output_msg += "\n*(Not: AutoGPT API'leri ve modeli simülasyon modunda çalıştırılmıştır)*"
            
        return output_msg
        
    except Exception as e:
        return f"Efendim, otonom araştırma motorunda bir hata oluştu: {str(e)}"
