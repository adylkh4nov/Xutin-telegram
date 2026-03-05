"""Получение погоды через OpenWeatherMap API."""
import html
import datetime
import warnings
import requests
from datetime import datetime as dt
from config import weather_token

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

_API = 'https://api.openweathermap.org/data/2.5/weather'

_MONTHS = {
    1: 'января',   2: 'февраля',  3: 'марта',    4: 'апреля',
    5: 'мая',      6: 'июня',     7: 'июля',      8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября',   12: 'декабря',
}


def _format(data: dict) -> str:
    """Форматирует JSON-ответ OWM в HTML-строку."""
    city_name   = html.escape(data['name'])
    cur_weather = int(data['main']['temp'])
    feels_like  = int(data['main']['feels_like'])
    description = html.escape(data['weather'][0]['description'].capitalize())
    humidity    = data['main']['humidity']
    wind        = data['wind']['speed']
    sunrise     = datetime.datetime.fromtimestamp(data['sys']['sunrise'])
    sunset      = datetime.datetime.fromtimestamp(data['sys']['sunset'])
    length_day  = sunset - sunrise

    now  = dt.now()
    date = f"{now.day} {_MONTHS[now.month]} {now.year}"
    h, rem = divmod(int(length_day.total_seconds()), 3600)
    m = rem // 60

    return (
        f'🌍 <b>Погода в {city_name}</b> на {date}\n\n'
        f'🌡 Температура: <b>{cur_weather} °C</b>\n'
        f'🤔 Ощущается как: {feels_like} °C\n'
        f'☁️ {description}\n'
        f'💧 Влажность: {humidity}%\n'
        f'💨 Ветер: {wind} м/с\n'
        f'🌅 Восход: {sunrise.strftime("%H:%M")}\n'
        f'🌇 Закат:  {sunset.strftime("%H:%M")}\n'
        f'⏱ Длина дня: {h} ч {m} мин'
    )


def get_weather(city: str) -> str:
    """Погода по названию города."""
    try:
        r = requests.get(_API, params={
            'q': city, 'appid': weather_token, 'units': 'metric', 'lang': 'ru',
        }, verify=False, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return f'❌ Город "<b>{html.escape(city)}</b>" не найден.'
        return _format(data)
    except requests.exceptions.RequestException as e:
        return f'❌ Ошибка сети: {html.escape(str(e))}'
    except Exception:
        return '❌ Не удалось получить погоду. Проверьте название города.'


def get_weather_by_coords(lat: float, lon: float) -> str:
    """Погода по координатам геолокации."""
    try:
        r = requests.get(_API, params={
            'lat': lat, 'lon': lon, 'appid': weather_token, 'units': 'metric', 'lang': 'ru',
        }, verify=False, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return '❌ Не удалось определить погоду по геолокации.'
        return _format(data)
    except requests.exceptions.RequestException as e:
        return f'❌ Ошибка сети: {html.escape(str(e))}'
    except Exception:
        return '❌ Не удалось получить погоду по геолокации.'
