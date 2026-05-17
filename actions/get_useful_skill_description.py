def run_action(parameters):
    """
    Yararlı bir yetenek seçer ve tanımını döndürür.

    Parameters:
        parameters (dict): Yetenek seçimi için parametreler.
                           Örn: {'skill': 'Yaratıcı Düşünme'}.
                           Eğer 'skill' parametresi belirtilmezse, varsayılan olarak 'Problem Çözme' kullanılır.

    Returns:
        str: Seçilen yeteneğin adı ve faydalarının bir açıklaması.
             Eğer istenen yetenek tanımlı değilse, bir hata mesajı döndürür.
    """

    # Tanımlanmış yetenekler ve açıklamaları
    skill_descriptions = {
        "Problem Çözme": (
            "Seçilen Yetenek: Problem Çözme\n\n"
            "Açıklama ve Faydaları:\n"
            "- Karşılaşılan zorlukları analiz etme, kök nedenlerini anlama ve etkili çözümler geliştirme becerisidir.\n"
            "- Bilgi teknolojilerinden mühendisliğe, günlük yaşamdan iş dünyasına kadar her alanda merkezi bir rol oynar.\n"
            "- Yenilikçiliği teşvik eder ve karmaşık durumlar karşısında bireylerin veya takımların ilerlemesini sağlar.\n"
            "- Veri analizi, mantıksal akıl yürütme ve yaratıcı düşünmeyi birleştirerek en uygun yolu bulmaya yardımcı olur."
        ),
        "Yaratıcı Düşünme": (
            "Seçilen Yetenek: Yaratıcı Düşünme\n\n"
            "Açıklama ve Faydaları:\n"
            "- Yeni fikirler üretme, alışılmışın dışında düşünme ve özgün çözümler bulma becerisidir.\n"
            "- Sanattan bilime, teknolojiden iş dünyasına kadar birçok alanda önemlidir.\n"
            "- Mevcut sorunlara farklı açılardan bakmayı ve yenilikçi yaklaşımlar geliştirmeyi sağlar.\n"
            "- Risk almayı, denemeyi ve başarısızlıkları öğrenme fırsatı olarak görmeyi teşvik eder."
        ),
        "Eleştirel Düşünme": (
            "Seçilen Yetenek: Eleştirel Düşünme\n\n"
            "Açıklama ve Faydaları:\n"
            "- Bilgiyi tarafsız bir şekilde analiz etme, değerlendirme ve mantıksal sonuçlara varma becerisidir.\n"
            "- Yanlış bilgiyi ayıklamayı, argümanları sorgulamayı ve sağlam kararlar almayı sağlar.\n"
            "- Hem kişisel hem de profesyonel yaşamda daha bilinçli seçimler yapılmasına yardımcı olur.\n"
            "- Karmaşık konuları derinlemesine anlama ve geçerli kanıtlara dayalı görüşler oluşturma yeteneğini geliştirir."
        ),
        "İletişim Becerileri": (
            "Seçilen Yetenek: İletişim Becerileri\n\n"
            "Açıklama ve Faydaları:\n"
            "- Fikirleri, bilgileri ve duyguları açık, etkili ve anlaşılır bir şekilde aktarabilme yeteneğidir.\n"
            "- Hem sözlü hem de yazılı ifadeyi, aktif dinlemeyi ve beden dilini kapsar.\n"
            "- Ekip çalışmasını güçlendirir, yanlış anlaşılmaları azaltır ve ilişkileri geliştirir.\n"
            "- Liderlik, satış, eğitim ve müşteri hizmetleri gibi birçok meslekte başarının anahtarıdır."
        )
        # İstenirse daha fazla yetenek eklenebilir
    }

    # parameters sözlüğünden 'skill' anahtarını alır.
    # Eğer 'skill' anahtarı yoksa, varsayılan olarak "Problem Çözme" değerini kullanır.
    selected_skill = parameters.get('skill', 'Problem Çözme')

    # Seçilen yeteneğin açıklamalar sözlüğünde olup olmadığını kontrol eder.
    if selected_skill in skill_descriptions:
        return skill_descriptions[selected_skill]
    else:
        # Eğer istenen yetenek bulunamazsa, bir hata mesajı döndürür.
        available_skills = ", ".join(skill_descriptions.keys())
        return (
            f"Hata: '{selected_skill}' adında bir yetenek bulunamadı. "
            f"Mevcut yetenekler: {available_skills}"
        )