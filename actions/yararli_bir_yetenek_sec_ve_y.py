def run_action(parameters):
    """
    Yararlı bir yetenek seçer ve açıklamasını döndürür.

    Parameters:
    parameters (dict): Bu özel uygulamada doğrudan kullanılmayan parametreler sözlüğü.
                       Gelecekteki genişletmeler için yer tutucudur.

    Returns:
    dict: Seçilen yeteneğin adını ve açıklamasını içeren bir sözlük.
    """
    skill_name = "Eleştirel Düşünme"
    skill_description = (
        "Eleştirel düşünme, bilgiyi objektif bir şekilde analiz etme, "
        "argümanları değerlendirme, varsayımları sorgulama ve bilinçli kararlar verme yeteneğidir. "
        "Bu yetenek, karmaşık sorunları çözmek, yanıltıcı bilgilere karşı durmak, "
        "mantıklı sonuçlar çıkarmak ve daha iyi hükümler vermek için hayati öneme sahiptir. "
        "Hem kişisel yaşamda hem de profesyonel ortamlarda, karar alma süreçlerini geliştirir, "
        "öğrenmeyi derinleştirir ve yenilikçi çözümler üretmeye yardımcı olur."
    )

    return {
        "skill": skill_name,
        "description": skill_description
    }