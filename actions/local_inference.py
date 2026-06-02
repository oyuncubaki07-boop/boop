from integrations.llama_cpp_adapter import query_local_llm

def run_action(parameters: dict) -> str:
    """
    Yerel olarak llama.cpp altyapısında barındırılan yapay zeka modeline hızlı soru gönderir.
    
    Parametreler:
        parameters (dict): 'prompt' (str, zorunlu) anahtarını bekler.
                           Örnek: {"prompt": "Python'da hızlı sıralama (quicksort) nasıl yazılır?"}
    """
    try:
        prompt = parameters.get("prompt")
        
        if not prompt:
            return "Efendim, yerel nöral ağa soru sormak için bir 'prompt' belirtmelisiniz. Örnek: {'prompt': 'Yapay zeka nedir?'}"
            
        result = query_local_llm(prompt)
        
        if "error" in result:
            return f"Efendim, yerel çıkarım motorunda bir sorun oluştu: {result['error']}"
            
        response = result.get("response", "Efendim, nöral ağdan boş bir yanıt döndü.")
        tokens = result.get("tokens_used", 0)
        
        output_msg = f"Efendim, yerel modelden gelen yanıt:\n> {response}\n"
        if tokens > 0:
            output_msg += f"\n*(Kullanılan Toplam Token: {tokens})*"
            
        if result.get("offline"):
            output_msg += "\n*(Not: llama_cpp kitaplığı/modeli bulunmadığı için simüle edilmiştir)*"
            
        return output_msg
        
    except Exception as e:
        return f"Efendim, yerel çıkarım işleminde bir hata oluştu: {str(e)}"
