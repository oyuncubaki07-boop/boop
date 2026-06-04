def run_action(parameters):
    """
    Seçilen yararlı bir yeteneği ve önemini açıklayan bir metin döndürür.
    Yetenek, 'parameters' sözlüğünden 'skill_name' anahtarı ile seçilir.

    Args:
        parameters (dict): İşlem için gerekli olabilecek parametreler.
                           'skill_name' (str) anahtarı, açıklanacak yeteneği belirtir.
                           Örnek: `{"skill_name": "Problem Çözme Yeteneği"}` veya
                           `{"skill_name": "eleştirel düşünme"}`.
                           Büyük/küçük harf ve boşluklar otomatik olarak düzeltilir.

    Returns:
        str: Seçilen yetenek ve önemi hakkında bilgi içeren bir metin.
             Eğer 'skill_name' belirtilmezse veya eşleşen bir yetenek bulunamazsa,
             mevcut yetenekleri listeleyen veya bir hata mesajı içeren bir metin döner.
    """
    ALL_SKILLS = {
        "problem_çözme_yeteneği": {
            "name": "Problem Çözme Yeteneği",
            "description": (
                "Açıklama:\n"
                "Problem çözme yeteneği, karşılaşılan zorlukları, engelleri veya karmaşık durumları "
                "tanımlama, analiz etme ve bu durumlar için etkili çözümler geliştirme becerisidir. "
                "Bu, mantıksal düşünme, yaratıcılık, eleştirel analiz ve karar verme süreçlerini içerir.\n\n"
                "Neden Yararlıdır:\n"
                "1. Her Alanda Uygulanabilirlik: Kişisel yaşamdan profesyonel kariyere, bilimden sanata kadar her alanda sorunlar ortaya çıkar ve çözüme ihtiyaç duyar.\n"
                "2. İnovasyon ve Gelişim: Mevcut problemleri çözmek, yeni fikirlerin ve daha iyi süreçlerin keşfedilmesine yol açar.\n"
                "3. Karar Verme Kalitesi: Problemleri etkili bir şekilde analiz edebilmek, daha bilinçli ve doğru kararlar almanızı sağlar.\n"
                "4. Stres Yönetimi ve Verimlilik: Sorunları çözebilme yeteneği, belirsizliği azaltır, stresi yönetmeye yardımcı olur ve iş akışını veya kişisel hedeflere ulaşmayı kolaylaştırır.\n"
                "5. Öğrenme ve Adaptasyon: Çözülen her problem, gelecekte benzer durumlarla başa çıkmak için değerli deneyimler ve bilgiler sağlar. Değişen koşullara uyum sağlamanın anahtarıdır.\n\n"
                "Kısacası, problem çözme yeteneği, bireylerin ve organizasyonların zorluklar karşısında ilerlemesini, gelişmesini ve başarılı olmasını sağlayan temel bir yaşam becerisidir."
            )
        },
        "eleştirel_düşünme": {
            "name": "Eleştirel Düşünme",
            "description": (
                "Açıklama:\n"
                "Eleştirel düşünme, bilgiyi objektif bir şekilde analiz etme, değerlendirme ve mantıksal yargılara varma becerisidir. "
                "Varsayımları sorgulamayı, kanıtları incelemeyi ve farklı bakış açılarını göz önünde bulundurmayı içerir.\n\n"
                "Neden Yararlıdır:\n"
                "1. Bilinçli Kararlar: Daha iyi, daha mantıklı ve bilinçli kararlar almanızı sağlar.\n"
                "2. Yanlış Bilgiyi Ayıklama: Günümüz bilgi çağında, yanlış veya yanıltıcı bilgileri tespit etme ve ayıklama yeteneği kazandırır.\n"
                "3. Etkili Problem Çözümü: Problemleri daha derinlemesine anlamaya ve daha yaratıcı çözümler geliştirmeye yardımcı olur.\n"
                "4. Bağımsız Düşünce: Kendi fikirlerinizi oluşturma ve başkalarının etkisinden sıyrılarak bağımsız kararlar verme becerisini geliştirir.\n"
                "5. İletişim ve Tartışma: Fikirleri daha net ifade etme ve yapıcı tartışmalara katılma yeteneğini artırır."
            )
        },
        "duygusal_zeka": {
            "name": "Duygusal Zeka (EQ)",
            "description": (
                "Açıklama:\n"
                "Duygusal zeka, kişinin kendi duygularını ve başkalarının duygularını anlama, yönetme, motive etme ve sosyal ilişkilerde etkili bir şekilde kullanma becerisidir. "
                "Kendini tanıma, öz-denetim, motivasyon, empati ve sosyal beceriler gibi bileşenleri içerir.\n\n"
                "Neden Yararlıdır:\n"
                "1. Daha Sağlıklı İlişkiler: Hem kişisel hem de profesyonel hayatta daha güçlü ve anlamlı ilişkiler kurmayı sağlar.\n"
                "2. Etkili Liderlik: Liderlerin empati kurma, ilham verme ve ekipleri motive etme yeteneklerini geliştirir.\n"
                "3. Stres ve Çatışma Yönetimi: Duygusal dengeyi koruyarak stresli durumlarla ve kişilerarası çatışmalarla daha yapıcı bir şekilde başa çıkmaya yardımcı olur.\n"
                "4. İletişim Becerileri: Duyguları doğru anlama ve ifade etme kapasitesi, iletişimin kalitesini artırır.\n"
                "5. Kariyer Başarısı: Yüksek EQ'ya sahip kişilerin iş yerinde daha başarılı olduğu, terfi alma olasılıklarının daha yüksek olduğu gözlemlenmiştir."
            )
        },
        "zaman_yönetimi": {
            "name": "Zaman Yönetimi",
            "description": (
                "Açıklama:\n"
                "Zaman yönetimi, bireylerin belirli görevler, projeler veya etkinlikler üzerinde harcadıkları zamanı planlama ve kontrol etme becerisidir. "
                "Hedef belirleme, önceliklendirme, planlama, delegasyon ve dikkat dağıtıcı unsurları engellemeyi içerir.\n\n"
                "Neden Yararlıdır:\n"
                "1. Verimlilik Artışı: Görevleri daha kısa sürede tamamlayarak genel verimliliği artırır.\n"
                "2. Stres Azaltma: Son dakika telaşını ve aceleciliği ortadan kaldırarak stresi azaltır.\n"
                "3. Daha İyi Karar Verme: Öncelikleri belirleyerek önemli işlere odaklanmayı ve daha iyi kararlar almayı sağlar.\n"
                "4. Hedeflere Ulaşma: Bireysel ve profesyonel hedeflere ulaşma şansını artırır.\n"
                "5. İş-Yaşam Dengesi: İş ile kişisel yaşam arasındaki dengeyi korumaya yardımcı olur, tükenmişliği önler."
            )
        },
        "iletişim_becerileri": {
            "name": "İletişim Becerileri",
            "description": (
                "Açıklama:\n"
                "İletişim becerileri, düşüncelerin, fikirlerin, duyguların ve bilgilerin net, etkili ve anlaşılır bir şekilde başkalarına aktarılması ve anlaşılması yeteneğidir. "
                "Hem sözlü hem de yazılı ifade, aktif dinleme ve beden dili gibi unsurları kapsar.\n\n"
                "Neden Yararlıdır:\n"
                "1. İlişkileri Geliştirir: Kişisel ve profesyonel ilişkileri güçlendirir, yanlış anlaşılmaları azaltır.\n"
                "2. Çatışmaları Çözer: Açık ve etkili iletişim, çatışmaların daha yapıcı bir şekilde çözülmesine yardımcı olur.\n"
                "3. Takım Çalışmasını Destekler: Takım üyeleri arasında bilgi akışını ve işbirliğini artırır.\n"
                "4. Liderliği Güçlendirir: Liderlerin vizyonlarını aktarmalarına, ekiplerini motive etmelerine ve etkili geri bildirim sağlamalarına olanak tanır.\n"
                "5. İkna Yeteneği: Fikirleri ve önerileri daha ikna edici bir şekilde sunma becerisini geliştirir."
            )
        }
    }

    selected_skill_key = parameters.get("skill_name")

    if selected_skill_key:
        # Gelen parametreyi küçük harfe çevirip boşlukları alt çizgi ile değiştirerek anahtar oluştur
        normalized_key = selected_skill_key.lower().replace(" ", "_")
        skill_info = ALL_SKILLS.get(normalized_key)

        if skill_info:
            return f"Yetenek: {skill_info['name']}\n\n{skill_info['description']}"
        else:
            available_skill_names = ", ".join([skill_data['name'] for skill_data in ALL_SKILLS.values()])
            return (
                f"Üzgünüm, '{selected_skill_key}' adında bir yetenek bulunamadı. "
                f"Mevcut yetenekler şunlardır: {available_skill_names}."
            )
    else:
        # Hiçbir yetenek belirtilmezse, mevcut yetenekleri listeleyen bir mesaj dön
        available_skill_list = "\n- ".join([skill_data['name'] for skill_data in ALL_SKILLS.values()])
        return (
            "Lütfen detaylı bilgi almak istediğiniz bir yeteneği 'skill_name' parametresi ile belirtin. "
            "Örnek: `parameters={'skill_name': 'Problem Çözme Yeteneği'}`\n\n"
            "Mevcut Yararlı Yetenekler:\n"
            f"- {available_skill_list}\n\n"
            "Herhangi birini seçerek detaylı bilgi alabilirsiniz."
        )

TOOL_NAME: yararli_yetenek_aciklayici