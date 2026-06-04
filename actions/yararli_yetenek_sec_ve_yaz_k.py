def run_action(parameters):
    """
    Belirtilen parametreye göre uygun bir "yararlı yetenek" seçer ve bu yeteneği
    açıklayan bir metin döndürür. Bu, bir AI aracının hangi dahili aracı veya
    yeteneği kullanacağını belirlemek için kullanılabilir.

    Args:
        parameters (str): Gerçekleştirilecek görevi veya istenen yeteneği belirten bir metin.
                          Örn: "Hesaplama yap: 5 + 3", "İnternetten hava durumunu öğren",
                          "Bu metni İngilizceye çevir: Merhaba dünya."

    Returns:
        str: Seçilen yeteneği ve ilgili eylemi açıklayan bir metin.
    """
    parameters_lower = parameters.lower()

    if any(keyword in parameters_lower for keyword in ["hesapla", "matematik", "topla", "çıkar", "çarp", "böl", "sonuç", "sayı"]):
        skill = "Matematiksel Hesaplama"
        action = "Verilen matematiksel ifadeyi veya sayılarla ilgili işlemi hesaplıyorum."
    elif any(keyword in parameters_lower for keyword in ["ara", "bul", "bilgi", "internet", "web", "öğren", "nedir", "kimdir", "nerede", "ne zaman"]):
        skill = "Web Arama ve Bilgi Edinme"
        action = "İlgili bilgiyi internette arıyor ve sana sunuyorum."
    elif any(keyword in parameters_lower for keyword in ["yaz", "oluştur", "hikaye", "kod", "metin", "üret", "makale", "e-posta", "şiir"]):
        skill = "Metin/İçerik Üretimi"
        action = "İsteğine göre yeni bir metin, kod, hikaye veya başka bir içerik oluşturuyorum."
    elif any(keyword in parameters_lower for keyword in ["çevir", "dil", "tercüme", "çeviri"]):
        skill = "Dil Çevirisi"
        action = "Verilen metni belirtilen veya uygun dile çeviriyorum."
    elif any(keyword in parameters_lower for keyword in ["özetle", "kısalt", "özet", "ana fikir"]):
        skill = "Metin Özetleme"
        action = "Verilen uzun metnin ana fikirlerini çıkarıp özetliyorum."
    elif any(keyword in parameters_lower for keyword in ["plan", "takvim", "randevu", "zamanla", "hatırlatıcı", "organizasyon"]):
        skill = "Planlama ve Takvim Yönetimi"
        action = "Bir etkinlik planlıyor, takvime ekliyor veya bir hatırlatıcı ayarlıyorum."
    elif any(keyword in parameters_lower for keyword in ["resim", "görsel", "çiz", "fotoğraf", "grafik", "tasarım"]):
        skill = "Görsel Üretimi"
        action = "Verilen açıklamaya uygun bir görsel veya resim oluşturuyorum."
    elif any(keyword in parameters_lower for keyword in ["analiz", "veriyi incele", "raporla", "değerlendir"]):
        skill = "Veri Analizi"
        action = "Sağlanan verileri inceliyor, analiz ediyor ve sonuçları raporluyorum."
    elif any(keyword in parameters_lower for keyword in ["talimat", "adım adım", "nasıl yapılır", "yönerge"]):
        skill = "Adım Adım Talimat Verme"
        action = "Belirli bir görevi nasıl yapacağına dair adım adım talimatlar sağlıyorum."
    else:
        skill = "Genel Yardımcı Yetenek"
        action = "Belirtilen göreve en uygun genel yardımcı yeteneği kullanıyor veya daha fazla detay bekliyorum."

    return f"Seçilen Yetenek: {skill}. Yapılacak Eylem: {action}"