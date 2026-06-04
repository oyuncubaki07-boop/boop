def run_action(parameters):
    """
    Bu fonksiyon, gelen 'parameters' sözlüğüne göre çeşitli eylemleri yönetmek için bir rehberdir.
    Genellikle bir otomasyon aracı, web kancası veya komut istemcisi tarafından çağrılır.

    Parametreler:
        parameters (dict): İşlenecek bilgileri içeren bir sözlük.
                           Örnek: {"action_type": "read_data", "id": 123, "filter": "active"}
    """
    print(f"run_action çağrıldı. Gelen parametreler: {parameters}")

    # --- 1. Parametreleri Ayrıştırma ve Doğrulama ---
    # Gelen parametreleri alıp, varsayılan değerler atayabilir veya doğrulayabilirsiniz.
    action_type = parameters.get("action_type", "unknown_action")
    item_id = parameters.get("id", None)
    data_payload = parameters.get("data", None)

    print(f"Tespit edilen eylem türü: {action_type}")
    if item_id:
        print(f"Hedef ID: {item_id}")
    if data_payload:
        print(f"Veri yükü: {data_payload}")

    # --- 2. Eylem Türüne Göre İş Mantığını Uygulama ---
    # Farklı 'action_type' değerlerine göre farklı işlemler gerçekleştirin.
    if action_type == "read_data":
        print(f"Veri okuma eylemi başlatılıyor. ID: {item_id if item_id else 'Tümü'}")
        # Burada veritabanından okuma, API'den veri çekme gibi işlemler yapılabilir.
        # Örnek:
        # try:
        #     result_data = my_database_api.get_item(item_id)
        #     return {"status": "success", "action": "read_data", "data": result_data}
        # except Exception as e:
        #     return {"status": "error", "action": "read_data", "message": str(e)}
        print("Okuma işlemi simülasyonu tamamlandı.")
        return {"status": "success", "action": "read_data", "message": f"ID {item_id} için veri okundu."}

    elif action_type == "write_data":
        print(f"Veri yazma/güncelleme eylemi başlatılıyor. ID: {item_id if item_id else 'Yeni'}, Veri: {data_payload}")
        if not data_payload:
            print("Hata: Yazılacak veri bulunamadı.")
            return {"status": "error", "action": "write_data", "message": "Yazılacak veri (data) eksik."}
        # Burada veritabanına yazma, API'ye POST etme gibi işlemler yapılabilir.
        print("Yazma işlemi simülasyonu tamamlandı.")
        return {"status": "success", "action": "write_data", "message": f"ID {item_id} için veri yazıldı.", "payload_received": data_payload}

    elif action_type == "delete_item":
        print(f"Öğe silme eylemi başlatılıyor. ID: {item_id}")
        if not item_id:
            print("Hata: Silinecek öğenin ID'si eksik.")
            return {"status": "error", "action": "delete_item", "message": "Silinecek ID eksik."}
        # Burada bir öğeyi silme işlemi yapılabilir.
        print("Silme işlemi simülasyonu tamamlandı.")
        return {"status": "success", "action": "delete_item", "message": f"ID {item_id} başarıyla silindi."}

    elif action_type == "perform_calculation":
        print(f"Hesaplama eylemi başlatılıyor. Veri: {data_payload}")
        if isinstance(data_payload, dict) and "num1" in data_payload and "num2" in data_payload:
            try:
                result = data_payload["num1"] + data_payload["num2"]
                print(f"Hesaplama sonucu: {result}")
                return {"status": "success", "action": "perform_calculation", "result": result}
            except TypeError:
                return {"status": "error", "action": "perform_calculation", "message": "Sayısal değerler bekleniyor."}
        else:
            return {"status": "error", "action": "perform_calculation", "message": "Geçersiz hesaplama parametreleri."}

    else:
        # Tanımlanmamış eylem türü durumunda geri dönüş.
        print(f"Bilinmeyen eylem türü: {action_type}. Varsayılan hata döndürülüyor.")
        return {"status": "error", "action": "unknown", "message": f"Bilinmeyen eylem türü: {action_type}"}

    # --- 3. Sonuç Döndürme ---
    # Her eylem sonunda, çağıran sisteme bir durum ve/veya sonuç döndürülmesi yaygın bir pratiktir.
    # Yukarıdaki 'return' ifadeleri zaten bu adımı gerçekleştirmektedir.