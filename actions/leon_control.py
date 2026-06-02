from integrations.leon_adapter import query_leon

def run_action(parameters: dict) -> str:
    """
    Leon AI kişisel asistanı ile bağlantı kurar ve komutlarınızı ona iletir.
    
    Parametreler:
        parameters (dict): 'command' veya 'query' anahtarıyla Leon'a gönderilecek mesajı bekler.
                           Örnek: {"command": "saat kaç?"}
    """
    try:
        command = parameters.get("command") or parameters.get("query")
        
        if not command:
            return "Efendim, Leon'a göndermek için bir komut belirtmelisiniz. Örnek: {'command': 'selam de'}"
            
        result = query_leon(command)
        output = result.get("output", "Efendim, Leon'dan boş bir yanıt döndü.")
        
        if result.get("offline"):
            return f"Efendim, Leon sunucusu şu an kapalı. Simüle edilen yanıt:\n> {output}"
            
        return f"Efendim, Leon'un yanıtı:\n> {output}"
        
    except Exception as e:
        return f"Efendim, Leon entegrasyonunda bir hata oluştu: {str(e)}"
