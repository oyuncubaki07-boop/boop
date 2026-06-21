import collections

# Kritik 1, 4, 6'yı ele almak için yetenek tanımlarını ayrı bir veri yapısında tutma.
# Bu yapı, yeni yeteneklerin veya mevcut yeteneklerin kriterlerinin kolayca eklenmesine/değiştirilmesine olanak tanır.
# Anahtar kelimeler, daha spesifik eşleşmeler için tasarlanmıştır. Çok kelimeli anahtar kelimeler (örn. "problem çözme")
# tam ifade olarak, tek kelimeliler ise kelime bazında aranacaktır.
SKILLS_DATA = [
    {
        "name": "Python Programlama",
        "explanation": "Veri analizi, otomasyon, web geliştirme ve yapay zeka gibi birçok alanda son derece değerlidir. Başlangıç dostu ve güçlü bir dildir.",
        "keywords": ["python", "programlama", "coding", "yazılım", "tech", "teknoloji", "development", "developer", "automation", "ai", "yapay zeka", "data science", "veri bilimi"]
    },
    {
        "name": "Etkili İletişim ve Topluluk Önünde Konuşma",
        "explanation": "Fikirleri açıkça ifade etme, başkalarını ikna etme ve profesyonel ilişkileri geliştirme becerisi her alanda başarı için kritiktir.",
        "keywords": ["iletişim", "communication", "public speaking", "topluluk önünde konuşma", "konuşma", "sunum", "presentation", "persuasion", "sosyal", "social", "hitabet"]
    },
    {
        "name": "Eleştirel Düşünme ve Problem Çözme",
        "explanation": "Herhangi bir meslekte ve günlük yaşamda karmaşık sorunları analiz etme, farklı bakış açılarını değerlendirme ve etkili çözümler bulma yeteneği.",
        "keywords": ["eleştirel düşünme", "problem çözme", "critical thinking", "problem solving", "analitik düşünme", "analytic thinking", "mantık", "logic", "analiz", "analysis"]
    },
    {
        "name": "Yeni Bir Yabancı Dil Öğrenmek",
        "explanation": "Kültürel anlayışı artırır, seyahat ve iş imkanlarını genişletir ve bilişsel yetenekleri geliştirir.",
        "keywords": ["dil", "language", "yabancı dil", "foreign language", "ingilizce", "spanish", "ispanyolca", "chinese", "çince", "global", "uluslararası", "seyahat"]
    },
    {
        "name": "Veri Okuryazarlığı ve Temel Veri Analizi",
        "explanation": "Günümüz dijital çağında veriyi anlama, yorumlama ve kararlar almak için kullanma becerisi, hemen hemen her sektörde büyük önem taşır.",
        "keywords": ["veri", "data", "veri analizi", "data analysis", "analiz", "analysis", "veri okuryazarlığı", "data literacy", "istatistik", "statistics", "excel"]
    },
    {
        "name": "Temel Finansal Okuryazarlık ve Bütçeleme",
        "explanation": "Kişisel finansı yönetmek, yatırım yapmak ve uzun vadeli finansal hedefler belirlemek için hayati öneme sahiptir. Geleceğin güvencesidir.",
        "keywords": ["finans", "financial", "bütçeleme", "budgeting", "yatırım", "investment", "ekonomi", "economy", "para", "money", "personal finance", "kişisel finans"]
    }
]

# Kritik 5'i ele almak için varsayılan yetenek tanımı.
DEFAULT_SKILL = {
    "name": "Eleştirel Düşünme ve Problem Çözme",
    "explanation": "Hangi alanda olursanız olun, karmaşık durumları anlama ve etkili çözümler üretme yeteneği başarının temelini oluşturur."
}

def run_action(parameters):
    """
    Bu fonksiyon, verilen parametrelere göre veya varsayılan olarak yararlı bir yetenek seçer ve hakkında bilgi verir.
    Yetenek seçimi, dışarıdan yapılandırılmış bir veri seti üzerinden skorlama sistemiyle yapılır,
    böylece daha sürdürülebilir, genişletilebilir ve esnektir.

    Parametreler:
        parameters (dict): Yararlı yetenek seçimi için ipuçları içerebilecek bir sözlük.
                           Örnek anahtarlar: "preference" (tercih), "field" (alan).

    Dönüş:
        str: Seçilen yararlı yetenek ve neden önemli olduğuna dair bir açıklama.
    """
    preference_input = parameters.get("preference", "").lower()
    field_input = parameters.get("field", "").lower()

    # Kritik 2'yi ele almak için girdiyi normalleştirme ve anahtar kelime eşleştirme hassasiyetini artırma.
    # Tek kelimeli anahtar kelimeler için kelime setini, çok kelimeli anahtar kelimeler için tüm metni kullanırız.
    combined_input_text = f"{preference_input} {field_input}".strip()
    search_words = set(combined_input_text.split())

    best_skill = DEFAULT_SKILL
    max_score = 0
    feedback_message = ""

    # Kritik 3'ü ele almak için skorlama sistemini kullanma. En yüksek skora sahip yetenek seçilir.
    # Eşit skorlarda, listede ilk bulunan yetenek öncelikli olur.
    for skill in SKILLS_DATA:
        current_score = 0
        for keyword in skill["keywords"]:
            # Çok kelimeli anahtar kelimeler için tam ifade eşleşmesine öncelik verilir (daha yüksek skor).
            if " " in keyword:
                if keyword in combined_input_text:
                    current_score += 2 # Çok kelimeli eşleşmeler daha güçlü bir tercih gösterir
            else:  # Tek kelimeli anahtar kelimeler
                if keyword in search_words:
                    current_score += 1

        if current_score > max_score:
            max_score = current_score
            best_skill = skill

    # Kritik 5'i ele almak için varsayılan seçildiğinde kullanıcıya geri bildirim sağlama.
    if max_score == 0:
        feedback_message = "Tercihlerinizle doğrudan eşleşen özel bir yetenek bulunamadı, bu yüzden genel geçer bir öneride bulunduk."

    output_parts = [f"Seçilen Yararlı Yetenek: {best_skill['name']}"]
    if feedback_message:
        output_parts.append(f"Not: {feedback_message}")
    output_parts.append(f"Neden Önemli: {best_skill['explanation']}")

    # Kritik 8'i ele almak için güvenlik notu:
    # Bu fonksiyonun çıktısı, dahili olarak tanımlanmış (SKILLS_DATA, DEFAULT_SKILL) verilerden oluşturulur.
    # Ham kullanıcı girdisi doğrudan açıklama metinlerine dahil edilmediği için,
    # doğrudan XSS (Cross-Site Scripting) veya komut enjeksiyonu gibi güvenlik riskleri minimaldir.
    # Ancak, eğer `parameters` içindeki değerler herhangi bir sanitizasyon işlemi olmadan doğrudan çıktıya eklenseydi,
    # potansiyel riskler ortaya çıkabilirdi.

    return "\n".join(output_parts)

TOOL_NAME: useful_skill_selector