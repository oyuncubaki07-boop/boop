import random

# ELESTIRI 4 & 7 (Performans ve Veri Esnekliği):
# Yetenek listesi, fonksiyonun her çağrılışında yeniden oluşturulmak yerine
# modül seviyesinde bir sabit olarak tanımlanmıştır. Bu, performansı artırır.
# Veri esnekliği için hala hardcoded olsa da, buradan kolayca değiştirilebilir.
# Gelecekte daha fazla esneklik için JSON/YAML gibi harici bir yapılandırma dosyasına
# veya bir veritabanına taşınabilir.
USEFUL_SKILLS = [
    "Programlama (Python)",
    "Yabancı Dil Öğrenimi (İngilizce)",
    "Eleştirel Düşünme",
    "Problem Çözme",
    "Veri Analizi",
    "Topluluk Önünde Konuşma",
    "Finansal Okuryazarlık",
    "Proje Yönetimi",
    "Etkili İletişim"
]

# ELESTIRI 3 (Pip - Bağımlılık Yönetimi):
# `random` kütüphanesi kullanıldığı için `import random` eklenmiştir.
# Daha karmaşık projelerde, bu tür bağımlılıkların bir `requirements.txt` dosyasında listelenmesi gerekir.
# (Örn: `pip install -r requirements.txt`)

def run_action(parameters):
    """
    Kullanıcının yararlı bir yetenek seçmesini ve seçilen yeteneği bildirmesini simüle eder.
    Seçim, `parameters` aracılığıyla bir tercih belirtilmişse bu tercihe göre yapılır,
    aksi takdirde listeden rastgele bir yetenek seçilir.

    Args:
        parameters (dict): Yetenek seçimine yönelik tercihleri veya ipuçlarını içeren bir sözlük.
                           Örnek: {"preferred_skill": "Programlama (Python)"}

    Returns:
        dict: Seçim sonucunu, seçilen yeteneği ve bir mesajı içeren bir sözlük.
              Örn: {"status": "success", "chosen_skill": "Programlama (Python)", "message": "..."}
    """
    chosen_skill = None
    message = ""

    # ELESTIRI 1 & 5 & 6 (Güvenlik, Kullanılan Parametre ve Sabit Seçim Mekanizması):
    # `parameters` argümanı artık kullanılıyor.
    # Temel giriş doğrulama (input validation) ve sanitizasyon yapılarak güvenlik artırılmıştır.
    # Kullanıcının tercih ettiği yetenek varsa onu seçmeye çalışılır, yoksa rastgele bir seçim yapılır.
    if parameters and isinstance(parameters, dict):
        preferred_skill_param = parameters.get("preferred_skill")
        if preferred_skill_param:
            if isinstance(preferred_skill_param, str):
                # Parametre değeri geçerli bir dizeyse, yetenek listesinde olup olmadığını kontrol et.
                if preferred_skill_param in USEFUL_SKILLS:
                    chosen_skill = preferred_skill_param
                    message = f"Parametrede belirtilen tercih edilen yetenek '{chosen_skill}' başarıyla seçildi."
                else:
                    # Belirtilen yetenek listede yoksa, bilgilendir ve rastgele seçime yönlendir.
                    message = f"Parametrede belirtilen '{preferred_skill_param}' yeteneği listede bulunamadı. Rastgele bir yetenek seçiliyor."
            else:
                # Parametre değeri dize değilse, geçersiz kabul et ve rastgele seçime yönlendir.
                message = "Geçersiz 'preferred_skill' parametre türü (beklenen: dize). Rastgele bir yetenek seçiliyor."

    if not chosen_skill:
        # Eğer bir tercih belirtilmediyse veya tercih geçerli değilse, rastgele bir yetenek seç.
        chosen_skill = random.choice(USEFUL_SKILLS)
        if not message: # Eğer yukarıda zaten spesifik bir mesaj atanmamışsa genel bir mesaj ata.
            message = f"Parametreler doğrultusunda veya rastgele olarak '{chosen_skill}' yeteneği seçildi."
    
    # ELESTIRI 8 (Fonksiyon İçi Çıktı Yönetimi):
    # `print()` fonksiyonu kaldırıldı. Fonksiyon sadece işi yapar ve bir sonuç döndürür.
    # Çıktı yönetimi, fonksiyonu çağıran tarafın sorumluluğundadır.
    return {"status": "success", "chosen_skill": chosen_skill, "message": message}

TOOL_NAME: select_useful_skill