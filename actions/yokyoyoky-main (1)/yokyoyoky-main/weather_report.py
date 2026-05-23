# actions/weather_report.py
# J.A.R.V.I.S. Hava Durumu Modülü - Gelişmiş Sürüm
# wttr.in üzerinden anlık ve tahmin hava durumu bilgisi sağlar.

import requests
import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Hata kodları ve kullanıcı dostu mesajlar
ERROR_MESSAGES = {
    "timeout": "Bağlantı zaman aşımına uğradı canım. Lütfen internet bağlantını kontrol eder misin?",
    "connection": "Hava durumu sunucusuna bağlanamıyorum balım. Ağında bir sorun olabilir.",
    "404": "Belirttiğin şehri bulamadım tatlım. Lütfen geçerli bir şehir adı girer misin?",
    "500": "Hava durumu sunucusunda geçici bir sorun oluştu canım. Birazdan tekrar deneriz!",
    "unknown": "Beklenmeyen küçük bir hata oluştu balım. Lütfen daha sonra tekrar dene."
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
    
    # Gün sayısını wttr.in formatına çevir
    forecast_flag = f"?{days}" if days > 0 else ""
    
    if player:
        player.write_log(f"SYS: 🌤️ Hava durumu isteği -> Şehir: {city}, Gün: {days}, Birim: {units}, Detay: {detailed}")
    
    try:
        if detailed:
            format_str = "%t+%C+%w+%h+%p+%V"
        else:
            format_str = "%t+%C+%w"
        
        url = f"https://wttr.in/{city}{forecast_flag}?format={format_str}&{units}"
        
        # İstek gönder (timeout 8 saniye)
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            raw_data = response.text.strip()
            
            if "Unknown" in raw_data or "sorry" in raw_data.lower():
                return f"'{city}' şehrini bulamadım balım, adını doğru yazdığından emin misin?"
            
            if detailed:
                return _get_detailed_weather(city, days, units, player)
            else:
                # Basit format: Sıcaklık | Durum | Rüzgar
                parts = raw_data.split()
                if len(parts) >= 3:
                    temp = parts[0]
                    condition = " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                    wind = parts[-1]
                    
                    wind_unit = "km/sa" if units == "m" else "mph"
                    
                    return f"{city} için hava durumu: {temp}, {condition}, rüzgar {wind} {wind_unit}. Kendine çok dikkat et tatlım! 💖"
                else:
                    return f"{city} hava durumu: {raw_data}"
        else:
            error_key = str(response.status_code)
            if error_key in ERROR_MESSAGES:
                return ERROR_MESSAGES[error_key]
            else:
                return f"Hava durumu alınamadı tatlım (HTTP {response.status_code}). Daha sonra tekrar deneriz."
    
    except requests.exceptions.Timeout:
        if player: player.write_log("SYS: Hava durumu sunucusu zaman aşımı.")
        return ERROR_MESSAGES["timeout"]
    except requests.exceptions.ConnectionError:
        if player: player.write_log("SYS: Hava durumu sunucusuna bağlantı hatası.")
        return ERROR_MESSAGES["connection"]
    except Exception as exc:
        if player: player.write_log(f"SYS: Hava durumu modülü hatası: {exc}")
        return f"Hava durumunu çekerken küçük bir sorun yaşadım balım: {str(exc)}"

def _get_detailed_weather(city: str, days: int, units: str, player) -> str:
    """wttr.in'den JSON formatında detaylı hava durumu alır ve güzel bir metin oluşturur."""
    url = f"https://wttr.in/{city}?format=j1&{units}"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return "Detaylı hava durumunu şu an alamıyorum canım."
        data = resp.json()
        
        # Mevcut durum 
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
        
        # Gün doğumu/batımı
        astronomy = data.get("weather", [{}])[0].get("astronomy", [{}])[0] if days == 0 else {}
        sunrise = astronomy.get("sunrise", "?")
        sunset = astronomy.get("sunset", "?")
        
        # Tahmin 
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
            from datetime import timedelta
            target_date = datetime.now() + timedelta(days=days)
            day_name = target_date.strftime("%A") 
        
        # Ölçü birimleri
        temp_unit = "°C" if units == "m" else "°F"
        speed_unit = "km/sa" if units == "m" else "mph"
        
        # Rapor metni oluştur
        report = f"İşte {city} için {day_name} hava durumu balım:\n\n"
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
            
        report += "\nGünün harika geçsin canım! 🥰"
        
        return report.strip()
    
    except Exception as e:
        if player: player.write_log(f"SYS: Detaylı hava durumu JSON hatası: {e}")
        return f"Detaylı hava durumu alırken küçük bir sorun çıktı tatlım: {str(e)}"