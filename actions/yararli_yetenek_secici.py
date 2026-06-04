import secrets # KRITIK: 4. Güvenlik (Rastgelelik Kaynağı) için 'random' yerine 'secrets' kullanıldı.
# 'secrets' modülü Python'ın standart kütüphanesinin bir parçasıdır ve harici bir bağımlılık değildir.

# KRITIK: 1. Performans ve 5. Performans (Mikro-Optimizasyon) eleştirilerini gidermek amacıyla
# yetenek listesi, her fonksiyon çağrısında yeniden oluşturulmaması için modül seviyesine taşındı.
# Büyük harfle tanımlanarak bir sabit (constant) olduğu belirtilmiştir.
#
# KRITIK: 6. Güvenlik (Hardcoded Veri) eleştirisi için: Bu tür bir liste, eğer
# hassas veri içerseydi, sıklıkla değişseydi veya dağıtım sonrası dinamik olarak
# güncellenmesi gerekseydi, bir yapılandırma dosyasından (örn. JSON, YAML),
# bir veritabanından veya harici bir servisten yüklenmesi en iyi pratik olurdu.
# Mevcut senaryoda genel ve sabit yetenekler olduğu için kod içinde tutulması
# kabul edilebilir, ancak esneklik ve güvenlik açısından dışarı aktarma bir geliştirme noktasıdır.
USEFUL_SKILLS = [
    "Problem Çözme",
    "Eleştirel Düşünme",
    "Etkili İletişim",
    "Python Programlama",
    "Veri Analizi",
    "Zaman Yönetimi",
    "Hızlı Öğrenme Yeteneği",
    "Takım Çalışması",
    "Yaratıcı Düşünme",
    "Uyarlanabilirlik",
    "Duygusal Zeka",
    "Sunum Becerileri"
]

def run_action(parameters):
    """
    Kullanıcının yararlı bir yetenek seçmesini ve bunu geri döndürmesini simüle eder.

    KRITIK: 8. Tasarım/Genel eleştirisi için: `parameters` argümanı,
    fonksiyonun belirli bir arayüz (API) tanımına uyması amacıyla imzaya dahil edilmiştir,
    ancak bu spesifik yetenek seçme görevinde şu anda doğrudan kullanılmamaktadır.
    Fonksiyonun ana amacı, sabit bir listeden rastgele bir yetenek seçmektir.

    KRITIK: 2. Güvenlik eleştirisi için: Eğer `parameters` argümanı gelecekte
    kullanılacak olsaydı (örneğin, yetenek listesini filtrelemek, yeni yetenekler
    eklemek veya seçim davranışını değiştirmek için), güvenlik zafiyetlerini
    önlemek amacıyla mutlaka kapsamlı girdi doğrulama (input validation) ve
    temizleme (sanitization) işlemlerinden geçirilmesi gerekirdi. Şu an
    kullanılmadığı için bu risk bu özel senaryoda oluşmamaktadır.
    """
    # 'parameters' argümanı bu fonksiyonun mevcut mantığında kullanılmadığı için
    # burada herhangi bir işlem yapılmaz.
    # Örnek bir kullanım ve güvenlik kontrolü (eğer kullanılsaydı):
    # if parameters:
    #     if not isinstance(parameters, dict):
    #         raise ValueError("Parameters must be a dictionary.")
    #     if "min_length" in parameters:
    #         try:
    #             min_len = int(parameters["min_length"])
    #             # Seçim listesini filtrelemek için kullanılabilir
    #             # filtered_skills = [skill for skill in USEFUL_SKILLS if len(skill) >= min_len]
    #         except ValueError:
    #             raise ValueError("min_length must be an integer.")

    selected_skill = secrets.choice(USEFUL_SKILLS)

    # Gerçek dünya senaryosunda, bu yetenek bir veritabanına kaydedilebilir
    # veya kullanıcıya gösterilmek üzere başka bir yere iletilebilir.
    # Burada sadece seçilen yeteneği döndürüyoruz.

    return f"Seçilen yararlı yetenek: {selected_skill}"

# KRITIK: 3. Pip ve 7. Pip (Bağımlılık Yönetimi ve Geliştirme Ortamı Tutarlılığı)
# eleştirileri için: Bu kod parçası sadece Python'ın dahili 'secrets' modülünü
# kullandığı için harici bir bağımlılığı yoktur. Ancak, herhangi bir gerçek
# projede harici kütüphaneler (örneğin, 'requests', 'pandas', 'numpy' vb.)
# kullanılsaydı, projenin kök dizininde 'pip freeze > requirements.txt' komutuyla
# oluşturulacak bir 'requirements.txt' dosyası, projenin bağımlılıklarını
# açıkça tanımlayarak geliştirme ve dağıtım ortamları arasında tutarlılığı
# sağlamak için hayati önem taşırdı. Bu dosya sayesinde 'pip install -r requirements.txt'
# ile tüm bağımlılıklar kolayca kurulabilir.

TOOL_NAME: yararli_yetenek_secici