import random

def run_action(parameters):
    """
    Bu fonksiyon, verilen parametrelere göre yararlı bir yetenek seçer ve ekrana yazar.
    Parametreler, yetenek seçimini dinamik olarak etkilemek için kullanılır
    ve çeşitli seçim modları (rastgele, belirli bir yetenek adı, indeks ile) destekler.

    Args:
        parameters (dict): Yetenek seçimi için yapılandırma parametrelerini içeren bir sözlük.
                           Beklenen anahtarlar:
                           - 'skill_list' (list, isteğe bağlı): Seçim yapılacak yeteneklerin listesi.
                                                                Verilmezse varsayılan bir liste kullanılır.
                           - 'selection_mode' (str, isteğe bağlı): Seçim modu. 'random', 'specific' veya 'index' olabilir.
                                                                  Varsayılan 'random'dır.
                           - 'specific_skill_name' (str, isteğe bağlı): 'specific' modu için seçilecek yeteneğin adı.
                           - 'skill_index' (int, isteğe bağlı): 'index' modu için yeteneğin listedeki indeksi.

    Returns:
        str or None: Başarıyla seçilen yeteneğin adı. Bir hata oluşursa None döner.
    """
    
    # 1. Varsayılan yetenek listesi
    default_skills = [
        "Eleştirel Düşünme ve Problem Çözme",
        "İletişim ve İşbirliği",
        "Yaratıcılık ve İnovasyon",
        "Dijital Okuryazarlık",
        "Duygusal Zeka",
        "Adaptasyon ve Esneklik",
        "Zaman Yönetimi",
        "Liderlik",
        "Veri Okuryazarlığı",
        "İş Etiği ve Sorumluluk"
    ]

    selected_skill = None

    try:
        # 2. Parametre doğrulama: parametrelerin bir sözlük olup olmadığını kontrol et
        if not isinstance(parameters, dict):
            raise TypeError("Hata: 'parameters' argümanı bir sözlük (dictionary) olmalıdır.")

        # 3. Yetenek listesini parametrelerden al veya varsayılanı kullan
        skills_to_choose_from = parameters.get('skill_list', default_skills)
        if not isinstance(skills_to_choose_from, list) or not skills_to_choose_from:
            raise ValueError("Hata: 'skill_list' parametresi boş olmayan bir liste olmalıdır.")

        # 4. Seçim modunu belirle (varsayılan 'random')
        selection_mode = parameters.get('selection_mode', 'random').lower()

        # 5. Seçim mekanizmasını uygula
        if selection_mode == 'random':
            selected_skill = random.choice(skills_to_choose_from)
        elif selection_mode == 'specific':
            skill_name = parameters.get('specific_skill_name')
            if skill_name is None:
                raise ValueError("Hata: 'specific' seçim modu için 'specific_skill_name' parametresi gereklidir.")
            if not isinstance(skill_name, str):
                raise TypeError("Hata: 'specific_skill_name' bir metin (string) olmalıdır.")
            if skill_name not in skills_to_choose_from:
                raise ValueError(f"Hata: '{skill_name}' yeteneği listede bulunamadı. Mevcut yetenekler: {', '.join(skills_to_choose_from)}")
            selected_skill = skill_name
        elif selection_mode == 'index':
            skill_index = parameters.get('skill_index')
            if skill_index is None:
                raise ValueError("Hata: 'index' seçim modu için 'skill_index' parametresi gereklidir.")
            if not isinstance(skill_index, int):
                raise TypeError("Hata: 'skill_index' bir tam sayı (integer) olmalıdır.")
            if not (0 <= skill_index < len(skills_to_choose_from)):
                raise IndexError(f"Hata: Yetenek indeksi {skill_index} geçersiz. "
                                 f"0 ile {len(skills_to_choose_from) - 1} arasında olmalıdır.")
            selected_skill = skills_to_choose_from[skill_index]
        else:
            raise ValueError(f"Hata: Geçersiz seçim modu: '{selection_mode}'. "
                             f"'random', 'specific' veya 'index' olmalıdır.")

    # 6. Hata Yönetimi
    except (TypeError, ValueError, IndexError) as e:
        print(f"Hata oluştu: {e}")
        return None  # Hata durumunda None döndür
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
        return None # Bilinmeyen bir hata durumunda None döndür

    # 7. Yeteneği ekrana yaz
    if selected_skill:
        print(f"Seçilen yararlı yetenek: {selected_skill}")

    # 8. Seçilen yeteneği döndür
    return selected_skill