import random
from typing import Dict, Any, Optional

# Modül seviyesinde tanımlanarak her çağrıda yeniden oluşturulmayı önler.
_USEFUL_SKILLS: Dict[str, str] = {
    "Kritik Düşünme": "Bilgiyi objektif olarak analiz etme ve mantıksal yargılarda bulunma yeteneğidir. Karar verme süreçlerinizi geliştirir ve karmaşık sorunları çözmenize yardımcı olur.",
    "Problem Çözme": "Karşılaşılan zorlukları tanımlama, analiz etme ve etkili çözümler bulma becerisidir. Hem kişisel hem de profesyonel yaşamda sürekli karşılaşılan engelleri aşmak için değerlidir.",
    "Etkili İletişim": "Düşünceleri, fikirleri ve bilgiyi açık, öz ve ikna edici bir şekilde aktarabilme yeteneğidir. İlişkileri güçlendirir, yanlış anlaşılmaları azaltır ve işbirliğini artırır.",
    "Zaman Yönetimi": "Görevleri önceliklendirme ve zamanı verimli kullanma sanatıdır. Üretkenliği artırır, stresi azaltır ve hedeflerinize ulaşmanızı kolaylaştırır.",
    "Temel Programlama (Python)": "Temel düzeyde kod yazarak otomatik görevler oluşturma, veri işleme ve basit uygulamalar geliştirme becerisidir. Dijital çağda çok aranan ve kariyer gelişimine katkıda bulunan bir yetenektir.",
    "Veri Analizi": "Büyük veri setlerinden anlamlı içgörüler çıkarma ve bu verileri yorumlama yeteneğidir. Veriye dayalı karar alma süreçleri için vazgeçilmezdir ve stratejik düşünmeyi destekler.",
    "Finansal Okuryazarlık": "Para yönetimi, yatırım, bütçeleme ve borç yönetimi konularında bilgi sahibi olma ve doğru finansal kararlar verme yeteneğidir. Finansal bağımsızlık ve güvenlik için kritik öneme sahiptir.",
    "Duygusal Zeka": "Hem kendi hem de başkalarının duygularını anlama, yönetme ve empati kurma becerisidir. Liderlik, ekip çalışması ve kişilerarası ilişkilerde kilit rol oynar."
}


def run_action(parameters: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Yararlı bir yetenek seçer ve bu yetenek hakkında bilgiler döndürür.

    Args:
        parameters: Opsiyonel bir sözlük. Aşağıdaki anahtarlar desteklenir:
            - "skills": Kullanılacak yetenek sözlüğü (varsayılan: _USEFUL_SKILLS).
            - "include_message": True/False. True ise sonuçta hazır bir
              ``message`` alanı eklenir (varsayılan: True).

    Returns:
        {
            "chosen_skill": str,
            "description": str,
            "message": str   # sadece include_message=True olduğunda presenti
        }

    Raises:
        ValueError: Seçilebilecek yetenek listesi boş olduğunda.
    """
    if parameters is None:
        parameters = {}

    # Esneklik: parametre üzerinden özel bir yetenek listesi sağlanabilir.
    skill_set = parameters.get("skills", _USEFUL_SKILLS)
    if not isinstance(skill_set, dict) or not skill_set:
        raise ValueError("Yetenek listesi boş veya geçersiz bir sözlük sağlanamadı.")

    chosen_skill_name = random.choice(list(skill_set.keys()))
    chosen_skill_description = skill_set[chosen_skill_name]

    result: Dict[str, str] = {
        "chosen_skill": chosen_skill_name,
        "description": chosen_skill_description,
    }

    # Redundansı azaltmak için message sadece istenirse eklenir.
    if parameters.get("include_message", True):
        result["message"] = (
            f"Seçilen yararlı yetenek: {chosen_skill_name}\n\n"
            f"Açıklama: {chosen_skill_description}\n\n"
            f"Bu yeteneği geliştirmek, kişisel ve profesyonel yaşamınızda önemli faydalar sağlayacaktır!"
        )

    return result


# Örnek kullanım (modül doğrudan çalıştırıldığında)
if __name__ == "__main__":
    # Varsayılan yetenek listesiyle bir örnek
    print(run_action({}))
    # Özel bir yetenek listesi ve message kapatma örneği
    custom_skills = {
        "Öğrenme Yeteneği": "Yeni bilgileri hızlıca kavrama ve uygulama kapasitesi."
    }
    print(run_action({"skills": custom_skills, "include_message": False}))