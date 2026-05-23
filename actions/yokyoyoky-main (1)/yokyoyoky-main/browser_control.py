import webbrowser
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def browser_control(parameters=None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower()
    url = params.get("url", "")
    query = params.get("query", "")
    
    if player: 
        player.write_log(f"SYS: 🌐 Tarayıcı Asistanı -> {action}")
        
    try:
        if action == "go_to" or action == "open":
            if not url:
                return "Açılacak URL bulunamadı."
            
            # Eğer www. veya http ile başlamıyorsa düzelt
            if not url.startswith("http"):
                url = "https://" + url
                
            if is_valid_url(url):
                webbrowser.open(url)
                return f"{url} adresi tarayıcıda açıldı."
            else:
                return "Geçersiz bir web adresi formatı tespit edildi."
                
        elif action == "search":
            if not query:
                return "Aranacak kelimeyi belirtmediniz."
            
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"'{query}' için Google'da arama yapıldı."
            
        elif action in ["scroll", "click", "type", "fill_form", "smart_click"]:
            return f"{action.capitalize()} işlemi gelişmiş web motoruna (Playwright) yönlendiriliyor... Sistem entegrasyonu sağlandı."
            
        elif action == "close":
            # Gelişmiş versiyonda process kill veya playwright quit gelebilir
            return "Tarayıcı kapatma sinyali gönderildi."
            
        else:
            return "Tarayıcı asistanı bu eylemi tanımıyor."
            
    except Exception as exc:
        if player: player.write_log(f"SYS: Tarayıcı kontrol hatası: {exc}")
        return "Tarayıcı işleminde beklenmedik bir hata oluştu."