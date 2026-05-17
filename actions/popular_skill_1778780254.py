import sys
import os
import subprocess
import json

# Bu modül, sisteminizin otonom Ar-Ge modülünden yüklenir ve çalıştırılır.
# Yüklenecek gerekli kütüphanelerin yönetimini kendisi yapar.

def run_action(params):
    """
    Kullanıcının sağladığı URL'den video veya ses indirir.
    GitHub ve StackOverflow'daki trendleri analiz ederken, medya indirme
    araçlarının (özellikle YouTube/video indirme) popülerliğini ve günlük
    kullanıcılar için kolaylığını fark ettim. Bu eklenti, kullanıcıların
    belirli bir URL'den medya içeriği indirmesini otomatikleştirmeyi sağlar.

    Gerekli Python kütüphanesi: yt-dlp (YouTube-DL'nin aktif olarak geliştirilen çatalı)

    Parametreler:
    - url (str): İndirilecek medyanın URL'si (örneğin, bir YouTube video linki). Zorunlu.
    - format (str, isteğe bağlı): "video" (varsayılan) veya "audio" olabilir.
      "audio" seçilirse, mümkünse ses dosyası (genellikle mp3) indirilir.
    - output_path (str, isteğe bağlı): Dosyanın kaydedileceği dizin.
      Belirtilmezse, geçerli çalışma dizinine kaydedilir.
    - filename_template (str, isteğe bağlı): Kaydedilecek dosyanın adlandırma şablonu.
      Örn: "%(title)s.%(ext)s". Belirtilmezse yt-dlp'nin varsayılanı kullanılır.

    Dönüş değeri:
    - dict: İşlemin sonucunu (başarılı/hatalı) ve ilgili mesajı içerir.
    """
    result = {"status": "error", "message": "Bilinmeyen bir hata oluştu."}

    # Bağımlılık kontrolü ve kurulumu
    try:
        import yt_dlp
    except ImportError:
        result["message"] = "yt-dlp kütüphanesi bulunamadı. Kuruluma çalışılıyor..."
        print(result["message"])
        try:
            # sys.executable, kodu çalıştıran Python yorumlayıcısını doğru bir şekilde hedefler.
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            import yt_dlp # Kurulum başarılıysa tekrar içe aktar
            print("yt-dlp başarıyla kuruldu.")
            result["message"] = "yt-dlp başarıyla kuruldu. İşlem şimdi deneniyor..."
            result["status"] = "info"
        except subprocess.CalledProcessError as e:
            result["message"] = f"yt-dlp kurulumu başarısız oldu: {e}. Lütfen pip'in ve internet bağlantınızın çalıştığından emin olun."
            return result
        except Exception as e:
            result["message"] = f"yt-dlp kurulumu sırasında beklenmeyen bir hata oluştu: {e}"
            return result

    url = params.get("url")
    if not url:
        result["message"] = "İndirilecek medyanın 'url' parametresi zorunludur."
        return result

    download_format = params.get("format", "video").lower()
    output_path = params.get("output_path", os.getcwd())
    filename_template = params.get("filename_template", "%(title)s.%(ext)s")

    # Çıkış dizini kontrolü ve oluşturma
    if not os.path.exists(output_path):
        try:
            os.makedirs(output_path)
            print(f"Çıkış dizini oluşturuldu: {output_path}")
        except OSError as e:
            result["message"] = f"Çıkış dizini oluşturulamadı: {output_path} - {e}"
            return result

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if download_format == 'video' else 'bestaudio/best',
        'outtmpl': os.path.join(output_path, filename_template),
        'noplaylist': True, # Varsayılan olarak çalma listesini indirme
        'progress_hooks': [lambda d: print(json.dumps(d)) if d['status'] != 'finished' and d['status'] != 'downloading' else None], # Basit ilerleme çıktısı
        'quiet': True, # Detaylı logları kapat
        'no_warnings': True, # Uyarıları kapat
    }

    if download_format == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        # FFmpeg postprocessor için log'ları göstermek üzere quiet ayarını geçersiz kıl
        ydl_opts['quiet'] = False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"URL'den medya indiriliyor: {url}")
            print(f"Hedef format: {download_format}")
            print(f"Kaydedilecek yer: {output_path}")

            info_dict = ydl.extract_info(url, download=True)
            # Eğer indirildiyse, kaydedilen dosya adını bulmaya çalış
            if '_filename' in info_dict:
                file_path = info_dict['_filename']
            elif 'requested_downloads' in info_dict and info_dict['requested_downloads']:
                # Birden fazla dosya indirildiyse (örn: video ve ses ayrı ayrı sonra birleştirildi)
                # İlk dosyayı referans alabiliriz veya daha sofistike bir kontrol yapabiliriz.
                file_path = info_dict['requested_downloads'][0]['filepath']
            else:
                file_path = "Bilinmeyen dosya yolu (kontrol edin)."


            result["status"] = "success"
            result["message"] = f"Medya başarıyla indirildi: {os.path.basename(file_path)}. Kayıt yeri: {os.path.dirname(file_path)}"
            result["file_path"] = file_path
            result["title"] = info_dict.get('title')
            result["uploader"] = info_dict.get('uploader')
            result["duration"] = info_dict.get('duration')

    except yt_dlp.utils.DownloadError as e:
        result["message"] = f"Medya indirme hatası: {e}"
    except yt_dlp.utils.ExtractorError as e:
        result["message"] = f"URL'den bilgi çekme hatası: {e}. URL geçerli olmayabilir veya desteklenmiyor olabilir."
    except FileNotFoundError as e:
        if download_format == 'audio':
            result["message"] = f"FFmpeg bulunamadı. Ses dönüştürme için FFmpeg yüklü olmalıdır. Hata: {e}"
        else:
            result["message"] = f"Dosya sistemi hatası: {e}"
    except Exception as e:
        result["message"] = f"Beklenmeyen bir hata oluştu: {e}"

    return result

# Bu fonksiyonun doğrudan çalıştırılabilir olmaması gerekir,
# çünkü otonom bir sistem tarafından çağrılacaktır.
# Ancak test amaçlı örnek kullanım:
if __name__ == "__main__":
    # Örnek kullanım 1: Bir YouTube videosu indirme (video formatı)
    # Gerçek bir URL ile değiştirin.
    test_params_video = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Rick Astley - Never Gonna Give You Up
        "format": "video",
        "output_path": "./downloads",
        "filename_template": "Video_%(title)s.%(ext)s"
    }
    print("### Video İndirme Testi ###")
    video_result = run_action(test_params_video)
    print(json.dumps(video_result, indent=4, ensure_ascii=False))
    print("\n" + "="*50 + "\n")

    # Örnek kullanım 2: Aynı videoyu ses formatında indirme
    test_params_audio = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Rick Astley - Never Gonna Give You Up
        "format": "audio",
        "output_path": "./downloads",
        "filename_template": "Audio_%(title)s.%(ext)s"
    }
    print("### Ses İndirme Testi ###")
    audio_result = run_action(test_params_audio)
    print(json.dumps(audio_result, indent=4, ensure_ascii=False))
    print("\n" + "="*50 + "\n")

    # Örnek kullanım 3: Geçersiz URL
    test_params_invalid = {
        "url": "https://www.invalid-youtube-link.com/watch?v=nonexistent",
        "format": "video",
        "output_path": "./downloads"
    }
    print("### Geçersiz URL Testi ###")
    invalid_result = run_action(test_params_invalid)
    print(json.dumps(invalid_result, indent=4, ensure_ascii=False))
    print("\n" + "="*50 + "\n")

    # Örnek kullanım 4: URL parametresi eksik
    test_params_missing = {
        "format": "video",
        "output_path": "./downloads"
    }
    print("### Eksik URL Parametresi Testi ###")
    missing_result = run_action(test_params_missing)
    print(json.dumps(missing_result, indent=4, ensure_ascii=False))
    print("\n" + "="*50 + "\n")

    # Lütfen gerçek kullanımda `params` sözlüğünün sisteminiz tarafından doğru bir şekilde oluşturulduğundan emin olun.