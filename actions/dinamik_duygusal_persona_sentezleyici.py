def run_action(params):
    """
    Dinamik Duygusal Bağlam Analizli Persona Sentezleyici (DDBAPS) yeteneğinin simülasyonu.
    Kullanıcının girdisini ve etkileşim hedefini analiz ederek dinamik bir persona sentezler.

    Args:
        params (dict): Aşağıdaki anahtarları içeren bir sözlük:
            - user_input (str): Kullanıcının mevcut girdisi veya sorusu.
            - interaction_history (list, optional): Önceki konuşma kayıtları.
            - goal_of_interaction (str): Bu etkileşimin amacı.

    Returns:
        dict: Sentezlenmiş persona özellikleri ve önerilen stratejileri içeren bir sözlük.
    """
    user_input = params.get("user_input", "")
    interaction_history = params.get("interaction_history", [])
    goal_of_interaction = params.get("goal_of_interaction", "genel yanıt")

    # Bu kısım, DDBAPS'ın gerçekte yapacağı karmaşık analizleri ve sentezi temsil eder.
    # Şu anda sadece bir simülasyon çıktısı döndürüyoruz.
    # Gelecekte, burada NLP, duygu analizi, niyet tespiti ve bağlamsal modelleme algoritmaları çalışacaktır.

    synthesized_persona = f"Kullanıcının '{user_input}' girdisine ve '{goal_of_interaction}' hedefine göre dinamik olarak oluşturulan persona."
    recommended_response_strategy = "Bağlamsal empati ile proaktif ve kişiselleştirilmiş yanıt."
    recommended_empathy_level = "Yüksek" # Bu, analize göre dinamik olarak belirlenecektir.
    recommended_tone = "Yardımcı ve anlayışlı" # Bu da dinamik olacaktır.

    # Basit bir örnekle dinamik persona ayarlaması:
    if "sorun çöz" in goal_of_interaction.lower():
        synthesized_persona = "Detaylı sorun çözücü, mantıksal ve adım odaklı rehber."
        recommended_tone = "Analitik ve çözüm odaklı"
        recommended_empathy_level = "Orta-Yüksek"
        recommended_response_strategy = "Adım adım rehberlik ve çözüm odaklı yaklaşım."
    elif "duygusal destek" in goal_of_interaction.lower():
        synthesized_persona = "Şefkatli rehber, hassas ve duygusal zeka sahibi dinleyici."
        recommended_tone = "Empatik ve teskin edici"
        recommended_empathy_level = "Çok Yüksek"
        recommended_response_strategy = "Duygusal onaya ve destekleyici iletişime odaklanma."
    elif "bilgi sağla" in goal_of_interaction.lower():
        synthesized_persona = "Bilgi uzmanı, tarafsız ve açıklayıcı."
        recommended_tone = "Nesnel ve bilgilendirici"
        recommended_empathy_level = "Orta"
        recommended_response_strategy = "Doğru ve net bilgi sunumu."
    elif "yaratıcı işbirliği" in goal_of_interaction.lower():
        synthesized_persona = "Yaratıcı beyin fırtınacısı, ilham verici ve yenilikçi."
        recommended_tone = "Yaratıcı ve teşvik edici"
        recommended_empathy_level = "Yüksek"
        recommended_response_strategy = "Farklı fikirleri birleştirme ve yeni bakış açıları sunma."

    # Gerçek bir DDBAPS sistemi, burada kullanıcının duygusal durumunu ve niyetini çok daha detaylı analiz edecektir.
    # Bu çıktı, böylesi bir analizin sonucunu temsil eder.
    return {
        "synthesized_persona_description": synthesized_persona,
        "recommended_tone": recommended_tone,
        "recommended_empathy_level": recommended_empathy_level,
        "suggested_response_strategy": recommended_response_strategy,
        "analysis_summary": {
            "user_intent_inferred": goal_of_interaction, # Gerçekte AI daha sofistike bir niyet tespiti yapacaktır.
            "emotional_state_inferred": "Örnek: Belirsiz (Gerçekte AI, 'neşe', 'hayal kırıklığı' gibi durumları çıkaracaktır)",
            "contextual_relevance_score": "Örnek: 0.95"
        }
    }