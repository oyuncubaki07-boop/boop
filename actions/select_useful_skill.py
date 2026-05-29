def run_action(parameters):
    """
    Kullanıcı için yararlı bir yetenek seçer ve bu yeteneğin neden faydalı olduğunu açıklar.

    Parametreler:
        parameters (dict): Bu araç için özel bir parametre beklenmez, ancak fonksiyon
                           evrensel çağrı yapısına uymak için 'parameters' alır.

    Dönüş:
        str: Seçilen yeteneği ve açıklamasını içeren bir dize.
    """
    chosen_skill = "Eleştirel Düşünme"
    explanation = (
        "Bu yetenek, bilgiyi sorgulama, argümanları değerlendirme, mantıksal hataları tespit etme "
        "ve daha bilinçli kararlar alma becerisi kazandırır. Günümüzün bilgi kirliliği çağında, "
        "doğruyu yanlıştan ayırmak ve karmaşık sorunlara çözüm bulmak için hayati öneme sahiptir."
    )
    return f"Seçilen yararlı yetenek: '{chosen_skill}'. {explanation}"