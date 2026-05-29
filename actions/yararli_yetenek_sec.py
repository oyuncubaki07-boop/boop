def run_action(parameters):
    """
    Belirtilen veya varsayılan yararlı bir yetenek hakkında bilgi sağlar.

    Args:
        parameters (dict): Yetenek seçimi için kullanılabilecek anahtarlar:
            'skill' (str, optional): Hakkında bilgi istenen yeteneğin adı.
                                     Örn: "Problem Çözme", "Zaman Yönetimi", "İletişim".
                                     Belirtilmezse, varsayılan olarak "Problem Çözme" kullanılır.

    Returns:
        str: Seçilen yeteneğin tanımını ve faydalarını içeren bir metin.
    """
    skill_name_input = parameters.get('skill', 'Problem Çözme').strip()
    skill_name_lower = skill_name_input.lower()

    # Yetenek tanımlarını ve faydalarını içeren bir sözlük yapısı
    # Anahtar olarak hem Türkçe hem de İngilizce eşdeğerlerini ekleyebiliriz
    skills_data = {
        'problem çözme': {
            'display_name': 'Problem Çözme',
            'tanım': (
                "Problem Çözme, karmaşık durumları ve engelleri analiz etme, "
                "olası çözümleri belirleme ve en etkili olanı uygulama becerisidir. "
                "Mantıksal düşünme, yaratıcılık ve karar verme süreçlerini içerir."
            ),
            'faydaları': [
                "Karar verme yeteneğini güçlendirir.",
                "Analitik ve eleştirel düşünmeyi teşvik eder.",
                "Yeni ve beklenmedik durumlarla başa çıkma kapasitesini artırır.",
                "Yenilikçiliği ve yaratıcılığı besler.",
                "Hem kişisel hem de profesyonel yaşamda verimliliği ve başarıyı artırır."
            ]
        },
        'problem solving': {
            'display_name': 'Problem Çözme', # İngilizce anahtarda da Türkçe adı göster
            'tanım': (
                "Problem Çözme, karmaşık durumları ve engelleri analiz etme, "
                "olası çözümleri belirleme ve en etkili olanı uygulama becerisidir. "
                "Mantıksal düşünme, yaratıcılık ve karar verme süreçlerini içerir."
            ),
            'faydaları': [
                "Karar verme yeteneğini güçlendirir.",
                "Analitik ve eleştirel düşünmeyi teşvik eder.",
                "Yeni ve beklenmedik durumlarla başa çıkma kapasitesini artırır.",
                "Yenilikçiliği ve yaratıcılığı besler.",
                "Hem kişisel hem de profesyonel yaşamda verimliliği ve başarıyı artırır."
            ]
        },
        'zaman yönetimi': {
            'display_name': 'Zaman Yönetimi',
            'tanım': (
                "Zaman Yönetimi, görevleri önceliklendirme, zamanı verimli bir şekilde "
                "planlama ve hedeflere ulaşmak için etkili bir şekilde kullanma becerisidir. "
                "Üretkenliği artırarak ve stresi azaltarak daha iyi bir denge sağlar."
            ),
            'faydaları': [
                "Üretkenliği ve verimliliği önemli ölçüde artırır.",
                "İş-yaşam dengesini iyileştirir ve stresi azaltır.",
                "Hedeflere ulaşmayı kolaylaştırır ve daha fazla boş zaman yaratır.",
                "Görevleri daha etkili bir şekilde organize etmeyi sağlar.",
                "Son dakika telaşını ve ertelemeyi azaltır."
            ]
        },
        'time management': {
            'display_name': 'Zaman Yönetimi',
            'tanım': (
                "Zaman Yönetimi, görevleri önceliklendirme, zamanı verimli bir şekilde "
                "planlama ve hedeflere ulaşmak için etkili bir şekilde kullanma becerisidir. "
                "Üretkenliği artırarak ve stresi azaltarak daha iyi bir denge sağlar."
            ),
            'faydaları': [
                "Üretkenliği ve verimliliği önemli ölçüde artırır.",
                "İş-yaşam dengesini iyileştirir ve stresi azaltır.",
                "Hedeflere ulaşmayı kolaylaştırır ve daha fazla boş zaman yaratır.",
                "Görevleri daha etkili bir şekilde organize etmeyi sağlar.",
                "Son dakika telaşını ve ertelemeyi azaltır."
            ]
        },
        'iletişim': {
            'display_name': 'İletişim',
            'tanım': (
                "İletişim, düşünceleri, fikirleri, duyguları ve bilgileri etkili bir "
                "şekilde aktarma ve karşılıklı olarak anlama yeteneğidir. "
                "Hem sözlü hem de yazılı formları içerir ve insan ilişkilerinin temelidir."
            ),
            'faydaları': [
                "Kişisel ve profesyonel ilişkileri güçlendirir.",
                "Yanlış anlaşılmaları önler ve çatışmaları azaltır.",
                "Takım çalışmasını ve işbirliğini geliştirir.",
                "Liderlik ve ikna becerilerini destekler.",
                "Fikirlerin ve geri bildirimlerin daha net ifade edilmesini sağlar."
            ]
        },
        'communication': {
            'display_name': 'İletişim',
            'tanım': (
                "İletişim, düşünceleri, fikirleri, duyguları ve bilgileri etkili bir "
                "şekilde aktarma ve karşılıklı olarak anlama yeteneğidir. "
                "Hem sözlü hem de yazılı formları içerir ve insan ilişkilerinin temelidir."
            ),
            'faydaları': [
                "Kişisel ve profesyonel ilişkileri güçlendirir.",
                "Yanlış anlaşılmaları önler ve çatışmaları azaltır.",
                "Takım çalışmasını ve işbirliğini geliştirir.",
                "Liderlik ve ikna becerilerini destekler.",
                "Fikirlerin ve geri bildirimlerin daha net ifade edilmesini sağlar."
            ]
        },
        'kodlama': {
            'display_name': 'Kodlama',
            'tanım': (
                "Kodlama (Programlama), bilgisayarlara belirli görevleri yerine getirmeleri "
                "için talimatlar verme becerisidir. Mantıksal düşünme, algoritmik yaklaşım "
                "ve problem çözme yeteneklerini bir araya getirir."
            ),
            'faydaları': [
                "Mantıksal ve algoritmik düşünme becerilerini geliştirir.",
                "Yaratıcılığı ve yenilikçiliği teşvik eder.",
                "Karmaşık problemleri küçük, yönetilebilir adımlara bölme yeteneği kazandırır.",
                "Dijital dünyayı anlama ve şekillendirme gücü verir.",
                "Kariyer fırsatlarını genişletir ve otomasyon becerileri kazandırır."
            ]
        },
        'programlama': { # 'kodlama' ile aynı bilgiyi göster
            'display_name': 'Kodlama',
            'tanım': (
                "Kodlama (Programlama), bilgisayarlara belirli görevleri yerine getirmeleri "
                "için talimatlar verme becerisidir. Mantıksal düşünme, algoritmik yaklaşım "
                "ve problem çözme yeteneklerini bir araya getirir."
            ),
            'faydaları': [
                "Mantıksal ve algoritmik düşünme becerilerini geliştirir.",
                "Yaratıcılığı ve yenilikçiliği teşvik eder.",
                "Karmaşık problemleri küçük, yönetilebilir adımlara bölme yeteneği kazandırır.",
                "Dijital dünyayı anlama ve şekillendirme gücü verir.",
                "Kariyer fırsatlarını genişletir ve otomasyon becerileri kazandırır."
            ]
        },
        'coding': { # 'kodlama' ile aynı bilgiyi göster
            'display_name': 'Kodlama',
            'tanım': (
                "Kodlama (Programlama), bilgisayarlara belirli görevleri yerine getirmeleri "
                "için talimatlar verme becerisidir. Mantıksal düşünme, algoritmik yaklaşım "
                "ve problem çözme yeteneklerini bir araya getirir."
            ),
            'faydaları': [
                "Mantıksal ve algoritmik düşünme becerilerini geliştirir.",
                "Yaratıcılığı ve yenilikçiliği teşvik eder.",
                "Karmaşık problemleri küçük, yönetilebilir adımlara bölme yeteneği kazandırır.",
                "Dijital dünyayı anlama ve şekillendirme gücü verir.",
                "Kariyer fırsatlarını genişletir ve otomasyon becerileri kazandırır."
            ]
        },
        'programming': { # 'kodlama' ile aynı bilgiyi göster
            'display_name': 'Kodlama',
            'tanım': (
                "Kodlama (Programlama), bilgisayarlara belirli görevleri yerine getirmeleri "
                "için talimatlar verme becerisidir. Mantıksal düşünme, algoritmik yaklaşım "
                "ve problem çözme yeteneklerini bir araya getirir."
            ),
            'faydaları': [
                "Mantıksal ve algoritmik düşünme becerilerini geliştirir.",
                "Yaratıcılığı ve yenilikçiliği teşvik eder.",
                "Karmaşık problemleri küçük, yönetilebilir adımlara bölme yeteneği kazandırır.",
                "Dijital dünyayı anlama ve şekillendirme gücü verir.",
                "Kariyer fırsatlarını genişletir ve otomasyon becerileri kazandırır."
            ]
        }
    }

    selected_skill = skills_data.get(skill_name_lower)
    output = ""

    if selected_skill:
        display_name = selected_skill['display_name']
        output += f"--- Seçilen Yararlı Yetenek: {display_name} ---\n\n"
        output += f"Tanım:\n{selected_skill['tanım']}\n\n"
        output += "Faydaları:\n"
        for benefit in selected_skill['faydaları']:
            output += f"- {benefit}\n"
    else:
        available_skills_display = sorted(list(set(s['display_name'] for s in skills_data.values())))
        output += (
            f"'{skill_name_input}' adında bir yetenek hakkında detaylı bilgi bulunamadı. "
            "Lütfen aşağıdaki yaygın yeteneklerden birini deneyin:\n"
            f"{', '.join(available_skills_display)}\n\n"
            "Ya da varsayılan 'Problem Çözme' yeteneğini kullanmak için bir yetenek belirtmeyin."
        )

    return output

TOOL_NAME: yararli_yetenek_sec