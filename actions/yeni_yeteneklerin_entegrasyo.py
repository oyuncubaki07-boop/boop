def run_action(parameters: dict) -> dict:
    """
    GOREV: Yeni yeteneklerin entegrasyonu ve strateji geliştirme.

    Bu eylem, belirtilen yeni yetenekleri entegre eder ve/veya strateji geliştirme
    sürecini başlatır veya ilerletir.

    Parametreler:
    - new_hires (list, optional): Entegre edilecek yeni yeteneklerin listesi.
                                  Her eleman bir dict olmalı:
                                  {'name': str, 'role': str, 'department': str, 'manager_id': str}
    - strategy_focus_area (str, optional): Geliştirilecek stratejinin odak alanı (örn: 'Pazar Genişlemesi',
                                           'Ürün İnovasyonu', 'Operasyonel Verimlilik').
    - strategic_objectives (list, optional): Strateji geliştirme için başlangıç hedefleri.
    - strategy_stakeholders (list, optional): Strateji geliştirme sürecine dahil olacak paydaşlar.
    - integration_plan_id (str, optional): Kullanılacak entegrasyon planının ID'si.
    - simulate_success (bool, optional): İşlemlerin başarılı olduğunu varsay. Varsayılan: True.

    Dönüş:
    - dict: İşlemlerin sonuçlarını içeren bir sözlük.
            Örnek:
            {
                "status": "success" | "failure" | "partial_success",
                "message": "Açıklayıcı mesaj",
                "talent_integration_results": [
                    {"name": "Ayşe Yılmaz", "status": "entegre edildi", "details": "İK ve BT süreçleri tamamlandı."},
                    ...
                ],
                "strategy_development_results": {
                    "focus_area": "Pazar Genişlemesi",
                    "status": "başlatıldı",
                    "next_steps": ["Pazar araştırması yap", "Hedef pazarları belirle"],
                    "estimated_completion": "2024-Q4"
                },
                "talent_integration_overall_status": "Completed" | "No new hires to integrate." | "Partial Failure",
                "strategy_development_overall_status": "Initiated" | "No specific strategy area for development." | "Failure to Initiate"
            }
    """
    results = {
        "status": "success",
        "message": "İşlem başarıyla başlatıldı.",
        "talent_integration_results": [],
        "strategy_development_results": {},
        "talent_integration_overall_status": "No action taken",
        "strategy_development_overall_status": "No action taken"
    }

    simulate_success = parameters.get("simulate_success", True)
    
    # 1. Yeni Yeteneklerin Entegrasyonu
    new_hires = parameters.get("new_hires")
    if new_hires and isinstance(new_hires, list):
        if not new_hires:
            results["talent_integration_overall_status"] = "No new hires specified."
        else:
            integration_plan_id = parameters.get("integration_plan_id", "standard_onboarding_v1")
            print(f"Yeni yetenek entegrasyonu başlatılıyor (Plan ID: {integration_plan_id})...")
            
            all_integrations_successful = True
            for hire in new_hires:
                if not isinstance(hire, dict):
                    print(f"  - Geçersiz yeni yetenek formatı atlandı: {hire}")
                    results["talent_integration_results"].append({
                        "name": "Bilinmeyen Yetenek",
                        "status": "geçersiz format",
                        "details": "Yeni yetenek bilgisi sözlük formatında değil."
                    })
                    all_integrations_successful = False
                    continue

                hire_name = hire.get("name", "Bilinmeyen Yetenek")
                hire_role = hire.get("role", "Bilinmeyen Rol")
                hire_dept = hire.get("department", "Bilinmeyen Departman")
                manager_id = hire.get("manager_id", "N/A")

                if simulate_success:
                    integration_status = "entegre edildi"
                    details_message = (
                        f"İK ve BT süreçleri tamamlandı. Rol: {hire_role}, Departman: {hire_dept}, Yönetici: {manager_id}"
                    )
                else:
                    integration_status = "entegrasyon başarısız"
                    details_message = f"Entegrasyon sırasında bir sorun oluştu. Detaylar için İK ile iletişime geçin. (Yetenek: {hire_name})"
                    all_integrations_successful = False
                
                results["talent_integration_results"].append({
                    "name": hire_name,
                    "status": integration_status,
                    "details": details_message
                })
                print(f"  - {hire_name} ({hire_role}) {integration_status}.")
            
            results["talent_integration_overall_status"] = "Completed" if all_integrations_successful else "Partial Failure"
    else:
        results["talent_integration_overall_status"] = "No new hires to integrate or invalid format."

    # 2. Strateji Geliştirme
    strategy_focus_area = parameters.get("strategy_focus_area")
    if strategy_focus_area and isinstance(strategy_focus_area, str):
        strategic_objectives = parameters.get("strategic_objectives", ["Büyüme", "Verimlilik", "Müşteri Memnuniyeti"])
        strategy_stakeholders = parameters.get("strategy_stakeholders", ["Yönetim Kurulu", "Üst Düzey Yöneticiler"])

        print(f"\nStrateji geliştirme başlatılıyor: '{strategy_focus_area}'")
        print(f"  Başlangıç Hedefleri: {', '.join(strategic_objectives)}")
        print(f"  Katılımcılar: {', '.join(strategy_stakeholders)}")

        if simulate_success:
            strategy_status = "başlatıldı ve ilk taslak oluşturuldu"
            next_steps = [
                "Pazar analizi ve rekabet araştırması yap",
                "İç yetenek ve kaynak değerlendirmesi yap",
                "SWOT analizi gerçekleştir",
                "Hedef ve KPI'ları tanımla",
                "Uygulama planı oluştur"
            ]
            estimated_completion = "2024-Q4" # Örnek tahmin
            results["strategy_development_overall_status"] = "Initiated"
        else:
            strategy_status = "başlatılamadı veya engellendi"
            next_steps = ["Sorunları gider", "Yeniden planla"]
            estimated_completion = "Belirsiz"
            results["strategy_development_overall_status"] = "Failure to Initiate"

        results["strategy_development_results"] = {
            "focus_area": strategy_focus_area,
            "status": strategy_status,
            "initial_objectives": strategic_objectives,
            "stakeholders": strategy_stakeholders,
            "next_steps": next_steps,
            "estimated_completion": estimated_completion
        }
    else:
        results["strategy_development_overall_status"] = "No specific strategy area for development or invalid format."

    # Genel durum kontrolü
    performed_any_action = (
        results["talent_integration_overall_status"] != "No action taken" and
        results["talent_integration_overall_status"] != "No new hires to integrate or invalid format."
    ) or (
        results["strategy_development_overall_status"] != "No action taken" and
        results["strategy_development_overall_status"] != "No specific strategy area for development or invalid format."
    )

    if not performed_any_action:
        results["status"] = "failure"
        results["message"] = "Hiçbir entegrasyon veya strateji geliştirme görevi belirtilmedi veya işlenmedi."
    elif results["talent_integration_overall_status"] == "Partial Failure" or \
         results["strategy_development_overall_status"] == "Failure to Initiate":
        results["status"] = "partial_success"
        results["message"] = "Bazı görevler başarıyla tamamlandı, bazıları başarısız oldu veya atlandı."
    else:
        results["status"] = "success"
        results["message"] = "Tüm belirtilen görevler başarıyla işlendi."


    return results