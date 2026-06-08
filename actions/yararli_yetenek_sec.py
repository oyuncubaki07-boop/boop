import logging
import os

# Güvenlik ve Performans: Yetenek bilgileri kod içine sabitlenmek yerine,
# modül seviyesinde bir veri yapısında tanımlanmıştır.
# Bu sayede hem kod okunabilirliği artar hem de değişiklikler için kodun
# yeniden dağıtılması gerekmez (eğer bu yapı bir veritabanı/konfigürasyon dosyasından beslenseydi).
SKILLS_DATABASE = {
    "kritik düşünme ve problem çözme": {
        "description": "Karşılaşılan sorunları analiz etme, farklı perspektiflerden değerlendirme, mantıklı çözümler geliştirme ve bu çözümleri etkin bir şekilde uygulama becerisini kapsar. Modern dünyada her alanda başarı için vazgeçilmez bir temel oluşturur. Sürekli öğrenme ve adaptasyon için de kilit bir roldedir."
    },
    "iletişim becerileri": {
        "description": "Fikirleri, bilgileri ve duyguları açık, etkili ve ikna edici bir şekilde hem sözlü hem de yazılı olarak ifade etme yeteneğidir. Aktif dinleme, empati kurma ve geri bildirim verme becerilerini de içerir. Kişisel ve profesyonel ilişkilerde başarı için temel bir taştır."
    },
    "zaman yönetimi": {
        "description": "Görevleri önceliklendirme, zamanı verimli kullanma, dikkat dağıtıcı unsurları yönetme ve hedeflere ulaşmak için etkili stratejiler uygulama becerisidir. Stres azaltma, üretkenliği artırma ve yaşam kalitesini iyileştirme konusunda kritik öneme sahiptir."
    }
    # Gelecekte ek yetenekler buraya kolayca eklenebilir
}

# Güvenlik ve Performans: Varsayılan yetenek anahtarı tanımlanmıştır.
DEFAULT_SKILL_KEY = "kritik düşünme ve problem çözme"

# Güvenlik: Loglama için logger yapılandırması.
# Hassas bilgilerin doğrudan konsola yazılması yerine, loglama mekanizması kullanılabilir.
# Log seviyesi ortam değişkeni ile kontrol edilebilir.
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_action(parameters: dict) -> dict:
    """
    Yararlı bir yetenek seçer ve hakkında bilgi döndürür.
    `parameters` sözlüğündeki 'skill_name' anahtarına göre yetenek seçimi yapılabilir.
    Eğer geçerli bir 'skill_name' belirtilmezse, varsayılan bir yetenek seçilir.

    Args:
        parameters (dict): Eylemin parametrelerini içeren bir sözlük.
                           Örnek: `{'skill_name': 'iletişim becerileri'}`

    Returns:
        dict: Eylemin başarı durumunu, seçilen yeteneği ve açıklamasını içeren bir sözlük.
    """
    chosen_skill_name = DEFAULT_SKILL_KEY
    skill_description = ""

    # Güvenlik - Girdi Doğrulama:
    # `parameters` sözlüğünün varlığı ve beklenen anahtarların doğruluğu kontrol edilir.
    if parameters and isinstance(parameters, dict):
        requested_skill = parameters.get("skill_name")
        if isinstance(requested_skill, str):
            # Küçük harfe çevrilerek case-insensitive arama yapılır.
            normalized_skill = requested_skill.lower()
            if normalized_skill in SKILLS_DATABASE:
                chosen_skill_name = normalized_skill
                logger.info(f"Parametrelerden '{requested_skill}' yeteneği seçildi.")
            else:
                logger.warning(f"İstenen yetenek '{requested_skill}' bulunamadı. Varsayılan yetenek '{DEFAULT_SKILL_KEY}' seçildi.")
        elif requested_skill is not None:
            logger.warning(f"'skill_name' parametresi geçersiz tipte ({type(requested_skill).__name__}). String bekleniyordu. Varsayılan yetenek '{DEFAULT_SKILL_KEY}' seçildi.")
    else:
        logger.info(f"Parametreler geçersiz veya boş. Varsayılan yetenek '{DEFAULT_SKILL_KEY}' seçildi.")

    # Seçilen yeteneğin bilgilerini al.
    skill_info = SKILLS_DATABASE.get(chosen_skill_name, {})
    skill_description = skill_info.get("description", "Açıklama bulunamadı.")

    # Güvenlik - Bilgi Sızıntısı Potansiyeli:
    # Bilgiler doğrudan 'print' ile konsola (veya loglara) yazdırılmak yerine,
    # fonksiyonun dönüş değeri olarak yapılandırılmış bir şekilde sağlanır.
    # 'print' ifadeleri sadece bilgilendirme amaçlıdır ve asıl veri aktarımı dönüş değeri üzerinden yapılır.
    # Hassas verilerin direkt 'print' edilmesi yerine, kontrollü loglama veya dönüş mekanizması tercih edilir.
    print(f"\n--- Seçilen Yetenek ---")
    print(f"Adı: '{chosen_skill_name.title()}'") # Baş harfleri büyük yazım
    print(f"Açıklama: {skill_description}")
    print(f"-----------------------\n")

    # Performans - Kaynak Tekrarı ve Ölçeklenebilirlik:
    # Veriler modül seviyesinde tanımlandığı için her çağrıda yeniden oluşturulmaz.
    # Dönüş değeri, yapılandırılmış ve genişletilebilir bir formattadır,
    # bu da farklı kullanım senaryoları (API yanıtı, UI gösterimi vb.) için esneklik sağlar.
    return {
        "status": "success",
        "message": f"'{chosen_skill_name.title()}' yeteneği seçildi ve bilgisi başarıyla alındı.",
        "chosen_skill": {
            "name": chosen_skill_name.title(),
            "description": skill_description
        }
    }

# pip - Bağımlılık Beyanı ve Ortam İzole Etme Eksikliği:
# Bu eleştiriler doğrudan Python koduna dahil edilemez, ancak projenin yapısı için önemlidir.
# Öneri:
# - Projenin kök dizinine bir `requirements.txt` dosyası eklenmeli ve kullanılan kütüphaneler (bu örnekte yok) belirtilmelidir.
#   Örnek `requirements.txt`:
#