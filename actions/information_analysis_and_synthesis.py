import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# --- NLTK Veri İndirmeleri (Pip Eleştirisi Çözümü) ---
# Gerçek bir üretim ortamında bu indirmeler uygulamanın kurulum aşamasında
# bir kez yapılmalı ve kodun her çalıştırılışında denenmemelidir.
# Ancak, bu fonksiyonun bağımsız çalışabilirliğini sağlamak amacıyla burada
# hata yönetimi ile birlikte yer almaktadır.
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    print("NLTK 'stopwords' verisi indiriliyor...")
    nltk.download('stopwords')
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("NLTK 'punkt' verisi indiriliyor...")
    nltk.download('punkt')

def run_action(parameters):
    """
    Seçilen yararlı yeteneği uygular: Bilgiyi Analiz Etme ve Sentezleme.

    Bu yetenek, karmaşık verileri ve metinleri parçalarına ayırma (analiz)
    ve bu parçaları anlamlı bir bütün halinde birleştirme (sentezleme) becerisini temsil eder.
    Amacı, derinlemesine anlayış sağlamak ve yeni fikirler üretmektir.

    Args:
        parameters (dict): Eylemin nasıl gerçekleştirileceğine dair ek bilgiler içerebilir.
                           Örnek: {'input_data': 'Uzun bir raporun ilk paragrafı burada.',
                                   'analysis_type': 'keywords',
                                   'max_length': 10000} # Maksimum girdi uzunluğu sınırı

    Returns:
        dict: Eylemin sonucunu ve seçilen yeteneği açıklayan bir sözlük.
    """
    skill_name = "Bilgiyi Analiz Etme ve Sentezleme"
    action_result = {
        "skill_chosen": skill_name,
        "description": (
            f"'{skill_name}' yeteneği seçildi. Bu yetenek, karmaşık bilgileri parçalara ayırarak "
            "anlamak, anahtar noktaları belirlemek ve bu noktaları yeni bir bakış açısıyla "
            "birleştirerek anlamlı çıktılar üretmek için kullanılır. Bu sürüm, NLTK kütüphanesini kullanarak "
            "daha gelişmiş metin işleme yetenekleri sunar ve girdi doğrulaması ile kaynak tüketimini yönetir."
        )
    }

    # --- Güvenlik ve Performans: Girdi Doğrulaması ve Kaynak Sınırlandırması (Eleştiri 1, 4) ---
    # Aşırı büyük girdilerin belleği ve işlemciyi tüketmesini önler (DoS riski).
    MAX_INPUT_LENGTH = parameters.get('max_length', 10000) # Varsayılan 10,000 karakter sınırı

    input_data = None
    if parameters and isinstance(parameters, dict) and 'input_data' in parameters:
        # Gelen veriyi string'e dönüştürmeye çalış ve olası hataları yakala
        try:
            input_data = str(parameters['input_data'])
        except Exception: # TypeError veya diğer dönüşüm hataları
            action_result["error"] = "Hata: 'input_data' geçerli bir metin olarak dönüştürülemedi. Lütfen bir metin girin."
            action_result["action_performed"] = "Girdi doğrulama hatası nedeniyle analiz yapılamadı."
            return action_result

        # Boş veya sadece boşluklardan oluşan metinleri kontrol et
        if not input_data.strip():
            action_result["action_performed"] = "Boş veya sadece boşluk içeren bir 'input_data' sağlandığı için analiz yapılmadı."
            return action_result

        # Girdi uzunluğunu kontrol et
        if len(input_data) > MAX_INPUT_LENGTH:
            action_result["error"] = (
                f"Hata: Sağlanan 'input_data' çok uzun ({len(input_data)} karakter). "
                f"Maksimum {MAX_INPUT_LENGTH} karakter kabul edilmektedir. "
                "DoS riskini azaltmak ve performansı artırmak için girdi sınırı uygulanmıştır."
            )
            action_result["action_performed"] = "Girdi uzunluğu sınırı aşıldığı için analiz yapılamadı."
            return action_result
    else:
        action_result["action_performed"] = "Herhangi bir 'input_data' sağlanmadığı için sadece yeteneğin tanımı yapıldı."
        return action_result # input_data yoksa buradan dön

    # input_data varsa analize devam et
    analysis_type = parameters.get('analysis_type', 'summary').lower() # Analiz tipini küçük harfe çevir

    try:
        # --- Performans ve Pip: Gelişmiş Metin İşleme (Eleştiri 2, 3, 5, 6) ---
        # NLTK ile daha verimli ve anlamlı işlemler.

        if analysis_type == 'keywords':
            # Metni temizle: Noktalama işaretlerini kaldır ve küçük harfe çevir
            # (re.sub ile tek geçiş, daha verimli)
            cleaned_text = re.sub(r'[^\w\s]', '', input_data).lower()
            
            # NLTK ile kelime belirteçleme (daha doğru kelime ayırma)
            words = word_tokenize(cleaned_text)
            
            # İngilizce ve Türkçe durak kelimeleri birleştir (daha iyi anahtar kelime tespiti için)
            stop_words = set(stopwords.words('english') + stopwords.words('turkish'))
            
            # Kısa kelimeleri (anlamsız olabilir) ve durak kelimeleri filtrele
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            
            if not filtered_words:
                action_result["analysis_output"] = {
                    "type": "Anahtar Kelime Analizi",
                    "extracted_keywords": [],
                    "note": "Metinde anlamlı anahtar kelime bulunamadı (durak kelimeler ve kısa kelimeler filtrelendikten sonra)."
                }
            else:
                word_counts = Counter(filtered_words)
                # En sık geçen ilk 7 kelimeyi anahtar kelime olarak al
                most_common_words = [word for word, count in word_counts.most_common(7)]
                action_result["analysis_output"] = {
                    "type": "Anahtar Kelime Analizi",
                    "extracted_keywords": most_common_words,
                    "note": (
                        "NLTK'nin `word_tokenize` fonksiyonu kullanılarak kelime belirteçleme yapılmış, "
                        "noktalama işaretleri çıkarılmış, küçük harfe çevrilmiş ve "
                        "İngilizce/Türkçe durak kelimeler filtrelenmiştir. "
                        "Kelime frekansına göre en sık geçen kelimeler belirlenmiştir."
                    )
                }
        elif analysis_type == 'summary':
            # NLTK'nin `sent_tokenize` fonksiyonu ile cümlelere ayırma (daha doğru cümle sınırları)
            sentences = sent_tokenize(input_data)
            
            num_sentences_for_summary = 3 # Özet için ilk N cümle (parametre olarak da alınabilir)
            
            if len(sentences) == 0:
                simulated_summary = "Özetlenecek cümle bulunamadı."
            elif len(sentences) <= num_sentences_for_summary:
                simulated_summary = " ".join(sentences)
            else:
                simulated_summary = " ".join(sentences[:num_sentences_for_summary])
            
            action_result["analysis_output"] = {
                "type": "Kısa Özetleme",
                "summary": simulated_summary.strip(),
                "note": (
                    "NLTK'nin `sent_tokenize` fonksiyonu kullanılarak metin cümlelere ayrılmıştır. "
                    f"İlk {num_sentences_for_summary} cümle basit bir özet olarak döndürülmüştür. "
                    "Bu yöntem, karmaşık bir anlamsal özetleyici olmamasına rağmen, cümle sınırlarını "
                    "daha doğru belirleyerek çıktının okunabilirliğini artırır."
                )
            }
        else:
            action_result["analysis_output"] = {
                "type": "Geçersiz Analiz Tipi",
                "message": f"Geçersiz 'analysis_type' belirtildi: '{analysis_type}'. "
                           "Desteklenen tipler: 'keywords', 'summary'."
            }
        action_result["action_performed"] = "Belirtilen veri üzerinde analiz denemesi yapıldı."

    except Exception as e:
        # --- Hata Yönetimi (Eleştiri 7) ---
        # Beklenmedik hataları yakala ve kullanıcıya bilgi ver.
        action_result["error"] = f"Analiz sırasında beklenmeyen bir hata oluştu: {str(e)}"
        action_result["action_performed"] = "Analiz işlemi hata nedeniyle tamamlanamadı."

    return action_result

TOOL_NAME: information_analysis_and_synthesis