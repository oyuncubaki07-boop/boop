# actions/weather_report.py

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import webbrowser
from urllib.parse import quote_plus

from core.config_loader import get_key


def _speak_and_log(message: str, player=None):
    if player:
        try:
            player.write_log(f"JARVIS: {message}")
        except Exception:
            pass


def _fetch_openweather(city: str, api_key: str, unit: str = "metric") -> dict:
    params = {
        "q": city,
        "appid": api_key,
        "units": unit,
        "lang": "en",
    }
    url = "https://api.openweathermap.org/data/2.5/weather?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _format_weather(data: dict, city: str, time_label: str, unit: str) -> str:
    main = data.get("main") or {}
    weather_list = data.get("weather") or [{}]
    weather_data = weather_list[0] if weather_list else {}

    temp = main.get("temp")
    feels_like = main.get("feels_like")
    humidity = main.get("humidity")
    description = str(weather_data.get("description") or "unknown conditions").strip()
    wind_speed = (data.get("wind") or {}).get("speed")
    country = (data.get("sys") or {}).get("country")

    unit_symbol = "C" if unit == "metric" else "F"
    location = city.strip()
    if country:
        location = f"{location}, {country}"

    parts = [f"Weather for {location} ({time_label})."]
    if temp is not None:
        parts.append(f"Temperature {temp:.0f}°{unit_symbol}.")
    if feels_like is not None:
        parts.append(f"Feels like {feels_like:.0f}°{unit_symbol}.")
    if description:
        parts.append(description.capitalize() + ".")
    if humidity is not None:
        parts.append(f"Humidity {humidity}%.")
    if wind_speed is not None:
        parts.append(f"Wind {wind_speed} m/s.")

    return " ".join(parts)


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None
):
    """
    Weather report action.
    Uses OpenWeather when an API key is available, otherwise falls back to a browser search.
    """

    parameters = parameters or {}
    city = parameters.get("city")
    time = parameters.get("time")
    unit = str(parameters.get("unit", "metric") or "metric").strip().lower()

    if not city or not isinstance(city, str):
        msg = "Sir, the city is missing for the weather report."
        _speak_and_log(msg, player)
        return msg

    city = city.strip()

    if unit not in ("metric", "imperial"):
        unit = "metric"

    if not time or not isinstance(time, str):
        time_label = "today"
    else:
        time_label = time.strip() or "today"

    api_key = str(parameters.get("api_key") or get_key("openweather_api_key", "")).strip()
    if api_key:
        try:
            data = _fetch_openweather(city, api_key, unit=unit)
            if str(data.get("cod")) not in ("200", "201"):
                message = str(data.get("message") or "OpenWeather returned an error.")
                msg = f"Sir, weather service could not resolve '{city}': {message}"
                _speak_and_log(msg, player)
                return msg

            msg = _format_weather(data, city, time_label, unit)
            _speak_and_log(msg, player)

            if session_memory:
                try:
                    session_memory.set_last_search(
                        query=f"weather in {city} {time_label}",
                        response=msg
                    )
                except Exception:
                    pass

            return msg
        except Exception:
            pass

    search_query = f"weather in {city} {time_label}"
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(url)
    except Exception:
        msg = "Sir, I couldn't open the browser for the weather report."
        _speak_and_log(msg, player)
        return msg

    msg = f"Showing the weather search for {city}, {time_label}, sir."
    _speak_and_log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(
                query=search_query,
                response=msg
            )
        except Exception:
            pass

    return msg
