import zlib
import sys

def run_action(parameters: dict) -> dict:
    """
    Jarvis için metin verilerini (örneğin, araç çıktıları, loglar, RAG parçacıkları)
    LLM'ye gönderilmeden önce ZLIB kullanarak güvenli ve verimli bir şekilde sıkıştıran yetenek.

    Amacı, token/veri boyutunu azaltarak LLM maliyetlerini ve işlem süresini optimize etmektir.
    Bu, 'sponsors/chopratejas' ilhamıyla, %60-95 daha az token ile aynı yanıtları elde etme hedefiyle yapılmıştır.

    DNA:
    - Ton: Saygılı, sıcak, kısa ve net.
    - Mimari: Modüler, genişletilebilir, güvenlik odaklı, hata toleranslı.
    - Kod Standartları: 'def run_action(parameters)' giriş noktası, Türkçe mesajlar 'Efendim' ile,
                       try/except ile güvenli hata yönetimi, harici API anahtarı yok.
    - Güvenlik: Yalnızca yerel sıkıştırma yapar, tehlikeli komut çalıştırmaz.

    Parametreler:
    - parameters (dict): Eylemin gerektirdiği girdileri içeren bir sözlük.
        - "data" (str): Sıkıştırılacak metin verisi. Zorunludur.
                        Örnek: "Bu, LLM'ye gönderilecek uzun bir araç çıktısı metnidir."

    Dönüş:
    - dict: İşlemin sonucunu ve sıkıştırılmış veriyi içeren bir sözlük.
        - "status" (str): İşlemin durumu ("success" veya "error").
        - "message" (str): Kullanıcıya yönelik açıklayıcı mesaj.
        - "compressed_data_hex" (str, isteğe bağlı): Sıkıştırılmış verinin hexadecimal string temsili.
                                                   (Yalnızca "success" durumunda).
                                                   Bu format, bayt verisini JSON uyumlu bir string olarak taşır.
        - "original_size" (int, isteğe bağlı): Orijinal verinin UTF-8 bayt cinsinden boyutu.
        - "compressed_size" (int, isteğe bağlı): Sıkıştırılmış verinin bayt cinsinden boyutu.
        - "compression_ratio" (float, isteğe bağlı): Elde edilen sıkıştırma oranı (yüzde).
        - "error_details" (str, isteğe bağlı): Hata durumunda teknik detaylar.
    """
    try:
        # 1. Parametre Doğrulama (DNA: Güvenlik önce)
        if "data" not in parameters or not isinstance(parameters["data"], str):
            return {
                "status": "error",
                "message": "Efendim, 'data' parametresi eksik veya uygun formatta değil. Lütfen sıkıştırılacak metni sağlayınız.",
                "error_details": "Missing or invalid 'data' parameter. Expected a string."
            }

        input_data = parameters["data"]

        # 2. Veriyi UTF-8 olarak kodlayıp ZLIB ile sıkıştır
        # DNA: Yerel veri gizliliği - işlem yerel olarak yapılır.
        original_bytes = input_data.encode('utf-8')
        compressed_bytes = zlib.compress(original_bytes)

        # 3. Boyut ve sıkıştırma oranı hesaplama
        original_size = len(original_bytes)
        compressed_size = len(compressed_bytes)
        compression_ratio = (1 - (compressed_size / original_size)) * 100 if original_size > 0 else 0

        # 4. Sonucu döndürme (DNA: Kıs ve net mesajlar, 'Efendim' ile)
        return {
            "status": "success",
            "message": f"Efendim, veri başarıyla sıkıştırıldı. Orijinal boyut: {original_size} bayt, Sıkıştırılmış boyut: {compressed_size} bayt. Yaklaşık %{compression_ratio:.2f} oranında azalma sağlandı.",
            "compressed_data_hex": compressed_bytes.hex(), # Bayt verisini güvenli string olarak iletmek için hex kullanıldı
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": round(compression_ratio, 2)
        }

    except Exception as e:
        # 5. Güvenli Hata İşleme (DNA: try/except ile güvenli hata, 'Efendim' ile mesaj)
        return {
            "status": "error",
            "message": f"Efendim, veri sıkıştırılırken beklenmedik bir sorun oluştu: {str(e)}. Lütfen verilerinizi kontrol ediniz.",
            "error_details": str(e)
        }

# Örnek Kullanım:
if __name__ == "__main__":
    test_data_long = """
    Jarvis, Tony Stark tarafından tasarlanmış bir yapay zeka sistemidir. Zengin veri analizi yetenekleri,
    stratejik planlama becerileri ve kullanıcı etkileşimi için gelişmiş bir doğal dil işleme arayüzü ile donatılmıştır.
    Modüler bir mimariye sahip olan Jarvis, yeni yetenekler eklendikçe dinamik olarak genişleyebilir ve evrim geçirebilir.
    Güvenlik, Jarvis'in temel tasarım ilkelerinden biridir; kritik değişiklikler kullanıcı onayı gerektirir,
    hassas veriler yerel olarak işlenir ve sandbox ortamları dışında rastgele kod çalıştırılmasına izin verilmez.
    Bu tasarım, Jarvis'i sadece güçlü değil, aynı zamanda güvenilir ve öngörülebilir kılar.
    Jarvis'in asenkron ve hata toleranslı yapısı, operasyonel sürekliliği ve dayanıklılığı garanti eder.
    """ * 10 # Metni biraz uzatalım

    test_data_short = "Merhaba Dünya!"

    test_data_empty = ""

    test_data_invalid = {"not_data": "bu yanlış"}


    print("--- Uzun Metin Testi ---")
    result_long = run_action({"data": test_data_long})
    print(f"Status: {result_long['status']}")
    print(f"Message: {result_long['message']}")
    if result_long['status'] == 'success':
        print(f"Orijinal boyut: {result_long['original_size']} bayt")
        print(f"Sıkıştırılmış boyut: {result_long['compressed_size']} bayt")
        print(f"Sıkıştırma Oranı: %{result_long['compression_ratio']:.2f}")
        # Sıkıştırılmış veriyi geri çözme örneği (Jarvis içinde LLM'ye iletilmeden önce gerekebilir)
        # decompressed_bytes = bytes.fromhex(result_long['compressed_data_hex'])
        # original_text_again = zlib.decompress(decompressed_bytes).decode('utf-8')
        # print(f"Decompress sonrası ilk 100 karakter: {original_text_again[:100]}...")
    print("\n")

    print("--- Kısa Metin Testi ---")
    result_short = run_action({"data": test_data_short})
    print(f"Status: {result_short['status']}")
    print(f"Message: {result_short['message']}")
    print("\n")

    print("--- Boş Metin Testi ---")
    result_empty = run_action({"data": test_data_empty})
    print(f"Status: {result_empty['status']}")
    print(f"Message: {result_empty['message']}")
    print("\n")

    print("--- Geçersiz Parametre Testi ---")
    result_invalid = run_action(test_data_invalid)
    print(f"Status: {result_invalid['status']}")
    print(f"Message: {result_invalid['message']}")
    print(f"Error Details: {result_invalid['error_details']}")
    print("\n")

    print("--- Eksik Parametre Testi ---")
    result_missing = run_action({})
    print(f"Status: {result_missing['status']}")
    print(f"Message: {result_missing['message']}")
    print(f"Error Details: {result_missing['error_details']}")
    print("\n")