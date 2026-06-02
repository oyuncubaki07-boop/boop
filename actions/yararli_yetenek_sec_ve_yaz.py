# ELESTIRI NOTU: Gerçek dünya projelerinde, harici bağımlılıklar (varsa) 'pip install -r requirements.txt'
# komutuyla kurulabilmesi için bir 'requirements.txt' dosyası bulundurmak iyi bir pratiktir.

def run_action(parameters):
    """
    Yararlı bir yetenek seçer ve bu yeteneği açıklar.
    Bu fonksiyon, kritik düşünme ve problem çözme yeteneğini detaylandırır.

    parameters:
        Bu argüman, fonksiyonun imza gerekliliği nedeniyle dahil edilmiştir
        ancak mevcut uygulamada doğrudan kullanılmamaktadır. Gelecekte
        fonksiyonun davranışını parametreleştirmek (örneğin, farklı bir yetenek seçmek)
        için genişletilebilir ve bu durumda güvenlik doğrulama adımları eklenmelidir.
    """
    selected_skill = "Eleştirel Düşünme ve Problem Çözme"
    
    # f-string kullanımı, string birleştirme için modern Python'da oldukça verimlidir.
    # Bu metin statik olduğu için enjeksiyon riski yoktur. Ancak genel prensip olarak,
    # kullanıcıdan gelen veya güvenilmeyen kaynaklardan alınan veriler doğrudan
    # çıktıya basılmadan önce mutlaka temizlenmelidir (sanitize).
    skill_details = (
        f"Seçilen Yararlı Yetenek: {selected_skill}\n\n"
        "Açıklama: Eleştirel düşünme, bir konuyu veya problemi objektif bir şekilde "
        "değerlendirme, geçerli ve güvenilir bilgiyi ayırt etme, varsayımları sorgulama "
        "ve mantıklı sonuçlara ulaşma yeteneğidir. Problem çözme ise, karşılaşılan "
        "zorlukları analiz ederek en uygun ve etkili çözümleri bulma sürecidir.\n\n"
        "Bu iki yetenek, herhangi bir alanda karmaşık durumlarla başa çıkmak, doğru "
        "kararlar almak ve sürekli öğrenme ve gelişme için temel teşkil eder. "
        "Özellikle teknoloji, bilim, mühendislik ve günlük yaşamda vazgeçilmezdir."
    )
    
    # Eleştiri 1, 4 ve 6'yı ele almak için:
    # Fonksiyonun doğrudan çıktı (I/O) işlemi yapmak yerine, oluşturduğu değeri döndürmesi
    # daha esnek ve test edilebilir bir yapı sağlar. Bu, çıktının nasıl kullanılacağına
    # (örneğin konsola yazdırma, loglama, bir API yanıtı olarak gönderme) karar verme
    # sorumluluğunu çağıran koda bırakır ve potansiyel terminal enjeksiyon risklerini
    # (statik içerik için geçerli olmasa da genel bir prensip olarak) çağıran tarafın
    # yönetmesine olanak tanır. Performans açısından da I/O yükü çağrı noktasına taşınır.
    return skill_details

# Örnek kullanım (fonksiyonun döndürdüğü değeri göstermek için):
if __name__ == "__main__":
    output = run_action(None) # parameters kullanılmadığı için None geçilebilir
    print(output)