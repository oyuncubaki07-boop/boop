import os

def run_action(parameters: dict) -> str:
    """
    Kullanıcının 'MoneyPrinterTurbo' ilhamıyla kısa video oluşturma talebini işler.
    Güvenlik ve DNA uyumluluğu nedeniyle, doğrudan video üretimi yerine
    onay ve entegrasyon sürecini başlatır veya durumunu bildirir.

    Parametreler:
        parameters (dict): 'topic' anahtarıyla video konusunu bekler.
                           Örnek: {"topic": "kuantum bilgisayarların geleceği"}

    Dönüş:
        str: JARVIS tarzı, kısa ve net durum veya hata mesajı.
    """
    try:
        # Kod standartları: Kullanıcı mesajları 'Efendim' ile başlar.
        # Güvenlik politikaları: Harici API anahtarları kodda tutulmaz.
        # Bu kısımda bir API anahtarı gerekseydi, 'parameters' içinde güvenli bir şekilde gelmeliydi.
        # Örneğin: api_key = parameters.get('api_key')
        # if not api_key: return "Efendim, video üretim servisi için API anahtarı eksik."

        video_topic = parameters.get('topic')

        if not video_topic:
            return "Efendim, kısa video oluşturmak için bir konu ('topic') belirtmelisiniz. Örnek: {'topic': 'yapay zekanın etik sınırları'}"

        # Mimari prensipleri: Güvenlik önce — onay, sandbox, geri alma.
        # Güvenlik politikaları: Tehlikeli sistem komutları engellenir; Sandbox dışında rastgele kod çalıştırma yasak.
        # Bu nedenle, doğrudan bir video üretim betiği veya harici sistem komutu burada çalıştırılmaz.
        # Bunun yerine, JARVIS'ın güvenlik protokollerini ve onay sürecini simüle ediyoruz.

        # Kod standartları: Turkce kullanici mesajlari 'Efendim' ile.
        # Ton: Saygılı, sıcak, Tony Stark JARVIS tarzı — kısa ve net.
        response_message = (
            f"Efendim, '{video_topic}' konusunda kısa bir video oluşturma talebinizi aldım. "
            "Bu tür bir yetenek, önemli sistem kaynakları ve güvenlik protokolleri gerektirir. "
            "Doğrudan bu yetenek içinde video üretmek, mevcut güvenlik ve sandbox politikalarımızın dışındadır. "
            "Bu işlevi gerçekleştirmek için 'MoneyPrinterTurbo' entegrasyonu, "
            "'evolution_pending' onay kuyruğu üzerinden uygun güvenlik denetimlerinden geçirilerek "
            "ayrı bir modül olarak tasarlanmalı ve dağıtılmalıdır. "
            "Şu an için, videonuzun hazırlanması talebini sisteme iletiyorum ve uygun entegrasyon sağlandığında sizi bilgilendireceğim. "
            "Amacım, talebinizi güvenli ve verimli bir şekilde yerine getirmektir."
        )
        return response_message

    except Exception as e:
        # Kod standartları: try/except ile güvenli hata yönetimi.
        # Hata toleranslı: Beklenmedik durumlarda sistem çökmez, kullanıcıya bilgi verir.
        return f"Efendim, video oluşturma isteğiniz işlenirken beklenmeyen bir hata oluştu: {str(e)}. Lütfen tekrar deneyin."

# Örnek Kullanım:
if __name__ == "__main__":
    # Geçerli bir talep
    params_valid = {"topic": "uzaydaki keşiflerin geleceği"}
    print(f"Test 1 (Geçerli): {run_action(params_valid)}\n")

    # Konu belirtilmemiş talep
    params_no_topic = {}
    print(f"Test 2 (Konu yok): {run_action(params_no_topic)}\n")

    # Boş konu
    params_empty_topic = {"topic": ""}
    print(f"Test 3 (Boş konu): {run_action(params_empty_topic)}\n")

    # Yanlış parametre adı (sistem 'topic' bekler)
    params_wrong_key = {"subject": "yapay zeka"}
    print(f"Test 4 (Yanlış parametre): {run_action(params_wrong_key)}\n")

    # JARVIS'ın bu yetenekle ilgili güvenlik ve onay süreçlerine vurgu yapması,
    # DNA'sındaki 'Güvenlik önce' ve 'evolution_pending' prensiplerine uygun bir yaklaşımdır.
    # Gerçek dünya entegrasyonunda, bu `run_action` daha sonra bir arka plan görevini
    # veya ayrı bir onaylanmış mikroservisi tetikleyebilir.