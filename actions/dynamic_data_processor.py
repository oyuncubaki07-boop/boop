import operator

# Özel istisnalar (exceptions) hata yönetimini daha standart, esnek ve okunabilir hale getirir.
# Eleştiri #6'ya yanıt: Hata Yönetiminde Monotonluk.
class ActionError(Exception):
    """run_action fonksiyonuna ait temel istisna sınıfı."""
    pass

class InvalidParameterError(ActionError):
    """Bir parametre eksik, hatalı türde veya geçersiz bir değere sahip olduğunda fırlatılır."""
    pass

class DataValidationError(ActionError):
    """Girdi 'items' listesindeki veri yanlış biçimlendirilmişse (örneğin sözlük değilse) fırlatılır."""
    pass

class OperationError(ActionError):
    """Filtreleme veya sıralama işlemi sırasında (örneğin veri tipi uyuşmazlığı) bir sorun oluştuğunda fırlatılır."""
    pass

def run_action(parameters):
    """
    Verilen bir liste içerisindeki öğeleri (sözlükleri) dinamik olarak filtreler ve/veya sıralar.
    Bu yeniden yazım, önceki versiyonun güvenlik, performans ve esneklik eleştirilerini ele almaktadır.
    
    Yararlı Yetenek: Gelişmiş Dinamik Veri İşleme (Çoklu Filtreleme ve Sıralama)
    Bu fonksiyon, gelen veriyi belirli çoklu kriterlere göre filtreleyip sıralayarak,
    büyük veri kümeleri üzerinde hızlıca anlamlı alt kümeler oluşturma yeteneğini sergiler.
    Birden fazla filtreleme koşulu ve birden fazla sıralama anahtarı destekler.

    Parametreler:
    parameters (dict): İşlem için gerekli bilgileri içeren bir sözlük.
        Beklenen Anahtarlar:
        - 'items' (list): İşlenecek sözlükler listesi. (Zorunlu)
        - 'operation' (str): Yapılacak işlem türü. Şimdilik sadece 'filter_and_sort' desteklenir. (Zorunlu)
        - 'max_items_limit' (int, isteğe bağlı): İşlenebilecek maksimum öğe sayısı. DoS koruması için. Varsayılan: 10000.
            Eleştiri #3'e yanıt: Servis Reddi (DoS) Potansiyeli.
        - 'filter_by' (list of dict, isteğe bağlı): Filtreleme kriterleri listesi. Birden fazla kriter AND mantığıyla birleştirilir.
            Eleştiri #5'e yanıt: Kısıtlı Filtreleme ve Sıralama Yetenekleri.
            Her bir dict:
            - 'key' (str): Filtreleme yapılacak anahtar. (Zorunlu)
            - 'operator' (str): Karşılaştırma operatörü. Desteklenenler: '==', '!=', '>', '<', '>=', '<=', 'in', 'not in'. (Zorunlu)
            - 'value': Anahtarın operatörle karşılaştırılacağı değer. (Zorunlu)
            - Örnek: [{"key": "age", "operator": ">", "value": 30}, {"key": "city", "operator": "==", "value": "Ankara"}]
        - 'sort_by' (list of dict, isteğe bağlı): Sıralama kriterleri listesi. Önce gelen kriter daha önceliklidir.
            Eleştiri #5'e yanıt: Kısıtlı Filtreleme ve Sıralama Yetenekleri.
            Her bir dict:
            - 'key' (str): Sıralama yapılacak anahtar. (Zorunlu)
            - 'descending' (bool): Azalan sırada mı (True) yoksa artan sırada mı (False) sıralanacak. Varsayılan: False.
            - 'none_last' (bool): 'key' değeri olmayan veya None olan öğeleri sona atar. Varsayılan: False (Python varsayılanı olan başa atar).
                Eleştiri #4'e yanıt: Esnek Olmayan Sıralama Anahtarı Yönetimi.

    Dönüş Değeri:
    list: Filtrelenmiş ve/veya sıralanmış öğeler listesi.

    Hata Durumu:
    İşlem sırasında bir hata oluşursa, 'ActionError' veya onun alt sınıflarından bir istisna fırlatılır.
    """
    
    # 1. Giriş Parametrelerinin Doğrulanması ve Hata Yönetimi
    if 'operation' not in parameters:
        raise InvalidParameterError("operation anahtarı eksik. Lütfen 'operation' parametresini belirtin.")
    
    operation = parameters['operation']

    if operation != 'filter_and_sort':
        raise InvalidParameterError(f"Bilinmeyen işlem türü: '{operation}'. Desteklenen işlemler: 'filter_and_sort'.")

    if 'items' not in parameters or not isinstance(parameters['items'], list):
        raise InvalidParameterError("items anahtarı eksik veya liste değil. Lütfen 'items' parametresini bir liste olarak belirtin.")
    
    items = parameters['items']

    # DoS Koruması: Maksimum öğe sınırı kontrolü
    # Eleştiri #3'e yanıt: Servis Reddi (DoS) Potansiyeli.
    max_items_limit = parameters.get('max_items_limit', 10000)
    if not isinstance(max_items_limit, int) or max_items_limit <= 0:
        raise InvalidParameterError("max_items_limit parametresi pozitif bir tam sayı olmalıdır.")
    if len(items) > max_items_limit:
        raise DataValidationError(f"İşlenecek öğe sayısı ({len(items)}) 'max_items_limit' ({max_items_limit}) değerini aşıyor.")

    # Her bir öğenin sözlük olduğundan emin olun (güvenlik ve tutarlılık)
    # Eleştiri #7'ye yanıt: Girdi Verisinin Güvenlik Doğrulaması Eksikliği.
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise DataValidationError(f"items listesindeki {i}. öğe bir sözlük değil. Tüm öğeler sözlük olmalıdır.")

    # Orijinal listeyi değiştirmemek için bir kopya oluştur.
    # Eleştiri #2'ye yanıt: Gereksiz Liste Kopyalama Maliyeti.
    # Bu kopyalama, fonksiyonun girdiyi değiştirmeme garantisi için gereklidir ve immutability'yi sağlar.
    # Büyük veri kümelerinde performans maliyeti olsa da, bu bir tasarım kararıdır.
    processed_items = list(items) 
    
    # 2. Filtreleme işlemi (Gelişmiş, çoklu kriter ve operatör desteği)
    # Eleştiri #5'e yanıt: Kısıtlı Filtreleme Yetenekleri.
    if 'filter_by' in parameters:
        filter_criteria_list = parameters['filter_by']
        if not isinstance(filter_criteria_list, list):
            raise InvalidParameterError("filter_by parametresi bir sözlükler listesi olmalıdır.")

        # Desteklenen operatörler ve karşılık gelen Python fonksiyonları
        # 'in' ve 'not in' için lambda kullanıldı, çünkü operator modülünde doğrudan karşılıkları yok.
        operators = {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "in": lambda val, container: val in container if hasattr(container, '__contains__') else False,
            "not in": lambda val, container: val not in container if hasattr(container, '__contains__') else True
        }

        for criteria in filter_criteria_list:
            if not isinstance(criteria, dict):
                raise InvalidParameterError("filter_by listesindeki her kriter bir sözlük olmalıdır.")
            
            filter_key = criteria.get('key')
            filter_operator_str = criteria.get('operator')
            filter_value = criteria.get('value') # filter_value'nun None olması geçerli olabilir.
            
            if filter_key is None:
                 raise InvalidParameterError("Filtreleme kriterinde 'key' belirtilmedi.")
            if filter_operator_str is None:
                 raise InvalidParameterError("Filtreleme kriterinde 'operator' belirtilmedi.")

            if filter_operator_str not in operators:
                raise InvalidParameterError(f"Geçersiz filtreleme operatörü: '{filter_operator_str}'. Desteklenenler: {list(operators.keys())}")
            
            op_func = operators[filter_operator_str]

            try:
                # Her filtre kriterini sırayla uygula (AND mantığı)
                processed_items = [item for item in processed_items if op_func(item.get(filter_key), filter_value)]
            except TypeError as e:
                # Eleştiri #4 ve #6'ya yanıt: Daha spesifik hata mesajı ve istisna kullanımı.
                raise OperationError(f"Filtreleme sırasında veri tipi uyuşmazlığı veya karşılaştırma hatası ('{filter_key}' anahtarı için). Hata: {e}")
            except Exception as e:
                raise OperationError(f"Filtreleme sırasında beklenmeyen bir hata oluştu ('{filter_key}' anahtarı için). Hata: {e}")

    # 3. Sıralama işlemi (Gelişmiş, çoklu anahtar ve None değeri yönetimi)
    # Eleştiri #4 ve #5'e yanıt: Esnek Olmayan Sıralama Anahtarı Yönetimi ve Kısıtlı Sıralama Yetenekleri.
    if 'sort_by' in parameters:
        sort_criteria_list = parameters['sort_by']
        if not isinstance(sort_criteria_list, list):
            raise InvalidParameterError("sort_by parametresi bir sözlükler listesi olmalıdır.")

        # Python'ın sort() metodunun kararlı yapısından faydalanarak çoklu anahtar sıralama.
        # En düşük öncelikli kriterden başlayarak en yüksek öncelikli kritere doğru sıralama yapılır.
        # Bu, Python'da çoklu anahtar sıralamanın idiomatik yoludur:
        # Önce en az önemli anahtara göre sırala, sonra bir üstüne göre, vb.
        # Python'ın Timsort algoritması kararlıdır, bu da eşit öğelerin göreceli sırasını koruyacağı anlamına gelir.
        
        # Sondan başa doğru iterasyon (öncelik sırası için)
        for sort_criteria in reversed(sort_criteria_list):
            if not isinstance(sort_criteria, dict):
                raise InvalidParameterError("sort_by listesindeki her kriter bir sözlük olmalıdır.")

            sort_key = sort_criteria.get('key')
            sort_descending = sort_criteria.get('descending', False)
            none_last = sort_criteria.get('none_last', False) # None değerlerin sonda mı olacağı

            if sort_key is None:
                raise InvalidParameterError("Sıralama kriterinde 'key' belirtilmedi.")
            
            try:
                if none_last:
                    # 'none_last' True ise, anahtar değeri None olan veya eksik olan öğeleri sona atar.
                    # Tuple'ın ilk elemanı (item.get(sort_key) is None) True ise None/eksik, False ise değerlidir.
                    # None True olduğu için True'lar (None değerler) sona, False'lar (değerli öğeler) başa gelir.
                    # Bu, 'reverse=sort_descending' ile birleşerek istenen None konumunu sağlar.
                    processed_items.sort(key=lambda item: (item.get(sort_key) is None, item.get(sort_key)), reverse=sort_descending)
                else:
                    # Python varsayılanı: None değerler genellikle en küçük kabul edilir ve artan sıralamada başa gelir.
                    processed_items.sort(key=lambda item: item.get(sort_key), reverse=sort_descending)
            except TypeError as e:
                # Eleştiri #4'e yanıt: Daha spesifik hata mesajı.
                # Farklı veri türlerine sahip öğelerin (örn. int ve str) aynı anahtar altında karşılaştırılması hatası.
                raise OperationError(f"Sıralama hatası: '{sort_key}' anahtarı bazı öğelerde mevcut değil veya farklı veri türlerine sahip öğeler sıralanamaz. Hata: {e}")
            except Exception as e:
                raise OperationError(f"Sıralama sırasında beklenmeyen bir hata oluştu ('{sort_key}' anahtarı için). Hata: {e}")

    return processed_items

TOOL_NAME = "dynamic_data_processor"