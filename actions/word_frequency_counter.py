import re
from collections import Counter

def run_action(parameters):
    """
    Yararlı bir yetenek: Metin Analizi - Kelime Frekansı Sayma.

    Bu fonksiyon, verilen metindeki kelime frekanslarını sayar.
    Metni küçük harflere çevirir (Unicode duyarlı `casefold` kullanarak),
    noktalama işaretlerini kaldırır ve kelime bazında sayım yaparak metin analizi yapar.
    Güvenlik, performans, dil desteği ve hata yönetimi iyileştirmeleri içerir.

    Args:
        parameters (dict): Girdi parametrelerini içeren bir sözlük.
                           'text' anahtarı altında analiz edilecek metni bekler.
                           Opsiyonel olarak 'max_length' anahtarı altında metin uzunluğu
                           sınırı belirlenebilir (varsayılan: 100,000 karakter).
                           Örnek: {'text': 'Bu bir test metni. Test metni güzel bir metin.', 'max_length': 50000}

    Returns:
        dict: Her kelimenin frekansını gösteren bir sözlük.
              Örnek: {'bu': 1, 'bir': 2, 'test': 2, 'metni': 2, 'güzel': 1}
        str: Hata mesajı eğer bir sorun oluşursa (parametre eksikliği, metin çok uzun, tip hatası vb.).
    """
    # 1. Güvenlik (Girdi Doğrulama)
    if 'text' not in parameters:
        return "Hata: 'text' parametresi eksik. Lütfen analiz edilecek metni sağlayın."

    text = parameters['text']

    if not isinstance(text, str):
        return "Hata: 'text' parametresi bir metin (string) olmalıdır."

    # Metin uzunluğu sınırlaması (potansiyel DoS saldırılarını ve bellek tüketimini önler)
    MAX_TEXT_LENGTH_DEFAULT = 100_000
    max_length_param = parameters.get('max_length')

    if isinstance(max_length_param, (int, float)) and max_length_param > 0:
        max_length = int(max_length_param) # float gelirse int'e çevir
    else:
        max_length = MAX_TEXT_LENGTH_DEFAULT # Geçersiz veya eksikse varsayılana dön

    if len(text) > max_length:
        return f"Hata: Metin boyutu çok büyük ({len(text)} karakter). İzin verilen maksimum boyut {max_length} karakterdir."

    try:
        # 4. Dil Desteği (Türkçe) - `casefold()` ile Unicode uyumlu küçük harf dönüştürme.
        # `lower()` belirli Unicode karakterler için sorun çıkarabilirken, `casefold()` daha agresif bir eşdeğerlik sağlar.
        processed_text = text.casefold()

        # 3. Noktalama İşaretleri ve Özel Karakterler
        # `\b\w+\b` regex'i sadece harf, sayı ve alt çizgiyi (Unicode karakterler dahil) kelime olarak kabul eder.
        # Bu, çoğu temel kelime frekansı sayım senaryosu için yeterlidir.
        # Eğer tireli kelimeleri (örn: "orta-sınıf") tek kelime saymak istenirse regex '\b[\w-]+\b' olarak değiştirilebilir.
        words = re.findall(r'\b\w+\b', processed_text)

        # 5. Hata Yönetimi
        # `Counter` büyük listelerde bile genellikle verimlidir ancak aşırı büyük girdilerde (
        # metin uzunluğu kısıtlaması bunu önemli ölçüde azaltır)
        # potansiyel MemoryError'ları yakalamak için try-except bloğu kullanılır.
        word_counts = Counter(words)

        # Counter nesnesini standart bir sözlüğe çevirerek döndür
        return dict(word_counts)

    except MemoryError:
        # 5. Kapsamlı hata yönetimi: Bellek yetersizliği durumunu yakala
        return "Hata: Metin işlenirken bellek yetersizliği oluştu. Metin çok büyük olabilir."
    except Exception as e:
        # 5. Kapsamlı hata yönetimi: Diğer beklenmedik hataları yakala
        return f"Hata: Metin analizi sırasında beklenmedik bir sorun oluştu: {str(e)}"

TOOL_NAME = 'word_frequency_counter'