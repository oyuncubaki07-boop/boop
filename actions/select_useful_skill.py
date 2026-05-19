def run_action(parameters):
    """
    Kullanıcının isteğine göre belirli bir kategoride faydalı bir yetenek seçer ve tanımlar.

    JARVIS Konseyi İç Mimar Değerlendirmesi'nde belirtilen güvenlik, performans,
    genişletilebilirlik, hata yönetimi ve kod tekrarı prensiplerine uygun olarak yeniden yapılandırılmıştır.

    Parametreler:
        parameters (dict): Girdi parametrelerini içeren bir sözlük.
                           Beklenen anahtar:
                           - 'kategori' (str, isteğe bağlı): Seçilecek yeteneğin kategorisi
                             ('programlama', 'iletişim', 'genel' gibi).
                             Belirtilmezse veya geçersizse 'genel' kullanılır.
                             Değer küçük/büyük harf duyarsızdır (örn. "PROGRAMLAMA" veya "programlama" kabul edilir).

    Dönüş:
        str: Seçilen yeteneğin adını ve tanımını içeren bir metin mesajı.
             Hata durumunda, bir hata mesajı döndürülür.
    """
    # Kod Tekrarı (DRY Prensibi), Performans ve Genişletilebilirlik için yetenek verileri sözlükte tutulur.
    # Yeni yetenekler veya kategoriler eklemek için sadece bu sözlüğü güncellemek yeterlidir.
    skills_data = {
        'programlama': {
            'adi': "Etkili Hata Ayıklama (Debugging)",
            'tanimi': (
                "Yazılım hatalarını hızlı ve sistematik bir şekilde bulma, "
                "analiz etme ve düzeltme yeteneği. Logları okuma, adım adım çalıştırma "
                "ve test odaklı geliştirme gibi pratikleri kapsar."
            )
        },
        'iletişim': {
            'adi': "Aktif Dinleme ve Etkili Geri Bildirim",
            'tanimi': (
                "Karşıdaki kişinin mesajını tam olarak anlama, duygu ve düşüncelerine değer verme, "
                "ve yapıcı geri bildirim sağlayarak işbirliğini güçlendirme yeteneği."
            )
        },
        'genel': { # Varsayılan kategori
            'adi': "Analitik Problem Çözme ve Eleştirel Düşünme",
            'tanimi': (
                "Karmaşık sorunları bileşenlerine ayırma, mantıksal adımlarla çözüm stratejileri "
                "geliştirme ve bilgiyi objektif değerlendirme yeteneği. Her alanda başarı için temeldir."
            )
        }
    }

    try:
        # Güvenlik (Enjeksiyon Açıkları, Veri Doğrulama):
        # 'kategori' parametresi alınır ve küçük harfe dönüştürülür.
        # Geçersiz veya bilinmeyen bir kategori belirtilirse 'genel' varsayılan olarak kullanılır.
        # Bu, kötü niyetli girdilerin doğrudan kod akışını etkilemesini engeller.
        istenen_kategori = parameters.get('kategori', 'genel').lower()

        # İzin verilen kategoriler listesi ile kontrol (güvenlik ve veri doğrulama)
        if istenen_kategori not in skills_data:
            # Belirtilen kategori geçersizse veya mevcut değilse uyarı verip varsayılan kategoriye düşülür.
            print(f"Uyarı: '{istenen_kategori}' geçersiz veya bilinmeyen bir kategori. 'genel' kategoriye düşülüyor.")
            istenen_kategori = 'genel'

        # Sözlükten yetenek bilgilerini alma (Performans)
        yetenek = skills_data[istenen_kategori]
        yetenek_adi = yetenek['adi']
        yetenek_tanimi = yetenek['tanimi']

        return f"Seçilen Yararlı Yetenek: {yetenek_adi}\nTanım: {yetenek_tanimi}"

    except Exception as e:
        # Hata Yönetimi: Beklenmedik durumları veya parametre işleme hatalarını yakalar.
        # Hata mesajı kullanıcıya döndürülür veya loglanır.
        print(f"Hata oluştu: {e}")
        return f"Yetenek seçimi sırasında bir hata oluştu: {str(e)}. Lütfen girdi parametrelerini kontrol edin."

TOOL_NAME = 'select_useful_skill'