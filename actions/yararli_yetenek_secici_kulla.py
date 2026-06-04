def run_action(parameters):
    """
    'Yararlı Yetenek Seçici' (Useful Skill Selector) fonksiyonu.
    Gelen 'parameters' sözlüğündeki bilgilere (kullanıcı niyeti, bağlam, mevcut araçlar vb.)
    dayanarak en uygun eylemi veya yeteneği seçer ve döndürür.

    Args:
        parameters (dict): Eylem seçimi için gerekli olabilecek çeşitli bilgileri içeren bir sözlük.
                           Örnek anahtarlar:
                           - 'user_intent' (str): Kullanıcının ana niyeti veya isteği.
                           - 'context' (dict): Eylemi belirlemeye yardımcı olacak ek bağlamsal bilgiler
                                               (örn. konum, tarih, belirli değerler).
                           - 'available_tools' (list): Sistemde mevcut olan araçların/yeteneklerin listesi.

    Returns:
        dict: Seçilen eylemi ve bu eylemin gerektirdiği argümanları içeren bir sözlük.
              Format: {'action_name': 'yeteneğin_adı', 'arguments': {'arg1': 'değer1', ...}}
              Hiçbir uygun eylem bulunamazsa bir varsayılan eylem döndürülür.
    """
    user_intent = parameters.get('user_intent', '').lower()
    context = parameters.get('context', {})
    available_tools = parameters.get('available_tools', [])

    # Varsayılan eylem, eğer hiçbir eşleşme bulunamazsa
    selected_action = {
        "action_name": "fallback_action",
        "arguments": {"message": "Anlamadım veya uygun bir yetenek bulamadım. Lütfen daha açık belirtin."}
    }

    # --- Niyet Tabanlı Yetenek Seçimi Mantığı ---
    # Kullanıcının niyetine göre öncelikli yetenekleri belirle
    if "hava durumu" in user_intent or "weather" in user_intent:
        selected_action = {
            "action_name": "get_current_weather",
            "arguments": {"location": context.get("location", "current_location")}
        }
    elif "hatırlatıcı kur" in user_intent or "reminder" in user_intent:
        # Niyetten ilgili bilgileri çıkarmaya çalış
        task_description = user_intent.replace("hatırlatıcı kur", "").strip()
        selected_action = {
            "action_name": "set_new_reminder",
            "arguments": {
                "task": task_description if task_description else "belirtilmemiş görev",
                "time": context.get("time"),
                "date": context.get("date")
            }
        }
    elif "hesapla" in user_intent or "calculate" in user_intent:
        # Hesaplama ifadesini niyette veya bağlamda ara
        expression = context.get("expression", user_intent.replace("hesapla", "").strip())
        if expression:
            selected_action = {
                "action_name": "perform_arithmetic_calculation",
                "arguments": {"expression": expression}
            }
    elif "araştır" in user_intent or "search" in user_intent:
        query = user_intent.replace("araştır", "").strip()
        if query:
            selected_action = {
                "action_name": "web_search",
                "arguments": {"query": query}
            }
    elif "liste" in user_intent and ("yapılacaklar" in user_intent or "todo" in user_intent):
        selected_action = {
            "action_name": "manage_todo_list",
            "arguments": {"command": "view_all"} # Veya "add_item", "remove_item" gibi daha spesifik olabilir
        }
    elif "merhaba" in user_intent or "selam" in user_intent or "hi" in user_intent:
        selected_action = {
            "action_name": "greet_user",
            "arguments": {"response_type": "friendly"}
        }
    # --- Mevcut Araçlara Göre Yetenek Optimizasyonu ---
    # Eğer daha spesifik bir araç mevcutsa, genel yeteneği bu araçla değiştirebiliriz.
    if selected_action["action_name"] == "web_search" and "google_search_api" in available_tools:
        # Genel web arama yerine Google API'yi kullanmayı tercih et
        selected_action["action_name"] = "use_google_search_api"
        # Argümanlar genellikle aynı kalır veya araca özel küçük ayarlamalar yapılabilir
    
    if selected_action["action_name"] == "get_current_weather" and "weather_api_service" in available_tools:
        # Genel hava durumu yerine belirli bir API'yi kullanmayı tercih et
        selected_action["action_name"] = "query_weather_api_service"

    # --- Daha Karmaşık Mantıklar (buraya eklenebilir) ---
    # - Kullanıcının geçmiş etkileşimlerine veya tercihlerine göre kişiselleştirme.
    # - Birden fazla yeteneği bir araya getiren iş akışları (örneğin, "Hava durumunu öğren ve bana hatırlat").
    # - Kaynak kısıtlamalarına göre yetenek seçimi (örneğin, bir araç devre dışıysa yedek kullanma).
    # - Makine öğrenimi tabanlı niyet sınıflandırma ve yetenek eşleştirme.

    return selected_action