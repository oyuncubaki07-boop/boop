def run_action(parameters):
    """
    Yeni yeteneklerin bir organizasyona entegrasyon sürecini yönetir.
    Bu fonksiyon, yetenek bilgilerini alır ve entegrasyon adımlarını simüle eder
    veya gerçek sistemlerdeki ilgili operasyonları tetikler.

    Args:
        parameters (dict): Yeni yeteneğe ait bilgileri içeren bir sözlük.
                           Beklenen anahtarlar:
                           - 'talent_name' (str): Yeteneğin adı.
                           - 'talent_id' (str): Yeteneğin benzersiz kimliği.
                           - 'skills' (list, isteğe bağlı): Yeteneğin sahip olduğu beceriler listesi.
                           - 'preferred_team_type' (str, isteğe bağlı): Yeteneğin tercih ettiği takım türü (örn: 'Yazılım', 'Pazarlama').
                           - 'start_date' (str, isteğe bağlı): Yeteneğin başlangıç tarihi (YYYY-MM-DD formatında).
                           - 'manager_id' (str, isteğe bağlı): Atanacak yöneticinin kimliği.
                           - 'onboarding_checklist' (list, isteğe bağlı): Özel ek onboarding görevleri.

    Returns:
        dict: Entegrasyon sürecinin durumu, mesajı ve detaylarını içeren bir sözlük.
              Örnek:
              {
                  "status": "success",
                  "message": "Entegrasyon süreci başarıyla tamamlandı.",
                  "talent_id": "TY001",
                  "talent_name": "Ayşe Yılmaz",
                  "details": [
                      {"step": "Profil Oluşturma", "status": "completed"},
                      {"step": "Onboarding Görev Ataması", "tasks": [...], "status": "completed"},
                      ...
                  ],
                  "final_recommendation": "Yazılım Geliştirme Takımı",
                  "assigned_manager": "MGR101",
                  "assigned_mentor": "Mentor A"
              }
    """
    talent_name = parameters.get('talent_name')
    talent_id = parameters.get('talent_id')
    skills = parameters.get('skills', [])
    preferred_team_type = parameters.get('preferred_team_type', 'genel')
    start_date = parameters.get('start_date', 'Belirtilmedi')
    manager_id = parameters.get('manager_id', 'Atanmadı')
    onboarding_checklist = parameters.get('onboarding_checklist', [])

    if not talent_name or not talent_id:
        return {
            "status": "error",
            "message": "Parametrelerde 'talent_name' veya 'talent_id' eksik."
        }

    integration_steps = []
    integration_status = "success"
    integration_message = f"{talent_name} (ID: {talent_id}) için entegrasyon süreci başlatıldı."

    print(f"--- Yeni Yetenek Entegrasyonu Başlatılıyor: {talent_name} (ID: {talent_id}) ---")

    # Adım 1: İlk Kurulum ve Profil Oluşturma
    print(f"1. {talent_name} için yetenek profili oluşturuluyor...")
    # Gerçek bir uygulamada burada veritabanına kayıt veya bir HR sistemine API çağrısı yapılır.
    integration_steps.append({"step": "Profil Oluşturma", "status": "completed"})
    print("   Profil başarıyla oluşturuldu.")

    # Adım 2: Onboarding Görevlerinin Atanması
    print(f"2. İlk onboarding görevleri atanıyor...")
    default_onboarding_tasks = [
        "İnsan Kaynakları evraklarını tamamlama",
        "Kurumsal e-posta ve iletişim araçlarını kurma",
        "Şirket politikalarını gözden geçirme",
        "Hoş geldin oturumuna katılma"
    ]
    all_onboarding_tasks = default_onboarding_tasks + onboarding_checklist
    # Gerçek bir uygulamada burada bir görev yönetim sistemine görevler eklenir.
    integration_steps.append({
        "step": "Onboarding Görev Ataması",
        "tasks": all_onboarding_tasks,
        "status": "completed"
    })
    print(f"   {len(all_onboarding_tasks)} adet onboarding görevi atandı.")

    # Adım 3: Beceri Eşleştirme ve Takım Önerisi
    print(f"3. Beceriler eşleştiriliyor: {', '.join(skills) if skills else 'Beceri belirtilmedi'}")
    # Gerçek bir uygulamada burada mevcut projeler/takımlarla beceri eşleştirme algoritması çalıştırılır.
    recommended_team = f"'{preferred_team_type}' ve becerilere göre bir takım (örn: Proje X Takımı)"
    integration_steps.append({
        "step": "Beceri Eşleştirme ve Takım Önerisi",
        "recommended_team": recommended_team,
        "status": "completed"
    })
    print(f"   Önerilen yerleştirme: {recommended_team}.")

    # Adım 4: Kaynak Sağlama
    print(f"4. Gerekli kaynaklar (yazılım lisansları, donanım vb.) sağlanıyor...")
    # Gerçek bir uygulamada burada IT veya ilgili departmanlara talep gönderilir.
    integration_steps.append({"step": "Kaynak Sağlama", "status": "completed"})
    print("   Kaynaklar sağlandı.")

    # Adım 5: Yönetici ve Mentor Ataması (eğer uygulanabilirse)
    print(f"5. Yönetici atanıyor ve bir mentor belirleniyor...")
    # Gerçek bir uygulamada burada bir atama sistemi veya yöneticinin onayı beklenir.
    assigned_mentor = "Mentor X"  # Yer tutucu
    integration_steps.append({
        "step": "Yönetici ve Mentor Ataması",
        "manager_id": manager_id,
        "mentor": assigned_mentor,
        "status": "completed"
    })
    print(f"   Yönetici: {manager_id}, Mentor: {assigned_mentor}.")

    print(f"--- {talent_name} için entegrasyon süreci tamamlandı ---")

    return {
        "status": integration_status,
        "message": integration_message,
        "talent_id": talent_id,
        "talent_name": talent_name,
        "details": integration_steps,
        "final_recommendation": recommended_team,
        "assigned_manager": manager_id,
        "assigned_mentor": assigned_mentor
    }