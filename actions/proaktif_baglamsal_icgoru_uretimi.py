def run_action(params):
    query = params.get("query", "")
    if not query:
        return {"error": "Sorgu parametresi eksik. Lütfen bir 'query' sağlayın.", "direct_answer": "", "proactive_insights": []}

    # Bu fonksiyon, "Proaktif Bağlamsal İçgörü Üretimi" yeteneğinin bir simülasyonudur.
    # Gerçek bir LLM, sorguyu derinlemesine bağlamsal olarak anlayarak ve bilgi tabanını kullanarak
    # çok daha zengin, alakalı ve kişiselleştirilmiş içgörüler üretecektir.
    
    direct_response = f"'{query}' ile ilgili temel yanıtınız burada:
    (Gerçek bir LLM bu noktada sorgunuzla ilgili doğrudan ve doğru bilgiyi sağlar.)"

    proactive_insights = []
    # Basit anahtar kelime bazlı örnek içgörü üretimi
    query_lower = query.lower()

    if "python" in query_lower and ("dosya okuma" in query_lower or "file read" in query_lower):
        proactive_insights.append("Hata işleme (try-except blokları) ile kodunuzu daha sağlam hale getirmeyi unutmayın.")
        proactive_insights.append("Büyük dosyalarla çalışıyorsanız, belleği verimli kullanmak için dosyayı satır satır okumayı veya chunk'lara ayırmayı düşünün.")
        proactive_insights.append("Farklı dosya formatları (CSV, JSON, YAML) için ilgili kütüphanelere (örn. csv, json, PyYAML) göz atın.")
        proactive_insights.append("Dosya yollarını yönetirken os modülünü veya pathlib'ı kullanmak platformlar arası uyumluluk sağlar.")
    elif "python" in query_lower:
        proactive_insights.append("Python'da sanal ortamlar (venv/conda) projelerin bağımlılıklarını izole etmek için önemlidir.")
        proactive_insights.append("Popüler kütüphaneleri (örn. requests, pandas, numpy) ve kullanım alanlarını keşfedebilirsiniz.")
        proactive_insights.append("Verimli kod yazma ve performans optimizasyonu için en iyi pratikleri inceleyin.")
    elif "web geliştirme" in query_lower or "web development" in query_lower:
        proactive_insights.append("Frontend (HTML, CSS, JavaScript) ve Backend (Python/Django/Flask, Node.js/Express) teknolojileri arasındaki farkları ve entegrasyonlarını araştırın.")
        proactive_insights.append("API tasarımı (RESTful/GraphQL) ve kullanımı hakkında bilgi edinin.")
        proactive_insights.append("Web güvenliği açıklarına (SQL Injection, XSS, CSRF) karşı önlemleri öğrenmek hayati önem taşır.")
    else:
        # Genel proaktif içgörüler
        proactive_insights.append("Bu sorgunuzla bağlantılı olabilecek ek kavramlar veya ilgili teknolojileri araştırın.")
        proactive_insights.append("Karşılaşabileceğiniz potansiyel sorunlara yönelik önleyici ipuçları veya sıkça sorulan sorulara göz atın.")
        proactive_insights.append("Konuyla ilgili derinlemesine öğrenme kaynaklarını, güncel makaleleri veya uzman görüşlerini keşfedin.")
        proactive_insights.append("Gelecekteki olası ihtiyaçlarınız için bu konunun farklı kullanım senaryolarını düşünün.")

    return {
        "direct_answer": direct_response,
        "proactive_insights": proactive_insights,
        "simulation_note": "Yukarıdaki yanıtlar, 'Proaktif Bağlamsal İçgörü Üretimi' yeteneğinin basitleştirilmiş bir simülasyonudur. Gerçek bir LLM, sorguyu çok daha karmaşık bir bağlamda analiz ederek daha zengin, doğru ve kişiselleştirilmiş içgörüler üretir."
    }