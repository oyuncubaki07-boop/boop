import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
# heapq doğrudan kullanılmasa da, kritik bir kütüphane olmadığı için listede tutulabilir.
# Ancak bu uygulamada sorted() fonksiyonu yeterli gelmektedir.

def run_action(parameters):
    """
    Bu fonksiyon, metin özetleme (text summarization) yeteneğini simüle eder.
    Verilen bir metni, cümle skorlama (sentence scoring) yöntemi kullanarak
    belirli bir kelime sayısına yaklaşık olarak özetlemeye çalışır.
    Türkçe metinler için optimize edilmiştir.

    Args:
        parameters (dict): Aşağıdaki anahtarları içermesi beklenen bir sözlük:
            'text_to_summarize' (str): Özetlenecek metin.
            'target_word_count' (int, optional): İstenen özetin yaklaşık kelime sayısı. Varsayılan 50.

    Returns:
        dict: İşlemin sonucunu ve özetlenmiş metni içeren bir sözlük.
              Hata durumunda 'status': 'error' ve 'message' iletilir.
              Başarı durumunda 'status': 'success', 'skill': 'text_summarization',
              'summarized_text' ve 'message' iletilir.
    """
    text_to_summarize = parameters.get('text_to_summarize')
    target_word_count = parameters.get('target_word_count', 50)

    # --- Parametre Doğrulama ---
    if not isinstance(text_to_summarize, str) or not text_to_summarize.strip():
        return {
            "status": "error",
            "message": "Özetlenecek metin ('text_to_summarize') parametresi eksik veya geçersiz."
        }
    if not isinstance(target_word_count, int) or target_word_count <= 0:
        return {
            "status": "error",
            "message": "Hedef kelime sayısı ('target_word_count') parametresi geçersiz. Pozitif bir tam sayı olmalı."
        }

    # --- NLTK Verilerini İndirme (Gerekirse) ---
    # Bu adımlar, NLTK kaynaklarının mevcut olup olmadığını kontrol eder
    # ve yoksa indirir. Gerçek bir uygulamada bu indirme bir kerelik olmalıdır
    # veya deployment sürecine dahil edilmelidir.
    try:
        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
    except LookupError:
        try:
            # quiet=True ile indirme mesajlarını konsolda göstermeyiz
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            # İndirme hatası durumunda kullanıcıya bilgi ver
            return {
                "status": "error",
                "message": f"NLTK kaynakları indirilemedi: {e}. Lütfen internet bağlantınızı kontrol edin veya NLTK'yi manuel olarak yapılandırın (pip install nltk; python -c 'import nltk; nltk.download(\"punkt\"); nltk.download(\"stopwords\")')."
            }

    original_words_list = word_tokenize(text_to_summarize, language='turkish')
    
    if not original_words_list:
        return {
            "status": "success",
            "skill": "text_summarization",
            "original_text_length_words": 0,
            "summarized_text_length_words": 0,
            "summarized_text": "",
            "message": "Boş metin özetlendi."
        }
    
    # Eğer metin zaten hedef kelime sayısından kısaysa, tamamını döndür
    if len(original_words_list) <= target_word_count:
        return {
            "status": "success",
            "skill": "text_summarization",
            "original_text_length_words": len(original_words_list),
            "summarized_text_length_words": len(original_words_list),
            "summarized_text": text_to_summarize,
            "message": "Metin zaten hedef uzunluktan kısa veya eşit. Tamamı özet olarak döndürüldü."
        }

    # --- Metin İşleme ve Cümle Skorlama ---
    sentences = sent_tokenize(text_to_summarize, language='turkish')
    stop_words = set(stopwords.words("turkish"))

    # Kelime frekanslarını hesapla
    word_frequencies = {}
    for word in original_words_list: # original_words_list zaten tokenize edilmiş kelimeler içerir
        word_lower = word.lower()
        if word_lower.isalnum() and word_lower not in stop_words:
            word_frequencies[word_lower] = word_frequencies.get(word_lower, 0) + 1

    # Maksimum frekansı bul (normalization için)
    # Eğer hiç anlamlı kelime bulunamazsa max_frequency 1 olarak kalır, sıfıra bölmeyi önler.
    max_frequency = max(word_frequencies.values()) if word_frequencies else 1

    # Kelime frekanslarını normalize et
    for word_lower in word_frequencies:
        word_frequencies[word_lower] = word_frequencies[word_lower] / max_frequency

    # Cümle skorlarını hesapla
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        # Cümlenin kendi kelimelerini tokenize et
        for word_in_sentence in word_tokenize(sentence.lower(), language='turkish'):
            if word_in_sentence in word_frequencies:
                # Cümle skoruna kelimenin normalize edilmiş frekansını ekle
                sentence_scores[i] = sentence_scores.get(i, 0) + word_frequencies[word_in_sentence]

    # Skorlu cümleleri sırala (yüksek skordan düşüğe)
    # item[0] cümle indeksi, item[1] skordur.
    sorted_sentences_by_score = sorted(sentence_scores.items(), key=lambda item: item[1], reverse=True)

    # --- Özetleme ---
    # Hedef kelime sayısına yaklaşana kadar en yüksek skorlu cümleleri seç
    selected_sentence_info = [] # (original_index, sentence_text) çiftlerini saklar
    current_word_count = 0
    
    # Eğer hiç skorlu cümle yoksa (örneğin sadece stopwords içeren metin)
    if not sorted_sentences_by_score:
        # Bu durumda summarized_text boş kalır ve aşağıdaki mesaj bunu ele alır.
        pass

    for original_idx, _score in sorted_sentences_by_score:
        sentence = sentences[original_idx]
        sentence_word_count = len(word_tokenize(sentence, language='turkish'))

        # Eğer bu cümleyi eklemek hedefi çok aşmayacaksa ekle
        # veya henüz hiçbir cümle eklenmemişse (ilk cümleyi her zaman ekle)
        # 1.5 katsayısı, esnek bir üst sınır sağlar.
        if (current_word_count + sentence_word_count <= target_word_count * 1.5) or not selected_sentence_info:
            selected_sentence_info.append((original_idx, sentence))
            current_word_count += sentence_word_count
        
        # Hedef kelime sayısına ulaşıldığında veya yaklaşıldığında dur
        # En az bir cümle seçilmiş olmalı ki boş özet dönmesin
        if current_word_count >= target_word_count and len(selected_sentence_info) > 0:
            break
    
    # Seçilen cümleleri orijinal metindeki sırasına göre düzenle
    # Bu, özetin daha okunabilir olmasını sağlar.
    selected_sentence_info.sort(key=lambda item: item[0]) # Sadece indekslere göre sırala

    final_summary_parts = [sentence_text for _idx, sentence_text in selected_sentence_info]
    summarized_text = " ".join(final_summary_parts)

    final_summarized_words_list = word_tokenize(summarized_text, language='turkish')


    # --- Sonuç Mesajı Oluşturma ---
    message = (f"Metin başarıyla özetlendi. Orijinal metnin {len(original_words_list)} kelimesinden, "
               f"{len(final_summarized_words_list)} kelimelik yaklaşık bir özet oluşturuldu "
               f"(hedef ~{target_word_count} kelimeye yakın). "
               f"Cümle skorlama yöntemi kullanıldı.")
    
    if len(final_summarized_words_list) == 0 and len(original_words_list) > 0:
        message = "Metin çok kısaydı, sadece stopwords içeriyordu veya anlamlı cümleler bulunamadı. Boş özet döndürüldü."
    elif len(final_summarized_words_list) == 0 and len(original_words_list) == 0:
        message = "Boş metin özetlendi." # Bu durum yukarıda da yakalanıyor, ama tutarlılık için tekrar.

    return {
        "status": "success",
        "skill": "text_summarization",
        "original_text_length_words": len(original_words_list),
        "summarized_text_length_words": len(final_summarized_words_list),
        "summarized_text": summarized_text,
        "message": message
    }