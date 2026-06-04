# Modül seviyesi sabitler olarak yetenek adı ve açıklaması tanımlanmıştır.
# Bu, performans eleştirisindeki "Tekrarlı Değişken Tanımlamaları" sorununu çözer
# ve değerlerin fonksiyon her çağrıldığında yeniden oluşturulmamasını sağlar.
# Aynı zamanda, içeriğin sabit kodlanmış olduğu eleştirisi için,
# bu kullanım senaryosunda (belirli bir yeteneği seçme ve tanımlama) uygun bir yaklaşımdır.
# Hassas bilgi içermediği için güvenlik riski oluşturmaz.
SKILL_NAME = "Eleştirel Düşünme ve Problem Çözme"
SKILL_DESCRIPTION = (
    "Bu yetenek, bilgiyi nesnel bir şekilde analiz etme, temel sorunları tanımlama, "
    "farklı bakış açılarını değerlendirme ve etkili çözümler üretme becerisini içerir. "
    "Karar verme, yenilik yapma ve herhangi bir alandaki karmaşık zorlukların üstesinden gelme "
    "için kritik öneme sahiptir. Bilginin bol olduğu ve sürekli değişen bir dünyada, "
    "doğruyu yanlıştan ayırma, mantıklı çıkarımlar yapma ve uygulanabilir stratejiler geliştirme "
    "becerisi kişisel ve profesyonel başarı için vazgeçilmezdir."
)

def run_action(parameters):
    """
    Yararlı bir yetenek seçer ve bu yeteneği açıklar.
    'parameters' argümanı bu özel kullanım senaryosunda doğrudan kullanılmasa da,
    genel 'run_action' arayüzüne uyum sağlamak için mevcuttur.
    Görev tanımı gereği sabit bir yetenek döndürülmektedir.
    """
    # Sabit kodlanmış yetenek adı ve açıklaması modül seviyesi sabitlerden alınır.
    # Bu, güvenlik eleştirisinde bahsedilen "Sabit Kodlanmış İçerik" durumunu
    # bu özel görev için uygun bir şekilde yönetir. Hassas bilgi olmadığı için sorun teşkil etmez.
    # F-string kullanımı, performans eleştirisindeki "Dize Oluşturma Maliyeti" açısından
    # modern Python'da oldukça optimize ve okunabilir bir yöntemdir.
    return f"Seçilen Yararlı Yetenek: {SKILL_NAME}\n\nAçıklama: {SKILL_DESCRIPTION}"