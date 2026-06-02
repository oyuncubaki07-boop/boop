import time
from integrations.chroma_adapter import add_to_memory, search_memory

def run_action(parameters: dict) -> str:
    """
    ChromaDB tabanlı yerel vektör veritabanını kullanarak kalıcı hafızaya bilgi yazar veya okur.
    
    Parametreler:
        parameters (dict):
            - 'operation' (str, zorunlu): 'store' (hafızaya yazma) veya 'recall' (hatırlama/sorgulama).
            - 'text' (str): Kaydedilecek bilgi metni ('store' işleminde zorunlu).
            - 'query' (str): Aranacak kelime veya konu başlığı ('recall' işleminde zorunlu).
            - 'doc_id' (str, isteğe bağlı): Kayıt için benzersiz kimlik (belirtilmezse zaman damgalı üretilir).
    """
    try:
        operation = parameters.get("operation")
        
        if not operation or operation not in ("store", "recall"):
            return "Efendim, hafıza işlemi gerçekleştirmek için geçerli bir 'operation' ('store' veya 'recall') belirtmelisiniz."
            
        if operation == "store":
            text = parameters.get("text")
            if not text:
                return "Efendim, hafızaya kaydetmek için bir 'text' (veri metni) girmelisiniz."
                
            doc_id = parameters.get("doc_id") or f"mem_{int(time.time())}"
            metadata = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "jarvis_interactive"
            }
            
            success = add_to_memory(doc_id, text, metadata)
            if success:
                return f"Efendim, verdiğiniz bilgiyi kalıcı hafızama kaydettim.\nKimlik: {doc_id}\nİçerik: \"{text}\""
            else:
                return "Efendim, bilgiyi hafızaya kaydederken bir hata ile karşılaşıldı."
                
        elif operation == "recall":
            query = parameters.get("query")
            if not query:
                return "Efendim, hafızamı sorgulamak için bir 'query' (arama konusu) girmelisiniz."
                
            results = search_memory(query, limit=3)
            
            if not results:
                return f"Efendim, hafızamda \"{query}\" konusuyla ilişkili herhangi bir kayıt bulamadım."
                
            msg = f"Efendim, hafızamı sorguladım ve en alakalı {len(results)} kaydı getirdim:\n\n"
            for idx, res in enumerate(results, 1):
                doc_text = res.get("document", "")
                meta = res.get("metadata", {})
                time_str = meta.get("timestamp", "Bilinmeyen Tarih")
                msg += f"[{idx}] (Tarih: {time_str})\n> {doc_text}\n\n"
                
            if any(r.get("simulated") for r in results):
                msg += "*(Not: ChromaDB yüklü olmadığı için düz dosya hafızası taranmıştır)*"
                
            return msg
            
    except Exception as e:
        return f"Efendim, hafıza modülünde bir hata oluştu: {str(e)}"
