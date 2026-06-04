def run_action(parameters):
    """
    Verilen görev tanımına ve mevcut yeteneklere göre en uygun yeteneği seçer.

    Args:
        parameters (dict): Şunları içermelidir:
            - "task_description" (str): Yapılacak görevin kısa tanımı.
            - "available_skills" (list): Uygulama tarafından kullanılabilecek yeteneklerin listesi (str).

    Returns:
        str: Seçilen yeteneğin adı. Eğer uygun bir yetenek bulunamazsa None döner.
    """
    task_description = parameters.get("task_description", "").lower()
    available_skills = parameters.get("available_skills", [])

    if not task_description or not available_skills:
        return None

    # Yeteneklerin anahtar kelimelerle eşleştiği bir harita
    # Bu harita, bir anahtar kelimeye karşılık gelebilecek yetenek isimlerini içerir.
    # İlk bulunan uygun yetenek önceliklidir.
    skill_mapping = {
        "oku": ["dosya_oku", "veri_oku", "metin_oku"],
        "yaz": ["dosya_yaz", "veri_yaz", "rapor_yaz"],
        "analiz": ["veri_analizi_yap", "istatistik_analizi"],
        "rapor": ["rapor_olustur", "ozet_hazirla"],
        "ara": ["bilgi_ara", "web_ara", "veritabanı_sorgula"],
        "gonder": ["mesaj_gonder", "eposta_gonder", "bildirim_gonder"],
        "hesapla": ["hesaplama_yap", "matematiksel_islem"],
        "planla": ["gorev_planla", "zaman_yonetimi"],
        "listele": ["gorevleri_listele", "kayitlari_listele"],
        "olustur": ["rapor_olustur", "belge_olustur", "plan_olustur"],
        "kontrol_et": ["durum_kontrol_et", "dogrulama_yap"],
        "duzenle": ["metin_duzenle", "ayarlari_duzenle"],
        "guncelle": ["veritabanı_guncelle", "durum_guncelle"],
        "sil": ["dosya_sil", "kayit_sil"],
        "yap": ["gorev_yurut", "otomatik_gorev_yap"],
        "yonet": ["kaynak_yonetimi", "kullanici_yonetimi"]
    }

    # 1. Aşama: Görev tanımındaki anahtar kelimelerle eşleşen yetenekleri ara
    for keyword, potential_skills_for_keyword in skill_mapping.items():
        if keyword in task_description:
            for skill_name in potential_skills_for_keyword:
                if skill_name in available_skills:
                    return skill_name # İlk bulunan ve mevcut olanı seç

    # 2. Aşama: Görev tanımında doğrudan yetenek isimlerini ara
    # Örneğin, "dosya_oku" yeteneği için "dosya_oku görevini yap" gibi bir tanım
    for skill_name in available_skills:
        if skill_name.lower() in task_description:
            return skill_name

    # 3. Aşama: Hiçbir özel eşleşme bulunamazsa genel bir yetenek ara (varsa)
    if "genel_islem_yap" in available_skills:
        return "genel_islem_yap"

    # Hiçbir uygun yetenek bulunamazsa
    return None