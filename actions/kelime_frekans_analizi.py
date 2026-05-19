import collections
import re
from typing import List, Dict, Set, Any

def validate_parameters(parameters: Dict[str, Any]) -> None:
    """
    Parametreleri doğrular ve hataları yükseltir.
    
    Parameters:
    ----------
    parameters : dict
        İşlem için gerekli parametreleri içeren bir sözlük.
        
    Raises:
    -------
    ValueError
        Gerekli parametreler eksikse veya geçersizse.
    TypeError
        Parametrelerin türleri yanlışsa.
    """
    if not isinstance(parameters, dict):
        raise TypeError("Parametreler bir sözlük olmalıdır.")
    if 'text_list' not in parameters:
        raise ValueError("Parametreler 'text_list' anahtarını içermelidir.")

    text_list = parameters['text_list']
    top_n = parameters.get('top_n', 5)
    min_word_length = parameters.get('min_word_length', 1)
    # Stopwords burada sadece doğrulama için alınır, asıl dönüşüm run_action içinde set'e yapılır.
    stopwords_param = parameters.get('stopwords', [])

    if not isinstance(text_list, list) or not all(isinstance(item, str) for item in text_list):
        raise TypeError("'text_list' dizelerden oluşan bir liste olmalıdır.")
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError(f"'top_n' pozitif bir tam sayı olmalıdır. Alınan değer: {top_n}")
    if not isinstance(min_word_length, int) or min_word_length < 0:
        raise ValueError(f"'min_word_length' negatif olmayan bir tam sayı olmalıdır. Alınan değer: {min_word_length}")
    if not isinstance(stopwords_param, list) or not all(isinstance(item, str) for item in stopwords_param):
        raise TypeError("'stopwords' dizelerden oluşan bir liste olmalıdır.")

def preprocess_text(text: str, min_word_length: int, stopwords: Set[str]) -> List[str]:
    """
    Verilen metni ön işler: küçük harfe çevirir, kelimelere ayırır,
    minimum kelime uzunluğuna ve durak kelimelere göre filtreler.

    Parameters:
    ----------
    text : str
        İşlenecek metin.
    min_word_length : int
        En az bu uzunluktaki kelimeler sayılır.
    stopwords : set
        Analizden çıkarılacak durak kelimelerin kümesi.

    Returns:
    -------
    List[str]
        Filtrelenmiş ve ön işlenmiş kelimelerin listesi.
    """
    # Metni küçük harfe çevir ve kelimelere ayır.
    # re.findall(r'\b\w+\b', ...) sadece harf ve rakamlardan oluşan kelimeleri bulur
    # Python'da \w, Unicode karakterler için de genellikle geçerlidir (harfler, rakamlar, alt çizgi).
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Kelime uzunluğunu ve durak kelime kontrolünü uygula
    filtered_words = [
        word for word in words 
        if len(word) >= min_word_length and word not in stopwords
    ]
    return filtered_words

def run_action(parameters: Dict[str, Any]) -> Dict[str, int]:
    """
    Verilen metin listesindeki kelime frekanslarını analiz eder ve en sık geçen kelimeleri döndürür.
    Bu, metin analizi, anahtar kelime çıkarma veya temel veri madenciliği için yararlı bir yetenektir.

    Parameters:
    ----------
    parameters : dict
        İşlem için gerekli parametreleri içeren bir sözlük. Şunları içermesi beklenir:
        - 'text_list' (list): Analiz edilecek metin dizelerinin listesi.
        - 'top_n' (int, optional): Döndürülecek en sık kelime sayısı. Varsayılan değer 5'tir.
        - 'min_word_length' (int, optional): En az bu uzunluktaki kelimeler sayılır. Varsayılan değer 1'dir.
        - 'stopwords' (list, optional): Analizden çıkarılacak kelimelerin listesi (ör. "ve", "bir", "bu").
                                        Varsayılan olarak boş bir listedir.

    Returns:
    -------
    dict
        En sık geçen kelimelerin ve bunların frekanslarının bir sözlüğü.
        Örnek: {'kelime1': 10, 'kelime2': 7, ...}

    Raises:
    -------
    ValueError
        Gerekli parametreler eksikse veya geçersizse.
    TypeError
        Parametrelerin türleri yanlışsa.
    """
    # 1. Parametre Doğrulaması
    validate_parameters(parameters)

    # 2. Parametreleri Çıkar ve Hazırla
    text_list: List[str] = parameters['text_list']
    top_n: int = parameters.get('top_n', 5)
    min_word_length: int = parameters.get('min_word_length', 1)
    # Stopwords listesini performansı artırmak için bir kümeye (set) dönüştür
    stopwords: Set[str] = {word.lower() for word in parameters.get('stopwords', [])}

    all_filtered_words: List[str] = []
    
    # 3. Metinleri Ön İşle ve Kelimeleri Topla
    for text in text_list:
        try:
            processed_words = preprocess_text(text, min_word_length, stopwords)
            all_filtered_words.extend(processed_words)
        except Exception as e:
            # Metin işleme sırasında oluşabilecek beklenmedik hataları yakala
            print(f"Uyarı: Metin işlenirken bir hata oluştu: '{text[:50]}...'. Hata: {e}")
            # Hatanın uygulamayı tamamen durdurmamasını sağlamak için devam et
            continue 

    # 4. Kelime Frekanslarını Hesapla
    word_counts = collections.Counter(all_filtered_words)

    # 5. En Sık Geçen Kelimeleri Al
    most_common = word_counts.most_common(top_n)

    return {word: count for word, count in most_common}

TOOL_NAME = 'kelime_frekans_analizi'