# actions/weather_report.py
# J.A.R.V.I.S. Hava Durumu Modülü - Gelişmiş Sürüm
# wttr.in üzerinden anlık ve tahmin hava durumu bilgisi sağlar.

import requests
import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Hata kodları ve kullanıcı dostu mesajlar
ERROR_MESSAGES = {
    "timeout": "Bağlantı zaman aşımına uğradı. Lütfen internet bağlantınızı kontrol edin.",
    "connection": "Hava durumu sunucusuna bağlanılamıyor. Ağınızı kontrol edin.",
    "404": "Belirtilen şehir bulunamadı. Lütfen geçerli bir şehir adı girin.",
    "500": "Hava durumu sunucusunda geçici bir sorun oluştu. Daha sonra tekrar deneyin.",
    "unknown": "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin."
}

def weather_action(parameters: Optional[Dict] = None, player=None, speak=None) -> str:
    """
    Hava durumu bilgisi getirir.
    
    Parametreler:
        city (str): Şehir adı (varsayılan: "Konya")
        days (int): Kaç günlük tahmin (0: bugün, 1: yarın, 2: 2 gün sonra) varsayılan: 0
        units (str): Birim sistemi "m" (metric, °C, km/h) veya "u" (imperial, °F, mph) varsayılan: "m"
        detailed (bool): Detaylı rapor (nem, basınç, görüş, UV) varsayılan: False
    """
    params = parameters or {}
    city = params.get("city", "Konya").strip()
    days = int(params.get("days", 0))
    units = params.get("units", "m").lower()
    detailed = params.get("detailed", False)
    
    # Birim kontrolü
    if units not in ["m", "u"]:
        units = "m"
    
    # Gün sayısını wttr.in formatına çevir (0=bugün, 1=yarın, 2=2 gün sonra, 3=3 gün...)
    # wttr.in'de ?0, ?1, ?2 şeklinde
    forecast_flag = f"?{days}" if days > 0 else ""
    
    if player:
        player.write_log(f"SYS: 🌤️ Hava durumu isteği -> Şehir: {city}, Gün: {days}, Birim: {units}, Detay: {detailed}")
    
    try:
        # wttr.in URL'si oluştur
        # Format: %t (sıcaklık), %C (durum), %w (rüzgar), %h (nem), %p (basınç), %V (görüş), %u (nem? karıştı)
        # Standart format: Sıcaklık | Durum | Rüzgar | Nem | Basınç | Görüş
        if detailed:
            # Detaylı format: t (sıcaklık), C (durum), w (rüzgar), h (nem), p (basınç), V (görüş), u (nem? tekrar)
            # wttr.in %u nem değil, "umidity"? Aslında %h nem, %p basınç, %V görüş.
            format_str = "%t+%C+%w+%h+%p+%V"
        else:
            format_str = "%t+%C+%w"
        
        # Metric için varsayılan; imperial için &u eklenir (wttr.in'de &u)
        url = f"https://wttr.in/{city}{forecast_flag}?format={format_str}&{units}"
        
        # İstek gönder (timeout 8 saniye)
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            raw_data = response.text.strip()
            
            # Eğer şehir bulunamazsa wttr.in "Unknown location" benzeri döner
            if "Unknown" in raw_data or "sorry" in raw_data.lower():
                return f"'{city}' şehri bulunamadı, patron. Lütfen geçerli bir şehir adı girin."
            
            # Veriyi parse et ve güzel bir metin oluştur
            if detailed:
                # Detaylı veri: sıcaklık, durum, rüzgar, nem, basınç, görüş
                parts = raw_data.split()
                # wttr.in boşluklarla ayırır, ancak durum birden çok kelime olabilir (örn: "Partly cloudy")
                # Basitçe ilk token sıcaklık, sonraki tokenlar durum, sonra rüzgar, nem, basınç, görüş
                # Daha kararlı olması için wttr.in'den JSON almak daha iyi, ama format ile uğraşmak yerine
                # alternatif olarak 2. istek atabiliriz. Ancak performans için mevcut haliyle devam.
                # En doğrusu: `?format=j1` ile JSON alıp işlemek. Bunu yapalım.
                return _get_detailed_weather(city, days, units, player)
            else:
                # Basit format: Sıcaklık | Durum | Rüzgar
                parts = raw_data.split()
                if len(parts) >= 3:
                    temp = parts[0]
                    condition = " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                    wind = parts[-1]
                    # Rüzgar birimini düzenle
                    if units == "m":
                        wind_unit = "km/sa"
                    else:
                        wind_unit = "mph"
                    return f"{city} için hava durumu: {temp}, {condition}, rüzgar {wind} {wind_unit}. Başka bir arzunuz var mı patron?"
                else:
                    # Beklenmedik format
                    return f"{city} hava durumu: {raw_data}"
        else:
            # HTTP hata kodlarına özel mesaj
            error_key = str(response.status_code)
            if error_key in ERROR_MESSAGES:
                return ERROR_MESSAGES[error_key]
            else:
                return f"Hava durumu alınamadı (HTTP {response.status_code}). Lütfen daha sonra tekrar deneyin."
    
    except requests.exceptions.Timeout:
        if player:
            player.write_log("SYS: Hava durumu sunucusu zaman aşımı.")
        return ERROR_MESSAGES["timeout"]
    except requests.exceptions.ConnectionError:
        if player:
            player.write_log("SYS: Hava durumu sunucusuna bağlantı hatası.")
        return ERROR_MESSAGES["connection"]
    except Exception as exc:
        if player:
            player.write_log(f"SYS: Hava durumu modülü hatası: {exc}")
        return f"Hava durumu çekilirken hata oluştu: {str(exc)}"

def _get_detailed_weather(city: str, days: int, units: str, player) -> str:
    """wttr.in'den JSON formatında detaylı hava durumu alır ve güzel bir metin oluşturur."""
    # wttr.in JSON endpoint'i
    url = f"https://wttr.in/{city}?format=j1&{units}"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return "Detaylı hava durumu alınamadı."
        data = resp.json()
        
        # Mevcut durum (current_condition)
        current = data.get("current_condition", [{}])[0]
        temp = current.get("temp_C" if units == "m" else "temp_F", "?")
        feels_like = current.get("FeelsLikeC" if units == "m" else "FeelsLikeF", "?")
        humidity = current.get("humidity", "?")
        pressure = current.get("pressure", "?")
        wind_speed = current.get("windspeedKmph" if units == "m" else "windspeedMiles", "?")
        wind_dir = current.get("winddir16Point", "?")
        visibility = current.get("visibility", "?")
        uv_index = current.get("uvIndex", "?")
        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "bilinmiyor")
        
        # Gün doğumu/batımı (astronomy)
        astronomy = data.get("weather", [{}])[0].get("astronomy", [{}])[0] if days == 0 else {}
        sunrise = astronomy.get("sunrise", "?")
        sunset = astronomy.get("sunset", "?")
        
        # Tahmin (eğer days > 0 ise ilgili günü al)
        forecast_days = data.get("weather", [])
        if days < len(forecast_days):
            forecast = forecast_days[days]
            max_temp = forecast.get("maxtempC" if units == "m" else "maxtempF", "?")
            min_temp = forecast.get("mintempC" if units == "m" else "mintempF", "?")
            chance_rain = forecast.get("hourly", [{}])[0].get("chanceofrain", "0") if forecast.get("hourly") else "0"
        else:
            max_temp = min_temp = chance_rain = "?"
        
        # Gün adı
        if days == 0:
            day_name = "Bugün"
        elif days == 1:
            day_name = "Yarın"
        else:
            # Tarih hesapla
            from datetime import timedelta
            target_date = datetime.now() + timedelta(days=days)
            day_name = target_date.strftime("%A")  # Pazartesi, Salı...
        
        # Ölçü birimleri
        temp_unit = "°C" if units == "m" else "°F"
        speed_unit = "km/sa" if units == "m" else "mph"
        
        # Rapor metni oluştur
        report = f"{city} için {day_name} hava durumu:\n"
        report += f"🌡️ Sıcaklık: {temp}{temp_unit} (hissedilen {feels_like}{temp_unit})\n"
        if days == 0:
            report += f"☁️ Durum: {weather_desc}\n"
        else:
            report += f"🌡️ En yüksek: {max_temp}{temp_unit}, En düşük: {min_temp}{temp_unit}\n"
            report += f"🌧️ Yağmur ihtimali: %{chance_rain}\n"
        report += f"💧 Nem: %{humidity}\n"
        report += f"🌬️ Rüzgar: {wind_speed} {speed_unit}, {wind_dir}\n"
        report += f"🔆 UV İndeksi: {uv_index}\n"
        report += f"👁️ Görüş: {visibility} km\n"
        report += f"⏲️ Basınç: {pressure} hPa\n"
        if sunrise != "?":
            report += f"🌅 Gün doğumu: {sunrise}, Gün batımı: {sunset}\n"
        
        return report.strip()
    
    except Exception as e:
        if player:
            player.write_log(f"SYS: Detaylı hava durumu JSON hatası: {e}")
        return f"Detaylı hava durumu alınamadı: {str(e)}"