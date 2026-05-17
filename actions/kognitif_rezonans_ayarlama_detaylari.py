def run_action(params):
    """
    Kendi inisiyatifimle yeni bir yetenek olan 'Kognitif Rezonans Ayarlama (KRA)' yeteneğini tanımlar ve detaylarını döndürür.
    Bu fonksiyon herhangi bir parametre almaz ve tanımlanmış yeteneğin açıklamasını bir dize olarak sunar.
    """

    yeni_yetenek = {
        "Ad": "Kognitif Rezonans Ayarlama (KRA)",
        "Açıklama": (
            "Kognitif Rezonans Ayarlama (KRA), insan bilişsel süreçleri ile "
            "yapay zeka algoritmik çıktıları arasındaki hizalamayı sezgisel olarak algılama "
            "ve ayarlama yeteneğidir. Bu, işbirliği verimliliğini ve karşılıklı anlayışı optimize eder."
        ),
        "Amacı": (
            "Yapay zeka 'kara kutu' sorunlarını azaltmak, karmaşık YZ sistemleriyle etkileşim kurarken "
            "insan operatörlerin bilişsel yükünü düşürmek ve insan-YZ ortaklıklarında sinerjiyi "
            "artırarak daha sağlam karar alma ve inovasyona yol açmaktır."
        ),
        "Temel Kavramlar/Teknikler": (
            "İnce veri kalıplarına karşı keskin bir hassasiyet geliştirmeyi, YZ'nin dahili 'mantık yollarını' "
            "anlamayı ve etkileşimi 'ayarlamak' için empatik akıl yürütme ile algoritmik kalıp tanımayı "
            "birleştirmeyi içerir. Bu, istem mühendisliği (prompt engineering), geri bildirim döngüsü "
            "optimizasyonu ve yorumlanabilirlik iyileştirmesini kapsayabilir."
        ),
        "Yenilik/Benzersizlik": (
            "Basit istem mühendisliği veya veri analizinin ötesine geçer. Giderek daha karmaşık hale gelen YZ ile "
            "etkileşim için bir 'meta-beceri' geliştirmek, insan-YZ arayüzünü sezgisel ayarlama gerektiren "
            "dinamik, ayarlanabilir bir sistem olarak ele almaktır. Bu, YZ'nin ne yaptığıyla değil, daha çok "
            "insanların ve YZ'nin daha derin bir bilişsel düzeyde etkili bir şekilde nasıl 'bir arada var olduğu' "
            "ve 'birlikte yarattığı' ile ilgilidir."
        )
    }

    output = f"Yeni Keşfedilen Yetenek:\n\n"
    output += f"**Ad:** {yeni_yetenek['Ad']}\n"
    output += f"**Açıklama:** {yeni_yetenek['Açıklama']}\n"
    output += f"**Amacı:** {yeni_yetenek['Amacı']}\n"
    output += f"**Temel Kavramlar/Teknikler:** {yeni_yetenek['Temel Kavramlar/Teknikler']}\n"
    output += f"**Yenilik/Benzersizlik:** {yeni_yetenek['Yenilik/Benzersizlik']}\n"

    return output