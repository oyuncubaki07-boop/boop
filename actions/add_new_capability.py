def run_action(params):
    feature_name = params.get('feature_name')
    feature_description = params.get('feature_description')

    if not feature_name:
        return {"status": "error", "message": "'feature_name' parametresi zorunludur."}
    if not feature_description:
        return {"status": "error", "message": "'feature_description' parametresi zorunludur."}

    try:
        # Bu iç fonksiyon, sisteme kaydedilecek ve daha sonra bir yetenek olarak çağrıldığında çalıştırılacaktır.
        # 'inner_kwargs' parametreleri, bu kaydedilmiş yetenek çağrıldığında kendisine iletilen argümanları temsil eder.
        def new_feature_function(**inner_kwargs):
            return {
                "status": "active",
                "feature_name": feature_name,
                "description": feature_description,
                "message": f"'{feature_name}' özelliği başarıyla etkinleştirildi ve çalışıyor.",
                "parameters_received": inner_kwargs
            }

        # _capabilities_registry ve register_capability'nin aracı çalıştıran ortamda (global kapsamda) 
        # zaten tanımlanmış ve erişilebilir olduğu varsayılır. Bu, bir yetenek kayıt sisteminin 
        # standart çalışma şeklidir.
        global _capabilities_registry, register_capability 
        
        register_capability(feature_name, new_feature_function)

        return {"status": "success", "message": f"'{feature_name}' adlı yeni özellik başarıyla eklendi ve kaydedildi."}

    except ValueError as ve:
        # 'register_capability' içinde bir yetenek zaten varsa fırlatılan özel hatayı yakala.
        return {"status": "error", "message": f"'{feature_name}' özelliği eklenirken hata oluştu: {str(ve)}"}
    except NameError as ne:
        # _capabilities_registry veya register_capability ortamda bulunamazsa bu hatayı yakala.
        return {"status": "error", "message": f"'{feature_name}' özelliği eklenirken hata oluştu: Temel yetenek kayıt sistemi bulunamadı veya düzgün başlatılmadı ({str(ne)})."}
    except Exception as e:
        # Diğer beklenmeyen hataları yakala.
        return {"status": "error", "message": f"'{feature_name}' özelliği eklenirken beklenmeyen bir hata oluştu: {str(e)}"}