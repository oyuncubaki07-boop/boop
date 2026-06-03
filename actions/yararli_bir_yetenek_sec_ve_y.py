def run_action(parameters):
    """
    Yararlı bir yeteneği seçer ve detaylı bir açıklamasını döndürür.
    `parameters` argümanı bu fonksiyonda doğrudan kullanılmasa da fonksiyon imzası gereği mevcuttur.
    """
    skill_name = "Eleştirel Düşünme (Critical Thinking)"
    description = (
        f"**Yetenek:** {skill_name}\n\n"
        "**Açıklama:** Eleştirel düşünme, karmaşık durumları veya sorunları analiz etmek, kanıtları değerlendirmek, mantıksal bağlantılar kurmak ve bilinçli kararlar vermek için kullanılan bilişsel bir süreçtir. "
        "Bilgiyi sorgulama, önyargıları tanıma ve farklı bakış açılarını dikkate alma yeteneğini içerir.\n\n"
        "**Neden Yararlıdır:**\n"
        "1.  **Daha İyi Karar Verme:** Kişisel ve profesyonel hayatta daha sağlam ve mantıklı kararlar alınmasını sağlar.\n"
        "2.  **Problem Çözme:** Sorunların temel nedenlerini belirlemede ve etkili çözümler geliştirmede yardımcı olur.\n"
        "3.  **Yenilikçilik:** Mevcut durumları sorgulayarak ve farklı yaklaşımları değerlendirerek yeni fikirlerin ortaya çıkmasına zemin hazırlar.\n"
        "4.  **Bilgi Kirliliğinden Korunma:** Özellikle günümüz bilgi çağında, yanlış veya yanıltıcı bilgileri ayırt etme yeteneği sunar.\n"
        "5.  **İletişim ve İkna:** Düşünceleri daha net ve ikna edici bir şekilde ifade etmeyi sağlar.\n\n"
        "**Uygulama Alanları:** İş hayatında stratejik planlamadan günlük yaşamdaki alışveriş tercihlerine kadar geniş bir yelpazede uygulanabilir. "
        "Bir projenin risklerini değerlendirirken, karmaşık bir kodu hata ayıklarken veya bir makalenin argümanlarını incelerken eleştirel düşünme becerileri vazgeçilmezdir."
    )
    return description