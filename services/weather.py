"""Получение прогноза погоды через OpenWeatherMap Forecast API."""
import html
import datetime
import warnings
import requests
from config import weather_token

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

_FORECAST_API = 'https://api.openweathermap.org/data/2.5/forecast'

_MONTHS = {
    1: 'января',   2: 'февраля',  3: 'марта',    4: 'апреля',
    5: 'мая',      6: 'июня',     7: 'июля',      8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября',   12: 'декабря',
}

_ICON_MAP = {
    '01d': '☀️', '01n': '🌙',
    '02d': '⛅', '02n': '⛅',
    '03d': '🌥', '03n': '🌥',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧', '09n': '🌧',
    '10d': '🌦', '10n': '🌧',
    '11d': '⛈', '11n': '⛈',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫', '50n': '🌫',
}


def _icon(code: str) -> str:
    return _ICON_MAP.get(code, '🌡')


def _format_forecast(data: dict, day: str) -> str:
    city_name = html.escape(data['city']['name'])

    # Определяем дату по локальному времени города
    tz_offset = datetime.timedelta(seconds=data['city']['timezone'])
    now_local  = datetime.datetime.utcnow() + tz_offset
    today      = now_local.date()
    target     = today if day == 'today' else today + datetime.timedelta(days=1)

    slots = []
    for item in data['list']:
        dt_local = datetime.datetime.utcfromtimestamp(item['dt']) + tz_offset
        if dt_local.date() == target:
            slots.append((dt_local, item))

    if not slots:
        label = 'сегодня' if day == 'today' else 'завтра'
        return f'❌ Нет данных о погоде на {label}.'

    day_label  = 'сегодня' if day == 'today' else 'завтра'
    date_label = f'{target.day} {_MONTHS[target.month]}'

    lines = [f'🌍 <b>Погода в {city_name}</b> — {day_label}, {date_label}\n']

    temps, winds, humidities = [], [], []

    for dt_local, item in slots:
        time_str = dt_local.strftime('%H:%M')
        temp     = round(item['main']['temp'])
        feels    = round(item['main']['feels_like'])
        icon     = _icon(item['weather'][0]['icon'])
        desc     = item['weather'][0]['description'].capitalize()
        wind     = item['wind']['speed']
        hum      = item['main']['humidity']

        temps.append(temp)
        winds.append(wind)
        humidities.append(hum)

        lines.append(
            f'<code>{time_str}</code>  <b>{temp:+d}°C</b> (ощущ. {feels:+d}°C)  {icon} {desc}'
        )

    min_t    = min(temps)
    max_t    = max(temps)
    max_wind = max(winds)
    avg_hum  = round(sum(humidities) / len(humidities))

    lines.append(f'\n📊 Мин: <b>{min_t:+d}°C</b>  |  Макс: <b>{max_t:+d}°C</b>')
    lines.append(f'💨 Ветер: до {max_wind:.0f} м/с  |  💧 Влажность: ~{avg_hum}%')

    return '\n'.join(lines)


def get_forecast(city: str, day: str) -> str:
    """Прогноз по названию города."""
    try:
        r = requests.get(_FORECAST_API, params={
            'q': city, 'appid': weather_token,
            'units': 'metric', 'lang': 'ru', 'cnt': 40,
        }, verify=False, timeout=10)
        data = r.json()
        if str(data.get('cod')) != '200':
            return f'❌ Город "<b>{html.escape(city)}</b>" не найден.'
        return _format_forecast(data, day)
    except requests.exceptions.RequestException as e:
        return f'❌ Ошибка сети: {html.escape(str(e))}'
    except Exception:
        return '❌ Не удалось получить прогноз. Проверьте название города.'


def get_forecast_by_coords(lat: float, lon: float, day: str) -> str:
    """Прогноз по координатам геолокации."""
    try:
        r = requests.get(_FORECAST_API, params={
            'lat': lat, 'lon': lon, 'appid': weather_token,
            'units': 'metric', 'lang': 'ru', 'cnt': 40,
        }, verify=False, timeout=10)
        data = r.json()
        if str(data.get('cod')) != '200':
            return '❌ Не удалось определить погоду по геолокации.'
        return _format_forecast(data, day)
    except requests.exceptions.RequestException as e:
        return f'❌ Ошибка сети: {html.escape(str(e))}'
    except Exception:
        return '❌ Не удалось получить прогноз по геолокации.'
