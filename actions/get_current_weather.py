def run_action(params):
    import requests

    from core.config_loader import get_key

    city = params['city']
    unit = params.get('unit', 'metric')
    api_key = str(params.get('api_key') or get_key('openweather_api_key', '')).strip()
    if not api_key:
        return {'error': 'OpenWeather API key missing. Add openweather_api_key to config/api_keys.json or config/apı keylerim.py.'}

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    full_url = f"{base_url}?q={city}&appid={api_key}&units={unit}"

    try:
        response = requests.get(full_url)
        response.raise_for_status() # HTTP hataları için hata fırlat
        data = response.json()

        if data.get('cod') == 200:
            main_data = data['main']
            weather_data = data['weather'][0]
            weather_report = {
                'city': city,
                'temperature': main_data['temp'],
                'feels_like': main_data['feels_like'],
                'humidity': main_data['humidity'],
                'description': weather_data['description'],
                'wind_speed': data['wind']['speed'],
                'unit': 'Celsius' if unit == 'metric' else 'Fahrenheit'
            }
            return weather_report
        else:
            # API'den gelen hata mesajını veya bilinen bir hatayı döndür
            return {'error': data.get('message', 'Bilinmeyen bir hata oluştu.')}

    except requests.exceptions.RequestException as e:
        return {'error': f"Ağ hatası veya API erişim sorunu: {e}"}
    except KeyError as e:
        return {'error': f"API yanıtında eksik veri veya beklenmeyen format: {e}. Yanıt: {data}" if 'data' in locals() else f"API yanıtında eksik veri: {e}"}
    except Exception as e:
        return {'error': f"Beklenmedik bir hata oluştu: {e}"}
