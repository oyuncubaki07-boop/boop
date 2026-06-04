import re # Düzenli ifade (regex) doğrulaması için

# --- Yardımcı Fonksiyonlar (Helper Functions) ---

def _log_warning(message: str):
    """
    Hata ve uyarı mesajlarını konsola yazan basit bir yardımcı fonksiyon.
    Gerçek uygulamalarda 'logging' modülü kullanılmalı ve uygun log seviyeleri (WARN, ERROR) ayarlanmalıdır.
    """
    print(f"UYARI: {message}")

def _get_string_param(parameters: dict, key: str, default: str, 
                      min_length: int = 0, max_length: int = None, 
                      allowed_chars_regex: str = None, 
                      param_display_name: str = "string parametresi") -> str:
    """
    Sözlükten güvenli bir şekilde string parametresi okur, tipini doğrular 
    ve ek uzunluk/karakter kısıtlamaları uygular.
    
    Eleştiriler:
    - #1 (Kapsamlı Girdi Doğrulama Eksikliği) için `min_length`, `max_length` ve `allowed_chars_regex` eklenmiştir.
    - #2 (Potansiyel Enjeksiyon Riski) için `allowed_chars_regex` temel bir koruma katmanı sağlar.
    - #6 (Kod Tekrarı ve Soyutlama Eksikliği) için bu fonksiyon soyutlama sağlar.
    """
    value = parameters.get(key, default) # İlk olarak default ile değeri al

    # Tip Doğrulama
    if not isinstance(value, str):
        _log_warning(f"Parametre '{key}' ({param_display_name}) geçersiz tipte. "
                     f"Varsayılan değer '{default}' kullanılıyor. Gelen değer: {value!r}")
        value = default # Geçersiz tipte ise varsayılan değere dön

    # Uzunluk Doğrulama (Kritik #1)
    if len(value) < min_length:
        _log_warning(f"Parametre '{key}' ({param_display_name}) minimum {min_length} karakterden kısa. "
                     f"Varsayılan değer '{default}' kullanılıyor. Gelen değer: '{value}'")
        return default
    
    if max_length is not None and len(value) > max_length:
        _log_warning(f"Parametre '{key}' ({param_display_name}) maksimum {max_length} karakterden uzun. "
                     f"Varsayılan değer '{default}' kullanılıyor. Gelen değer: '{value[:max_length]}...'")
        return default

    # Karakter Doğrulama (Kritik #1, #2 - Potansiyel Enjeksiyon Riski azaltma)
    # Bu, temel bir enjeksiyon koruma katmanıdır. Kapsamlı koruma için, 
    # girdinin kullanılacağı yere göre ek sanitasyon/kaçış işlemleri uygulanması ZORUNLUDUR.
    if allowed_chars_regex:
        if not re.fullmatch(allowed_chars_regex, value):
            _log_warning(f"Parametre '{key}' ({param_display_name}) izin verilmeyen karakterler içeriyor. "
                         f"Varsayılan değer '{default}' kullanılıyor. Gelen değer: '{value}'")
            return default
            
    return value

def _get_int_param(parameters: dict, key: str, default: int, 
                   min_value: int = None, max_value: int = None, 
                   param_display_name: str = "sayısal parametre") -> int:
    """
    Sözlükten güvenli bir şekilde integer parametresi okur, tipini dönüştürür 
    ve aralık doğrulaması uygular. Hata durumlarını loglar.
    
    Eleştiriler:
    - #1 (Kapsamlı Girdi Doğrulama Eksikliği) için `min_value` ve `max_value` eklenmiştir.
    - #5 (Hata Yönetiminde Loglama Eksikliği) için `_log_warning` kullanılır.
    - #6 (Kod Tekrarı ve Soyutlama Eksikliği) için bu fonksiyon soyutlama sağlar.
    """
    raw_value = parameters.get(key) # İlk başta varsayılan değer olmadan al
    
    int_value = default
    try:
        # Değer string, int veya başka bir tipte olabilir. None kontrolü yapılır.
        if raw_value is not None:
            int_value = int(raw_value)
        else: # Parametre yoksa veya None ise varsayılanı kullan
            int_value = default
    except (ValueError, TypeError): # String'den int'e dönüşüm hatası veya tipi uyumsuzluk
        _log_warning(f"Parametre '{key}' ({param_display_name}) geçersiz bir sayısal değere sahip. "
                     f"Varsayılan değer {default} kullanılıyor. Gelen değer: {raw_value!r}")
        return default # Geçersiz ise varsayılanı döndür

    # Değer Aralığı Doğrulama (Kritik #1)
    if min_value is not None and int_value < min_value:
        _log_warning(f"Parametre '{key}' ({param_display_name}) minimum {min_value} değerinden düşük. "
                     f"Varsayılan değer {default} kullanılıyor. Gelen değer: {int_value}")
        return default
        
    if max_value is not None and int_value > max_value:
        _log_warning(f"Parametre '{key}' ({param_display_name}) maksimum {max_value} değerinden yüksek. "
                     f"Varsayılan değer {default} kullanılıyor. Gelen değer: {int_value}")
        return default
        
    return int_value

def _get_boolean_param(parameters: dict, key: str, default: bool, 
                       true_values: tuple = ('true', '1', 'yes', 'on'), 
                       param_display_name: str = "boolean parametresi") -> bool:
    """
    Sözlükten güvenli bir şekilde boolean parametresi okur ve genişletilmiş dönüşüm uygular.
    
    Eleştiriler:
    - #3 (Boolean Yorumlama Sınırlılığı) için `true_values` tuşu ile genişletilmiş kontrol sağlar.
    - #6 (Kod Tekrarı ve Soyutlama Eksikliği) için bu fonksiyon soyutlama sağlar.
    - #8 (Boolean Dönüşümünün Daha Pythonik Yaklaşımı) için `in true_values` kullanılır.
    """
    raw_value = parameters.get(key)
    
    if raw_value is None: # Parametre yoksa veya None ise varsayılanı kullan
        return default

    # String olmayan değerleri string'e dönüştür ve küçük harfe çevir
    # (örn: raw_value bir int (1) veya bool (True) olabilir)
    if not isinstance(raw_value, str):
        raw_value = str(raw_value)
    
    normalized_value = raw_value.lower()

    if normalized_value in true_values:
        return True
    # Yaygın false değerleri için kontrol
    elif normalized_value in ('false', '0', 'no', 'off'):
        return False
    else:
        _log_warning(f"Parametre '{key}' ({param_display_name}) geçerli bir boolean değeri değil. "
                     f"Varsayılan değer {default} kullanılıyor. Gelen değer: '{raw_value}'")
        return default

def run_action(parameters: dict) -> str:
    """
    Bu fonksiyon, 'parameters' sözlüğünden güvenli bir şekilde değer okuma
    ve bu değerleri uygun tiplere dönüştürme yeteneğini gösterir.
    Kritikte belirtilen güvenlik, performans ve sürdürülebilirlik konuları
    yardımcı fonksiyonlar aracılığıyla ele alınarak daha sağlam ve sürdürülebilir bir yapı sunar.
    """

    # --- Parametreleri Güvenli ve Doğrulanmış Bir Şekilde Oku ---

    # 1. String parametre okuma (Kritik #1, #2, #6 ele alınmıştır)
    #    'task_name' için: minimum 3, maksimum 50 karakter, sadece alfanümerik, boşluk, tire, alt çizgiye izin ver.
    task_name = _get_string_param(
        parameters, 'task_name', 'default_task', 
        min_length=3, max_length=50, 
        allowed_chars_regex=r"^[a-zA-Z0-9\s\-_]+$", # Sadece harf, rakam, boşluk, tire, alt çizgiye izin verir
        param_display_name="görev adı"
    )
    # Kritik #2 (Potansiyel Enjeksiyon Riski) hakkında ek not:
    # Yukarıdaki regex basit bir koruma sağlar. Ancak 'task_name' değeri
    # bir veritabanı sorgusunda, kabuk komutunda veya HTML çıktısında
    # kullanılacaksa, ilgili bağlama özel (SQL enjeksiyonu, XSS vb. için) 
    # daha kapsamlı sanitasyon veya kaçış karakterleri uygulanması ZORUNLUDUR.

    # 2. Sayısal (Integer) parametre okuma (Kritik #1, #4, #5, #6 ele alınmıştır)
    #    'timeout' için: varsayılan 60 saniye, minimum 10, maksimum 300 saniye.
    #    Kritik #4 (Varsayılan Değerlerin Güvenlik Uyumluluğu) ele alınmıştır:
    #    Minimum 10 saniye gibi bir alt sınır, sistemin DoS saldırılarına karşı
    #    direncini artırmaya yardımcı olabilir, zira çok kısa zaman aşımları 
    #    kaynakların hızla tüketilmesine neden olabilir. Varsayılan ve aralıklar 
    #    sistem gereksinimlerine ve güvenlik politikalarına göre ayarlanmalıdır.
    timeout_seconds = _get_int_param(
        parameters, 'timeout', 60, # Varsayılan değer
        min_value=10, max_value=300, # Güvenlik ve performans için aralık kısıtlamaları
        param_display_name="zaman aşımı süresi"
    )
    
    # 3. Boolean parametre okuma (Kritik #3, #6, #8 ele alınmıştır)
    #    'is_urgent' için: 'true', '1', 'yes', 'on' değerlerini True olarak yorumlar.
    is_urgent = _get_boolean_param(
        parameters, 'is_urgent', False, # Varsayılan değer
        true_values=('true', '1', 'yes', 'on'), # Kabul edilecek True değerleri
        param_display_name="acil durum"
    )

    # Okunan ve işlenen parametrelerle bir eylem simülasyonu
    status_message = (
        f"Görev: '{task_name}' başlatılıyor. "
        f"Aciliyet: {'Yüksek' if is_urgent else 'Normal'}. "
        f"Zaman aşımı: {timeout_seconds} saniye."
    )

    # Gerçek bir uygulamada, `task_name`, `timeout_seconds`, `is_urgent`
    # gibi değerler kullanılarak belirli bir işlem (örneğin: bir arka plan görevi başlatma, 
    # bir API çağrısı yapma veya veritabanı işlemi) gerçekleştirilirdi.

    return status_message

TOOL_NAME: safe_parameter_reader