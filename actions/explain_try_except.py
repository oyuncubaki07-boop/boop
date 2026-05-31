def run_action(parameters):
    """
    Belirlenmiş yararlı bir yeteneği (örneğin, bir programlama konseptini) açıklar ve canlı bir örnekle gösterir.
    Bu örnekte, "Hata Yakalama (Try-Except Blokları)" yeteneği detaylandırılmıştır.

    Args:
        parameters (dict): Eylemin nasıl çalıştırılacağına dair parametreler.
                           Bu örnekte doğrudan kullanılmamaktadır ancak gelecekte
                           farklı yeteneklerin seçimi veya detaylandırılması için genişletilebilir.
                           Şu anda bu parametreye ihtiyaç duyulmamaktadır.
    """

    skill_name = "Hata Yakalama (Try-Except Blokları)"
    skill_description = """
    Python'da hata yakalama, programınızın çalışma zamanında oluşabilecek hataları
    (istisnaları) zarif bir şekilde yönetmek için kullanılan temel bir yetenektir.
    Bu, programınızın beklenmedik bir hata durumunda tamamen çökmesini engeller
    ve kullanıcıya daha bilgilendirici mesajlar gösterilmesine olanak tanır.

    **Nasıl Kullanılır:**
    - `'try'` bloğu, hata potansiyeli olan kodu içerir.
    - `'except'` bloğu, `'try'` bloğunda belirli bir hata türü oluştuğunda çalışacak kodu içerir.
    - `'else'` bloğu (isteğe bağlı), `'try'` bloğu hatasız tamamlanırsa çalışır.
    - `'finally'` bloğu (isteğe bağlı), hata oluşsa da oluşmasa da her zaman çalışır
      (örneğin, kaynakları serbest bırakmak için).

    **Örnek (Kodu çalıştırdığınızda aşağıdaki gibi bir etkileşim göreceksiniz):**
    """
    return skill_description