import zlib
import base64
import sys # Hata detaylarını loglamak için

def run_action(parameters: dict) -> dict:
    """
    Efendim, LLM'e gönderilecek büyük metin verilerini zlib ile sıkıştırır
    ve Base64 formatına dönüştürür. Bu sayede token tüketimi optimize edilir.

    Parametreler:
    - parameters (dict):
        - 'data' (str): Sıkıştırılacak ham metin verisi. Zorunludur.

    Dönüş:
    - dict: Sıkıştırma işleminin sonucunu içeren bir sözlük.
            Başarılı durumda sıkıştırılmış veriyi ve istatistikleri,
            hata durumunda ise hata mesajını içerir.
    """
    try:
        data_to_compress = parameters.get('data')

        # Güvenlik ve veri doğrulama
        if not isinstance(data_to_compress, str) or not data_to_compress:
            return {
                "status": "error",
                "message": "Efendim, lütfen 'data' anahtarı altında sıkıştırılacak geçerli bir metin (string) sağlayın.",
                "error_details": "Giriş verisi eksik, boş veya geçersiz türde."
            }

        original_bytes = data_to_compress.encode('utf-8')
        original_char_count = len(data_to_compress) # LLM token'ları genellikle karakter sayısıyla ilişkilidir

        # Veriyi zlib ile sıkıştır
        compressed_bytes = zlib.compress(original_bytes)

        # Sıkıştırılmış bayt verisini Base64 ile kodla (LLM'e metin olarak iletilebilmesi için)
        encoded_compressed_data_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
        compressed_b64_char_count = len(encoded_compressed_data_b64) # LLM'e gidecek metin boyutu

        # Sıkıştırma kazanç oranını hesapla
        compression_saving_percentage = 0.0
        if original_char_count > 0:
            compression_saving_percentage = (1 - (compressed_b64_char_count / original_char_count)) * 100

        return {
            "status": "success",
            "message": "Efendim, veri başarıyla sıkıştırıldı. Token tüketiminde %{:.2f} tasarruf sağlandı.".format(compression_saving_percentage),
            "original_data_char_count": original_char_count,
            "original_data_byte_count": len(original_bytes),
            "compressed_data_b64_char_count": compressed_b64_char_count,
            "compressed_data_raw_byte_count": len(compressed_bytes),
            "compression_saving_percentage": round(compression_saving_percentage, 2),
            "compressed_data_b64": encoded_compressed_data_b64 # LLM'e gönderilecek Base64 kodlu sıkıştırılmış veri
        }

    except Exception as e:
        # Güvenli hata işleme: Detayları konsola yaz, kullanıcıya genel bir hata mesajı dön.
        error_traceback = traceback.format_exc()
        print(f"JARVIS/compress_for_llm Hata: {error_traceback}", file=sys.stderr) # Hata detaylarını stderr'e yaz

        return {
            "status": "error",
            "message": "Efendim, veri sıkıştırılırken beklenmeyen bir hata oluştu.",
            "error_details": str(e) # Geliştirici için hata mesajı
        }

# Geri dönüştürme fonksiyonu (JARVIS'in dahili kullanımı veya ayrı bir yetenek olarak)
def decompress_b64_data(compressed_data_b64: str) -> dict:
    """
    Efendim, Base64 kodlu zlib sıkıştırılmış veriyi orijinal haline geri dönüştürür.

    Parametreler:
    - compressed_data_b64 (str): Base64 kodlu sıkıştırılmış metin verisi. Zorunludur.

    Dönüş:
    - dict: Açma işleminin sonucunu içeren bir sözlük.
    """
    try:
        if not isinstance(compressed_data_b64, str) or not compressed_data_b64:
            return {
                "status": "error",
                "message": "Efendim, lütfen 'compressed_data_b64' anahtarı altında geçerli bir Base64 kodlu sıkıştırılmış metin sağlayın.",
                "error_details": "Giriş verisi eksik, boş veya geçersiz türde."
            }

        # Base64 çözme
        decoded_compressed_bytes = base64.b64decode(compressed_data_b64)

        # zlib ile açma
        decompressed_bytes = zlib.decompress(decoded_compressed_bytes)

        # Metne dönüştürme
        decompressed_text = decompressed_bytes.decode('utf-8')

        return {
            "status": "success",
            "message": "Efendim, veri başarıyla açıldı.",
            "decompressed_text": decompressed_text,
            "original_b64_char_count": len(compressed_data_b64),
            "decompressed_char_count": len(decompressed_text)
        }

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"JARVIS/decompress_b64_data Hata: {error_traceback}", file=sys.stderr)

        return {
            "status": "error",
            "message": "Efendim, veriyi açarken beklenmeyen bir hata oluştu.",
            "error_details": str(e)
        }

# **Örnek Kullanım (Jarvis'in iç simülasyonu için):**
if __name__ == '__main__':
    long_text = "JARVIS, Tony Stark'ın yapay zeka asistanıdır. Çoklu görev yetenekleri, gelişmiş analitik becerileri ve kullanıcı dostu arayüzü ile bilinir. Bu metin, sıkıştırma yeteneğinin ne kadar etkili olduğunu test etmek amacıyla tekrar eden ifadeler içermektedir. JARVIS DNA'sı modülerlik, güvenlik ve hata toleransını önceliklendirir. Her yeni yetenek bu prensiplere uygun olmalıdır. Bu metin oldukça uzun ve tekrar eden kısımlara sahip olduğundan, zlib sıkıştırması için iyi bir adaydır. LLM'lere gönderilmeden önce bu tür metinleri sıkıştırmak, hem maliyetleri düşürür hem de performans artışı sağlar. Tony Stark'ın JARVIS'i her zaman en verimli çözümleri sunar. JARVIS, her zaman yanınızda. JARVIS, geleceğin teknolojisi. JARVIS, sizin için burada. JARVIS, daima en iyisi. JARVIS, Tony Stark'ın en iyi arkadaşı. JARVIS, eşsiz bir yapay zeka. JARVIS, inanılmaz bir sistem. JARVIS, her zaman hazır. JARVIS, en iyi asistan." * 10 # Metni uzat

    print("--- Sıkıştırma Testi ---")
    compression_result = run_action({'data': long_text})
    print(f"Sıkıştırma Sonucu: {compression_result}")

    if compression_result['status'] == 'success':
        print("\n--- Geri Dönüştürme Testi ---")
        decompression_result = decompress_b64_data(compression_result['compressed_data_b64'])
        print(f"Geri Dönüştürme Sonucu: {decompression_result}")
        print(f"Orijinal metin ile geri dönüştürülen metin aynı mı? {long_text == decompression_result.get('decompressed_text')}")
    else:
        print("Sıkıştırma başarısız olduğu için geri dönüştürme testi atlandı.")

    print("\n--- Hata Testi (Geçersiz Giriş) ---")
    error_result = run_action({'data': 12345}) # String olmayan veri
    print(f"Hata Sonucu: {error_result}")

    error_result_empty = run_action({'data': ''}) # Boş veri
    print(f"Hata Sonucu (Boş): {error_result_empty}")

    error_result_missing = run_action({}) # 'data' eksik
    print(f"Hata Sonucu (Eksik): {error_result_missing}")